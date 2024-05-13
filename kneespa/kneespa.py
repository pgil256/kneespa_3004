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
import csv
from os.path import exists

import RPi.GPIO as GPIO

EMERGENCYSTOP = 16
EXTRAFORWARD = 27
EXTRABACKWARD = 22
EXTRAENABLE = 17

import AProtocols
import BProtocols
import CProtocols
import DProtocols

import ABProtocols
import ACProtocols
import ADProtocols

import comm

import config

#these are for the PyQT5. There is overlap and should be cleaned up.
#pyrcc5 resources.qrc -o resources_rc.py

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QTime, QTimer, QEvent, QDateTime, QThread, QObject, pyqtSignal, QElapsedTimer
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
    '''
    finished = pyqtSignal()
    stopped = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(str)
    APressure = pyqtSignal(str)
    statusEmit = pyqtSignal(int, int, int, float)
    AstatusEmit = pyqtSignal(int, int, int, float)
#    doneEmit = pyqtSignal()
    '''
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
      position = int(inches * (factor / 8.0))
      print(' positioned to {} in. {} pos {}'.format(inches, position, actuator))

      if(self.newC):
        command = 'A{}{}'.format(actuator, inches)
      else:
        if(actuator == self.actuatorC):
          command = 'K{}'.format(position)
        else:
          command = 'A{}{}'.format(actuator, inches)
      self.arduino.send(command)
      print('cmd {}'.format(command.strip()))

#      while(not self.I2Cstatus):
#        time.sleep(0.1)

      self.I2Cstatus = False
      print('end')

    def setToCDistance(self, degrees):

      position = self.config.CMarks['{:.1f}'.format(degrees)]

      print(' positioned to {} degrees pos {}'.format(degrees, position))
      command = 'K{}'.format(position)
      self.arduino.send(command)
      print('cmd {}'.format(command.strip()))

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

        self.newC = True

        self.ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint) 

        qtRectangle = self.frameGeometry()
        farX = QDesktopWidget().screenGeometry().topRight().x()-50
        newX = farX - qtRectangle.topRight().x()
