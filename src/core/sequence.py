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

    def _sleep_responsive(self, seconds: float) -> bool:
        """Sleep in small chunks so aborts are responsive.
        Returns True if aborted during sleep.
        """
        end = time.monotonic() + max(0.0, seconds)
        while time.monotonic() < end:
            if self._stop:
                return True
            # sleep in short bursts (10ms)
            time.sleep(min(0.01, end - time.monotonic()))
        return False

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
                    try:
                        a1, a2, a3 = map(float, row[:3])
                    except (ValueError, IndexError):
                        # Not a valid data row (maybe header), skip
                        continue

                        # Per-row dt (4th column). Fallback to default if missing/invalid.
                    dt = self._dt
                    if len(row) >= 4 and row[3].strip():
                        try:
                            dt = float(row[3])
                        except ValueError:
                            pass

                    self.stepEmitted.emit(a1, a2, a3)

                    # Sleep, but allow responsive abort
                    if self._sleep_responsive(dt):
                        self.aborted.emit()
                        break
        finally:
            self.finished.emit()