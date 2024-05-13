#!/usr/bin/env python
# coding: utf-8

# adc https://github.com/adafruit/Adafruit_Blinka/blob/master/examples/analog_in.py

from time import sleep
import os
from datetime import datetime, timedelta
import sys
import time

import RPi.GPIO as GPIO

import smcG2 as SMCG2

EXTRAFORWARD = 17
EXTRABACKWARD = 27

import AProtocols
import BProtocols
import CProtocols

import adc
import config

#these are for the PyQT5. There is overlap and should be cleaned up.
#pyrcc5 resources.qrc -o resources_rc.py

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QTime, QTimer, QEvent, QDateTime, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDesktopWidget, QTableWidgetItem

os.chdir('/home/pi/kneespa')

DEGREES = u'\u00b0'

# Step 1: Create a worker class
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        """Long-running task."""
        for i in range(5):
            sleep(1)
            self.progress.emit(i + 1)
            print(i)
        self.finished.emit()
        print('finisihed')
#the kneespa.ui is the UI definition file. It is created via the QT Designer tool
Ui_MainWindow, QtBaseClass = uic.loadUiType('kneespa.ui')

#this is the main program class which is the UI. It is driven by PyQT5 processes and interacts with the pump.ui file for display

class KeyboardWidget(QWidget):

    def keyPressEvent(self, keyEvent):
        print(keyEvent.text())

class MyApp(QMainWindow):
    def rebootApp(self):
       os.system("sudo shutdown -r now")
       os._exit(1)

    def shutdownApp(self):
       os.system("sudo shutdown -h now")
       os._exit(1)

    def exitApp(self):
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

    def __init__(self,):
        super(MyApp, self).__init__()

        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)
#        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint) 

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().screenGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        centerWidth = centerPoint.x() - self.ui.mainFrame.width()/2
        centerHeight = centerPoint.y() - self.ui.mainFrame.height()/2
        centerPoint = self.ui.mainFrame.frameGeometry().center() - QtCore.QRect(QtCore.QPoint(), self.ui.mainFrame.sizeHint()).center()
#        self.ui.mainFrame.move(centerWidth,centerHeight)

        self.goTimer = QTimer(self)
        self.goTimer.timeout.connect(self.blinkGo)
        self.blinkingGo = True

        self.statusTimer = QTimer(self)
        self.statusTimer.timeout.connect(self.clearStatus)

        self.ui.exitBtn.hide()
        if(os.path.exists("debug.txt")):
          self.ui.exitBtn.show()
          self.show()
        else:
           self.showMaximized()
           self.showFullScreen()

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
        self.resetBtns(True)

        self.I2Cstatus = 0

        self.ui.goBackBtn.clicked.connect(self.goBack)
        self.ui.setupBtn.clicked.connect(self.gotoSetup)

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].clicked.connect(self.letterBtn)

        for i in range(len(self.numberButtons)):
          self.numberButtons[i].clicked.connect(self.numberBtn)
        self.ui.button1Btn.clicked.connect(self.numberBtn)

        self.ui.buttonClearBtn.clicked.connect(self.btnsClear)
        self.ui.buttonGoBtn.clicked.connect(self.btnsGo)

        self.ui.buttonClearBtn.installEventFilter(self)

        self.ui.axialPressureSlider.valueChanged.connect(self.axialPressureChanged)
        self.ui.horizontalFlexionSlider.valueChanged.connect(self.horizontalFlexionChanged)
        self.ui.leftLatFlexionSlider.valueChanged.connect(self.leftLatFlexionchanged)
        self.ui.rightLatFlexionSlider.valueChanged.connect(self.rightLatFlexionchanged)
        self.ui.cyclesSlider.valueChanged.connect(self.cyclesChanged)

        self.ui.forwardAxialFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(12, 0.065))
        self.ui.reverseAxialFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(12, 0.065))
        self.ui.resetAxialFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(12))
        self.axialFlexionPosition = 0.0
        self.axialFlexionClicks = 0

        self.ui.forwardHorizontalFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(13, 0.065))
        self.ui.reverseHorizontalFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(13, 0.065))
        self.ui.resetHorizontalFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(13))
        self.horizontalFlexionPosition = 0.0
        self.horizontalFlexionClicks = 0

        self.ui.forwardLateralFlexionBtn.clicked.connect(lambda: self.forwardFlexionBtn(14, 0.0328))
        self.ui.reverseLateralFlexionBtn.clicked.connect(lambda: self.reverseFlexionBtn(14, 0.0328))
        self.ui.resetLateralFlexionBtn.clicked.connect(lambda: self.resetFlexionBtn(14))
        self.lateralFlexionPosition = 0.0
        self.lateralFlexionClicks = 0

        self.ui.forwardExtraBtn.clicked.connect(self.forwardExtraBtnClicked)
        self.ui.reverseExtraBtn.clicked.connect(self.reverseExtraBtnClicked)
        self.ui.resetExtraBtn.clicked.connect(self.resetExtraBtnClicked)

        self.ui.axialFlexionPositionTxt.hide()
        self.ui.horizontalFlexionPositionTxt.hide()
        self.ui.lateralFlexionPositionTxt.hide()
        self.ui.extraPositionTxt.hide()

        self.config = config.Configuration()
        self.config.getConfig()

        self.adc = adc.ADC()


        fileTime = datetime.fromtimestamp(os.path.getmtime(__file__))
        version = 'V-{}'.format(fileTime.strftime("%m.%d.%Y"))
        self.ui.versionLbl.setText(version)

        self.threadpool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # Step 2: Create a QThread object


        self.worker = None
        self.ui.stackedWidget.setCurrentIndex(0)