#        self.move(newX, qtRectangle.topLeft().y()+50)
        print(qtRectangle.bottomLeft().y())

        self.elapsedTimer = QTimer(self)
        self.elapsedTimer.timeout.connect(self.updateTime)

        self.hourFormat = '24'
        self.ui.timeMMLbl.setText("")
        self.ui.timeColonLbl.setText("")
        self.ui.timeSSLbl.setText("")

        self.protocolTimer = QElapsedTimer()
        self.protocolTimer.clockType = QElapsedTimer.SystemTime

        self.ui.timeGroup.hide()


        self.completeTimer = QTimer(self)
        self.completeTimer.timeout.connect(self.blinkComplete)
        self.blinkingComplete = False
        self.blinkingCompleteCount = 0

        self.goTimer = QTimer(self)
        self.goTimer.timeout.connect(self.blinkGo)
        self.blinkingGo = True

        self.stopTimer = QTimer(self)
        self.stopTimer.timeout.connect(self.blinkStop)
        self.blinkingStop = True

        self.resetTimer = QTimer(self)
        self.resetTimer.timeout.connect(self.blinkReset)
        self.blinkingReset = False

        self.logger = False
        self.unlockId = ''

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
        self.ui.logoutBtn.clicked.connect(self.logout)

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
        self.BDegreeList = {0:5, 5:4, 10:3, 15:2, 20:1, 25:0, 30:0}

        self.protocolValue = ''

        self.ui.axialPressureSlider.valueChanged.connect(self.axialPressureChanged)
        self.ui.minusHorizontalFlexionSlider.valueChanged.connect(self.minusHorizontalFlexionChanged)
        self.ui.plusHorizontalFlexionSlider.valueChanged.connect(self.plusHorizontalFlexionChanged)
        self.ui.leftLatFlexionSlider.valueChanged.connect(self.leftLatFlexionchanged)
        self.ui.rightLatFlexionSlider.valueChanged.connect(self.rightLatFlexionchanged)
        self.ui.cyclesSlider.valueChanged.connect(self.cyclesChanged)

        self.ui.ABaxialPressureSlider.valueChanged.connect(self.ABaxialPressureChanged)
        self.ui.minusABHorizontalFlexionSlider.valueChanged.connect(self.minusABHorizontalFlexionChanged)
        self.ui.plusABHorizontalFlexionSlider.valueChanged.connect(self.plusABHorizontalFlexionChanged)
        self.ui.ACDaxialPressureSlider.valueChanged.connect(self.ACDaxialPressureChanged)
        self.ui.ACDleftLatFlexionSlider.valueChanged.connect(self.ACDleftLatFlexionchanged)
        self.ui.ACDrightLatFlexionSlider.valueChanged.connect(self.ACDrightLatFlexionchanged)

        self.ui.forwardAxialFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorA, 0.065, '04'))
        self.ui.reverseAxialFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorA, 0.065, '04'))
        self.ui.forwardFastAxialFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorA, 0.065, '20'))
        self.ui.reverseFastAxialFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorA, 0.065, '20'))
        self.ui.resetAxialFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(self.actuatorA))
        self.axialFlexionPosition = 0
        self.ui.axialFlexionPositionSlider.valueChanged.connect(self.axialFlexionPositionChanged)
        self.ui.axialFlexionPositionLbl.setText('0 in')
        self.ui.axialFlexionPositionBtn.clicked.connect(lambda: self.movePositionFlexionBtn(self.actuatorA))
        self.ui.axialFlexionPositionStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorA))
        self.ui.axialFlexionPressureSlider.valueChanged.connect(self.axialFlexionPressureChanged)
        self.ui.axialFlexionPressureLbl.setText('0 lb')
        self.ui.axialFlexionPressureBtn.clicked.connect(self.axialFlexionPressureBtn)
        self.ui.axialFlexionPressureStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorA))

        self.ui.axialPressureUpLbl.mousePressEvent = self.axialPressureUp
        self.ui.axialPressureDownLbl.mousePressEvent = self.axialPressureDown

        self.ui.ABaxialPressureUpLbl.mousePressEvent = self.ABaxialPressureUp
        self.ui.ABaxialPressureDownLbl.mousePressEvent = self.ABaxialPressureDown
        self.ui.minusABHorizontalFlexionUpLbl.mousePressEvent = self.minusABHorizontalFlexionUp
        self.ui.minusABHorizontalFlexionDownLbl.mousePressEvent = self.minusABHorizontalFlexionDown
        self.ui.plusABHorizontalFlexionUpLbl.mousePressEvent = self.plusABHorizontalFlexionUp
        self.ui.plusABHorizontalFlexionDownLbl.mousePressEvent = self.plusABHorizontalFlexionDown

        self.ui.minusHorizontalUpLbl.mousePressEvent = self.minusHorizontalUp
        self.ui.minusHorizontalDownLbl.mousePressEvent = self.minusHorizontalDown
        self.ui.plusHorizontalUpLbl.mousePressEvent = self.plusHorizontalUp
        self.ui.plusHorizontalDownLbl.mousePressEvent = self.plusHorizontalDown

        self.ui.leftLatUpLbl.mousePressEvent = self.leftLatUp
        self.ui.leftLatDownLbl.mousePressEvent = self.leftLatDown
        self.ui.rightLatUpLbl.mousePressEvent = self.rightLatUp
        self.ui.rightLatDownLbl.mousePressEvent = self.rightLatDown


        self.ui.ACDaxialPressureUpLbl.mousePressEvent = self.ACDaxialPressureUp
        self.ui.ACDaxialPressureDownLbl.mousePressEvent = self.ACDaxialPressureDown
        self.ui.ACDleftLatUpLbl.mousePressEvent = self.ACDleftLatUp
        self.ui.ACDleftLatDownLbl.mousePressEvent = self.ACDleftLatDown
        self.ui.ACDrightLatUpLbl.mousePressEvent = self.ACDrightLatUp
        self.ui.ACDrightLatDownLbl.mousePressEvent = self.ACDrightLatDown


        self.ui.forwardHorizontalFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorB, 0.065, '04'))
        self.ui.reverseHorizontalFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorB, 0.065, '04'))
        self.ui.forwardFastHorizontalFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorB, 0.065, '20'))
        self.ui.reverseFastHorizontalFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorB, 0.065, '20'))
        self.ui.resetHorizontalFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(self.actuatorB))
        self.horizontalFlexionPosition = -15

        self.ui.horizontalPositionFlexionSlider.valueChanged.connect(self.horizontalPositionFlexionChanged)
        self.ui.horizontalPositionFlexionLbl.setText('-15' + DEGREES)
        self.ui.horizontalPositionFlexionBtn.clicked.connect(lambda: self.movePositionFlexionBtn(self.actuatorB))
        self.ui.horizontalPositionFlexionStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorB))

        self.ui.forwardLateralFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorC, 0.0328, '04'))
        self.ui.reverseLateralFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorC, 0.0328, '04'))
        self.ui.forwardFastLateralFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(self.actuatorC, 0.0328, '20'))
        self.ui.reverseFastLateralFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(self.actuatorC, 0.0328, '20'))
        self.ui.resetLateralFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(self.actuatorC))
        self.lateralFlexionPosition = 0
        self.ui.lateralFlexionPositionSlider.valueChanged.connect(self.lateralFlexionPositionChanged)
        self.ui.lateralFlexionPositionLbl.setText('0' + DEGREES)
        self.ui.lateralFlexionPositionBtn.clicked.connect(lambda: self.movePositionFlexionBtn(self.actuatorC))
        self.ui.lateralFlexionPositionStopBtn.clicked.connect(lambda: self.stopPositionFlexionBtn(self.actuatorC))

        self.ui.cyclesSlider.sliderMoved.connect(self.cyclesSliderMoved)
        self.ui.axialPressureSlider.sliderMoved.connect(self.axialPressureSliderMoved)
        self.ui.minusHorizontalFlexionSlider.sliderMoved.connect(self.minusHorizontalFlexionSliderMoved)
        self.ui.plusHorizontalFlexionSlider.sliderMoved.connect(self.plusHorizontalFlexionSliderMoved)
        self.ui.leftLatFlexionSlider.sliderMoved.connect(self.leftLatFlexionSliderMoved)
        self.ui.rightLatFlexionSlider.sliderMoved.connect(self.rightLatFlexionSliderMoved)

        self.ui.ABaxialPressureSlider.sliderMoved.connect(self.ABaxialPressureSliderMoved)
        self.ui.ACDaxialPressureSlider.sliderMoved.connect(self.ACDaxialPressureSliderMoved)
        self.ui.minusABHorizontalFlexionSlider.sliderMoved.connect(self.minusABHorizontalFlexionSliderMoved)
        self.ui.plusABHorizontalFlexionSlider.sliderMoved.connect(self.plusABHorizontalFlexionSliderMoved)
        self.ui.ACDleftLatFlexionSlider.sliderMoved.connect(self.ACDleftLatFlexionSliderMoved)
        self.ui.ACDrightLatFlexionSlider.sliderMoved.connect(self.ACDrightLatFlexionSliderMoved)

        self.ui.axialFlexionPressureSlider.sliderMoved.connect(self.axialFlexionPressureSliderMoved)
        self.ui.horizontalPositionFlexionSlider.sliderMoved.connect(self.horizontalPositionFlexionSliderMoved)
        self.ui.lateralFlexionPositionSlider.sliderMoved.connect(self.lateralFlexionSliderMoved)

        self.ui.forwardExtraBtn.clicked.connect(self.forwardExtraBtnClicked)
        self.ui.reverseExtraBtn.clicked.connect(self.reverseExtraBtnClicked)
        self.ui.forwardFastExtraBtn.clicked.connect(self.forwardFastExtraBtnClicked)
        self.ui.reverseFastExtraBtn.clicked.connect(self.reverseFastExtraBtnClicked)
        self.ui.resetExtraBtn.clicked.connect(self.resetExtraBtnClicked)

        self.ui.measureWeightBtn.clicked.connect(self.measureWeightBtnClicked)
        self.ui.measureLocationBtn.clicked.connect(self.measureLocationBtnClicked)

        self.ui.resetArduinoBtn.clicked.connect(self.resetArduinoBtn)
        self.ui.resetArduino2Btn.clicked.connect(self.resetArduinoBtn)

        self.ui.emergencyStopLbl.mousePressEvent = self.emergencyStopLbl
        self.ui.emergencyStop2Lbl.mousePressEvent = self.emergencyStopLbl


        self.ui.cyclesGroupBox.hide()
        self.ui.AGroupBox.hide()
        self.ui.CDGroupBox.hide()
        self.ui.BGroupBox.hide()
        self.ui.ABGroupBox.hide()
        self.ui.AXGroupBox.hide()
        self.ui.ACDGroupBox.hide()

        self.config = config.Configuration()
        self.config.getConfig()

        self.CMarks = {}
        for i in range(16):
          u = (i * 220) + 98
          angle = (i *2.5) -20
          print(i, angle, u)
          self.CMarks[angle] = u

        print(self.config.AMarks)
        print(self.config.BMarks)
        print(self.config.CMarks)

        self.actuatorA = 12
        self.actuatorB = 13
        self.actuatorC = 14

        self.ui.logoutBtn.show()
        filename = 'users.csv'
        found = False
        if(exists(filename)):
          with open(filename, mode='rt') as f:
            fieldNames = ['id', 'name']
            csvReader = csv.DictReader(f, delimiter=',', fieldnames=fieldNames)
            for row in csvReader:
              if(row['id'] == self.unlockCode):
                found = True
                break
        else:
           if(self.config.unlock == ''):
              found = True
              self.ui.logoutBtn.hide()
           else:
              found = self.config.unlock == self.unlockCode

        if(found):
           self.unlocked = True
           self.ui.unlockGroup.hide()
           self.ui.cyclesGroupBox.show()
           self.resetBtns(True)
           for i in range(len(self.letterButtons)):
             self.letterButtons[i].setEnabled(True)
             self.letterButtons[i].setStyleSheet("background-color: grey;color:white")
           self.ui.setupBtn.show()

           self.logProtocol('Unlocked', 0,  0,  0,  0,  0,  0)

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
#        self.signals.doneEmit.connect(self.setDone)#readyToGo)
#        self.arduino.doneEmit.connect(self.setDone)
        '''

      # 1 - create Worker and Thread inside the Form
        self.arduino = comm.Arduino()  # no parent!
        print(self.arduino.doneEmit)
        self.thread = QThread()  # no parent!

       # 2 - Connect Worker`s Signals to Form method slots to post data.
        self.arduino.doneEmit.connect(self.setDone)
       # 3 - Move the Worker object to the Thread object
        self.arduino.moveToThread(self.thread)
       # 4 - Connect Worker Signals to the Thread slots
        self.arduino.finished.connect(self.thread.quit)
#        self.arduino.statusEmit.connect(self.statusEmit)
        self.arduino.AstatusEmit.connect(self.statusEmit)
        self.arduino.readyToGoEmit.connect(self.readyToGo)

       # 5 - Connect Thread started signal to Worker operational slot method
        self.thread.started.connect(self.arduino.run)

       # * - Thread finished signal will close the app if you want!
       #self.thread.finished.connect(app.exit)

        self.arduino.positionEmit.connect(self.readPosition)
        self.arduino.statusEmit.connect(self.status)
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

        '''
        self.playVideoMP4 = PlayMP4('-40 -40 800 450', self.videoList)
        self.playingVideoThread = QThread()  # no parent!
#        self.playVideoMP4.doneEmit.connect(self.setDone)
        self.playVideoMP4.moveToThread(self.playingVideoThread)
        self.playVideoMP4.finished.connect(self.playingVideoThread.quit)
        self.playingVideoThread.started.connect(self.playVideoMP4.run)
       #self.playingVideoThread.finished.connect(app.exit)
       # 6 - Start the thread
        self.playingVideoThread.start()

        QTimer.singleShot(2000, lambda:self.playVideoMP4.done())

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

        QTimer.singleShot(2000, self.sendCalibration)
        QTimer.singleShot(5000, self.sendZeroMark)
        self.arduino.displayWeightEmit.connect(self.displayWeight)

    def updateTime(self):
        if(not self.protocolTimer.isValid()):
          return
        elapsed = self.protocolTimer.elapsed()
        seconds=(elapsed/1000)%60
        seconds = int(seconds)
        minutes=(elapsed/(1000*60))%60
        minutes = int(minutes)
        dt = QDateTime.currentDateTime()
        textDT = dt.toString('dddd, MMMM d').upper()
        time = QTime.currentTime()
        textHH = time.toString('hh:mm:ss ap').split(' ')[0]
        textMM = '{:02d}'.format(minutes)
        textSS = '{:02d}'.format(seconds)
        textPM = ''
        text = ':'
