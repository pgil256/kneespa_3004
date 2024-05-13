# -*- coding: utf-8 -*-
"""

@author: grimesr
"""
from datetime import datetime
import time
import threading

import RPi.GPIO as GPIO

import serial

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt5.QtCore import pyqtSlot


ARDUINOI2C = 26

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

'''
Incremental Increase/decrease max at 5
Left 20     -20   0"
Left 15     -15   1/8"
Left 10     -10   1/4"
Left 5        -5     3/8"
CENTER      0     1/2"
Right 5     +5     5/8"
Right 10  +10   3/4"
Right 15  +15   7/8"
Right 20  +20    1"

 1 degree = .025 inch
'''
DEGREES10 = 4
DEGREES0 = 0

class KeepPressure(QtCore.QRunnable):
   def __init__(self, _ser, pressure, parent=None):
     super(KeepPressure, self).__init__()

     self.pressure = pressure
     self.ser = _ser
     self.running = False

   @pyqtSlot()
   def run(self):
     print("Pressure Thread start")
     self.running = True

     self.setToPressure(self.pressure)

   def stop(self):
     print('Pressure stop')
     self.running = False

     self.setToPressure(self.pressure)

   def setToPressure(self, desiredPressure):
     print('thread {}'.format(desiredPressure))
     while self.running:
       command = 'I{}\n'.format(12)
       self.ser.write(command.encode())                #transmit data serially 

       command = 'P{}\n'.format(desiredPressure)
       self.ser.write(command.encode())                #transmit data serially 
       print('cmd {}'.format(command.strip()))

       time.sleep(0.5)

     print('end')

 
class Protocols(QtCore.QRunnable):
   progress = pyqtSignal(str)
   completed = pyqtSignal()
   finished = pyqtSignal()

   protocol = ''
   pressure = 0
   cycles = 0

   protocolList = ['S', 'C1', 'C2', 'C3', 'C0']
   def __init__(self, _CFactor, protocol, leftDegrees, rightDegrees, cycles, ser, parent=None):
#     QThread.__init__(self, parent)
     super(Protocols, self).__init__()

     self.arduino = ser

     self.CFactor = _CFactor
     print(self.CFactor)

     print('c protocol')
     self.signals = WorkerSignals()

     self.degreeList = {1:.025, 5:.625, 10:.75, 15:.875, 20:1, 0:.5, -5:.375, -10:.25, -15:.125, -20:0}

     self.protocol = protocol
     self.leftDegrees = leftDegrees
     self.rightDegrees = rightDegrees
     self.cycles = cycles

     self.isRunning = False
     self.I2Cstatus = 0

     print(self.protocol, self.protocolList)
     if(self.protocol not in self.protocolList):
        return

     self.ser = serial.Serial('/dev/ttyS0',115200)
     self.ser.flush()
     print(self.ser)

     self.isRunning = False
     self.exitFlag = threading.Event()

   @pyqtSlot()
   def run(self):
     print("Thread start")

     self.setupGPIO()
     self.isRunning = True

     if(self.protocol[0] == 'S'):
       print('setup')
       self.setup()

     if(self.protocol[0] == 'C'):
       self.CProtocol(self.protocol, self.leftDegrees, self.rightDegrees, self.cycles)
     print('thread END')
#     self.completed.emit()
     self.signals.finished.emit()  # Done
     GPIO.cleanup()           # clean up GPIO on normal exit

   def stop(self):
     print('stop')
     self.isRunning = False
     self.exitFlag.set()

     try:
       pass
#       self.actuator.set_target_speed(0) #stop here
     except Exception as e:
       print(str(e))


   def CProtocol(self, protocol, leftDegrees, rightDegrees, cycles):
     print('{} degrees {}/{} cycles {}'.format(protocol, leftDegrees, rightDegrees, cycles))

#     self.setToZero()

     if(protocol == 'C1'):
        self.protocol1(leftDegrees, cycles)
     if(protocol == 'C2'):
        self.protocol2(rightDegrees, cycles)
     if(protocol == 'C3'):
        self.protocol3(leftDegrees, rightDegrees, cycles)
     if(protocol == 'C0'):
        self.protocol0(leftDegrees)


   def killProtocol(self):
     self.isRunning = False

   def setup(self):
     inches = self.degreeList[10] #set as initial angle
     position = int(inches * self.CFactor)
     self.setToDistance(position)
     print(' positioned to {} in.'.format(inches))

   def setToPosition(self, speed, position):
     pass

   def I2CStatus(self):
     self.I2Cstatus = True


   def setToZero(self):
     inches = self.degreeList[0]
     position = int(inches * self.CFactor)
     command = 'Z14{}\n'.format(position)
     self.ser.write(command.encode())                #transmit data serially 
     while(self.I2Cstatus == 0):
       if(not self.isRunning):
          self.ser.write('X'.encode())                #transmit data serially 
          print('stopped')
          return

       time.sleep(0.1)
     print('end')


   def setToDistance(self, degrees):
     print(degrees)
