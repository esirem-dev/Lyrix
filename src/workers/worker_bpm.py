from PySide6.QtCore import QTimer, QObject, Signal

from utils.bpm import BPM


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
