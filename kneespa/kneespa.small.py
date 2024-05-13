#!/usr/bin/env python
# coding: utf-8

# adc https://github.com/adafruit/Adafruit_Blinka/blob/master/examples/analog_in.py

from time import sleep
import os
from datetime import datetime, timedelta
import sys
import time
import serial
from subprocess import Popen, PIPE

import RPi.GPIO as GPIO


EXTRAFORWARD = 27
EXTRABACKWARD = 22
EXTRAENABLE = 17

import AProtocols
import BProtocols
import CProtocols

import comm

import config

#these are for the PyQT5. There is overlap and should be cleaned up.
#pyrcc5 resources.qrc -o resources_rc.py

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QTime, QTimer, QEvent, QDateTime, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont
from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDesktopWidget, QTableWidgetItem

import glob


os.chdir('/home/pi/kneespa')

DEGREES = u'\u00b0'

class PlayMP4(QObject):
    finished = pyqtSignal()
    def __init__(self, _win, _videoList):
      super(PlayMP4, self).__init__()
      print('init player')

      self.win = _win
      self.videoList = _videoList
      self.playing = True

 
    def nextVideo(self, path):
       self.videoPath = path
       self.playing = True

    def stop(self):
       try:
          process = Popen(['killall', 'omxplayer.bin'], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
          stdout, stderr = process.communicate()
          print(stdout, stderr)
          process = Popen(['killall', 'feh'], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
          stdout, stderr = process.communicate()
          print(stdout, stderr)
          self.playing = False
       except Exception as e:
          print(str(e))
          print('omxplayer error')

    def done(self):
        print('done playing')
        self.playing = False

    def run(self):
       try:
         process = Popen(['feh', '-g', '580x436+26+475', '-B', 'white', '-x', '-D', '45', '--scale-down', '/home/pi/Scripts'], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
         stdout, stderr = process.communicate()
         print(stdout, stderr)
       except Exception as e:
         print(str(e))
         print('feh error')

       while self.playing:
         for path in self.videoList:
           print('playing ' + path + ' ' + self.win)
           try:
              print('omxplayer start ', path)
#omxplayer -o local --win "-40 -40 1280 720" --adev hdmi ../Videos/WhySittingDown.mp4
#              process = Popen(['omxplayer', '-o', 'hdmi', '-t', 'on', '--win' ,'-40 -40 1280 720', path], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
#              process = Popen(['omxplayer', '-o', 'hdmi', '-t', 'on', '--adev', 'hdmi', '--win' ,self.win, path], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
              process = Popen(['omxplayer', '-o', 'hdmi', '-t', 'on', '--win' ,self.win, path], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
              stdout, stderr = process.communicate()
              print(stdout, stderr)

              process = Popen(['feh' '-g', '640x480+50+500', '-x', '-D', '2', '--scale-down', '/home/pi/Scripts', '-o', 'hdmi', '-t', 'on', '--win' ,self.win, path], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
              stdout, stderr = process.communicate()
              print(stdout, stderr)
           except Exception as e:
              print(str(e))
              print('omxplayer error')
              self.playing = False
         sleep(0.1)

#         sleep(.25)


'''
class xPlayMP4(QObject):
   finished = pyqtSignal()

   def __init__(self, _ui, parent=None):
      super(PlayMP4, self).__init__()
      print('init player')
      self.ui = _ui

      self.videoPath = ''
      for file in glob.glob("/home/pi/*"):
            if('Video' in file.lower()):
              self.videoPath = file

      if(self.videoPath == ''):
          for file in glob.glob("/media/pi/*"):
            if('video' in file.lower()):
              self.videoPath = file
      
      print(self.videoPath)
      self.isRunning = True

      self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
      self.mediaPlayer.positionChanged.connect(self.position_changed)
      self.mediaPlayer.durationChanged.connect(self.duration_changed)
 
   def mediastate_changed(self, state):
        print(self.mediaPlayer.state(), QMediaPlayer.PlayingState)
 
   def position_changed(self, position):
        print('self.slider.setValue {}'.format(position))
        self.ui.positionLbl.setText(str(position))
 
   def duration_changed(self, duration):
        print('self.slider.setRange {}'.format(duration))
  
   def handle_errors(self):
        print("Error: " + self.mediaPlayer.errorString())
 
   def stop(self):
      self.isRunning = False

   def runVideo(self):
      self.playVideo()
      while True:
        print('true loop')
        self.mediaPlayer.play()
        print(self.mediaPlayer.state(), QMediaPlayer.PlayingState)
        if(not self.xisRunning):
          print('stopping loop')
          break
        time.sleep(.1)

   def playVideo(self):
      print('playing')

      fileName = '/home/pi/Videos/WhySittingDown.mp4'
      url = QtCore.QUrl.fromLocalFile(fileName)
#        url = QtCore.QUrl('WhySittingDown.mp4')
#      self.mediaPlayer.setMedia(QtMultimedia.QMediaContent(url))
 #       self.mediaPlayer.setMedia('WhySittingDown.mp4')
 #     self.mediaPlayer.play()



class xArduino(QtCore.QRunnable):#QObject):
   finished = pyqtSignal()
   progress = pyqtSignal(int)
   doneEmit = pyqtSignal()
   readyToGoEmit = pyqtSignal()
   positionEmit = pyqtSignal(str)
   pressureEmit = pyqtSignal(str)

   def __init__(self, parent=None):
      super(Arduino, self).__init__()
      print('init com')

   def run(self):

      print('startSerial')
      self.doneEmit.emit()

      try:
        self.serialCOM1 = serial.Serial('/dev/ttyS0', 115200, timeout=10, write_timeout=1)
        time.sleep(2)
        print(self.serialCOM1)
        self.connected = True
      except Exception as ex:
         print(str(ex))

      print('Inited')

      self.readFromCOM1(self.serialCOM1)

   def handleCOM1(self, ser, data):

       tokens = data.split('|')
       print(tokens)
       if(tokens[0] == 'DONE'):
          print('self.doneEmit.emit()')
          self.doneEmit.emit()
       if(tokens[0] == 'P'):
          self.positionEmit.emit(tokens[1])
       if(tokens[0] == 'Ready to Go'):
          self.readyToGoEmit.emit()

   def readFromCOM1(self, ser):
      global startRun
      while True:
        try:
          reading = ser.readline().decode().strip()
#          print(reading)
          if(len(reading) > 0):
            self.handleCOM1(ser, reading)
        except Exception as ex:
          print(str(ex))

        time.sleep(0.1)


   def send(self, command):

     command += '\n'
     print('cmd {}'.format(command.strip()))
     self.serialCOM1.write(command.encode())                #transmit data serially 
     self.serialCOM1.flush()
'''

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
    doneEmit = pyqtSignal()

'''
     degrees vs distance
      0 0" extended (will hold here and return)
      5 5" extended (will hold here and return)
     10 4" extended (will hold here and return)
     15 3"
     20 2"
     25 1"
     30 Full retract
'''
DEGREES0 = 0
DEGREES5 = 5
DEGREES10 = 10



#the kneespa.ui is the UI definition file. It is created via the QT Designer tool
Ui_MainWindow, QtBaseClass = uic.loadUiType('kneespa.ui')

#this is the main program class which is the UI. It is driven by PyQT5 processes and interacts with the pump.ui file for display

class KeyboardWidget(QWidget):

    def keyPressEvent(self, keyEvent):
        print(keyEvent.text())

class MyApp(QMainWindow):
    def rebootApp(self):
       GPIO.cleanup()           # clean up GPIO on normal exit
       os.system("sudo shutdown -r now")
       os._exit(1)

    def shutdownApp(self):
       GPIO.cleanup()           # clean up GPIO on normal exit
       os.system("sudo shutdown -h now")
       os._exit(1)

    def exitApp(self):
       GPIO.cleanup()           # clean up GPIO on normal exit
       os._exit(1)

    def keyPressEvent(self, event):
        super(Example, self).keyPressEvent(event)
        print('keypress')

    def onKey(self, event):
        # keyPressEvent defined in child
        print('pressed from myDialog: ', event.key())

    def eventFilter(self, obj, event):
#        print(event.type())
        if event.type() == QEvent.MouseButtonPress:
           if obj == self.ui.buttonClearBtn:
              pass
#             print('clear btn - pressed')


        if event.type() == QEvent.MouseButtonRelease:
           if obj == self.ui.buttonClearBtn:
             pass
#             print('clear btn - release')

        return super(QMainWindow, self).eventFilter(obj, event)

    def setToDistance(self, inches, actuator, factor):
      position = int(inches * (factor / 6.0))
      print(' positioned to {} in. {} pos {}'.format(inches, position, actuator))

      if(actuator == self.actuatorC):
        command = 'K{}{}'.format(actuator, position)
      else:
        command = 'A{}{}'.format(actuator, position)
      self.arduino.send(command)
      print('cmd {}'.format(command.strip()))

#      while(not self.I2Cstatus):
#        time.sleep(0.1)

      self.I2Cstatus = False
      print('end')

    def getserial(self):
  # Extract serial from cpuinfo file
       cpuserial = "00000000"
       try:
         f = open('/proc/cpuinfo','r')
         for line in f:
           if line[0:6]=='Serial':
             cpuserial = line[18:26]
         f.close()
       except:
         cpuserial = "ERROR   "
       print(cpuserial.upper())
       return cpuserial.upper()

    def __init__(self,):
        super(MyApp, self).__init__()

        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)
#        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint) 

        qtRectangle = self.frameGeometry()
        farX = QDesktopWidget().screenGeometry().topRight().x()-50
        newX = farX - qtRectangle.topRight().x()
        self.move(newX, qtRectangle.topLeft().y()+50)
        print(qtRectangle.bottomLeft().y())

        self.goTimer = QTimer(self)
        self.goTimer.timeout.connect(self.blinkGo)
        self.blinkingGo = True

        self.sliderGoBtn = None
        self.sliderTimer = QTimer(self)
        self.sliderTimer.timeout.connect(lambda:self.blinkSlider(self.sliderGoBtn))
        self.sliderGo = True

        self.statusTimer = QTimer(self)
        self.statusTimer.timeout.connect(self.clearStatus)

        self.ui.exitBtn.hide()
        if(os.path.exists("debug.txt")):
          self.ui.exitBtn.show()
          self.show()
        else:
           self.showMaximized()
           self.showFullScreen()

        self.unlocked = False
        self.ui.unlockGroup.show()
        self.unlockCode = ''

        self.ui.exitBtn.clicked.connect(self.shutdown)
        self.ui.shutdownBtn.clicked.connect(self.shutdown)

        self.numberButtons = []
        self.numberButtons.append(self.ui.button1Btn)
        self.numberButtons.append(self.ui.button2Btn)
        self.numberButtons.append(self.ui.button3Btn)
        self.numberButtons.append(self.ui.button4Btn)
        self.numberButtons.append(self.ui.button5Btn)
        self.numberButtons.append(self.ui.button6Btn)
        self.numberButtons.append(self.ui.button7Btn)
        self.numberButtons.append(self.ui.button8Btn)
        self.numberButtons.append(self.ui.button9Btn)
        self.numberButtons.append(self.ui.button0Btn)

        self.letterButtons = []
        self.letterButtons.append(self.ui.buttonABtn)
        self.letterButtons.append(self.ui.buttonBBtn)
        self.letterButtons.append(self.ui.buttonCBtn)
        self.letterButtons.append(self.ui.buttonDBtn)

        self.firstLetter = ''

        self.task = None
#        self.resetBtns(True)

        self.I2Cstatus = 0

        self.ui.goBackBtn.clicked.connect(self.goBack)
        self.ui.setupBtn.clicked.connect(self.gotoSetup)
        self.ui.setupBtn.hide()

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].clicked.connect(self.letterBtn)
          self.letterButtons[i].setEnabled(False)
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].clicked.connect(self.numberBtn)
          self.numberButtons[i].setEnabled(True)
          self.numberButtons[i].setStyleSheet("background-color: blue;color:white")

#        self.ui.button1Btn.clicked.connect(self.numberBtn)

        self.ui.buttonClearBtn.clicked.connect(self.btnsClear)
        self.ui.buttonGoBtn.clicked.connect(self.btnsGo)

        self.ui.buttonClearBtn.installEventFilter(self)

        self.degreeList = {0:5, -5:4, -10:3, -15:2, -20:1, -25:0, -30:0}
        self.CdegreeList = {-20:0, -10:0.5, 0:1, 10:1.5, 20:2}

        self.ui.axialPressureSlider.valueChanged.connect(self.axialPressureChanged)
        self.ui.horizontalFlexionSlider.valueChanged.connect(self.horizontalFlexionChanged)
        self.ui.leftLatFlexionSlider.valueChanged.connect(self.leftLatFlexionchanged)
        self.ui.rightLatFlexionSlider.valueChanged.connect(self.rightLatFlexionchanged)
        self.ui.cyclesSlider.valueChanged.connect(self.cyclesChanged)
        self.ui.cyclesSlider_Lat.valueChanged.connect(self.cyclesLatChanged)

        self.ui.forwardAxialFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorA, 0.065, '04'))
        self.ui.reverseAxialFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorA, 0.065, '04'))
        self.ui.forwardFastAxialFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorA, 0.065, '20'))
        self.ui.reverseFastAxialFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorA, 0.065, '20'))
        self.ui.resetAxialFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(self.actuatorA))
        self.axialFlexionPosition = 0.0
        self.axialFlexionClicks = 0
        self.ui.axialFlexionPositionSlider.valueChanged.connect(self.axialFlexionPositionChanged)
        self.ui.axialFlexionPositionLbl.setText('0 in')
        self.ui.axialFlexionPositionBtn.clicked.connect(lambda: self.movePositionFlexionBtn(self.actuatorA))
        self.ui.axialFlexionPositionStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorA))
        self.ui.axialFlexionPressureSlider.valueChanged.connect(self.axialFlexionPressureChanged)
        self.ui.axialFlexionPressureLbl.setText('0 lb')
        self.ui.axialFlexionPressureBtn.clicked.connect(self.axialFlexionPressureBtn)
        self.ui.axialFlexionPressureStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorA))


        self.ui.forwardHorizontalFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorB, 0.065, '04'))
        self.ui.reverseHorizontalFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorB, 0.065, '04'))
        self.ui.forwardFastHorizontalFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorB, 0.065, '20'))
        self.ui.reverseFastHorizontalFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorB, 0.065, '20'))
        self.ui.resetHorizontalFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(self.actuatorB))
        self.horizontalFlexionPosition = 0.0
        self.horizontalFlexionClicks = 0
        self.ui.horizontalPositionFlexionSlider.valueChanged.connect(self.horizontalPositionFlexionChanged)
        self.ui.horizontalPositionFlexionLbl.setText('0' + DEGREES)
        self.ui.horizontalPositionFlexionBtn.clicked.connect(lambda: self.movePositionFlexionBtn(self.actuatorB))
        self.ui.horizontalPositionFlexionStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorB))

        self.ui.forwardLateralFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorC, 0.0328, '04'))
        self.ui.reverseLateralFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorC, 0.0328, '04'))
        self.ui.forwardFastLateralFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorC, 0.0328, '20'))
        self.ui.reverseFastLateralFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorC, 0.0328, '20'))
        self.ui.resetLateralFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(self.actuatorC))
        self.lateralFlexionPosition = 0.0
        self.lateralFlexionClicks = 0
        self.ui.lateralFlexionPositionSlider.valueChanged.connect(self.lateralFlexionPositionChanged)
        self.ui.lateralFlexionPositionLbl.setText('0' + DEGREES)
        self.ui.lateralFlexionPositionBtn.clicked.connect(lambda: self.movePositionFlexionBtn(self.actuatorC))
        self.ui.lateralFlexionPositionStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorC))

        self.ui.axialFlexionPressureSlider.sliderMoved.connect(self.axialFlexionPressureSliderMoved)
        self.ui.horizontalPositionFlexionSlider.sliderMoved.connect(self.horizontalPositionFlexionSliderMoved)
        self.ui.lateralFlexionPositionSlider.sliderMoved.connect(self.lateralFlexionSliderMoved)

        self.ui.forwardExtraBtn.clicked.connect(self.forwardExtraBtnClicked)
        self.ui.reverseExtraBtn.clicked.connect(self.reverseExtraBtnClicked)
        self.ui.forwardFastExtraBtn.clicked.connect(self.forwardFastExtraBtnClicked)
        self.ui.reverseFastExtraBtn.clicked.connect(self.reverseFastExtraBtnClicked)
        self.ui.resetExtraBtn.clicked.connect(self.resetExtraBtnClicked)

        self.ui.measureWeightBtn.clicked.connect(self.measureWeightBtnClicked)

        self.ui.resetArduinoBtn.clicked.connect(self.resetArduinoBtn)

        self.ui.axialFlexionPositionTxt.hide()
        self.ui.horizontalFlexionPositionTxt.hide()
        self.ui.lateralFlexionPositionTxt.hide()
        self.ui.extraPositionTxt.hide()

        self.config = config.Configuration()
        self.config.getConfig()

        self.actuatorA = 12
