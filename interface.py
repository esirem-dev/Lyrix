import sys
from turtle import back

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QTimer, QObject, Signal

import time

from lyrix import Lyrix

from colorthief import ColorThief
from urllib.request import urlopen
import io

app = QGuiApplication(sys.argv)

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('main.qml')

def read_file(file_name):
    with open(file_name, 'rb') as f:
        return f.read()

class Backend(QObject):

    clearLyrics = Signal(None)
    addLyric = Signal([int, str])
    updateColor = Signal([str, str])
    updateCover = Signal(str)
    selectLine = Signal(int)

    def __init__(self):
        super().__init__()
        self.currentlyPlaying = {"item":{"id":""}}
        self.lastTimeRefresh = 0
        self.lyrics = {}
        self.lastIndexLine = -1

        self.timerSetup = QTimer()
        self.timerSetup.setInterval(1000)
        self.timerSetup.timeout.connect(self.threadCurrentlyPlaying)
        self.timerSetup.start()
        
        self.timerLineSelector = QTimer()
        self.timerLineSelector.setInterval(50)
        self.timerLineSelector.timeout.connect(self.threadLineSelector)
        self.timerLineSelector.start()
        
    def linkLyrix(self, link):
        self.lyrix = link
    
    def newSong(self, song):
        self.clearLyrics.emit()
        self.lyrics = self.lyrix.getLyrics(song["item"]["id"])
        
        i = 0
        for l in self.lyrics["lyrics"]["lines"]:
            self.addLyric.emit(i, l["words"])
            i += 1

        backgroundColor = "#" + str(hex(abs(self.lyrics["colors"]["background"]))).replace("0x", "")
        textColor = "#" + str(hex(abs(self.lyrics["colors"]["text"]))).replace("0x", "")
        imgUrl = song["item"]["album"]["images"][0]["url"].replace("https", "http")
        
        fd = urlopen(imgUrl)
        f = io.BytesIO(fd.read())
        color_thief = ColorThief(f)
        backgroundColor = '#%02x%02x%02x' % color_thief.get_color(quality=1)        
        
        self.updateColor.emit(backgroundColor, textColor)
        self.updateCover.emit(imgUrl)
            
    def threadCurrentlyPlaying(self):
        currentlyPlaying = self.lyrix.getCurrentlyPlaying()
        idSong = currentlyPlaying["item"]["id"]
        
        if(idSong != self.currentlyPlaying["item"]["id"]):
            self.newSong(currentlyPlaying)
            
        self.currentlyPlaying = currentlyPlaying
        self.lastTimeRefresh = time.time()
            
    def threadLineSelector(self):
        if(not "progress_ms" in self.currentlyPlaying):
            return
        
        progress_ms = int(self.currentlyPlaying["progress_ms"]) - 700
        timing = int(progress_ms + (time.time()*1000 - self.lastTimeRefresh*1000))
        
        i = 0 
        for l in self.lyrics["lyrics"]["lines"]:
            if(int(l["startTimeMs"]) >= timing):
                break
            i += 1 
        
        if(self.lastIndexLine != i):
            self.selectLine.emit(i-1)
            self.lastIndexLine = i

backend = Backend()

lyrix = Lyrix(cookies=read_file("cookies.txt"))
lyrix.loadAccessToken()
backend.linkLyrix(lyrix)

engine.rootObjects()[0].setProperty('backend', backend)

# sys.exit(0)
sys.exit(app.exec_())