#     inches = self.degreeList[degrees] #set as initial angle
     inches = (degrees *0.05) + 1
     position = int(inches * self.CFactor / 6)
     print(' positioned to {} deg {} in. {} pos'.format(degrees, inches, position))

     command = 'K{}'.format(position)
     self.arduino.send(command)
     print('cmd {}'.format(command.strip()))

     while(self.I2Cstatus == 0):
       if(not self.isRunning):
          self.arduino.send('X')                #transmit data serially 
          print('stopped')
          return

       time.sleep(0.1)
     self.I2Cstatus = 0
     print('end')


   def setToDistancex(self, position):
     print(position)

     command = 'K{}\n'.format(position)
     print('cmd {}'.format(command.strip()))
     self.ser.write(command.encode())                #transmit data serially 

     while(self.I2Cstatus == 0):
       if(not self.isRunning):
          self.ser.write('X'.encode())                #transmit data serially 
          print('stopped')
          return

       time.sleep(0.1)
     self.I2Cstatus = 0
     print('end')

   def setToPressure(self, desiredPressure):

     command = 'I{}\n'.format(12)
     self.ser.write(command.encode())                #transmit data serially 

     command = 'P{}\n'.format(desiredPressure)
     self.ser.write(command.encode())                #transmit data serially 
     print('cmd {}'.format(command.strip()))

     while(self.I2Cstatus == 0):
       if(not self.isRunning):
          self.ser.write('X\n'.encode())                #transmit data serially 
          print('stopped')
          return

       time.sleep(0.1)
     self.I2Cstatus = 0
     print('end')

   def retract(self):
     command = 'I{}\n'.format(14)
     self.ser.write(command.encode())                #transmit data serially 

     command = 'R+\n'
     self.ser.write(command.encode())                #transmit data serially 
     while(self.I2Cstatus == 0):
       if(not self.isRunning):
          self.ser.write('X'.encode())                #transmit data serially 
          print('stopped')
          return

       time.sleep(0.1)
     print('end')

   def protocol0(self, degrees):

     self.threadpool = QtCore.QThreadPool()
     print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
     self.pressureWorker = KeepPressure(self.ser, 3)
     self.threadpool.start(self.pressureWorker)

     self.setToDistance(degrees)
     print(' positioned to {} in.'.format(inches))
     time.sleep(10)
     self.pressureWorker.stop()

     self.signals.finished.emit()


   def protocol1(self, degrees, cycles):

     for cycle in range(1, cycles+1):
       print('cycle {}'.format(cycle))

       self.setToDistance(DEGREES0)

       print('Positioned to 0 degrees')

       dir = 1
       if(degrees < 0):
         dir = -1
       for push in range(1, abs(degrees)+1, 1):
         if(not self.isRunning):
           print('stopped')
           return

         self.signals.progress.emit('Cycle {} Degrees {}'.format(cycle, push * dir))

         self.setToDistance(push * dir)

         print('positioned')
         print('  degrees {}'.format(push * dir))
         print('  hold 5')
         self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, push * dir))

         self.exitFlag.wait(timeout=5)

       print('  hold +15')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, degrees))
       self.exitFlag.wait(timeout=15)
       self.setToDistance(DEGREES0)

     print(' release')
     self.setToDistance(DEGREES0)

     self.signals.finished.emit()

   def protocol2(self, degrees, cycles):

     for cycle in range(1, cycles+1):
       print('cycle {}'.format(cycle))

       self.setToDistance(DEGREES0)

       print('Positioned to 0 degrees')

       for push in range(1, degrees+1, 1):
         if(not self.isRunning):
           print('stopped')
           return

         self.signals.progress.emit('Cycle {} Degrees {}'.format(cycle, push))

         print('move {}'.format(push))

         self.setToDistance(push)

         print('positioned')
         print('  degrees {}'.format(push * dir))
         print('  hold 5')
         self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, push))

         self.exitFlag.wait(timeout=5)

       print('  hold +15')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, degrees))
       self.exitFlag.wait(timeout=15)
       self.setToDistance(DEGREES0)

     print(' release')
     self.setToDistance(DEGREES0)

     self.signals.finished.emit()

   def protocol3(self, leftDegrees, rightDegrees, cycles):

     for cycle in range(1, cycles+1):
       print('cycle {}'.format(cycle))

       self.setToDistance(DEGREES0)

       print('Positioned to 0 degrees')

       dir = 1
       if(leftDegrees < 0):
         dir = -1
       for push in range(1, abs(leftDegrees)+1, 1):
         if(not self.isRunning):
           print('stopped')
           return

         self.signals.progress.emit('Cycle {} Degrees {}'.format(cycle, push * dir))

         self.setToDistance(push * dir)

         print('positioned')
         print('  degrees {}'.format(-push))
         print('  hold 5')
         self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, -push))

         self.exitFlag.wait(timeout=5)

       print('  hold +5')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, -push))
       self.exitFlag.wait(timeout=5)

       self.setToDistance(DEGREES0)
       print('Positioned to 0 degrees')

       for push in range(1, rightDegrees+1, 1):
         if(not self.isRunning):
           print('stopped')
           return

         self.signals.progress.emit('Cycle {} Degrees {}'.format(cycle, push))

         print('move {}'.format(push))

         self.setToDistance(push)

         print('positioned')
         print('  degrees {}'.format(push))
         print('  hold 5')
         self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, push))

         self.exitFlag.wait(timeout=5)

       print('  hold +5')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, push))
       self.exitFlag.wait(timeout=5)

     print(' release')
     self.setToDistance(DEGREES0)

     self.signals.finished.emit()


   def setI2CStatus(self, channel):
      self.I2Cstatus = 1
      print('self.I2Cstatus = 1')

   def setupGPIO(self):

     GPIO.setmode(GPIO.BCM)
     GPIO.setwarnings(False)

#     GPIO.remove_event_detect(ARDUINOI2C)
#     GPIO.setup(ARDUINOI2C, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#     GPIO.add_event_detect(ARDUINOI2C, GPIO.RISING, callback=self.setI2CStatus, bouncetime = 200)

     print('setupGPIO')

