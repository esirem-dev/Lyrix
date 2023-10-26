import sys
from turtle import back

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, QObject, Signal, QThread, SIGNAL, SLOT

import time

from utils.spotify_controler import SpotifyControler
from utils.bpm import BPM
import version

from colorthief import ColorThief
from urllib.request import urlopen
import io
import json

app = QGuiApplication(sys.argv)
app.setOrganizationName("Nicow")
app.setOrganizationDomain("nicow.eu")
app.setApplicationName("Lyrix")
# set the logo of the application
app.setWindowIcon(QIcon("img/logo/logo.ico"))

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load("main.qml")


def read_file(file_name):
    with open(file_name, "rb") as f:
        return f.read()


class WorkerToken(QObject):
    finished = Signal()
    error = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):
        self.app.log("WorkerToken", "Démarrage...")
        self.timerToken = QTimer()
        self.timerToken.setInterval(3000)
        self.timerToken.timeout.connect(self.loadToken)
        self.timerToken.start()
        self.timerTokenForceRefresh = QTimer()
        self.timerTokenForceRefresh.setInterval(1000 * 60 * 10)
        self.timerTokenForceRefresh.timeout.connect(self.loadTokenForce)
        self.timerTokenForceRefresh.start()
        self.loadToken()
        self.app.log("WorkerToken", "Démarré")

    def loadToken(self):
        self.app.log("WorkerToken", "Exécution...")
        if self.app.spotify.token != "":
            return
        if not self.app.spotify.loadAccessToken():
            self.error.emit()
            self.app.log("WorkerToken", "Erreur lors du chargement du token")
        else:
            self.app.log("WorkerToken", "Token chargé")
            self.timerToken.stop()
            self.finished.emit()

    def loadTokenForce(self):
        self.app.log("WorkerToken", "Exécution force...")
        try:
            res = self.app.spotify.loadAccessToken()
            self.app.log("WorkerToken", "Token chargé : " + str(res))
        except:
            self.app.log("WorkerToken", "Erreur lors du chargement du token")
            pass


class WorkerCurrentlyPlaying(QObject):
    finished = Signal()
    spotifyNotStarted = Signal()
    newSong = Signal(dict, dict, str, str)

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):
        self.app.log("WorkerCurrentlyPlaying", "Démarrage...")
        self.timerCurrentlyPlaying = QTimer()
        self.timerCurrentlyPlaying.setInterval(5000)
        self.timerCurrentlyPlaying.timeout.connect(self.exec)
        self.timerCurrentlyPlaying.start()
        self.exec()
        self.app.log("WorkerCurrentlyPlaying", "Démarré")

    def exec(self):
        self.app.log("WorkerCurrentlyPlaying", "Exécution...")
        newCurrentlyPlaying = self.app.spotify.getCurrentlyPlaying()

        if newCurrentlyPlaying == "":
            self.spotifyNotStarted.emit()
            self.app.log("WorkerCurrentlyPlaying", "Spotify non démarré")
            return

        if (
            self.app.currentlyPlaying == ""
            or newCurrentlyPlaying["item"]["id"]
            != self.app.currentlyPlaying["item"]["id"]
        ):
            lyrics = self.app.spotify.getLyrics(newCurrentlyPlaying["item"]["id"])

            if lyrics == "":
                imgUrl = newCurrentlyPlaying["item"]["album"]["images"][0][
                    "url"
                ].replace("https", "http")
                fd = urlopen(imgUrl)
                f = io.BytesIO(fd.read())
                color_thief = ColorThief(f)
                backgroundColor = "#%02x%02x%02x" % color_thief.get_color(quality=1)
                textColor = "#eeeeee"
            else:
                backgroundColor = "#" + format(
                    lyrics["colors"]["background"] + (1 << 24), "x"
                ).rjust(6, "0")
                textColor = "#" + format(
                    lyrics["colors"]["text"] + (1 << 24), "x"
                ).rjust(6, "0")

            self.app.log("WorkerCurrentlyPlaying", "Nouvelle chanson détectée")
            self.newSong.emit(newCurrentlyPlaying, lyrics, backgroundColor, textColor)

        self.app.currentlyPlaying = newCurrentlyPlaying
        self.app.log(
            "WorkerCurrentlyPlaying",
            "currentlyPlaying : " + str(self.app.currentlyPlaying),
        )
        self.app.lastTimeRefresh = time.time()


