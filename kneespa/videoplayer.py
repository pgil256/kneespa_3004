import signal
import os
import sys
from time import sleep
import time

import glob

from subprocess import Popen, PIPE
import threading

import RPi.GPIO as GPIO

import logging

# create logger

logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)

# create formatter
longFormatter = logging.Formatter('%(asctime)s:%(message)s',datefmt='%Y-%m-%d %H:%M:%S')
shortFormatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s',datefmt='%H:%M:%S')

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# add formatter to ch
ch.setFormatter(shortFormatter)

# add ch to logger
logger.addHandler(ch)

# create console handler and set level to debug
fh = logging.FileHandler('buttons.log', mode='w')
fh.setLevel(logging.DEBUG)
# add formatter to fh
fh.setFormatter(longFormatter)
# add fh to logger
logger.addHandler(fh)


os.chdir(os.path.dirname(os.path.abspath(__file__)))

HEARTBEAT_LED = 17    # pin11

FASTBLINK = 50
SLOWBLINK = 600

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#catch Ctrl+C
def signal_handler(signal, frame):

  GPIO.cleanup()           # clean up GPIO on normal exit
  sys.exit('You pressed Ctrl+C!')

signal.signal(signal.SIGINT, signal.SIG_DFL)

def exitApp(self):
       os._exit(1)


class playMP4(threading.Thread):
    def __init__(self, _videoPath):
       threading.Thread.__init__(self)
       self.baseVideoPath = 'Videos/'
       self.videoPath = _videoPath
       self.playing = True

    def __del__(self):
       self.wait()

    def nextVideo(self, path):
       self.videoPath = path
       self.playing = True

    def stop(self):
       try:
          process = Popen(['killall', 'omxplayer.bin'], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
          stdout, stderr = process.communicate()
          print(stdout, stderr)
          self.playing = False
       except Exception as e:
          print(str(e))
          print('omxplayer error')

    def done(self):
        print('done playing')
        self.background.play()

    def run(self):
       while self.playing:
         print('playing ' + self.videoPath)
         logger.debug('playing ' + self.videoPath)
         path = self.baseVideoPath + self.videoPath
         try:
            print('omxplayer start')
            process = Popen(['omxplayer', '-b', '-o', 'hdmi', path], stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
            stdout, stderr = process.communicate()
            print(stdout, stderr)
         except Exception as e:
            print(str(e))
            print('omxplayer error')
         sleep(0.001)

#         sleep(.25)


class MyApp():
    def blinkLED(self):
        if(self.LEDTimer.interval() != self.blink):
          print('LED {}'.format(self.LEDTimer.interval()))
          logger.debug('LED {}'.format(self.LEDTimer.interval()))
          self.blink = self.LEDTimer.interval()

        if(self.LEDState):
          GPIO.output(HEARTBEAT_LED, GPIO.LOW)  # led on
        else:
          GPIO.output(HEARTBEAT_LED, GPIO.HIGH) # led off
        self.LEDState = not self.LEDState

    def __init__(self):
        super(MyApp, self).__init__()


        self.buttons = [0] * 40
        self.readConfig()

        self.setupGPIO()

        self.player = playMP4("video.0.mp4")
        try:
           self.player.start()
        except:
           print("Error: unable to start thread")
        print("Thread started")

    def buttonDetected(self, channel):
        print('Button {} Detected'.format(channel))
        logger.debug('Button {} Detected'.format(channel))

        video = 'video.{}.mp4'.format(self.buttons[channel])

        if not os.path.exists(self.player.baseVideoPath + video):
          print('no video for ' + video)
          logger.debug('no video for ' + video)
          return

        self.player.stop()
        self.player.nextVideo(video)
        print("Thread started")
        logger.debug("Thread started")

    def stop(self):
       self.player.stop()

    def setupGPIO(self):

       for button in range(len(self.buttons)):
         if(self.buttons[button] > 0):
           print(button)
           logger.debug('button {}'.format(button))

           GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
           GPIO.add_event_detect(button, GPIO.RISING, callback=self.buttonDetected, bouncetime = 500)
       print('setupGPIO')

    def readConfig(self):

      file1 = open('buttons.txt', 'r')
      count = 0
 
      while True:
        count += 1
 
        # Get next line from file
        line = file1.readline()
 
        # if line is empty
        # end of file is reached
        if not line:
          break

        parts =  line.strip().split(":")
        index = int(parts[0])
        gpio = int(parts[1])
        self.buttons[gpio] = index
        print("{}:{}".format(index, gpio))

      print(self.buttons)
      file1.close()

if __name__ == '__main__':

  app = MyApp()
  logger.debug('Starting')

  try:
     while True:
       sleep(1)
#       getch = input('input')
#       print(len(getch))
#       if(getch == 'q'):
#         app.stop()
#         break
  except Exception as ex:
    print(str(ex))

  GPIO.cleanup()           # clean up GPIO on normal exit
  sys.exit()