#        if(self.getserial() == '09DC25B8'):
#          self.actuatorA = 13
#          self.config.AFactor = self.config.BFactor
        self.actuatorB = 13
        self.actuatorC = 14

        if(self.config.unlock == ''):
           self.unlocked = True
           self.ui.unlockGroup.hide()
           self.resetBtns(True)
           for i in range(len(self.letterButtons)):
             self.letterButtons[i].setEnabled(True)
             self.letterButtons[i].setStyleSheet("background-color: grey;color:white")
           self.ui.setupBtn.show()

        self.signals = WorkerSignals()


        fileTime = datetime.fromtimestamp(os.path.getmtime(__file__))
        version = 'V-{}'.format(fileTime.strftime("%m.%d.%Y"))
        self.ui.versionLbl.setText(version)

        self.threadpool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # Step 2: Create a QThread object


        self.worker = None
        self.ui.stackedWidget.setCurrentIndex(0)

        '''
      # Step 2: Create a QThread object
        self.thread = QThread()
      # Step 3: Create a worker object
        self.arduino = Arduino()
      # Step 4: Move worker to the thread
        self.arduino.moveToThread(self.thread)
      # Step 5: Connect signals and slots
        self.thread.started.connect(self.arduino.run)
        self.arduino.finished.connect(self.thread.quit)
        self.arduino.finished.connect(self.thread.deleteLater)
      # Step 6: Start the thread
        self.thread.start()

        self.arduino.readyToGoEmit.connect(self.setDone)#readyToGo)
        self.arduino.doneEmit.connect(self.setDone)
        '''

      # 1 - create Worker and Thread inside the Form
        self.arduino = comm.Arduino()  # no parent!
        self.thread = QThread()  # no parent!

       # 2 - Connect Worker`s Signals to Form method slots to post data.
        self.arduino.doneEmit.connect(self.setDone)

       # 3 - Move the Worker object to the Thread object
        self.arduino.moveToThread(self.thread)

       # 4 - Connect Worker Signals to the Thread slots
        self.arduino.finished.connect(self.thread.quit)
        self.arduino.readyToGoEmit.connect(self.readyToGo)

       # 5 - Connect Thread started signal to Worker operational slot method
        self.thread.started.connect(self.arduino.run)

       # * - Thread finished signal will close the app if you want!
       #self.thread.finished.connect(app.exit)

        self.arduino.positionEmit.connect(self.readPosition)
        self.arduino.pressureEmit.connect(self.readPressure)
       # 6 - Start the thread
        self.thread.start()


        self.videoPath = ''
        self.videoList = []
        for file in glob.glob("/home/pi/Videos/*.mp4"):
          self.videoList.append(file)
        print(self.videoList)

        self.scriptList = []
        for file in glob.glob("/home/pi/Scripts/*.mp4"):
          self.scriptList.append(file)

        print(self.scriptList)

        self.playVideoMP4 = PlayMP4('-40 -40 800 450', self.videoList)
        self.playingVideoThread = QThread()  # no parent!