#        if (time.second() % 2) == 0:
#            text = ':'
        if(self.hourFormat == '12'):
           textPM = time.toString('AP')
           textTime = time.toString('h:mm ap').split(' ')[0]
        else:
           textTime = time.toString('h:mm').split(' ')[0]
        textTime = textTime.replace(":", text)

        self.ui.timeMMLbl.setText(textMM)
        self.ui.timeColonLbl.setText(text)
        self.ui.timeSSLbl.setText(textSS)

    def logout(self):
        self.unlocked = False
        self.unlockId = ''
        self.ui.unlockGroup.show()
        self.ui.cyclesGroupBox.hide()
        self.btnsClear()
        self.resetBtns(True)
        self.ui.setupBtn.hide()
        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(False)
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")
        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(True)
          self.numberButtons[i].setStyleSheet("background-color: blue;color:white")
        self.logProtocol('Locked', 0,  0,  0,  0,  0,  0)

    def logProtocol(self, protocol, cycles, pressure, degrees, startDegrees,leftLat, rightLat):
        return
        timeStamp = datetime.now().strftime('%m/%d/%Y %H:%M')
        filename = datetime.now().strftime('%m-%d-%Y') + '.csv'
        if(exists(filename)):
          self.logger = False;
          with open(filename, 'a') as f:
            csvWriter = csv.writer(f) 
            # writing the fields 
            csvWriter.writerow([timeStamp, self.unlockId, protocol, cycles, pressure, degrees, startDegrees,leftLat, rightLat])
        else:
          with open(filename, 'w') as f:
            # creating a csv writer object 
            csvWriter = csv.writer(f) 
            # writing the fields 
            csvWriter.writerow(['TimeStamp', 'Id', 'Protocol','Cycles','Axial Pressure','Horizontal Degrees','Start Degrees','Left Lat Degrees','Right Lat Degrees'])
            csvWriter.writerow([timeStamp, self.unlockId, protocol, cycles, pressure, degrees, startDegrees,leftLat, rightLat])
            self.logger = True

    def rightLatUp(self, event):
        self.rightLatAngle = self.ui.rightLatFlexionSlider.value()
        self.rightLatAngle += 10
        if(self.rightLatAngle > 20):
           self.rightLatAngle = 20
        self.ui.rightLatFlexionSlider.setValue(self.rightLatAngle)
        self.ui.rightLatFlexionLbl.setText(str(self.rightLatAngle))

    def rightLatDown(self, event):
        self.rightLatAngle = self.ui.rightLatFlexionSlider.value()
        self.rightLatAngle -= 10
        if(self.rightLatAngle < 0):
           self.rightLatAngle = 0
        self.ui.rightLatFlexionSlider.setValue(self.rightLatAngle)
        self.ui.rightLatFlexionLbl.setText(str(self.rightLatAngle))

    def leftLatUp(self, event):
        self.leftLatAngle = self.ui.leftLatFlexionSlider.value()
        self.leftLatAngle += 10
        if(self.leftLatAngle > 20):
           self.leftLatAngle = 20
        self.ui.leftLatFlexionSlider.setValue(self.leftLatAngle)
        self.ui.leftLatFlexionLbl.setText(str(-self.leftLatAngle))

    def leftLatDown(self, event):
        self.leftLatAngle = self.ui.leftLatFlexionSlider.value()
        self.leftLatAngle -= 10
        if(self.leftLatAngle < 0):
           self.leftLatAngle = 0
        self.ui.leftLatFlexionSlider.setValue(self.leftLatAngle)
        self.ui.leftLatFlexionLbl.setText(str(-self.leftLatAngle))

    def ACDaxialPressureUp(self, event):
        self.axialPressure = self.ui.ACDaxialPressureSlider.value()
        self.axialPressure += 5
        if(self.axialPressure > 80):
           self.axialPressure = 80
        self.ui.ACDaxialPressureSlider.setValue(self.axialPressure)
        self.ui.ACDaxialPressureLbl.setText(str(self.axialPressure)+' lb')

    def ACDaxialPressureDown(self, event):
        self.axialPressure = self.ui.ACDaxialPressureSlider.value()
        self.axialPressure -= 5
        if(self.axialPressure < 10):
           self.axialPressure = 10
        self.ui.ACDaxialPressureSlider.setValue(self.axialPressure)
        self.ui.ACDaxialPressureLbl.setText(str(self.axialPressure)+' lb')

    def ACDrightLatUp(self, event):
        self.rightLatAngle = self.ui.ACDrightLatFlexionSlider.value()
        self.rightLatAngle += 5
        if(self.rightLatAngle > 20):
           self.rightLatAngle = 20
        self.ui.ACDrightLatFlexionSlider.setValue(self.rightLatAngle)
        self.ui.ACDrightLatFlexionLbl.setText(str(self.rightLatAngle) + DEGREES)

    def ACDrightLatDown(self, event):
        self.rightLatAngle = self.ui.ACDrightLatFlexionSlider.value()
        self.rightLatAngle -= 5
        if(self.rightLatAngle < 0):
           self.rightLatAngle = 0
        self.ui.ACDrightLatFlexionSlider.setValue(self.rightLatAngle)
        self.ui.ACDrightLatFlexionLbl.setText(str(self.rightLatAngle) + DEGREES)

    def ACDleftLatUp(self, event):
        self.leftLatAngle = self.ui.ACDleftLatFlexionSlider.value()
        self.leftLatAngle += 5
        if(self.leftLatAngle > 20):
           self.leftLatAngle = 20
        self.ui.ACDleftLatFlexionSlider.setValue(self.leftLatAngle)
        self.ui.ACDleftLatFlexionLbl.setText(str(-self.leftLatAngle) + DEGREES)

    def ACDleftLatDown(self, event):
        self.leftLatAngle = self.ui.ACDleftLatFlexionSlider.value()
        self.leftLatAngle -= 5
        if(self.leftLatAngle < 0):
           self.leftLatAngle = 0
        self.ui.ACDleftLatFlexionSlider.setValue(self.leftLatAngle)
        self.ui.ACDleftLatFlexionLbl.setText(str(-self.leftLatAngle) + DEGREES)


    def minusHorizontalUp(self, event):
        self.minusHorizontalDegrees = self.ui.minusHorizontalFlexionSlider.value()
        self.minusHorizontalDegrees -= 5
        if(self.minusHorizontalDegrees < 15):
           self.minusHorizontalDegrees = 15
        self.ui.minusHorizontalFlexionSlider.setValue(self.minusHorizontalDegrees)
        self.ui.minusHorizontalFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)

    def minusHorizontalDown(self, event):
        self.minusHorizontalDegrees = self.ui.minusHorizontalFlexionSlider.value()
        self.minusHorizontalDegrees += 5
        if(self.minusHorizontalDegrees > 25):
           self.minusHorizontalDegrees = 25
        self.ui.minusHorizontalFlexionSlider.setValue(self.minusHorizontalDegrees)
        self.ui.minusHorizontalFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)

    def plusHorizontalUp(self, event):
        self.plusHorizontalDegrees = self.ui.plusHorizontalFlexionSlider.value()
        self.plusHorizontalDegrees -= 5
        if(self.plusHorizontalDegrees <= 5):
           self.plusHorizontalDegrees = 5
        self.ui.plusHorizontalFlexionSlider.setValue(self.plusHorizontalDegrees)
        self.ui.plusHorizontalFlexionLbl.setText(str(self.plusHorizontalDegrees) + DEGREES)

    def plusHorizontalDown(self, event):
        self.plusHorizontalDegrees = self.ui.plusHorizontalFlexionSlider.value()
        self.plusHorizontalDegrees += 5
        if(self.plusHorizontalDegrees >= 15):
           self.plusHorizontalDegrees = 15
        self.ui.plusHorizontalFlexionSlider.setValue(self.plusHorizontalDegrees)
        self.ui.plusHorizontalFlexionLbl.setText(str(self.plusHorizontalDegrees) + DEGREES)

    def minusABHorizontalFlexionUp(self, event):
        self.minusHorizontalDegrees = self.ui.minusABHorizontalFlexionSlider.value()
        self.minusHorizontalDegrees -= 5
        if(self.minusHorizontalDegrees < 15):
           self.minusHorizontalDegrees = 15
        self.ui.minusABHorizontalFlexionSlider.setValue(self.minusHorizontalDegrees)
        self.ui.minusABHorizontalFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)

    def minusABHorizontalFlexionDown(self, event):
        self.minusHorizontalDegrees = self.ui.minusABHorizontalFlexionSlider.value()
        self.minusHorizontalDegrees += 5
        if(self.minusHorizontalDegrees > 25):
           self.minusHorizontalDegrees = 25
        self.ui.minusABHorizontalFlexionSlider.setValue(self.minusHorizontalDegrees)
        self.ui.minusABHorizontalFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)

    def plusABHorizontalFlexionUp(self, event):
        self.plusHorizontalDegrees = self.ui.plusABHorizontalFlexionSlider.value()
        self.plusHorizontalDegrees -= 5
        if(self.plusHorizontalDegrees < 5):
           self.plusHorizontalDegrees = 5
        self.ui.plusABHorizontalFlexionSlider.setValue(self.plusHorizontalDegrees)
        self.ui.plusABHorizontalFlexionLbl.setText(str(self.plusHorizontalDegrees) + DEGREES)

    def plusABHorizontalFlexionDown(self, event):
        self.plusHorizontalDegrees = self.ui.plusABHorizontalFlexionSlider.value()
        self.plusHorizontalDegrees += 5
        if(self.plusHorizontalDegrees > 15):
           self.plusHorizontalDegrees = 15
        self.ui.plusABHorizontalFlexionSlider.setValue(self.plusHorizontalDegrees)
        self.ui.plusABHorizontalFlexionLbl.setText(str(self.plusHorizontalDegrees) + DEGREES)



    def axialPressureUp(self, event):
        self.axialPressure = self.ui.axialPressureSlider.value()
        self.axialPressure += 5
        if(self.axialPressure > 80):
           self.axialPressure = 80
        self.ui.axialPressureSlider.setValue(self.axialPressure)
        self.ui.axialPressureLbl.setText(str(self.axialPressure)+' lb')

    def axialPressureDown(self, event):
        self.axialPressure = self.ui.axialPressureSlider.value()
        self.axialPressure -= 5
        if(self.axialPressure < 10):
           self.axialPressure = 10
        self.ui.axialPressureSlider.setValue(self.axialPressure)
        self.ui.axialPressureLbl.setText(str(self.axialPressure)+' lb')

    def ABaxialPressureUp(self, event):
        self.axialPressure = self.ui.ABaxialPressureSlider.value()
        self.axialPressure += 5
        if(self.axialPressure > 80):
           self.axialPressure = 80
        self.ui.ABaxialPressureSlider.setValue(self.axialPressure)
        self.ui.ABaxialPressureLbl.setText(str(self.axialPressure)+' lb')

    def ABaxialPressureDown(self, event):
        self.axialPressure = self.ui.ABaxialPressureSlider.value()
        self.axialPressure -= 5
        if(self.axialPressure < 10):
           self.axialPressure = 10
        self.ui.ABaxialPressureSlider.setValue(self.axialPressure)
        self.ui.ABaxialPressureLbl.setText(str(self.axialPressure)+' lb')


    def emergencyStopLbl(self, event):
        self.arduino.send('X')
        if(self.worker != None):
           self.worker.stop()
        self.btnsClear()
        self.stopTimer.start(500)

    def sendZeroMark(self):
        print('sendZeroMark')
        self.arduino.send('L5{:3} {:3}'.format(self.config.AMarks['0.0'], self.config.BMarks['0.0']))

    def sendCalibration(self):
        print('sendCalibration')
        self.arduino.send('L0{}'.format(self.config.calibration))

    def blinkReset(self):
        if(self.blinkingReset):
          self.ui.resetArduinoBtn.show()
          self.ui.resetArduino2Btn.show()
        else:
          self.ui.resetArduinoBtn.hide()
          self.ui.resetArduino2Btn.hide()
        self.blinkingReset = not self.blinkingReset

    def resetArduinoBtn(self):
        self.ui.resetArduinoBtn.setEnabled(False)
        self.ui.resetArduino2Btn.setEnabled(False)
        self.resetTimer.start(500)

        self.I2Cstatus = 0
        self.arduino.send('Y')
        self.I2Cstatus = 1
        while(self.I2Cstatus == 0):
          time.sleep(0.5)
          QApplication.processEvents()
          print('time.sleep(0.5)', self.I2Cstatus)
        self.I2Cstatus = 0
        print('end Y')
        self.blinkingReset = False
        QApplication.processEvents()
        for i in range(12):
          QApplication.processEvents()
          sleep(.3)

        self.I2Cstatus = 0
        self.sendZeroMark()
        self.I2Cstatus = 0
        while(self.I2Cstatus == 0):
          time.sleep(0.5)
          QApplication.processEvents()
          print('time.sleep(0.5)', self.I2Cstatus)
        self.I2Cstatus = 0
        print('end L5')
        QApplication.processEvents()
        for i in range(12):
          QApplication.processEvents()
          sleep(.3)

        QApplication.processEvents()
        position = 0
        print(' positioned to {}'.format(position))
        command = 'I12{}'.format(position)
        self.arduino.send(command)
        self.I2Cstatus = 0
        QApplication.processEvents()
        while(self.I2Cstatus == 0):
          QApplication.processEvents()
          time.sleep(0.5)
        self.I2Cstatus = 0
        print('end I12')
        for i in range(5):
          QApplication.processEvents()
          sleep(.3)

        QApplication.processEvents()
        position = 1213
        print(' positioned to {}'.format(position))
        command = 'A132.0'
        self.arduino.send(command)
        self.I2Cstatus = 0
        while(self.I2Cstatus == 0):
          QApplication.processEvents()
          time.sleep(0.5)
        self.I2Cstatus = 0
        print('end I13')
        for i in range(5):
          QApplication.processEvents()
          sleep(.3)

        QApplication.processEvents()
        position = self.config.CMarks['{:.1f}'.format(0)]
        print(' positioned to {} degrees pos {}'.format(0, position))
        command = 'I14{}'.format(position)
        self.arduino.send(command)
        self.I2Cstatus = 0
        while(self.I2Cstatus == 0):
          QApplication.processEvents()
          time.sleep(0.5)
        self.I2Cstatus = 0
        print('end I14')
        for i in range(5):
          QApplication.processEvents()
          sleep(.3)

        self.arduino.send('L0{}'.format(self.config.calibration))


        self.ui.horizontalPositionFlexionSlider.setValue(-15)
        self.ui.horizontalPositionFlexionLbl.setText('-15' + DEGREES)
        self.setupHorizontalDegrees = -15

        self.ui.axialFlexionPositionSlider.setValue(0)
        self.ui.axialFlexionPositionLbl.setText('0 in')
        self.axialFlexionPosition = 0

        self.ui.lateralFlexionPositionSlider.setValue(0)
        self.ui.lateralFlexionPositionLbl.setText('0' + DEGREES)
        self.setupLateralDegrees = 0
        self.ui.resetArduinoBtn.setEnabled(True)
        self.ui.resetArduino2Btn.setEnabled(True)
        self.blinkingReset = True
        self.blinkReset()
        self.resetTimer.stop()

    def readPressure(self, pressure):
        self.ui.axialFlexionPressureLbl.setText(pressure + ' lb')

    def cyclesSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        if(rounded == 0):
          rounded = 1
        self.ui.cyclesSlider.setValue(rounded)
        self.ui.cyclesLbl.setText(str(rounded))

    def axialPressureSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.axialPressureSlider.setValue(rounded)
        self.ui.axialPressureLbl.setText(str(rounded) + ' lb')

    def ABaxialPressureSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.ABaxialPressureSlider.setValue(rounded)
        self.ui.ABaxialPressureLbl.setText(str(rounded) + ' lb')

    def ACDaxialPressureSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.ACDaxialPressureSlider.setValue(rounded)
        self.ui.ACDaxialPressureLbl.setText(str(rounded) + ' lb')

    def axialFlexionPressureSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.axialFlexionPressureSlider.setValue(rounded)
        self.ui.axialFlexionPressureLbl.setText(str(rounded) + ' lb')

    def minusHorizontalFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.minusHorizontalFlexionSlider.setValue(rounded)
        self.ui.minusHorizontalFlexionLbl.setText(str(rounded) + DEGREES)

    def plusHorizontalFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.plusHorizontalFlexionSlider.setValue(rounded)
        self.ui.plusHorizontalFlexionLbl.setText(str(rounded) + DEGREES)

    def minusABHorizontalFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.minusABHorizontalFlexionSlider.setValue(rounded)
        self.ui.minusABHorizontalFlexionLbl.setText(str(rounded) + DEGREES)

    def plusABHorizontalFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.plusABHorizontalFlexionSlider.setValue(rounded)
        self.ui.plusABHorizontalFlexionLbl.setText(str(rounded) + DEGREES)

    def leftLatFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.leftLatFlexionSlider.setValue(rounded)
        self.ui.leftLatFlexionLbl.setText(str(-rounded) + DEGREES)

    def rightLatFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.rightLatFlexionSlider.setValue(rounded)
        self.ui.rightLatFlexionLbl.setText(str(rounded) + DEGREES)

    def ACDleftLatFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.ACDleftLatFlexionSlider.setValue(rounded)
        self.ui.ACDleftLatFlexionLbl.setText(str(-rounded) + DEGREES)

    def ACDrightLatFlexionSliderMoved(self, event):
        rounded = int(round(event/5)*5)
        self.ui.ACDrightLatFlexionSlider.setValue(rounded)
        self.ui.ACDrightLatFlexionLbl.setText(str(rounded) + DEGREES)

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

    def measureLocationBtnClicked(self):
        print('measureLocation')
        self.arduino.send('L6')

    def readyToGo(self):
        print('self.I2Cstatus = True')
        self.I2Cstatus = True
        self.ui.statusLbl.setText('Ready to Start')

    def status(self, positionA, positionB, steps, pressure):
