#!/usr/bin/python3
#
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QStyle, QSizePolicy, QDesktopWidget
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTime, QTimer, QThread, QDateTime, pyqtSignal, QRect, QPoint,  QUrl, Qt
from PyQt5.QtGui import QIcon, QPalette, QScreen

import glob
import subprocess
import shutil

#Silver Palms.652009962126, 652009962133': 'Rattler', '816597933979': 'Backyard King'

#to convert resource file
#pyrcc5 resources.qrc -o resources_rc.py

import signal
import os
import sys
from time import sleep
import time
import configparser

#catch Ctrl+C, not used much in PyQT apps
def signal_handler(signal, frame):

  print('You pressed Ctrl+C!')
  sys.exit(0)

signal.signal(signal.SIGINT, signal.SIG_DFL)

def exitApp(self):
       os._exit(1)

Ui_MainWindow, QtBaseClass = uic.loadUiType('Video.ui')

class playMP4(QThread):
    path = ''
    def __init__(self, _videoPath):
        QThread.__init__(self)

        self.videoPath = _videoPath

    def __del__(self):
        self.wait()

    def run(self):
        print('playing ' + self.videoPath)
        try:
           subprocess.call(['omxplayer', '-o', 'hdmi', self.videoPath])
        except Exception as e:
           print(str(e))
           print('omxplayer error')

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
#    def __init__(self, *args, **kwargs):
#        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
    def __init__(self):
        super(MyApp, self).__init__()

        self.ui = Ui_MainWindow()

#        self.move(0, 0)
        p =self.palette()
        p.setColor(QPalette.Window, Qt.black)
#        self.setPalette(p)

        self.statusTimer = QTimer(self)
        self.statusTimer.timeout.connect(self.updateName)

        self.ui.setupUi(self)
#        self.setWindowFlags(self.windowFlags() | QtCore.Qt.X11BypassWindowManagerHint)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint) 

        self.ui.exitBtn.clicked.connect(self.exitApp)

        self.ui.goBackBtn.clicked.connect(self.gotoGoBack)
        self.ui.barcodeTxt.returnPressed.connect(self.onBarcodePressed)
        self.ui.playing = False

        self.refresh = '000'
        self.reboot = '411411'
        self.shutdown = '911911'

        self.videoPath = '/home/pi/Videos'

        self.getConfig()

        self.setupScreens()

        self.ui.stackedWidget.setCurrentIndex(0)

    def refreshUSB(self):

        src = '/media/pi/VIDEOS'

        count = 0
        for file in glob.glob("/media/pi/VIDEOS/*.mp4"):
           shutil.copy2(file, self.videoPath)
           count +=  1

        if(count == 0):
          self.ui.nameLbl.setText('Nothing found')
        else:
          self.ui.nameLbl.setText('Videos copied')
        self.statusTimer.start(3000)

        return

        self.videoPath = ''
        for file in glob.glob("/media/pi/*"):
            print(file)
            if('video' in file.lower()):
              self.videoPath = file

        if(self.videoPath == ''):
            for file in glob.glob("/home/pi/*"):
              if('video' in file.lower()):
                self.videoPath = file

        self.items = {}
        if(self.videoPath != ''):
          print(self.videoPath)
          for file in glob.glob(self.videoPath+'/*.mp4'):
            print(file)
            file = os.path.basename(file)
            parts = file.split('.')
            self.items.update({parts[1]:parts[0]})


    def exitApp(self):
       os._exit(1)

    def done(self):
        print("Done playing video!")
        self.ui.playing = False
        self.statusTimer.start(3000)

    def onBarcodePressed(self):
        barcode = self.ui.barcodeTxt.text()
        self.ui.barcodeTxt.setText('')
        if(self.ui.playing == True):
          print('flushing ' + barcode)
          return

        if(barcode == self.reboot):
          os.system("sudo shutdown -r now")
          self.exitApp()

        if(barcode == self.shutdown):
          os.system("sudo shutdown -h now")
          self.exitApp()

        if(barcode == self.refresh):
           self.refreshUSB()
           return

        if(barcode[:1] == '-'):
          self.exitApp()
        print(barcode)

        print(self.videoPath + '/*.' + barcode + '.mp4')
        found = False
        for file in glob.glob(self.videoPath + '/*.' + barcode + '.mp4'):
           found = True
           videopath = os.path.basename(file)
           print(videopath)
           items = videopath.split('.')
           video = items[0]
           self.ui.nameLbl.setText(video)
           self.ui.nameLbl.repaint()
           self.videoThread = playMP4(file)
           self.videoThread.finished.connect(self.done)
           self.ui.playing = True
           self.videoThread.start()

        if(found != True):
           self.ui.nameLbl.setText('Not Found')

    def setupScreens(self):

        screen1 = app.screens()[0];
#        screen2 = app.screens()[1];

        ag = QDesktopWidget().availableGeometry()
        sg = QDesktopWidget().screenGeometry()

        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = screen.width() - widget.width()
        y = screen.height() - widget.height()
        self.move(x/2, y)

        self.ui.barcodeTxt.setText('')

    def gotoSetup(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def gotoGoBack(self):
        print('go back')
        self.ui.stackedWidget.setCurrentIndex(0)

    def exitApp(self):
        os._exit(1)

    def clickedReset(self):
        print("sudo reboot now")

    def clickedShutdown(self):
        print("sudo shutdown now")
 
    def updateName(self):
        self.ui.nameLbl.setText('')

    def getConfig(self):
     
       self.config = configparser.ConfigParser(allow_no_value=True)
       self.configFile = "video.cfg"
         # Load configuration

       if not os.path.exists(self.configFile):
         self.config['Options'] = {'refreshusb':self.refreshusb, 'reboot':self.reboot,'shutdown':self.shutdown}
         self.config.write(open(self.configFile, 'w'))
       else:
     
        try:
          self.config.read(self.configFile)

          section = 'Options'

          if(not self.config.has_section(section)):
             self.config.add_section(section)

          if(not self.config.has_option(section, 'reboot')):
             self.config.set('Options', 'reboot', str(self.reboot))
          else:
             self.reboot = self.config['Options']['reboot']

          if(not self.config.has_option(section, 'shutdown')):
             self.config.set('Options', 'shutdown', str(self.shutdown))
          else:
             self.shutdown = self.config['Options']['shutdown']

          if(not self.config.has_option(section, 'refreshusb')):
             self.config.set('Options', 'refreshusb', str(self.refresh))
          else:
             self.refresh = self.config['Options']['refreshusb']
        except Exception as e:
           print(str(e))
           print('Fatal error, could not load config file from "%s"' % self.configFile)

if __name__ == '__main__':
  app = QApplication(sys.argv)
  window = MyApp()

  window.show()

  app.exec_()

  sys.exit()
