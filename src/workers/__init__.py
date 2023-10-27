from .worker_currently_playing import WorkerCurrentlyPlaying
from .worker_bpm import WorkerBPM
from .worker_token import WorkerToken

from PySide6.QtCore import QObject

class WorkerLyrix(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