#        self.setupA()

        self.setupGPIO()

        # Step 2: Create a QThread object
        self.smcG2Athread = QThread()
        # Step 3: Create a worker object
        # Select the I2C address of the Simple Motor Controller (the device number).
        self.smcG2A = SMCG2.SMCG2(11, 0x0C)
        # Step 4: Move worker to the thread
        self.smcG2A.moveToThread(self.smcG2Athread)
        # Step 5: Connect signals and slots
        # Step 6: Start the thread
        print('G2A starting')
        self.smcG2Athread.start()
        self.smcG2Athread.started.connect(self.smcG2A.run)
        time.sleep(3)
        print('G2A started')

        self.smcG2Bthread = QThread()
        self.smcG2B = SMCG2.SMCG2(11, 0x0D)
        self.smcG2B.moveToThread(self.smcG2Bthread)
        print('G2B starting')
        self.smcG2Bthread.start()
        self.smcG2Bthread.started.connect(self.smcG2B.run)
        time.sleep(3)
        print('G2B started')

        self.smcG2Cthread = QThread()
        self.smcG2C = SMCG2.SMCG2(11, 0x0E)
        self.smcG2C.moveToThread(self.smcG2Cthread)
        print('G2C starting')
        self.smcG2Cthread.start()
        self.smcG2Cthread.started.connect(self.smcG2C.run)
        time.sleep(3)
        print('G2C started')

    def forwardExtraBtnClicked(self):
        GPIO.output(EXTRABACKWARD, GPIO.LOW)
        GPIO.output(EXTRAFORWARD, GPIO.HIGH)

    def reverseExtraBtnClicked(self):
        GPIO.output(EXTRAFORWARD, GPIO.LOW)
        GPIO.output(EXTRABACKWARD, GPIO.HIGH)

    def resetExtraBtnClicked(self):
        GPIO.output(EXTRAFORWARD, GPIO.LOW)
        GPIO.output(EXTRABACKWARD, GPIO.LOW)


    def forwardFlexionBtn(self, actuator, step):
        if(self.lateralFlexionPosition >= 6.0):
          self.lateralFlexionPosition = 6.0
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
          return

        if(actuator == 0x0C):
          if(self.axialFlexionPosition >= 60.0):
            self.axialFlexionPosition = 6.0
            self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
            return
        if(actuator == 0x0D):
          if(self.horizontalFlexionPosition >= 6.0):
            self.horizontalFlexionPosition = 6.0
            self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
            return
        if(actuator == 0x0E):
          if(self.lateralFlexionPosition >= 6.0):
            self.lateralFlexionPosition = 6.0
            self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
            return


        if(actuator == 0x0C):
          self.smcG2A.moveForTime(0.2)
          self.axialFlexionClicks += 1
          print(self.axialFlexionClicks)
          self.axialFlexionPosition += step
          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
        if(actuator == 0x0D):
          self.smcG2B.moveForTime(0.2)
          self.horizontalFlexionClicks += 1
          self.horizontalFlexionPosition += step
          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
        if(actuator == 0x0E):
          self.smcG2C.moveForTime(0.2)
          self.lateralFlexionClicks += 1
          print(self.lateralFlexionClicks)
          self.lateralFlexionPosition += step
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))

    def resetFlexionBtn(self, actuator):

        if(actuator == 0x0C):
          self.smcG2A.setReset()
          self.axialFlexionClicks = 0
          print(self.axialFlexionClicks)
          self.axialFlexionPosition = 0.0
          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
        if(actuator == 0x0D):
          self.smcG2B.setReset()
          self.horizontalFlexionClicks = 0
          self.horizontalFlexionPosition = 0.0
          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
        if(actuator == 0x0E):
          self.smcG2C.setReset()
          self.lateralFlexionClicks = 0
          print(self.lateralFlexionClicks)
          self.lateralFlexionPosition = 0.0
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))


    def reverseFlexionBtn(self, actuator, step):

        if(actuator == 0x0C):
          if(self.axialFlexionPosition <= 0.0):
            self.axialFlexionPosition = 0.0
            self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