#        print('A {} B {} C {} Pressure {}'.format(positionA, positionB, steps, pressure))
        if(self.worker != None):
           self.worker.status(positionA, positionB, steps, pressure)

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

    @QtCore.pyqtSlot()
    def setDone(self):
        print('Set Done self.I2Cstatus = True')
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

        if(actuator == self.actuatorB):
          if(int(speedFactor) <= 4):
            step = 5
          else:
            step = 10
          print('B {}'.format(self.horizontalFlexionPosition))
          if((self.horizontalFlexionPosition + step) > -5):
              return
          self.horizontalFlexionPosition += step
          print(self.horizontalFlexionPosition)

          command = 'E{}+{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.ui.horizontalPositionFlexionSlider.setValue(self.horizontalFlexionPosition)
          self.ui.horizontalPositionFlexionLbl.setText(str(self.horizontalFlexionPosition)+DEGREES)
          return

        if(actuator == self.actuatorA):
          print('A {}'.format(self.axialFlexionPosition))
          if(int(speedFactor) <= 4):
            step = 0.5
          else:
            step = 1
          if((self.axialFlexionPosition + step) > 8):
              return

          self.axialFlexionPosition += step

#          command = 'E{}+{}'.format(actuator, speedFactor)
          command = 'A12{}'.format(self.axialFlexionPosition)
          self.arduino.send(command)                #transmit data serially 
          print('xxxxxxxxxxxxxxxxxxxxxxxxx', self.axialFlexionPosition)
          self.ui.axialFlexionPositionSlider.setValue(self.axialFlexionPosition*2)
          self.ui.axialFlexionPositionLbl.setText(str(self.axialFlexionPosition) + ' in')
          sleep(.3)
          self.arduino.send('L5')
          return

        if(actuator == self.actuatorC):
          if(int(speedFactor) <= 4):
            step = 5
          else:
            step = 10
          if((self.lateralFlexionPosition + step) > 20):
              return
          self.lateralFlexionPosition += step

          position = self.config.CMarks['{:.1f}'.format(self.lateralFlexionPosition)]
          print(' positioned to {} degrees pos {}'.format(self.lateralFlexionPosition, position))
          command = 'K{}'.format(position)
