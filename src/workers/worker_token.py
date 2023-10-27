from PySide6.QtCore import QTimer, QObject, Signal


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