#        self.playVideoMP4.doneEmit.connect(self.setDone)
        self.playVideoMP4.moveToThread(self.playingVideoThread)
        self.playVideoMP4.finished.connect(self.playingVideoThread.quit)
        self.playingVideoThread.started.connect(self.playVideoMP4.run)
       #self.playingVideoThread.finished.connect(app.exit)
       # 6 - Start the thread
        self.playingVideoThread.start()

        '''
        self.playScriptMP4 = PlayMP4('50 500 620 909', self.scriptList)
        self.playingScriptThread = QThread()  # no parent!
#        self.playScriptMP4.doneEmit.connect(self.setDone)
        self.playScriptMP4.moveToThread(self.playingScriptThread)
        self.playScriptMP4.finished.connect(self.playingScriptThread.quit)
        self.playingScriptThread.started.connect(self.playScriptMP4.run)
       #self.playingScriptThread.finished.connect(app.exit)
       # 6 - Start the thread
        self.playingScriptThread.start()
        '''
        self.setupGPIO()

        QTimer.singleShot(3000, self.sendCalibbrarion)
        QTimer.singleShot(2000, lambda:self.playVideoMP4.done())
        self.arduino.displayWeightEmit.connect(self.displayWeight)

    def sendCalibbrarion(self):
        print('sendCalibbrarion')
        self.arduino.send('L0{}'.format(self.config.calibration))

    def resetArduinoBtn(self):
        self.arduino.send('Y')

        self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
        self.ui.horizontalPositionFlexionSlider.setValue(-20)
        self.ui.horizontalPositionFlexionLbl.setText('-20' + DEGREES)

        self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
        self.ui.axialFlexionPositionSlider.setValue(0)
        self.ui.axialFlexionPositionLbl.setText('0 in')

        self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
        self.ui.lateralFlexionPositionSlider.setValue(0)
        self.ui.lateralFlexionPositionLbl.setText('0' + DEGREES)

    def readPressure(self, pressure):
        self.ui.axialFlexionPressureLbl.setText(pressure + ' lb')

    def axialFlexionPressureSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.axialFlexionPressureSlider.setValue(rounded)
        self.ui.axialFlexionPressureLbl.setText(str(rounded) + ' lb')

    def horizontalPositionFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.horizontalPositionFlexionSlider.setValue(rounded)
        self.ui.horizontalPositionFlexionLbl.setText(str(rounded) + DEGREES)

    def lateralFlexionSliderMoved(self, event):
        rounded = int(round(event/10)*10)
        self.ui.lateralFlexionPositionSlider.setValue(rounded)
        self.ui.lateralFlexionPositionLbl.setText(str(rounded) + DEGREES)

    def displayWeight(self, weight):
        print('displayWeight')
        self.ui.measuredWeightLbl.setText(weight + ' lb')

    def measureWeightBtnClicked(self):
        print('measureWeight')
        self.arduino.send('L4')

    def readyToGo(self):
        print('readyToGo')
        self.ui.statusLbl.setText('Ready to Start')
        self.statusTimer.start(2000)

    def readPosition(self, position, steps, pressure, actuator):
        print('readPosition', position)
        if(actuator == self.actuatorB):
          inches = (position * 6) / self.config.BFactor
          inches = round(inches * 2.0) / 2.0
          print('inches ', inches)
          degrees = int(-(25 - (inches / 5) * 25))
          print('degrees ', degrees)
          self.ui.horizontalPositionFlexionSlider.setValue(degrees)
          self.ui.horizontalPositionFlexionLbl.setText('{}{}'.format(degrees, DEGREES))
          return
        if(actuator == self.actuatorA):
          inches = (position * 6) / self.config.AFactor
          inches = round(inches * 2.0) / 2.0
          print('inches ', inches)
          self.ui.axialFlexionPositionSlider.setValue(inches)
          self.ui.axialFlexionPositionLbl.setText('{:.1f} in.'.format(inches))
          self.ui.axialFlexionPressureLbl.setText(pressure + ' lb')
          return
        if(actuator == self.actuatorC):
          inches = steps / (self.config.CFactor / 6)
          inches = round(inches * 2.0) / 2.0
          print('inches ', inches)
          degrees = int((inches * 20) - 20)
          print('degrees ', degrees)
          self.ui.lateralFlexionPositionSlider.setValue(degrees)
          self.ui.lateralFlexionPositionLbl.setText('{}{}'.format(degrees, DEGREES))
          return

    def setDone(self):
        print('self.I2Cstatus = True')
        self.I2Cstatus = True
        if(self.worker):
          self.worker.I2CStatus()

    def forwardExtraBtnClicked(self):
        self.arduino.send('F+')
        GPIO.output(EXTRABACKWARD, GPIO.LOW)
        GPIO.output(EXTRAFORWARD, GPIO.HIGH)

    def reverseExtraBtnClicked(self):
        self.arduino.send('F-')
        GPIO.output(EXTRAFORWARD, GPIO.LOW)
        GPIO.output(EXTRABACKWARD, GPIO.HIGH)

    def forwardFastExtraBtnClicked(self):
        self.arduino.send('FF')
        GPIO.output(EXTRABACKWARD, GPIO.LOW)
        GPIO.output(EXTRAFORWARD, GPIO.HIGH)

    def reverseFastExtraBtnClicked(self):
        self.arduino.send('FR')
        GPIO.output(EXTRAFORWARD, GPIO.LOW)
        GPIO.output(EXTRABACKWARD, GPIO.HIGH)

    def resetExtraBtnClicked(self):
        self.arduino.send('F0')
        GPIO.output(EXTRAFORWARD, GPIO.LOW)
        GPIO.output(EXTRABACKWARD, GPIO.LOW)



    def forwardFlexionBtn(self, actuator, step, speedFactor):
        print(speedFactor)

        if(self.lateralFlexionPosition >= 6.0):
          self.lateralFlexionPosition = 6.0
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
          return

        if(actuator == self.actuatorA):
          if(self.axialFlexionPosition >= 60.0):
            self.axialFlexionPosition = 6.0
            self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
            return
        if(actuator == self.actuatorB):
          if(self.horizontalFlexionPosition >= 6.0):
            self.horizontalFlexionPosition = 6.0
            self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
            return
        if(actuator == self.actuatorC):
          if(self.lateralFlexionPosition >= 6.0):
            self.lateralFlexionPosition = 6.0
            self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
            return



        if(actuator == self.actuatorB):
          command = 'E{}+{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.horizontalFlexionClicks += 1
          self.horizontalFlexionPosition += step
          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
          return
        if(actuator == self.actuatorA):
          command = 'E{}+{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.axialFlexionClicks += 1
          print(self.axialFlexionClicks)
          self.axialFlexionPosition += step
          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
          return
        if(actuator == self.actuatorC):
          command = 'C{}+{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.lateralFlexionClicks += 1
          print(self.lateralFlexionClicks)
          self.lateralFlexionPosition += step
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
          return

    def reverseFlexionBtn(self, actuator, step, speedFactor):
        print(speedFactor)

        '''
        if(actuator == self.actuatorA):
          if(self.axialFlexionPosition <= 0.0):
            self.axialFlexionPosition = 0.0
            self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
#            return
        if(actuator == self.actuatorB):
          if(self.horizontalFlexionPosition <= 0.0):
            self.horizontalFlexionPosition = 0.0
            self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
            return
        if(actuator == self.actuatorC):
          if(self.lateralFlexionPosition <= 0.0):
            self.lateralFlexionPosition = 0.0
            self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
            return
        '''

        if(actuator == self.actuatorA):
          command = 'E{}-{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.axialFlexionClicks -= 1
          print(self.axialFlexionClicks)
          self.axialFlexionPosition -= step
          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
        if(actuator == self.actuatorB):
          command = 'E{}-{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.horizontalFlexionClicks -= 1
          self.horizontalFlexionPosition -= step
          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
        if(actuator == self.actuatorC):
          command = 'C{}-{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.lateralFlexionClicks -= 1
          print(self.lateralFlexionClicks)
          self.lateralFlexionPosition += step
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))

    def resetFlexionBtn(self, actuator):

        print(actuator)


        if(actuator == self.actuatorB):
          command = 'R{}'.format(actuator)
          self.arduino.send(command)                #transmit data serially 
          self.horizontalFlexionClicks = 0
          self.horizontalFlexionPosition = 0.0
          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
          self.ui.horizontalPositionFlexionSlider.setValue(-20)
          self.ui.horizontalPositionFlexionLbl.setText('-20' + DEGREES)
          return
        if(actuator == self.actuatorA):
          command = 'R{}'.format(actuator)
          self.arduino.send(command)                #transmit data serially 
          self.axialFlexionClicks = 0
          print(self.axialFlexionClicks)
          self.axialFlexionPosition = 0.0
          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
          self.ui.axialFlexionPositionSlider.setValue(0)
          self.ui.axialFlexionPositionLbl.setText('0 in')
          self.ui.axialFlexionPressureSlider.setValue(0)
          self.ui.axialFlexionPressureLbl.setText('0 lb')
          return
        if(actuator == self.actuatorC):
          command = 'R{}'.format(actuator)
          self.arduino.send(command)                #transmit data serially 
          self.lateralFlexionClicks = 0
          print(self.lateralFlexionClicks)
          self.lateralFlexionPosition = 0.0
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
          self.ui.lateralFlexionPositionSlider.setValue(0)
          self.ui.lateralFlexionPositionLbl.setText('0' + DEGREES)
          return

    def protocolCompleted(self):
        print('protocolCompleted')
        self.resetBtns(True)
        self.ui.statusLbl.setText('Protocol Completed')

    def clearStatus(self):
        self.ui.statusLbl.setText('')
        self.ui.programLbl.setText('')
        self.statusTimer.stop()

    def blinkGo(self):
        if(self.blinkingGo):
          self.ui.buttonGoBtn.setStyleSheet("background-color:#78909C")#green;color:78909C")
        else:
          self.ui.buttonGoBtn.setStyleSheet("background-color:green;")
        self.blinkingGo = not self.blinkingGo


    def btnsGo(self):
        print('btnsGo')
        if(not self.unlocked):
           self.blinkingGo = True
           self.blinkGo()
           print(self.config.unlock, self.unlockCode)
           if(self.config.unlock == self.unlockCode):
             self.unlocked = True
             self.ui.unlockGroup.hide()
             self.btnsClear()
             self.resetBtns(True)
             self.ui.setupBtn.show()
           else:
             self.unlockCode = ''
             self.ui.unlockKeyLbl.setText('')

           return

        self.blinkingGo = True
        self.blinkGo()

        QApplication.processEvents()


        self.ui.axialPressureSlider.setEnabled(False)
        self.ui.horizontalFlexionSlider.setEnabled(False)