#          command = 'C{}+{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 

          leftRight = ''
          if(self.lateralFlexionPosition > 0):
            leftRight = 'R'
          if(self.lateralFlexionPosition < 0):
            leftRight = 'L'
          self.ui.lateralFlexionPositionSlider.setValue(self.lateralFlexionPosition)
          self.ui.lateralFlexionPositionLbl.setText(str(abs(self.lateralFlexionPosition))+leftRight)


    def reverseFlexionBtn(self, actuator, step, speedFactor):
        print(speedFactor)
        print('A {}'.format(self.axialFlexionPosition))

        if(actuator == self.actuatorA):
          if(int(speedFactor) <= 4):
            step = 0.5
          else:
            step = 1
          if((self.axialFlexionPosition - step) < -5):
              return

          self.axialFlexionPosition -= step
#          command = 'E{}-{}'.format(actuator, speedFactor)
          command = 'A12{}'.format(self.axialFlexionPosition)
          self.arduino.send(command)                #transmit data serially 
          print('xxxxxxxxxxxxxxxxxxxxxxxxx', self.axialFlexionPosition)
          self.ui.axialFlexionPositionSlider.setValue(self.axialFlexionPosition*2)
          self.ui.axialFlexionPositionLbl.setText(str(self.axialFlexionPosition) + ' in')

        if(actuator == self.actuatorB):
          if(int(speedFactor) <= 4):
            step = 5
          else:
            step = 10
          print('B {}'.format(self.horizontalFlexionPosition))
          if((self.horizontalFlexionPosition - step) < -25):
              return
          self.horizontalFlexionPosition -= step
          print(self.horizontalFlexionPosition)

          command = 'E{}-{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          self.ui.horizontalPositionFlexionSlider.setValue(self.horizontalFlexionPosition)
          self.ui.horizontalPositionFlexionLbl.setText(str(self.horizontalFlexionPosition)+DEGREES)

        if(actuator == self.actuatorC):
          print(self.lateralFlexionPosition)
          if(int(speedFactor) <= 4):
            step = 5
          else:
            step = 10
          if((self.lateralFlexionPosition - step) < -20):
              return
          self.lateralFlexionPosition -= step

          position = self.config.CMarks['{:.1f}'.format(self.lateralFlexionPosition)]
          print(' positioned to {} degrees pos {}'.format(self.lateralFlexionPosition, position))
          command = 'K{}'.format(position)
#          command = 'C{}-{}'.format(actuator, speedFactor)
          self.arduino.send(command)                #transmit data serially 
          leftRight = ''
          if(self.lateralFlexionPosition > 0):
            leftRight = 'R'
          if(self.lateralFlexionPosition < 0):
            leftRight = 'L'
          self.ui.lateralFlexionPositionSlider.setValue(self.lateralFlexionPosition)
          self.ui.lateralFlexionPositionLbl.setText(str(abs(self.lateralFlexionPosition))+leftRight)

    def resetFlexionBtn(self, actuator):

        print(actuator)
        if(actuator == self.actuatorB):
#          command = 'R{}'.format(actuator)
          command = 'A{}2'.format(actuator)
          self.arduino.send(command)                #transmit data serially 
          self.horizontalFlexionPosition = -15
#          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
          self.ui.horizontalPositionFlexionSlider.setValue(self.horizontalFlexionPosition)
          self.ui.horizontalPositionFlexionLbl.setText(str(self.horizontalFlexionPosition) + DEGREES)
          return

        if(actuator == self.actuatorA):
          command = 'R{}'.format(actuator)
          self.arduino.send(command)                #transmit data serially 
          self.axialFlexionPosition = 0
#          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
          self.ui.axialFlexionPositionSlider.setValue(0)
          self.ui.axialFlexionPositionLbl.setText('0 in')
          self.ui.axialFlexionPressureSlider.setValue(0)
          self.ui.axialFlexionPressureLbl.setText('0 lb')
          sleep(5)
          self.arduino.send('L0{}'.format(self.config.calibration))
          return

        if(actuator == self.actuatorC):
          position = self.config.CMarks['{:.1f}'.format(0)]
          print(' positioned to {} degrees pos {}'.format(0, position))
          command = 'I14{}'.format(position)
          self.arduino.send(command)
          self.lateralFlexionPosition = 0
#          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
          self.ui.lateralFlexionPositionSlider.setValue(0)
          self.ui.lateralFlexionPositionLbl.setText('0' + DEGREES)
          return


    def AProtocolPressure(self, status):
#        print('AProtocolPressure')
        self.ui.AProgramLbl.setText(status)

    def protocolCompleted(self, finished):
        self.ui.AProgramLbl.setText(' ')
        self.protocolTimer.invalidate()
        if(finished):
          print('protocolCompleted')
          self.resetBtns(True)
          self.ui.statusLbl.setText('Protocol Completed')
          self.completeTimer.start(500)
          self.blinkingCompleteCount = 1
          self.blinkComplete()
        else:
          print('protocolStopped')
          self.ui.statusLbl.setText('Protocol STOPPED')

    def protocolStopped(self):
#        print('protocolStopped')
        self.ui.statusLbl.setText('Protocol STOPPED')
        self.ui.AProgramLbl.setText('')
        self.elapsedTimer.stop()
        self.ui.timeGroup.hide()
        self.protocolTimer.invalidate()

    def clearStatus(self):
        self.ui.statusLbl.setText('')
        self.ui.statusLbl_2.setText('')
        self.ui.programLbl.setText('')
        self.ui.programLbl_2.setText('')
        self.ui.AProgramLbl.setText('')