class WorkerBPM(QObject):
    newBPM = Signal(int)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.last_song = None
        self.bpm = BPM()

    def run(self):
        self.app.log("WorkerBPM", "Démarrage...")
        self.timerCheckBPM = QTimer()
        self.timerCheckBPM.setInterval(1000)
        self.timerCheckBPM.timeout.connect(self.exec)
        self.timerCheckBPM.start()
        self.exec()
        self.app.log("WorkerBPM", "Démarré")

    def exec(self):
        song = self.app.currentlyPlaying
        if song == "" or song is None:
            return

        try:
            if (
                self.last_song is None
                or song["item"]["id"] != self.last_song["item"]["id"]
            ):
                self.last_song = song
                artist = song["item"]["artists"][0]["name"]
                title = song["item"]["name"]
                new_bpm = self.bpm.get_bpm(artist, title)
                self.app.log(
                    "WorkerBPM",
                    f"BPM pour {artist} - {title} : {new_bpm}",
                )
                self.newBPM.emit(new_bpm)
        except Exception as e:
            import traceback

            traceback.print_exc()


class Backend(QObject):
    clearLyrics = Signal(None)
    addLyric = Signal(int, str)
    updateColor = Signal(str, str)
    updateCover = Signal(str)
    updateBPM = Signal(int)
    updateBackground = Signal(str)
    selectLine = Signal(int)
    setSyncType = Signal(str)
    setNoLyrics = Signal(bool)

    def __init__(self):
        super().__init__()
        self.currentlyPlaying = ""
        self.lastTimeRefresh = 0
        self.lyrics = {}
        self.lastIndexLine = -1

        self.theme = ""
        self.theme_settings = {}

    def log(self, module, msg):
        return
        print("[" + module + "] " + msg)

    def start(self):
        self.log("Backend", "Démarrage...")
        self.updateColor.emit("#333", "#fff")
        self.updateCover.emit("")
        self.updateBPM.emit(120)
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Démarrage...")
        self.addLyric.emit(1, f"Lyrix{version.LYRIX_VERSION} By Nicow")
        self.selectLine.emit(0)
        self.setSyncType.emit("LINE_SYNCED")

        self.threadToken = QThread()
        self.workerToken = WorkerToken(self)
        self.workerToken.moveToThread(self.threadToken)
        self.threadToken.started.connect(self.workerToken.run)
        self.workerToken.finished.connect(self.tokenLoaded)
        self.workerToken.error.connect(self.tokenError)
        self.threadToken.start()

        self.loadTheme()
        self.log("Backend", "Démarré")

    def tokenLoaded(self):
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Démarrage...")
        self.addLyric.emit(1, f"Lyrix{version.LYRIX_VERSION} By Nicow")
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

        self.threadBPM = QThread()
        self.workerBPM = WorkerBPM(self)
        self.workerBPM.moveToThread(self.threadBPM)
        self.threadBPM.started.connect(self.workerBPM.run)
        self.workerBPM.newBPM.connect(self.newBPM)
        self.threadBPM.start()

    def spotifyNotStarted(self):
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Spotify n'est pas démarré")
        self.selectLine.emit(0)
        if self.theme != "":
            self.updateColor.emit(
                self.theme_settings["backgroundColor"], self.theme_settings["textColor"]
            )
        else:
            self.updateColor.emit("#333", "#fff")
        self.updateCover.emit("")
        self.setSyncType.emit("LINE_SYNCED")

    def tokenError(self):
        self.clearLyrics.emit()
        self.addLyric.emit(0, "Erreur")
        self.addLyric.emit(
            1,
            "Impossible d'obtenir le token Spotify,\nvérifiez votre connexion internet",
        )
        self.addLyric.emit(2, "Nouvelle tentative dans 3 secondes...")
        self.selectLine.emit(1)
        self.setSyncType.emit("LINE_SYNCED")

    def linkSpotifyControler(self, link):
        self.log("linkSpotifyControler", "Lien avec le controler Spotify")
        self.spotify = link
        self.log("linkSpotifyControler", "Lien effectué: " + str(self.spotify))

    def loadTheme(self):
        if self.theme == "":
            return
        self.log("loadTheme", "Chargement du thème : " + self.theme)
        file = open("assets/themes/" + self.theme + ".json", "r")
        self.theme_settings = json.loads(file.read())
        self.log("loadTheme", "Thème chargé : " + str(self.theme_settings))

        if "backgroundImage" in self.theme_settings:
            self.updateBackground.emit(self.theme_settings["backgroundImage"])

    def newSong(self, song, lyrics, backgroundColor="#333", textColor=""):
        self.log("newSong", "Nouvelle chanson détectée : " + str(song))
        self.clearLyrics.emit()
        self.lyrics = lyrics

        if self.lyrics == "":
            self.lyrics = {
                "lyrics": {"lines": []},
                "colors": {"background": -0, "text": -0, "highlightText": -1},
            }
            self.lyrics["lyrics"]["lines"].append(
                {"startTimeMs": "0", "words": "Oups...", "syllables": []}
            )
            self.lyrics["lyrics"]["lines"].append(
                {
                    "startTimeMs": "5000",
                    "words": "J'ai un trou de mémoire...",
                    "syllables": [],
                }
            )
            self.lyrics["lyrics"]["lines"].append(
                {
                    "startTimeMs": str(60 * 1000 * 10),
                    "words": "Promis je vais essayer de retrouver pour la prochaine fois !",
                    "syllables": [],
                }
            )
            self.setNoLyrics.emit(True)
        else:
            self.setNoLyrics.emit(False)

        if "syncType" in self.lyrics["lyrics"]:
            self.setSyncType.emit(self.lyrics["lyrics"]["syncType"])
        else:
            self.setSyncType.emit("LINE_SYNCED")

        i = 0
        for l in self.lyrics["lyrics"]["lines"]:
            self.addLyric.emit(i, l["words"])
            i += 1

        # backgroundColor = "#" + str(hex(abs(self.lyrics["colors"]["background"]))).replace("0x", "")
        imgUrl = song["item"]["album"]["images"][0]["url"].replace("https", "http")

        if self.theme != "":
            self.updateColor.emit(
                self.theme_settings["backgroundColor"], self.theme_settings["textColor"]
            )
        else:
            self.updateColor.emit(backgroundColor, textColor)
        self.updateCover.emit(imgUrl)

    def newBPM(self, bpm):
        print("new bpm", bpm)
        if (bpm is not None) and (bpm > 0):
            self.updateBPM.emit(bpm)
        else:
            self.updateBPM.emit(120)

    def threadLineSelector(self):
        if self.currentlyPlaying == "" or not "lyrics" in self.lyrics:
            return

        if "syncType" in self.lyrics["lyrics"]:
            if self.lyrics["lyrics"]["syncType"] == "UNSYNCED":
                if self.currentlyPlaying["is_playing"]:
                    percent = (
                        int(
                            self.currentlyPlaying["progress_ms"]
                            + (time.time() * 1000 - self.lastTimeRefresh * 1000)
                        )
                        * 100
                        / self.currentlyPlaying["item"]["duration_ms"]
                    )
                else:
                    percent = (
                        self.currentlyPlaying["progress_ms"]
                        * 100
                        / self.currentlyPlaying["item"]["duration_ms"]
                    )
                index = int(len(self.lyrics["lyrics"]["lines"]) * percent / 100)
                if self.lastIndexLine != index:
                    self.lastIndexLine = index
                    self.selectLine.emit(index)
                return 0

        if self.currentlyPlaying["is_playing"]:
            progress_ms = int(self.currentlyPlaying["progress_ms"]) - 700
            timing = int(
                progress_ms + (time.time() * 1000 - self.lastTimeRefresh * 1000)
            )
        else:
            progress_ms = int(self.currentlyPlaying["progress_ms"])
            timing = int(progress_ms)

        i = 0
        for l in self.lyrics["lyrics"]["lines"]:
            if int(l["startTimeMs"]) >= timing:
                break
            i += 1

        if self.lastIndexLine != i:
            self.log("threadLineSelector", "Changement de ligne : " + str(i))
            self.selectLine.emit(i - 1)
            self.lastIndexLine = i


backend = Backend()

spotify = SpotifyControler(cookies=read_file("assets/config/cookies_spotify.txt"))
backend.linkSpotifyControler(spotify)

engine.rootObjects()[0].setProperty("backend", backend)

backend.start()
# sys.exit(0)
sys.exit(app.exec())
