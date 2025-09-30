import threading
import time
from typing import Optional, Dict

from PySide6.QtCore import QObject, Signal

from inputs import get_gamepad


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class Controller(QObject):
    """
    Reads an Xbox controller in a worker thread and emits mapped angle values.

    Mapping (default):
      - Left stick X  -> angle1
      - Left stick Y  -> angle2 (inverted so pushing up increases value)
      - Right stick Y -> angle3 (inverted)
    Buttons:
      - A (BTN_SOUTH) -> estopPressed
      - START (BTN_START) -> enableToggled (emit True on press)
    """
    anglesChanged = Signal(int, int, int)     # a1, a2, a3 (slider-ready ints)
    estopPressed = Signal()
    enableToggled = Signal(bool)              # True on press (edge)

    def __init__(
        self,
        angle1_range: tuple[int, int] = (0, 100),
        angle2_range: tuple[int, int] = (0, 100),
        angle3_range: tuple[int, int] = (0, 100),
        deadzone: float = 0.08,               # normalized stick deadzone (0..1)
        poll_hz: int = 60
    ):
        super().__init__()
        self._angle_ranges = (angle1_range, angle2_range, angle3_range)
        self._deadzone = deadzone
        self._poll_dt = 1.0 / max(1, poll_hz)

        # Raw values (Xbox sticks typically ±32768)
        self._raw: Dict[str, int] = {
            "ABS_X": 0, "ABS_Y": 0, "ABS_RX": 0, "ABS_RY": 0,
            "ABS_Z": 0, "ABS_RZ": 0
        }

        self._running = False
        self._th: Optional[threading.Thread] = None

        # Buttons debounce
        self._btn_state: Dict[str, int] = {
            "BTN_SOUTH": 0,   # A
            "BTN_START": 0,   # Start/Menu
        }
    def start(self):
        if self._running:
            return
        self._running = True
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

    def stop(self):
        self._running = False
        if self._th and self._th.is_alive():
            self._th.join(timeout=1.0)
        self._th = None

    def set_ranges(
        self,
        angle1_range: tuple[int, int],
        angle2_range: tuple[int, int],
        angle3_range: tuple[int, int],
    ):
        self._angle_ranges = (angle1_range, angle2_range, angle3_range)

    @staticmethod
    def _norm_axis(v: int) -> float:
        """Normalize raw stick value to [-1, 1]."""
        # Many drivers give range around ±32768; clamp just in case.
        return _clip(v / 32768.0, -1.0, 1.0)

    @staticmethod
    def _map_unit_to_range(u: float, lo: int, hi: int) -> int:
        """Map u in [-1,1] to integer in [lo,hi]."""
        # Convert to [0,1]
        t = (u + 1.0) / 2.0
        return int(round(lo + t * (hi - lo)))

    def _apply_deadzone(self, u: float) -> float:
        dz = self._deadzone
        if abs(u) < dz:
            return 0.0
        # Re-scale beyond deadzone so full throw still reaches 1.0
        s = (abs(u) - dz) / (1.0 - dz)
        return (s if u > 0 else -s)

    def _compute_angles(self) -> tuple[int, int, int]:
        a1_lo, a1_hi = self._angle_ranges[0]
        a2_lo, a2_hi = self._angle_ranges[1]
        a3_lo, a3_hi = self._angle_ranges[2]

        # Left stick
        lx = self._apply_deadzone(self._norm_axis(self._raw["ABS_X"]))
        ly = self._apply_deadzone(self._norm_axis(self._raw["ABS_Y"]))
        # Right stick
        ry = self._apply_deadzone(self._norm_axis(self._raw["ABS_RY"]))

        # Map: angle1 <- LX, angle2 <- -LY (up is positive), angle3 <- -RY
        a1 = self._map_unit_to_range(lx, a1_lo, a1_hi)
        a2 = self._map_unit_to_range(-ly, a2_lo, a2_hi)
        a3 = self._map_unit_to_range(-ry, a3_lo, a3_hi)
        return a1, a2, a3

    def _handle_button(self, code: str, state: int):
        prev = self._btn_state.get(code, 0)
        self._btn_state[code] = state
        # Rising edge
        if prev == 0 and state != 0:
            if code == "BTN_SOUTH":
                self.estopPressed.emit()
            elif code == "BTN_START":
                self.enableToggled.emit(True)

    def _loop(self):
        next_emit = 0.0
        # Start with a first emission (neutral)
        a1, a2, a3 = self._compute_angles()
        self.anglesChanged.emit(a1, a2, a3)

        while self._running:
            # Pull all pending events (blocks until at least one event)
            try:
                events = get_gamepad()
            except OSError:
                # Controller unplugged; back off a bit
                time.sleep(0.25)
                continue

            updated = False
            for e in events:
                if e.ev_type == "Absolute":
                    # Sticks / triggers
                    if e.code in self._raw:
                        self._raw[e.code] = int(e.state)
                        updated = True

                elif e.ev_type == "Key":
                    self._handle_button(e.code, int(e.state))

            # Throttle signal emission
            now = time.time()
            if updated and now >= next_emit:
                a1, a2, a3 = self._compute_angles()
                self.anglesChanged.emit(a1, a2, a3)
                next_emit = now + self._poll_dt