#        self.statusTimer.stop()

    def blinkComplete(self):
        if(self.blinkingComplete):
          self.ui.keypadWidget.setStyleSheet("border-radius:25px;border:4px solid white;background-color:white;")
        else:
          self.ui.keypadWidget.setStyleSheet("border-radius:25px;border:4px solid white;background-color:blue;")
        self.blinkingComplete = not self.blinkingComplete
        self.blinkingCompleteCount += 1
        if(self.blinkingCompleteCount > 5):
          self.completeTimer.stop()
          self.blinkingComplete = 0


    def blinkGo(self):
        if(self.blinkingGo):
          self.ui.buttonGoBtn.setStyleSheet("background-color:#78909C")#green;color:78909C")
        else:
          self.ui.buttonGoBtn.setStyleSheet("background-color:green;")
        self.blinkingGo = not self.blinkingGo


    def blinkStop(self):
        if(self.blinkingStop):
          self.ui.emergencyStopLbl.setStyleSheet("border:4px solid black;border-radius:20px;background-color:#78909C;")
          self.ui.emergencyStop2Lbl.setStyleSheet("border:4px solid black;border-radius:20px;background-color:#78909C;")
        else:
          self.ui.emergencyStopLbl.setStyleSheet("border:4px solid black;border-radius:20px;background-color:red;")
          self.ui.emergencyStop2Lbl.setStyleSheet("border:4px solid black;border-radius:20px;background-color:red;")
        self.blinkingStop = not self.blinkingStop


    def btnsGo(self):
        print('btnsGo')

        if(not self.unlocked):
           self.blinkingGo = True
           self.blinkGo()
           self.unlockId = self.unlockCode
           filename = 'users.csv'
           found = False
           if(exists(filename)):
             with open(filename, mode='rt') as f:
               fieldNames = ['id', 'name']
               csvReader = csv.DictReader(f, delimiter=',', fieldnames=fieldNames)
               for row in csvReader:
                 if(row['id'] == self.unlockCode):
                   found = True
                   break
           else:
             found = self.config.unlock == self.unlockCode

           if(found):
             self.unlocked = True
             self.unlockId = self.unlockCode
             self.ui.unlockGroup.hide()
             self.ui.cyclesGroupBox.show()
             self.btnsClear()
             self.resetBtns(True)
             self.ui.setupBtn.show()
           else:
             self.unlockCode = ''
             self.ui.unlockKeyLbl.setText('')

           return

        self.ui.setupBtn.hide()
        self.blinkingGo = True
        self.blinkGo()

        self.ui.timeMMLbl.setText("")
        self.ui.timeColonLbl.setText("")
        self.ui.timeSSLbl.setText("")

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(False)

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(False)

        self.ui.buttonGoBtn.setEnabled(False)


        self.ui.axialPressureSlider.setEnabled(False)
        self.ui.cyclesSlider.setEnabled(False)
 

        self.protocolValue += str(self.buttonValue)
        print('protocol {}'.format(self.protocolValue))


        self.ui.statusLbl_2.setText('')

        options = ' Cycles: ' + str(self.cycles)
        protocol = ''
        if(self.protocolValue[1:2].isnumeric()):
          protocol = self.protocolValue[0:1]
        else:
          protocol = self.protocolValue[0:2]

        self.ui.statusLbl.setText('Protocol Started')

        self.arduino.send('L5{:3} {:3}'.format(self.config.AMarks['0.0'], self.config.BMarks['0.0']))
        self.I2Cstatus = 0
        time.sleep(1.5)
#        while(self.I2Cstatus == 0):
#          time.sleep(0.1)
#        self.I2Cstatus = 0
        print('end')

        self.ui.timeGroup.show()
        self.protocolTimer.start()

        QApplication.processEvents()
        self.elapsedTimer.start(1000)

#        self.logProtocol(self.protocolValue, self.cycles, self.axialPressure, self.minusHorizontalDegrees, self.plusHorizontalDegrees,self.leftLatAngle, self.rightLatAngle)
        if(protocol == 'A'):
          self.worker = AProtocols.Protocols(self.config.AFactor, self.protocolValue, self.axialPressure, self.cycles, self.arduino)
          options = 'Pressure: ' + str(self.axialPressure)

        if(protocol == 'B'):
          inches = self.BDegreeList[self.minusHorizontalDegrees] #set as initial angle
          horizontalPosition = int(inches * self.config.BFactor / 6.0)
          inches = self.BDegreeList[self.plusHorizontalDegrees] #set as initial angle
          horizontalStartPosition = int(inches * self.config.BFactor / 6.0)

          self.worker = BProtocols.Protocols(self.config.BFactor, self.protocolValue, self.minusHorizontalDegrees, self.plusHorizontalDegrees, self.cycles, self.arduino)
          options = 'Minus ' + str(self.minusHorizontalDegrees) + DEGREES + ' Plus ' + str(self.plusHorizontalDegrees) + DEGREES

        if(protocol == 'C'):
          self.worker = CProtocols.Protocols(self.config.CFactor, self.protocolValue, self.leftLatAngle, self.rightLatAngle, self.cycles, self.arduino, self.config)
          options = 'Left: ' + str(self.leftLatAngle) + DEGREES + ' Right: ' + str(self.rightLatAngle) + DEGREES

        if(protocol == 'D'):
          self.worker = DProtocols.Protocols(self.config.CFactor, self.protocolValue, self.leftLatAngle, self.rightLatAngle, self.cycles, self.arduino, self.config)
          options = 'Left: ' + str(self.leftLatAngle) + DEGREES + ' Right: ' + str(self.rightLatAngle) + DEGREES

        if(protocol == 'AB'):
          self.worker = ABProtocols.Protocols(self.config.BFactor, self.protocolValue, self.axialPressure, self.minusHorizontalDegrees, self.plusHorizontalDegrees, self.cycles, self.arduino)
          options = 'Pressure: ' + str(self.axialPressure)

        if(protocol == 'AC'):
          self.plusHorizontalDegrees = 0
          self.worker = ACProtocols.Protocols(self.config.CFactor, self.protocolValue, self.axialPressure, self.leftLatAngle, self.rightLatAngle, self.plusHorizontalDegrees, self.cycles, self.arduino, self.config)
          options = 'Pressure: ' + str(self.axialPressure)

        if(protocol == 'AD'):
          self.plusHorizontalDegrees = 0
          self.worker = ADProtocols.Protocols(self.config.CFactor, self.protocolValue, self.axialPressure, self.leftLatAngle, self.rightLatAngle, self.plusHorizontalDegrees, self.cycles, self.arduino, self.config)
          options = 'Pressure: ' + str(self.axialPressure)

        self.ui.programLbl.setText(self.protocol)
        self.ui.programLbl_2.setText(options)

        self.worker.signals.finished.connect(self.protocolCompleted)
        self.worker.signals.progress.connect(self.protocolProgress)
        self.worker.signals.APressure.connect(self.AProtocolPressure)

        self.threadpool.start(self.worker)

        self.blinkGo()
        self.goTimer.start(500)

    def statusEmit(self, s1, s2, s3, s4):
        print('status emit: {} {} {} {}'.format(s1, s2, s3, s4))
#        self.ui.axialFlexionPressureLbl.setText(str(s4))
        self.ui.measuredWeightLbl.setText('{:.1f} lb'.format(s4))
#        self.ui.axialFlexionPressureSlider.setValue(round(s4/5,0))
        zero = int( self.config.AMarks['0.0'])
        inches = ((s1 + zero)  * 8.0)/ self.config.AFactor
        print(' positioned to {}  {} {} in.'.format(zero, s1, inches))
        self.ui.measuredLocationlbl.setText('{:.1f} in'.format(inches))

    def protocolProgress(self, status):
        print('Progress: {}'.format(status))
        if(status[:2] == '>>'):
          self.ui.statusLbl_2.setText(str(status))

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
          self.horizontalFlexionPosition = horizontalDegrees
          return
        if(actuator == self.actuatorA):
          inches = self.ui.axialFlexionPositionSlider.value() / 2.0
          self.setToDistance(inches, actuator, self.config.AFactor)
          self.axialFlexionPosition = inches
          return
        if(actuator == self.actuatorC):
          horizontalDegrees = self.ui.lateralFlexionPositionSlider.value()
          inches = abs((horizontalDegrees + 20) / 20)
          print('inches ', inches)
