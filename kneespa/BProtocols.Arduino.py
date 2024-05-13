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
DEGREES10 = 4

class KeepPressure(QtCore.QRunnable):
   def __init__(self, pressure, parent=None):
     super(KeepPressure, self).__init__()

     self.pressure = pressure

     self.running = False

   @pyqtSlot()
   def run(self):
     print("Pressure Thread start")
     self.running = True

   def stop(self):
     print('Pressure stop')
     self.running = False

     self.setToPressure(self.pressure)

   def setToPressure(self, desiredPressure):

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

   protocol = ''
   pressure = 0
   cycles = 0

   protocolList = ['S', 'B1', 'B2', 'B3', 'B0']
   def __init__(self, _BFactor, protocol, pressure, cycles, smcG2B, parent=None):
#     QThread.__init__(self, parent)
     super(Protocols, self).__init__()

     self.smcG2 = smcG2B

     self.BFactor = _BFactor

     self.signals = WorkerSignals()

     self.isRunning = False

     self.degreeList = {0:0, 5:5, 10:4, 15:3, 20:2, 25:1, 30:0}

     self.I2Cstatus = 0

     self.protocol = protocol
     self.pressure = pressure
     self.cycles = cycles

     print(self.protocol, self.protocolList)
     if(self.protocol not in self.protocolList):
        return

     self.ser = serial.Serial('/dev/ttyS0',115200)
     self.ser.flush()

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

     if(self.protocol[0] == 'B'):
       self.BProtocol(self.protocol, self.pressure, self.cycles)
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


   def BProtocol(self, protocol, degrees, cycles):
     print('{} degrees {} cycles {}'.format(protocol, degrees, cycles))

     if(protocol == 'B1'):
        self.protocol1(degrees, cycles)
     if(protocol == 'B2'):
        self.protocol2(degrees, cycles)
     if(protocol == 'B3'):
        self.protocol3(degrees, cycles)
     if(protocol == 'B0'):
        self.protocol0(degrees)


   def killProtocol(self):
     self.isRunning = False

   def setup(self):
     inches = self.degreeList[10] #set as initial angle
     position = int(inches * self.BFactor / 6.0)
     self.setToDistance(position)
     print(' positioned to {} in.'.format(inches))

   def setToPosition(self, speed, position):
     pass

   def setToDistance(self, position):
     print(position)

     command = 'A13{}\n'.format(position)
     self.ser.write(command.encode())                #transmit data serially 
     print('cmd {}'.format(command.strip()))

     while(self.I2Cstatus == 0):
       if(not self.isRunning):
          self.ser.write('X'.encode())                #transmit data serially 
          print('stopped')
          return

       time.sleep(0.1)
     self.I2Cstatus = 0
     print('end')

   def setToPressure(self, desiredPressure):

     command = 'I{}\n'.format(13)
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
     command = 'B\n'
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
#     self.pressureWorker = KeepPressure(3)
 #    self.threadpool.start(self.pressureWorker)

     inches = self.degreeList[degrees]
     position = int(inches * (self.BFactor / 6.0))
     self.smcG2.moveToDistance(position)
     print(' positioned to {} in.'.format(inches))

     self.signals.finished.emit()

   def Arduinoprotocol0(self, degrees):

     self.threadpool = QtCore.QThreadPool()
     print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
     self.pressureWorker = KeepPressure(3)
 #    self.threadpool.start(self.pressureWorker)

     inches = self.degreeList[degrees]
     position = int(inches * (self.BFactor / 6.0))
     self.setToDistance(position)
     print(' positioned to {} in.'.format(inches))

#     self.pressureWorker.stop()

     self.signals.finished.emit()



   def protocol1(self, degrees, cycles):

     for cycle in range(1, cycles+1):
       print('cycle {}'.format(cycle))

       print('self.setToPressure(5)')
#       self.setToPressure(5)

       inches = self.degreeList[10]
       position = int(inches * self.BFactor / 6.0)
       self.smcG2.moveToDistance(position)
       time.sleep(.5)
       print('move {}'.format(10))

       print('  hold 5')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, degrees))

       self.exitFlag.wait(timeout=5)

       inches = self.degreeList[degrees]
       position = int(inches * self.BFactor / 6.0)
       self.smcG2.moveToDistance(position)
       print('move {}'.format(degrees))

       print('  hold 5')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, DEGREES0))

       self.exitFlag.wait(timeout=5)

       if(not self.isRunning):
         print('stopped')
         return

     inches = self.degreeList[10]
     position = int(inches * self.BFactor / 6.0)
     self.smcG2.moveToDistance(position)
     time.sleep(.5)

     print(' release')

     self.signals.finished.emit()


   def Arduinoprotocol1(self, degrees, cycles):

     for cycle in range(1, cycles+1):
       print('cycle {}'.format(cycle))

       print('self.setToPressure(5)')
#       self.setToPressure(5)

       inches = self.degreeList[10]
       position = int(inches * self.BFactor / 6.0)
       self.setToDistance(position)
       time.sleep(.5)
       print('move {}'.format(10))

       print('  hold 5')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, degrees))

       self.exitFlag.wait(timeout=5)

       inches = self.degreeList[degrees]
       position = int(inches * self.BFactor / 6.0)
       self.setToDistance(position)
       print('move {}'.format(degrees))

       print('  hold 5')
       self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, DEGREES0))

       self.exitFlag.wait(timeout=5)

       if(not self.isRunning):
         print('stopped')
         return

     inches = self.degreeList[10]
     position = int(inches * self.BFactor / 6.0)
     self.setToDistance(position)
     time.sleep(.5)

     print(' release')

     self.signals.finished.emit()



   def protocol2(self, degrees, cycles):

     self.setToDistance(DEGREES0)

     for cycle in range(1, cycles+1):
       print('cycle {}'.format(cycle))

       currentDegrees = 5
       for push in range(currentDegrees, degrees+1, 5):
         if(not self.isRunning):
           print('stopped')
           return

         self.signals.progress.emit('Cycle {} Degrees {}'.format(cycle, push))

         print('move {}:{}'.format(push, self.degreeList[push]))

         self.setToDistance(self.degreeList[push])

         print('positioned')
         print('  degrees {}'.format(push))
         print('  hold 5')
         self.signals.progress.emit('Cycle {} Degrees {} hold 5 secs'.format(cycle, push))

         self.exitFlag.wait(timeout=5)

     print(' release')

     self.setToDistance(DEGREES0)

     self.signals.finished.emit()

   def protocol3(self, degrees, cycles):

     self.setToDistance(DEGREES0)

     for cycle in range(1, cycles+1):
       print('')
       print('cycle {}'.format(cycle))

       currentDegrees = 5
       for push in range(currentDegrees, degrees+1, 5):
         if(not self.isRunning):
           print('stopped')
           return

         self.signals.progress.emit('Cycle {} Degrees {}'.format(cycle, push))

         print('move {}:{}'.format(push, self.degreeList[push]))

         self.setToDistance(self.degreeList[push])

         print('positioned')
         print('  degrees {}'.format(push))
         print('  hold 5')
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

     GPIO.setup(ARDUINOI2C, GPIO.IN, pull_up_down=GPIO.PUD_UP)
     GPIO.remove_event_detect(ARDUINOI2C)
     GPIO.add_event_detect(ARDUINOI2C, GPIO.RISING, callback=self.setI2CStatus, bouncetime = 500)

     print('setupGPIO')

