# core/sequence.py
from PySide6.QtCore import QObject, Signal
import time, csv, pathlib

class SequenceWorker(QObject):
    started = Signal()
    finished = Signal()
    stepEmitted = Signal(float, float, float)
    aborted = Signal()

    def __init__(self, csv_path: str, dt=0.5):
        super().__init__()
        self._path = pathlib.Path(csv_path)
        self._dt = dt
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        self.started.emit()
        try:
            with self._path.open("r", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if self._stop:
                        self.aborted.emit()
                        break
                    a1, a2, a3 = map(float, row[:3])
                    self.stepEmitted.emit(a1, a2, a3)
                    time.sleep(self._dt)
        finally:
            self.finished.emit()