#          self.setToDistance(inches, actuator, self.config.CFactor)
          self.setToCDistance(horizontalDegrees)
          self.lateralFlexionPosition = horizontalDegrees
          return

    def axialFlexionPositionChanged(self):
        inches = self.ui.axialFlexionPositionSlider.value() / 2.0
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
        self.minusHorizontalDegrees = self.ui.horizontalPositionFlexionSlider.value()
        if((self.minusHorizontalDegrees % 5) != 0):
           return
        self.ui.horizontalPositionFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)
	
    def lateralFlexionPositionChanged(self):
        self.minusHorizontalDegrees = self.ui.lateralFlexionPositionSlider.value()
        if((self.minusHorizontalDegrees % 5) != 0):
           return
        self.ui.lateralFlexionPositionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)

    def ABaxialPressureChanged(self):
        self.axialPressure = self.ui.ABaxialPressureSlider.value()
        self.ui.ABaxialPressureLbl.setText(str(self.axialPressure) + "#")
        options = 'Pressure: ' + str(self.axialPressure)
        self.ui.programLbl_2.setText(options)
	
    def ACDaxialPressureChanged(self):
        self.axialPressure = self.ui.ACDaxialPressureSlider.value()
        self.ui.ACDaxialPressureLbl.setText(str(self.axialPressure) + "#")
        options = 'Pressure: ' + str(self.axialPressure)
        self.ui.programLbl_2.setText(options)
	
    def axialPressureChanged(self):
        self.axialPressure = self.ui.axialPressureSlider.value()
        self.ui.axialPressureLbl.setText(str(self.axialPressure) + "#")
        options = 'Pressure: ' + str(self.axialPressure)
        self.ui.programLbl_2.setText(options)
	
    def minusHorizontalFlexionChanged(self):
        self.minusHorizontalDegrees = self.ui.minusHorizontalFlexionSlider.value()
        self.ui.minusHorizontalFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)
        options = str(self.minusHorizontalDegrees) + DEGREES + ' Start ' + str(self.plusHorizontalDegrees) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def plusHorizontalFlexionChanged(self):
        self.plusHorizontalDegrees = self.ui.plusHorizontalFlexionSlider.value()
        self.ui.plusHorizontalFlexionLbl.setText(str(self.plusHorizontalDegrees) + DEGREES)
        options = str(self.plusHorizontalDegrees) + DEGREES + ' Start ' + str(self.plusHorizontalDegrees) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def minusABHorizontalFlexionChanged(self):
        self.minusHorizontalDegrees = self.ui.minusABHorizontalFlexionSlider.value()
        self.ui.minusABHorizontalFlexionLbl.setText(str(self.minusHorizontalDegrees) + DEGREES)
        options = str(self.minusHorizontalDegrees) + DEGREES + ' Start ' + str(self.plusHorizontalDegrees) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def plusABHorizontalFlexionChanged(self):
        self.plusHorizontalDegrees = self.ui.plusABHorizontalFlexionSlider.value()
        self.ui.plusABHorizontalFlexionLbl.setText(str(self.plusHorizontalDegrees) + DEGREES)
        options = str(self.minusHorizontalDegrees) + DEGREES + ' Start ' + str(self.plusHorizontalDegrees) + DEGREES
        self.ui.programLbl_2.setText(options)

    def leftLatFlexionchanged(self):
        self.leftLatAngle = self.ui.leftLatFlexionSlider.value() #20-
        self.ui.leftLatFlexionLbl.setText(str(self.leftLatAngle) + DEGREES)
        options = 'Left: ' + str(self.leftLatAngle) + DEGREES + ' Right: ' + str(self.rightLatAngle) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def rightLatFlexionchanged(self):
        self.rightLatAngle = self.ui.rightLatFlexionSlider.value()
        self.ui.rightLatFlexionLbl.setText(str(self.rightLatAngle) + DEGREES)
        options = 'Left: ' + str(self.leftLatAngle) + DEGREES + ' Right: ' + str(self.rightLatAngle) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def ACDleftLatFlexionchanged(self):
        self.leftLatAngle = self.ui.ACDleftLatFlexionSlider.value() #20-
        self.ui.ACDleftLatFlexionLbl.setText(str(self.leftLatAngle) + DEGREES)
        options = 'Left: ' + str(self.leftLatAngle) + DEGREES + ' Right: ' + str(self.rightLatAngle) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def ACDrightLatFlexionchanged(self):
        self.rightLatAngle = self.ui.ACDrightLatFlexionSlider.value()
        self.ui.ACDrightLatFlexionLbl.setText(str(self.rightLatAngle) + DEGREES)
        options = 'Left: ' + str(self.leftLatAngle) + DEGREES + ' Right: ' + str(self.rightLatAngle) + DEGREES
        self.ui.programLbl_2.setText(options)
	
    def cyclesChanged(self):
        self.cycles = self.ui.cyclesSlider.value()
        self.cycles = int(round(self.cycles/5)*5)
        if(self.cycles == 0):
          self.cycles = 1
        self.ui.cyclesLbl.setText(str(self.cycles))
        options = ' Cycles: ' + str(self.cycles)
        self.ui.programLbl.setText(self.protocol + options)

	
    def btnsClear(self):		#need to reset all acuators
        self.elapsedTimer.stop()
        self.ui.timeGroup.hide()
        self.protocolTimer.invalidate()

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(True)
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")


        if(not self.unlocked):
           self.unlockCode = ''
           self.ui.unlockKeyLbl.setText('')

           for i in range(len(self.numberButtons)):
             self.numberButtons[i].setStyleSheet("background-color: blue;color:white")

           return

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(True)

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(True)

        self.ui.buttonGoBtn.setEnabled(True)

        self.resetBtns(True)
        self.firstLetter = ''
        self.ui.statusLbl_2.setText('')

        if(self.worker != None):
           self.worker.stop()

        self.ui.setupBtn.show()


        self.ui.statusLbl.setText('Protocol Stopped')
#        self.statusTimer.start(3000)
        self.stopTimer.stop()
        self.ui.emergencyStopLbl.setStyleSheet("border:4px solid black;border-radius:20px;background-color:red;")
        self.ui.emergencyStop2Lbl.setStyleSheet("border:4px solid black;border-radius:20px;background-color:red;")


    def resetBtns(self, letters):
        self.goTimer.stop()
        if(self.task):
           self.task.stop()
           print('task stop')

        self.buttonValue = 0
        self.protocol = ''
#        self.protocolValue = ''
        self.firstLetter = ''

        self.axialPressure = 10
        self.minusHorizontalDegrees = 15
        self.plusHorizontalDegrees = 15
        self.leftLatAngle = 0
        self.rightLatAngle = 0
        self.cycles = 1

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(False)
          self.numberButtons[i].setStyleSheet("background-color: blue;color:white")

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(True)
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")

        self.senderNumber = self.ui.button0Btn

        self.ui.buttonGoBtn.setEnabled(False)
        self.ui.buttonGoBtn.setStyleSheet("background-color: green;")


        self.ui.cyclesSlider.setValue(1)
        self.ui.cyclesLbl.setText('1')
        self.ui.cyclesSlider.setEnabled(True)


        self.ui.axialPressureSlider.setValue(10)
        self.ui.axialPressureLbl.setText('10 lb')
        self.ui.axialPressureSlider.setEnabled(True)

        self.ui.minusHorizontalFlexionSlider.setValue(15)
        self.ui.minusHorizontalFlexionLbl.setText('15' + DEGREES)
        self.ui.minusHorizontalFlexionSlider.setEnabled(True)
        self.ui.plusHorizontalFlexionSlider.setValue(15)
        self.ui.plusHorizontalFlexionLbl.setText('15' + DEGREES)
        self.ui.plusHorizontalFlexionSlider.setEnabled(True)

        self.ui.ABaxialPressureSlider.setValue(10)
        self.ui.ABaxialPressureLbl.setText('10 lb')
        self.ui.minusABHorizontalFlexionSlider.setValue(15)
        self.ui.minusABHorizontalFlexionLbl.setText('15' + DEGREES)
        self.ui.plusABHorizontalFlexionSlider.setValue(15)
        self.ui.plusABHorizontalFlexionLbl.setText('15' + DEGREES)

        self.ui.AGroupBox.hide()
        self.ui.CDGroupBox.hide()
        self.ui.BGroupBox.hide()
        self.ui.ABGroupBox.hide()
        self.ui.AXGroupBox.hide()
        self.ui.ACDGroupBox.hide()
        self.ui.rightLatFlexionSlider.setValue(0)
        self.ui.rightLatFlexionLbl.setText('0' + DEGREES)
        self.ui.leftLatFlexionSlider.setValue(0)
        self.ui.leftLatFlexionLbl.setText('0' + DEGREES)

        self.ui.ACDaxialPressureSlider.setValue(10)
        self.ui.ACDaxialPressureLbl.setText('10 lb')
        self.ui.ACDrightLatFlexionSlider.setValue(0)
        self.ui.ACDrightLatFlexionLbl.setText('0' + DEGREES)
        self.ui.ACDleftLatFlexionSlider.setValue(0)
        self.ui.ACDleftLatFlexionLbl.setText('0' + DEGREES)

        self.ui.statusLbl.setText('')