#        self.ui.leftLatFlexionSlider.setEnabled(False)
#        self.ui.rightLatFlexionSlider.setEnabled(False)
        self.ui.cyclesSlider.setEnabled(False)
 

        self.protocolValue += str(self.buttonValue)
        print('protocol {}'.format(self.protocolValue))


        print(self.protocolValue[0])
        if(self.protocolValue[0] == 'A'):
          self.worker = AProtocols.Protocols(self.config.AFactor, self.protocolValue, self.axialPressure, self.cycles, self.arduino)

        if(self.protocolValue[0] == 'B'):
          self.worker = BProtocols.Protocols(self.config.BFactor, self.protocolValue, self.horizontalDegrees, self.cycles, self.arduino)

        if(self.protocolValue[0] == 'C'):
          self.worker = CProtocols.Protocols(self.config.CFactor, self.protocolValue, self.leftLatAngle, self.rightLatAngle, self.cycles, self.arduino)

        self.worker.signals.finished.connect(self.protocolCompleted)
        self.worker.signals.progress.connect(self.protocolProgress)

        self.threadpool.start(self.worker)

        self.blinkGo()
        self.goTimer.start(500)

    def protocolProgress(self, status):
        self.ui.statusLbl.setText(str(status))

    def blinkSlider(self, go):
        print('self.sliderGo', self.sliderGo)
        if(self.sliderGo):
          self.ui.horizontalPositionFlexionBtn.setStyleSheet("background-color:#78909C")#green;color:78909C")
        else:
          self.ui.horizontalPositionFlexionBtn.setStyleSheet("background-color:green;")
        self.sliderGo = not self.sliderGo

        self.ui.horizontalPositionFlexionBtn.update()

    def stopPositionFlexionBtn(self, actuator):
        self.arduino.send('X{}'.format(actuator))

    def movePositionFlexionBtn(self, actuator):
        if(actuator == self.actuatorB):
          print('actuator', actuator)
          horizontalDegrees = self.ui.horizontalPositionFlexionSlider.value()
          inches = abs((horizontalDegrees + 25) / 5)
          print('inches ', inches)
          self.setToDistance(inches, actuator, self.config.BFactor)
          return
        if(actuator == self.actuatorA):
          inches = self.ui.axialFlexionPositionSlider.value()
          self.setToDistance(inches, actuator, self.config.AFactor)
          return
        if(actuator == self.actuatorC):
          horizontalDegrees = self.ui.lateralFlexionPositionSlider.value()
          inches = abs((horizontalDegrees + 20) / 20)
          print('inches ', inches)
          self.setToDistance(inches, actuator, self.config.CFactor)
          return

    def axialFlexionPositionChanged(self):
        inches = self.ui.axialFlexionPositionSlider.value()
        self.ui.axialFlexionPositionLbl.setText(str(inches) + ' in')

    def axialFlexionPressureChanged(self):
        pounds = self.ui.axialFlexionPressureSlider.value()
        self.ui.axialFlexionPressureLbl.setText(str(pounds) + ' lb')
 
    def axialFlexionPressureBtn(self):
        print('axialFlexionPressureBtn')
        pressure = self.ui.axialFlexionPressureSlider.value()
        print(pressure)
        command = 'P{}'.format(pressure)
        self.arduino.send(command)
        print('cmd {}'.format(command.strip()))

    def horizontalPositionFlexionChanged(self):
        horizontalDegrees = self.ui.horizontalPositionFlexionSlider.value()
        if((horizontalDegrees % 5) != 0):
           return
        self.ui.horizontalPositionFlexionLbl.setText(str(horizontalDegrees) + DEGREES)
	
    def lateralFlexionPositionChanged(self):
        horizontalDegrees = self.ui.lateralFlexionPositionSlider.value()
        if((horizontalDegrees % 5) != 0):
           return
        self.ui.lateralFlexionPositionLbl.setText(str(horizontalDegrees) + DEGREES)

    def axialPressureChanged(self):
        self.axialPressure = self.ui.axialPressureSlider.value()
        self.ui.axialPressureLbl.setText(str(self.axialPressure) + "#")
	
    def horizontalFlexionChanged(self):
        self.horizontalDegrees = self.ui.horizontalFlexionSlider.value()
        self.ui.horizontalFlexionLbl.setText(str(self.horizontalDegrees) + DEGREES)
	
    def leftLatFlexionchanged(self):
        self.leftLatAngle = self.ui.leftLatFlexionSlider.value() #20-
        self.ui.leftLatFlexionLbl.setText(str(self.leftLatAngle) + DEGREES)
	
    def rightLatFlexionchanged(self):
        self.rightLatAngle = self.ui.rightLatFlexionSlider.value()
        self.ui.rightLatFlexionLbl.setText(str(self.rightLatAngle) + DEGREES)
	
    def cyclesChanged(self):
        self.cycles = self.ui.cyclesSlider.value()
        self.ui.cyclesLbl.setText(str(self.cycles))

    def cyclesLatChanged(self):
        self.cycles = self.ui.cyclesSlider_Lat.value()
        self.ui.cyclesLbl_Lat.setText(str(self.cycles))
	
    def btnsClear(self):		#need to reset all acuators
        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(True)
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")


        if(not self.unlocked):
           self.unlockCode = ''
           self.ui.unlockKeyLbl.setText('')

           for i in range(len(self.numberButtons)):
             self.numberButtons[i].setStyleSheet("background-color: blue;color:white")

           return

        self.resetBtns(True)
        self.firstLetter = ''

        if(self.worker != None):
           self.worker.stop()

        self.ui.statusLbl.setText('Protocol Stopped')
        self.statusTimer.start(3000)

    def resetBtns(self, letters):
        self.goTimer.stop()
        if(self.task):
           self.task.stop()
           print('task stop')

        self.buttonValue = 0
        self.protocol = ''
