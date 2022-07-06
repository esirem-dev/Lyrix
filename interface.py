import sys
from turtle import back

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QTimer, QObject, Signal, QThread, SIGNAL, SLOT

import time

from lyrix import Lyrix

from colorthief import ColorThief
from urllib.request import urlopen
import io

app = QGuiApplication(sys.argv)
app.setOrganizationName("Nicow")
app.setOrganizationDomain("nicow.eu")
app.setApplicationName("LyriX")
    
engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('main.qml')

def read_file(file_name):
    with open(file_name, 'rb') as f:
        return f.read()

class WorkerToken(QObject):
    finished = Signal()
    error = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):
        self.timerToken = QTimer()
        self.timerToken.setInterval(3000)
        self.timerToken.timeout.connect(self.loadToken)
        self.timerToken.start()
        self.loadToken()

    def loadToken(self):
        if(self.app.lyrix.token!=""):
            return
        if(not self.app.lyrix.loadAccessToken()):
            self.error.emit()
        else:
            self.timerToken.stop()
            self.finished.emit()

class WorkerCurrentlyPlaying(QObject):
    finished = Signal()
    spotifyNotStarted = Signal()
    newSong = Signal([dict, dict, str, str])

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):        
        self.timerCurrentlyPlaying = QTimer()
        self.timerCurrentlyPlaying.setInterval(5000)
        self.timerCurrentlyPlaying.timeout.connect(self.exec)
        self.timerCurrentlyPlaying.start()
        self.exec()

    def exec(self):
        newCurrentlyPlaying = self.app.lyrix.getCurrentlyPlaying()
        
        if(newCurrentlyPlaying == ""):
            self.spotifyNotStarted.emit()
            return
        
        if(self.app.currentlyPlaying == "" or newCurrentlyPlaying["item"]["id"] != self.app.currentlyPlaying["item"]["id"]):
            lyrics = self.app.lyrix.getLyrics(newCurrentlyPlaying["item"]["id"])
            
            if(lyrics == ""):
                imgUrl = newCurrentlyPlaying["item"]["album"]["images"][0]["url"].replace("https", "http")            
                fd = urlopen(imgUrl)
                f = io.BytesIO(fd.read())
                color_thief = ColorThief(f)
                backgroundColor = '#%02x%02x%02x' % color_thief.get_color(quality=1)
                textColor = "#eeeeee"
            else:
                backgroundColor = "#" + format(lyrics["colors"]["background"] + (1 << 24), "x").rjust(6, "0")
                textColor = "#" + format(lyrics["colors"]["text"] + (1 << 24), "x").rjust(6, "0")

            self.newSong.emit(newCurrentlyPlaying, lyrics, backgroundColor, textColor)
            
        self.app.currentlyPlaying = newCurrentlyPlaying
        self.app.lastTimeRefresh = time.time()

class Backend(QObject):
    clearLyrics = Signal(None)
    addLyric = Signal([int, str])
    updateColor = Signal([str, str])
    updateCover = Signal(str)
    selectLine = Signal(int)
    setSyncType = Signal(str)

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
        self.setSyncType.emit("LINE_SYNCED")
        
        self.threadToken = QThread()
        self.workerToken = WorkerToken(self)
        self.workerToken.moveToThread(self.threadToken)
        self.threadToken.started.connect(self.workerToken.run)
        self.workerToken.finished.connect(self.tokenLoaded)
        self.workerToken.error.connect(self.tokenError)
        self.workerToken.finished.connect(self.threadToken.quit)
        self.workerToken.finished.connect(self.workerToken.deleteLater)
        self.threadToken.finished.connect(self.threadToken.deleteLater)
        self.threadToken.start()

    def tokenLoaded(self):
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Démarrage...")
        self.addLyric.emit(1, "LyriX By Nicow")
        self.selectLine.emit(0)

        self.threadCurrentlyPlaying = QThread()
        self.workerCurrentlyPlaying = WorkerCurrentlyPlaying(self)
        self.workerCurrentlyPlaying.moveToThread(self.threadCurrentlyPlaying)
        self.threadCurrentlyPlaying.started.connect(self.workerCurrentlyPlaying.run)
        self.workerCurrentlyPlaying.spotifyNotStarted.connect(self.spotifyNotStarted)
        self.workerCurrentlyPlaying.newSong.connect(self.newSong)
        self.threadCurrentlyPlaying.start()

        self.timerLineSelector = QTimer()
        self.timerLineSelector.setInterval(100)
        self.timerLineSelector.timeout.connect(self.threadLineSelector)
        self.timerLineSelector.start()

    def spotifyNotStarted(self):
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Spotify n'est pas démarré")
        self.selectLine.emit(0)
        self.updateColor.emit("#333", "#fff")
        self.updateCover.emit("")
        self.setSyncType.emit("LINE_SYNCED")

    def tokenError(self):
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Erreur")
        self.addLyric.emit(1, "Impossible d'obtenir le token Spotify,\nvérifiez votre connexion internet")
        self.addLyric.emit(2, "Nouvelle tentative dans 3 secondes...")
        self.selectLine.emit(1)       
        self.setSyncType.emit("LINE_SYNCED")
   
    def linkLyrix(self, link):
        self.lyrix = link
    
    def newSong(self, song, lyrics, backgroundColor="#333", textColor=""):
        self.clearLyrics.emit()
        self.lyrics = lyrics
        
        if(self.lyrics == ""):
            self.lyrics = {'lyrics': {'lines': []}, 'colors': {'background': -0, 'text': -0, 'highlightText': -1}}
            self.lyrics["lyrics"]["lines"].append({'startTimeMs': '0', 'words': "Oups...", 'syllables': []})
            self.lyrics["lyrics"]["lines"].append({'startTimeMs': '5000', 'words': "J'ai un trou de mémoire...", 'syllables': []})
            self.lyrics["lyrics"]["lines"].append({'startTimeMs': str(60*1000*10), 'words': "Promis je vais essayer de retrouver pour la prochaine fois !", 'syllables': []})

        i = 0
        for l in self.lyrics["lyrics"]["lines"]:
            self.addLyric.emit(i, l["words"])
            i += 1

        # backgroundColor = "#" + str(hex(abs(self.lyrics["colors"]["background"]))).replace("0x", "")
        imgUrl = song["item"]["album"]["images"][0]["url"].replace("https", "http")
        
        self.updateColor.emit(backgroundColor, textColor)
        self.updateCover.emit(imgUrl)
        if("syncType" in self.lyrics["lyrics"]):
            self.setSyncType.emit(self.lyrics["lyrics"]["syncType"])
        else:
            self.setSyncType.emit("LINE_SYNCED")
            
    def threadCurrentlyPlaying(self):
        pass
            
    def threadLineSelector(self):
        if(self.currentlyPlaying=="" or not "lyrics" in self.lyrics):
            return
        
        if("syncType" in self.lyrics["lyrics"]):
            if(self.lyrics["lyrics"]["syncType"] == "UNSYNCED"):
                if(self.currentlyPlaying["is_playing"]):
                    percent = int(self.currentlyPlaying["progress_ms"] + (time.time()*1000 - self.lastTimeRefresh*1000)) * 100 / self.currentlyPlaying['item']['duration_ms']
                else:
                    percent = self.currentlyPlaying["progress_ms"] * 100 / self.currentlyPlaying['item']['duration_ms']
                index = int(len(self.lyrics["lyrics"]["lines"]) * percent/100)
                if(self.lastIndexLine != index):
                    self.lastIndexLine = index
                    self.selectLine.emit(index)
                return 0
            
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