#        self.ui.statusLbl_2.setText('')
        self.ui.programLbl.setText('')
        self.ui.programLbl_2.setText('')

        self.ui.setupBtn.show()

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


        if(self.protocolValue == 'C'):
           self.ui.CDLeftGroupBox.show()
           self.ui.CDRightGroupBox.show()
           self.ui.CDLeftGroupBox.move(2,2)
           self.ui.CDRightGroupBox.move(219,2)
           if(self.buttonValue == 1):
             self.ui.CDLeftGroupBox.show()
             self.ui.CDRightGroupBox.hide()
           if(self.buttonValue == 2):
             self.ui.CDLeftGroupBox.hide()
             self.ui.CDRightGroupBox.show()
             self.ui.CDRightGroupBox.move(2,2)

        if(self.protocolValue == 'D'):
           self.ui.CDLeftGroupBox.show()
           self.ui.CDRightGroupBox.show()
           self.ui.CDLeftGroupBox.move(2,2)
           self.ui.CDRightGroupBox.move(219,2)
           if(self.buttonValue == 1):
             self.ui.CDLeftGroupBox.hide()
             self.ui.CDRightGroupBox.show()
             self.ui.CDRightGroupBox.move(2,2)
           if(self.buttonValue == 2):
             self.ui.CDLeftGroupBox.show()
             self.ui.CDRightGroupBox.hide()

        if(self.protocolValue == 'ABx'):
           self.ui.ABGroupBox.show()
           self.ui.minusABGroupBox.hide()
           self.ui.plusABGroupBox.hide()
           if(self.buttonValue == 1):
             self.ui.minusABGroupBox.show()
             self.ui.plusABGroupBox.hide()
           if(self.buttonValue == 2):
             self.ui.minusABGroupBox.show()
             self.ui.plusABGroupBox.show()
#             self.ui.plusABGroupBox.move(198,2)

        if(self.protocolValue == 'AC'):
           self.ui.ACDLeftGroupBox.show()
           self.ui.ACDRightGroupBox.show()
           self.ui.ACDLeftGroupBox.move(195,2)
           self.ui.ACDRightGroupBox.move(195,2)
           if(self.buttonValue == 2):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 4):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 6):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 8):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 1):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 3):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 5):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 7):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 9):
             self.ui.ACDRightGroupBox.move(380,2)
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.show()

        if(self.protocolValue == 'AD'):
           self.ui.ACDLeftGroupBox.show()
           self.ui.ACDRightGroupBox.show()
           self.ui.ACDLeftGroupBox.move(190,2)
           self.ui.ACDRightGroupBox.move(190,2)
           if(self.buttonValue == 1):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 3):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 5):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 7):
             self.ui.ACDLeftGroupBox.hide()
             self.ui.ACDRightGroupBox.show()
           if(self.buttonValue == 2):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 4):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 6):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 8):
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.hide()
           if(self.buttonValue == 9):
             self.ui.ACDRightGroupBox.move(360,2)
             self.ui.ACDLeftGroupBox.show()
             self.ui.ACDRightGroupBox.show()

#             self.ui.ACDRightGroupBox.move(2,2)


        self.ui.buttonGoBtn.setEnabled(True)


    def limitBtns(self, buttons):
        for i in range(len(self.numberButtons)):
          self.numberButtons[i].setEnabled(True)

        for i in range(len(buttons)):
          self.numberButtons[buttons[i]-1].setEnabled(False)



    def letterBtn(self):

#        if(len(self.protocol) == 2):
#           return

        sender = self.sender().text()  # This is what you need

        if(self.firstLetter == ''):

          self.protocolValue = sender
          self.resetBtns(False)

          for i in range(len(self.letterButtons)):
            self.letterButtons[i].setEnabled(True)
            self.letterButtons[i].setStyleSheet("background-color: grey;color:white")
          self.sender().setStyleSheet("background-color: green;color:white")
#          self.firstLetter = ''

          if(sender == 'A'):
            self.firstLetter = sender
            self.protocol = 'Traction '
            self.limitBtns([9])
            self.ui.AGroupBox.show()
            self.ui.CDGroupBox.hide()
            self.ui.BGroupBox.hide()
            self.ui.ABGroupBox.hide()
            self.ui.AXGroupBox.hide()
            self.ui.ACDGroupBox.hide()

          if(sender == 'B'):
            self.protocol = 'Flexion '
            self.limitBtns([4,5,6,7,8,9])
            self.ui.AGroupBox.hide()
            self.ui.BGroupBox.show()
            self.ui.CDGroupBox.hide()
            self.ui.ABGroupBox.hide()
            self.ui.AXGroupBox.hide()
            self.ui.ACDGroupBox.hide()

          if(sender == 'C'):
            self.protocol = 'Lateral '
            self.limitBtns([4,5,6,7,8,9])
            self.ui.AGroupBox.hide()
            self.ui.BGroupBox.hide()
            self.ui.CDGroupBox.show()
            self.ui.CDLeftGroupBox.hide()
            self.ui.CDRightGroupBox.hide()
            self.ui.ABGroupBox.hide()
            self.ui.AXGroupBox.hide()
            self.ui.ACDGroupBox.hide()

          if(sender == 'D'):
            self.protocol = 'Lateral '
            self.limitBtns([10,4,5,6,7,8,9])
            self.ui.AGroupBox.hide()
            self.ui.BGroupBox.hide()
            self.ui.CDGroupBox.show()
            self.ui.CDLeftGroupBox.hide()
            self.ui.CDRightGroupBox.hide()
            self.ui.ABGroupBox.hide()
            self.ui.AXGroupBox.hide()
            self.ui.ACDGroupBox.hide()
        else:
          if(self.firstLetter == 'A'):
#            self.resetBtns(True)
            self.limitBtns([10])
            if(sender != 'A'):
              if(self.buttonValue > 0):
                return
              self.sender().setStyleSheet("background-color: green;color:white")
              self.firstLetter = sender
              self.protocolValue += sender

              self.ui.AGroupBox.hide()
              self.ui.BGroupBox.hide()
              self.ui.CDGroupBox.hide()
              self.ui.ABGroupBox.hide()
              self.ui.AXGroupBox.hide()
              self.ui.ACDGroupBox.hide()

              if(sender == 'B'):
                self.protocol = 'Flexion '
                self.limitBtns([10,5,6,7,8,9])
                self.ui.ABGroupBox.show()
                self.ui.AXGroupBox.hide()
                self.ui.ACDGroupBox.hide()
 
              if(sender == 'C'):
                self.limitBtns([10])
                self.protocol = 'Lateral '
                self.ui.ACDLeftGroupBox.hide()
                self.ui.ACDRightGroupBox.hide()
                self.ui.ACDGroupBox.show()
                self.ui.ACDLeftGroupBox.raise_()
    
              if(sender == 'D'):
                self.limitBtns([10])
                self.protocol = 'Lateral '
                self.ui.ACDGroupBox.show()
                self.ui.ACDLeftGroupBox.hide()
                self.ui.ACDRightGroupBox.hide()
                self.ui.ACDRightGroupBox.raise_()


        options = ' Cycles: ' + str(self.cycles)
        self.ui.programLbl.setText(self.protocol + options)
        self.ui.programLbl_2.setText('')

    def goBack(self):
        print(self.config.flexionPosition)
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

    def setupD(self):
        self.worker = DProtocols.Protocols(self.config.CFactor, 'S', 0, 0)
        self.worker.signals.finished.connect(self.protocolCompleted)
        self.threadpool.start(self.worker)


    def gotoSetup(self):
        self.ui.stackedWidget.setCurrentIndex(1)


    def shutdown(self):
#        self.playVideoMP4.stop()
#        self.playScriptMP4.stop()
        if(os.path.exists("debug.txt")):
           self.exitApp()
        print('shutdown')
        self.shutdownApp()

    '''
    def setI2CStatus(self, channel):
      self.I2Cstatus = GPIO.input(channel)
      print('self.I2Cstatus = {}'.format(self.I2Cstatus))
    '''

    def setupGPIO(self):

     GPIO.setmode(GPIO.BCM)
     GPIO.setwarnings(False)

     GPIO.setup(EMERGENCYSTOP, GPIO.OUT)

     GPIO.setup(EXTRAFORWARD, GPIO.OUT)
     GPIO.setup(EXTRABACKWARD, GPIO.OUT)
     GPIO.setup(EXTRAENABLE, GPIO.OUT)

     GPIO.output(EMERGENCYSTOP, GPIO.HIGH)
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