#        self.protocolValue = ''

        self.axialPressure = 0
        self.horizontalDegrees = 0
        self.leftLatAngle = 0
        self.rightLatAngle = 0
        self.cycles = 0

        self.ui.statusLbl.setText('')
        self.ui.programLbl.setText('')

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(False)
          self.numberButtons[i].setStyleSheet("background-color: blue;color:white")

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")

        self.senderNumber = self.ui.button0Btn

        self.ui.buttonGoBtn.setEnabled(False)
        self.ui.buttonGoBtn.setStyleSheet("background-color: green;")


        self.ui.cyclesSlider.setValue(0)
        self.ui.cyclesLbl.setText('0')
        self.ui.cyclesSlider.setEnabled(True)

        self.ui.cyclesSlider_Lat.setValue(0)
        self.ui.cyclesLbl_Lat.setText('0')


        self.ui.axialPressureSlider.setValue(0)
        self.ui.axialPressureLbl.setText('0#')
        self.ui.axialPressureSlider.setEnabled(True)
        titleRect = QtCore.QRect(self.ui.axialPressureTitleLbl.x(), self.ui.axialPressureTitleLbl.y(), self.ui.axialPressureTitleLbl.width(), self.ui.axialPressureTitleLbl.height())
        sliderRect = QtCore.QRect(self.ui.axialPressureSlider.x(), self.ui.axialPressureSlider.y(), self.ui.horizontalFlexionSlider.width(), self.ui.horizontalFlexionSlider.height())
        lblRect = QtCore.QRect(self.ui.axialPressureLbl.x(), self.ui.axialPressureLbl.y(), self.ui.axialPressureLbl.width(), self.ui.axialPressureLbl.height())
        self.ui.axialPressureTitleLbl.hide()
        self.ui.axialPressureSlider.hide()
        self.ui.axialPressureLbl.hide()

        self.ui.horizontalFlexionSlider.setValue(0)
        self.ui.horizontalFlexionLbl.setText('0' + DEGREES)
        self.ui.horizontalFlexionSlider.setEnabled(True)
        self.ui.horizontalFlexionTitleLbl.setGeometry(titleRect)
        self.ui.horizontalFlexionSlider.setGeometry(sliderRect)
        self.ui.horizontalFlexionLbl.setGeometry(lblRect)
        self.ui.horizontalFlexionTitleLbl.hide()
        self.ui.horizontalFlexionSlider.hide()
        self.ui.horizontalFlexionLbl.hide()


        self.ui.groupBox_Lat.hide()
        self.ui.rightLatFlexionSlider.setValue(0)
        self.ui.rightLatFlexionLbl.setText('0' + DEGREES)
        self.ui.leftLatFlexionSlider.setValue(0)
        self.ui.leftLatFlexionLbl.setText('0' + DEGREES)
        '''
         self.ui.leftLatFlexionSlider.setEnabled(True)
        self.ui.leftLatFlexionTitleLbl.setGeometry(titleRect)
        self.ui.leftLatFlexionSlider.setGeometry(sliderRect)
        self.ui.leftLatFlexionLbl.setGeometry(lblRect)
        self.ui.leftLatFlexionTitleLbl.hide()
        self.ui.leftLatFlexionSlider.hide()
        self.ui.leftLatFlexionLbl.hide()

        self.ui.rightLatFlexionSlider.setEnabled(True)
        self.ui.rightLatFlexionTitleLbl.setGeometry(titleRect)
        self.ui.rightLatFlexionSlider.setGeometry(sliderRect)
        self.ui.rightLatFlexionLbl.setGeometry(lblRect)
        self.ui.rightLatFlexionTitleLbl.hide()
        self.ui.rightLatFlexionSlider.hide()
        self.ui.rightLatFlexionLbl.hide()
        '''

    def keyPressEvent(self, event):
        pressed = event.key()
        print('pressed {}'.format(pressed))
        event.accept()

    def keyReleaseEvent(self, event):
        pressed = event.key()
        print('released {}'.format(pressed))
        event.accept()
 
    def setBtns(self):
        for i in range(len(self.letterButtons)):
          self.numberButtons[i].setEnabled(True)

        self.ui.buttonGoBtn.setEnabled(False)

    def numberBtn(self):

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setStyleSheet("background-color: blue;color:white")

        sender = self.sender().text()  # This is what you need
        self.sender().setStyleSheet("background-color: green;color:white")
        self.senderNumber = self.sender()

        self.buttonValue = int(sender)
        self.unlockCode += sender
        self.ui.unlockKeyLbl.setText(self.unlockCode)