#            return
        if(actuator == 0x0D):
          if(self.horizontalFlexionPosition <= 0.0):
            self.horizontalFlexionPosition = 0.0
            self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
            return
        if(actuator == 0x0E):
          if(self.lateralFlexionPosition <= 0.0):
            self.lateralFlexionPosition = 0.0
            self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))
            return

        if(actuator == 0x0C):
          self.smcG2A.moveForTime(-0.2)
          self.axialFlexionClicks -= 1
          print(self.axialFlexionClicks)
          self.axialFlexionPosition -= step
          self.ui.axialFlexionPositionTxt.setText(str(round(self.axialFlexionPosition,2)))
        if(actuator == 0x0D):
          self.smcG2B.moveForTime(-0.2)
          self.horizontalFlexionClicks -= 1
          self.horizontalFlexionPosition -= step
          self.ui.horizontalFlexionPositionTxt.setText(str(round(self.horizontalFlexionPosition,2)))
        if(actuator == 0x0E):
          self.smcG2C.moveForTime(-0.2)
          self.lateralFlexionClicks -= 1
          print(self.lateralFlexionClicks)
          self.lateralFlexionPosition += step
          self.ui.lateralFlexionPositionTxt.setText(str(round(self.lateralFlexionPosition,2)))

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
        self.blinkingGo = True
        self.blinkGo()

        QApplication.processEvents()

        self.ui.axialPressureSlider.setEnabled(False)
        self.ui.horizontalFlexionSlider.setEnabled(False)
        self.ui.leftLatFlexionSlider.setEnabled(False)
        self.ui.rightLatFlexionSlider.setEnabled(False)
        self.ui.cyclesSlider.setEnabled(False)

        self.protocolValue += str(self.buttonValue)
        print('protocol {}'.format(self.protocolValue))


        print(self.protocolValue[0])
        if(self.protocolValue[0] == 'A'):
          self.worker = AProtocols.Protocols(self.config.AFactor, self.protocolValue, self.axialPressure, self.cycles)

        if(self.protocolValue[0] == 'B'):
          self.worker = BProtocols.Protocols(self.config.BFactor, self.protocolValue,self.horizontalDegrees, self.cycles, self.smcG2B)

        if(self.protocolValue[0] == 'C'):
          self.worker = CProtocols.Protocols(self.config.CFactor, self.protocolValue,self.leftLatAngle, self.cycles)

        self.worker.signals.finished.connect(self.protocolCompleted)
        self.threadpool.start(self.worker)

        self.blinkGo()
        self.goTimer.start(500)

    def protocolProgress(self, status):
        self.ui.statusLbl.setText(status)

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
	
    def btnsClear(self):		#need to reset all acuators
        if(self.worker != None):
           self.worker.stop()
        self.resetBtns(True)
        self.firstLetter = ''

        for i in range(len(self.letterButtons)):
          self.letterButtons[i].setEnabled(True)
          self.letterButtons[i].setStyleSheet("background-color: grey;color:white")

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


        self.ui.leftLatFlexionSlider.setValue(0)
        self.ui.leftLatFlexionLbl.setText('20' + DEGREES)
        self.ui.leftLatFlexionSlider.setEnabled(True)
        self.ui.leftLatFlexionTitleLbl.setGeometry(titleRect)
        self.ui.leftLatFlexionSlider.setGeometry(sliderRect)
        self.ui.leftLatFlexionLbl.setGeometry(lblRect)
        self.ui.leftLatFlexionTitleLbl.hide()
        self.ui.leftLatFlexionSlider.hide()
        self.ui.leftLatFlexionLbl.hide()

        self.ui.rightLatFlexionSlider.setValue(0)
        self.ui.rightLatFlexionLbl.setText('0' + DEGREES)
        self.ui.rightLatFlexionSlider.setEnabled(True)
        self.ui.rightLatFlexionTitleLbl.setGeometry(titleRect)
        self.ui.rightLatFlexionSlider.setGeometry(sliderRect)
        self.ui.rightLatFlexionLbl.setGeometry(lblRect)
        self.ui.rightLatFlexionTitleLbl.hide()
        self.ui.rightLatFlexionSlider.hide()
        self.ui.rightLatFlexionLbl.hide()


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
            self.ui.axialPressureTitleLbl.show()
            self.ui.axialPressureSlider.show()
            self.ui.axialPressureLbl.show()
  
          if(sender == 'B'):
            self.protocol = 'Horizontal Flexion'
            self.limitBtns([4,5,6,7,8,9])
            self.ui.horizontalFlexionTitleLbl.show()
            self.ui.horizontalFlexionSlider.show()
            self.ui.horizontalFlexionLbl.show()

          if(sender == 'C'):
            self.protocol = 'Left Leg Lateral Flexion'
            self.limitBtns([4,5,6,7,8,9])
            self.ui.leftLatFlexionTitleLbl.show()
            self.ui.leftLatFlexionSlider.show()
            self.ui.leftLatFlexionLbl.show()
  
          if(sender == 'D'):
            self.protocol = 'Right Leg Lateral Flexion'
            self.limitBtns([10,4,5,6,7,8,9])
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
        if(os.path.exists("debug.txt")):
           self.exitApp()
        print('shutdown')
        self.shutdownApp()


    def setupGPIO(self):

     GPIO.setmode(GPIO.BCM)
     GPIO.setwarnings(False)

     GPIO.setup(EXTRAFORWARD, GPIO.OUT)
     GPIO.setup(EXTRABACKWARD, GPIO.OUT)
     print(EXTRAFORWARD)
     print(EXTRABACKWARD)


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



# Wait until the job finishes
#while conn.getJobs().get(print_id, None):
#    sleep(1)
#unlink(output)
