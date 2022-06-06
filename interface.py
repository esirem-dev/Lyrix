import sys
from turtle import back

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QTimer, QObject, Signal, QThread, SIGNAL, SLOT

import time
import threading

from lyrix import Lyrix

from colorthief import ColorThief
from urllib.request import urlopen
import io

app = QGuiApplication(sys.argv)
app.setOrganizationName("Nicow");
app.setOrganizationDomain("nicow.eu");
app.setApplicationName("LyriX");
    
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
        self.currentlyPlaying = ""
        self.lastTimeRefresh = 0
        self.lyrics = {}
        self.lastIndexLine = -1
        
    def start(self):
        self.updateColor.emit("#333", "#fff")
        self.updateCover.emit("")
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Démarrage...")
        self.addLyric.emit(1, "LyriX By Nicow")
        self.selectLine.emit(0)
        
        self.threadSetup = QThread()
        self.threadPlaying = QThread()
        
        self.timerStart = QTimer()
        self.timerStart.setInterval(1000)
        self.timerStart.moveToThread(self.threadSetup)
        self.timerStart.timeout.connect(self._start)
        self.threadSetup.started.connect(self.timerStart.start)
        
        self.timerToken = QTimer()
        self.timerToken.setInterval(3000)
        self.timerToken.moveToThread(self.threadSetup)
        self.timerToken.timeout.connect(self.loadToken)
        self.threadSetup.started.connect(self.timerToken.start)
        
        self.threadSetup.start()
        
    def loadToken(self):
        if(self.lyrix.token!=""):
            return
        
        self.updateColor.emit("#333", "#fff")
        self.updateCover.emit("")
        if(not self.lyrix.loadAccessToken()):
            self.clearLyrics.emit()
            self.addLyric.emit(0, "Erreur")
            self.addLyric.emit(1, "Impossible d'obtenir le token Spotify,\nvérifiez votre connexion internet")
            self.addLyric.emit(2, "Nouvelle tentative dans 3 secondes...")
            self.selectLine.emit(1)
        else:
            self.timerToken.stop()
        
    def _start(self):
        if(self.lyrix.token==""):
            return

        self.timerStart.stop()

        self.clearLyrics.emit()        
        self.timerCurrentlyPlaying = QTimer()
        self.timerCurrentlyPlaying.setInterval(5000)
        self.timerCurrentlyPlaying.timeout.connect(self.threadCurrentlyPlaying)
        self.threadPlaying.started.connect(self.timerCurrentlyPlaying.start)
        self.threadPlaying.start()

        self.timerLineSelector = QTimer()
        self.timerLineSelector.setInterval(50)
        self.timerLineSelector.timeout.connect(self.threadLineSelector)
        self.timerLineSelector.start()
   
    def linkLyrix(self, link):
        self.lyrix = link
    
    def newSong(self, song):
        self.clearLyrics.emit()
        self.lyrics = self.lyrix.getLyrics(song["item"]["id"])
        
        if(self.lyrics == ""):
            self.lyrics = {'lyrics': {'lines': []}, 'colors': {'background': -0, 'text': -0, 'highlightText': -1}}
            self.lyrics["lyrics"]["lines"].append({'startTimeMs': '0', 'words': "Oups...", 'syllables': []})
            self.lyrics["lyrics"]["lines"].append({'startTimeMs': '1', 'words': "J'ai un trou de mémoire...", 'syllables': []})
            self.lyrics["lyrics"]["lines"].append({'startTimeMs': str(60*1000*10), 'words': "Promis je vais essayer de retrouver pour la prochaine fois !", 'syllables': []})

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
        print("a")
        newCurrentlyPlaying = self.lyrix.getCurrentlyPlaying()
        print("b")
        
        if(newCurrentlyPlaying == ""):
            self.clearLyrics.emit()
            self.addLyric.emit(0, "Spotify n'est pas démarré")     
            self.selectLine.emit(0)   
            self.updateColor.emit("#333", "#fff")
            self.updateCover.emit("")
            return
        
        if(self.currentlyPlaying == "" or newCurrentlyPlaying["item"]["id"] != self.currentlyPlaying["item"]["id"]):
            self.newSong(newCurrentlyPlaying)
            
        self.currentlyPlaying = newCurrentlyPlaying
        self.lastTimeRefresh = time.time()
            
    def threadLineSelector(self):
        if(self.currentlyPlaying==""):
            return
            
        if(self.currentlyPlaying["is_playing"]):
            progress_ms = int(self.currentlyPlaying["progress_ms"]) - 700
            timing = int(progress_ms + (time.time()*1000 - self.lastTimeRefresh*1000))
        else:
            progress_ms = int(self.currentlyPlaying["progress_ms"])
            timing = int(progress_ms)
        
        i = 0 
        for l in self.lyrics["lyrics"]["lines"]:
            if(int(l["startTimeMs"]) >= timing):
                break
            i += 1 
        
        if(self.lastIndexLine != i):
            self.selectLine.emit(i-1)
            self.lastIndexLine = i

backend = Backend()

lyrix = Lyrix(cookies=read_file("cookies_spotify.txt"))
backend.linkLyrix(lyrix)

engine.rootObjects()[0].setProperty('backend', backend)

backend.start()
# sys.exit(0)
sys.exit(app.exec_())