#        if(self.protocolValue == 'A'):
#          self.ui.programLbl.setText(self.protocol + str(self.buttonValue) + ' cycles')
#        print(self.protocol + str(self.buttonValue) + ' cycles')


        self.ui.buttonGoBtn.setEnabled(True)


    def limitBtns(self, buttons):
        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(True)

        for i in range(len(buttons)):
          self.numberButtons[buttons[i]-1].setEnabled(False)



    def letterBtn(self):

        if(len(self.protocol) == 2):
           return

        sender = self.sender().text()  # This is what you need

        self.protocolValue = sender

        if(self.firstLetter == ''):
          self.resetBtns(False)

          for i in range(len(self.letterButtons)):
            self.letterButtons[i].setEnabled(True)
            self.letterButtons[i].setStyleSheet("background-color: grey;color:white")
          self.sender().setStyleSheet("background-color: green;color:white")
#          self.firstLetter = ''

          if(sender == 'A'):
#            self.firstLetter = sender
            self.protocol = 'Axial Flexion - Traction '
            self.limitBtns([6,7,8,9])
            self.ui.groupBox_2.show()
            self.ui.groupBox_Lat.hide()
            self.ui.axialPressureTitleLbl.show()
            self.ui.axialPressureSlider.show()
            self.ui.axialPressureLbl.show()
  
          if(sender == 'B'):
            self.protocol = 'Horizontal Flexion'
            self.limitBtns([4,5,6,7,8,9])
            self.ui.groupBox_2.show()
            self.ui.groupBox_Lat.hide()
            self.ui.horizontalFlexionTitleLbl.show()
            self.ui.horizontalFlexionSlider.show()
            self.ui.horizontalFlexionLbl.show()

          if(sender == 'C'):
            self.protocol = 'Left Leg Lateral Flexion'
            self.limitBtns([4,5,6,7,8,9])
            self.ui.groupBox_2.hide()
            self.ui.groupBox_Lat.show()
            self.ui.leftLatFlexionTitleLbl.show()
            self.ui.leftLatFlexionSlider.show()
            self.ui.leftLatFlexionLbl.show()
            self.ui.rightLatFlexionTitleLbl.show()
            self.ui.rightLatFlexionSlider.show()
            self.ui.rightLatFlexionLbl.show()
  
          if(sender == 'D'):
            self.protocol = 'Right Leg Lateral Flexion'
            self.limitBtns([10,4,5,6,7,8,9])
            self.ui.groupBox_2.show()
            self.ui.groupBox_Lat.hide()
            self.ui.rightLatFlexionTitleLbl.show()
            self.ui.rightLatFlexionSlider.show()
            self.ui.rightLatFlexionLbl.show()

        else:
          if(self.firstLetter == 'A'):
            self.resetBtns(True)
            self.limitBtns([10])
            self.sender().setStyleSheet("background-color: green;color:white")
            self.firstLetter = sender
            self.protocolValue += sender

            if(sender == 'B'):
              self.protocol = 'Axial-Horizontal Flexion '
              self.limitBtns([10,5,6,7,8,9])
              self.ui.axialPressureTitleLbl.show()
              self.ui.axialPressureSlider.show()
              self.ui.axialPressureLbl.show()
 
            if(sender == 'C'):
              self.limitBtns([10])
              self.protocol = 'Left Leg Lateral-Axial Flexion'
              self.ui.leftLatFlexionTitleLbl.show()
              self.ui.leftLatFlexionSlider.show()
              self.ui.leftLatFlexionLbl.show()
    
            if(sender == 'D'):
              self.limitBtns([10])
              self.protocol = 'Right Leg Lateral-Axial Flexion'
              self.ui.rightLatFlexionTitleLbl.show()
              self.ui.rightLatFlexionSlider.show()
              self.ui.rightLatFlexionLbl.show()


        self.ui.programLbl.setText(self.protocol)

    def goBack(self):
        print(self.config.flexionPosition)
        self.config.updateConfig()
        self.ui.stackedWidget.setCurrentIndex(0)

    def setupA(self):
        self.setupB()

    def setupB(self):
        self.worker = BProtocols.Protocols(self.config.BFactor, 'S', 0, 0)
        self.worker.signals.finished.connect(self.setupC)
        self.threadpool.start(self.worker)

    def setupC(self):
        self.worker = CProtocols.Protocols(self.config.CFactor, 'S', 0, 0)
        self.worker.signals.finished.connect(self.protocolCompleted)
        self.threadpool.start(self.worker)


    def gotoSetup(self):
        self.ui.stackedWidget.setCurrentIndex(1)


    def shutdown(self):
        self.playVideoMP4.stop()
        self.playScriptMP4.stop()
        if(os.path.exists("debug.txt")):
           self.exitApp()
        print('shutdown')
        self.shutdownApp()

    def setI2CStatus(self, channel):
      self.I2Cstatus = GPIO.input(channel)
      print('self.I2Cstatus = {}'.format(self.I2Cstatus))


    def setupGPIO(self):

     GPIO.setmode(GPIO.BCM)
     GPIO.setwarnings(False)

     GPIO.setup(EXTRAFORWARD, GPIO.OUT)
     GPIO.setup(EXTRABACKWARD, GPIO.OUT)
     GPIO.setup(EXTRAENABLE, GPIO.OUT)

     GPIO.output(EXTRAENABLE, GPIO.HIGH)

#     GPIO.setup(ARDUINOI2C, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#     GPIO.remove_event_detect(ARDUINOI2C)
#     GPIO.add_event_detect(ARDUINOI2C, GPIO.BOTH, callback=self.setI2CStatus, bouncetime = 500)

     print('setupGPIO')

def main():
  print(' >>> {} {}'.format(datetime.now(), 'app started'))

  pid = os.getpid()

  app = QApplication(sys.argv)

#start the UI. Pass the scale thread to it so the emit/signal to work
  window = MyApp()

  app.exec_()
#should never get here unless we are done.
  os._exit(0)
  
if __name__ == '__main__':

  try:
    main()
  except Exception as e:
    print(str(e))
    GPIO.cleanup()           # clean up GPIO on normal exit

