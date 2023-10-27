from PySide6.QtCore import QTimer, QObject, Signal


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
