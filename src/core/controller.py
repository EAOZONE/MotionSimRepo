"""HID-based controller polling using hidapi."""

from __future__ import annotations

import os
import sys
import struct
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QObject, Signal

try:  # optional dependency
    import hid  # type: ignore
except Exception:  # pragma: no cover - keep UI responsive when missing
    hid = None  # type: ignore

try:  # optional Windows dependency
    from inputs import get_gamepad as _inputs_get_gamepad  # type: ignore
    from inputs import UnpluggedError as _inputs_unplugged_error  # type: ignore
except Exception:  # pragma: no cover - optional
    _inputs_get_gamepad = None
    _inputs_unplugged_error = Exception


@dataclass(frozen=True)
class AxisSpec:
    index: int
    size: int = 1  # bytes (1 or 2)
    invert: bool = False


@dataclass(frozen=True)
class ButtonSpec:
    byte: int
    bit: int


@dataclass(frozen=True)
class TriggerSpec:
    axis: Optional[AxisSpec] = None
    button: Optional[ButtonSpec] = None


@dataclass
class HIDLayout:
    axes: Dict[str, AxisSpec]
    triggers: Dict[str, TriggerSpec]
    buttons: Dict[str, ButtonSpec]
    hat_index: Optional[int]

    @classmethod
    def from_report(cls, report: bytes) -> "HIDLayout":
        n = len(report)

        axes: Dict[str, AxisSpec] = {}
        if n >= 2:
            axes["lx"] = AxisSpec(0)
            axes["ly"] = AxisSpec(1, invert=True)
        if n >= 4:
            axes["rx"] = AxisSpec(2)
            axes["ry"] = AxisSpec(3, invert=True)

        hat_index = None
        if n > 4 and report[4] <= 8:
            hat_index = 4

        buttons: Dict[str, ButtonSpec] = {}
        if n > 5:
            buttons.update(
                {
                    "BTN_SOUTH": ButtonSpec(5, 0),
                    "BTN_EAST": ButtonSpec(5, 1),
                    "BTN_WEST": ButtonSpec(5, 2),
                    "BTN_NORTH": ButtonSpec(5, 3),
                }
            )

        triggers: Dict[str, TriggerSpec] = {
            "lt": TriggerSpec(button=ButtonSpec(5, 4) if n > 5 else None),
            "rt": TriggerSpec(button=ButtonSpec(5, 5) if n > 5 else None),
        }

        if n > 7:
            triggers["lt"] = TriggerSpec(axis=AxisSpec(6))
            triggers["rt"] = TriggerSpec(axis=AxisSpec(7))

        return cls(axes=axes, triggers=triggers, buttons=buttons, hat_index=hat_index)


def _normalize_unsigned(raw: int, bits: int) -> float:
    max_val = float((1 << bits) - 1)
    if max_val <= 0:
        return 0.0
    return (raw / max_val) * 2.0 - 1.0


def _apply_deadzone(value: float, dead: float) -> float:
    if abs(value) < dead:
        return 0.0
    return max(-1.0, min(1.0, value))


class ControllerWorker(QObject):
    """Polls a HID game controller and emits motion updates."""

    connected = Signal()
    disconnected = Signal()
    anglesChanged = Signal(float, float, float)  # pitch, roll, yaw
    estopRequested = Signal()
    homeRequested = Signal()
    enableToggle = Signal()
    debugEvent = Signal(str)

    def __init__(self, poll_hz: int = 120, deadzone: float = 0.10, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._running = False
        self._enabled = True
        self._dt = 1.0 / float(max(30, poll_hz))
        self._dead = float(deadzone)
        self._backend = "hid"

        self._device: Optional["hid.Device"] = None
        self._layout: Optional[HIDLayout] = None
        self._connected = False

        self._lx = 0.0
        self._ly = 0.0
        self._rx = 0.0
        self._ry = 0.0
        self._lt = -1.0
        self._rt = -1.0

        self._buttons: Dict[str, int] = {
            "BTN_SOUTH": 0,
            "BTN_EAST": 0,
            "BTN_WEST": 0,
            "BTN_NORTH": 0,
        }

        self._xinput_active = False
        self._last_axes_debug = 0.0
        self._xinput_center: Optional[Tuple[int, int, int, int]] = None
        self._inputs_center: Dict[str, float] = {}
        self._inputs_span: Dict[str, float] = {}

        self._preferred_vendor = _parse_int_env("MOTIONSIM_HID_VENDOR")
        self._preferred_product = _parse_int_env("MOTIONSIM_HID_PRODUCT")
        self._preferred_path = os.getenv("MOTIONSIM_HID_PATH")

    # ===== lifecycle =====================================================
    def start(self) -> None:
        self._running = True
        self._backend = self._select_backend()
        self.debugEvent.emit(f"Controller backend: {self._backend}")

        if self._backend == "inputs":
            self._inputs_loop()
        else:
            self._hid_loop()

    def stop(self) -> None:
        self._running = False

    def set_enabled(self, on: bool) -> None:
        self._enabled = bool(on)

    def toggle_enabled(self) -> None:
        self._enabled = not self._enabled

    # ===== helpers =======================================================
    def _select_backend(self) -> str:
        if sys.platform.startswith("win"):
            if _inputs_get_gamepad is not None:
                return "inputs"
            self.debugEvent.emit("inputs library unavailable; falling back to HID backend")
        return "hid"

    def _inputs_loop(self) -> None:
        last_emit = 0.0
        self._set_connected(False)

        while self._running:
            try:
                events = _inputs_get_gamepad()  # type: ignore[misc]
            except _inputs_unplugged_error:
                self._set_connected(False)
                time.sleep(0.5)
                continue
            except Exception as exc:  # pragma: no cover - defensive
                self.debugEvent.emit(f"inputs read failed: {exc}")
                self._set_connected(False)
                time.sleep(0.5)
                continue

            self._set_connected(True)

            for ev in events:
                code = getattr(ev, "code", None)
                etype = getattr(ev, "ev_type", None)
                state = getattr(ev, "state", None)
                if code is None or etype is None or state is None:
                    continue

                if etype == "Sync":
                    continue

                if etype in ("EV_ABS", "Absolute"):
                    if code == "ABS_X":
                        self._lx = _apply_deadzone(self._normalize_inputs_axis(state, "lx"), self._dead)
                    elif code == "ABS_Y":
                        self._ly = _apply_deadzone(self._normalize_inputs_axis(state, "ly"), self._dead)
                    elif code == "ABS_RX":
                        self._rx = _apply_deadzone(self._normalize_inputs_axis(state, "rx"), self._dead)
                    elif code == "ABS_RY":
                        self._ry = _apply_deadzone(self._normalize_inputs_axis(state, "ry"), self._dead)
                    elif code == "ABS_Z":
                        self._lt = max(-1.0, min(1.0, (state / 255.0) * 2.0 - 1.0))
                    elif code == "ABS_RZ":
                        self._rt = max(-1.0, min(1.0, (state / 255.0) * 2.0 - 1.0))

                elif etype in ("EV_KEY", "Key"):
                    prev = self._buttons.get(code, 0)
                    pressed = 1 if state else 0
                    if prev == pressed:
                        continue
                    self._buttons[code] = pressed
                    if pressed:
                        if code in ("BTN_SOUTH",):
                            self.enableToggle.emit()
                        elif code in ("BTN_EAST", "BTN_WEST"):
                            self.estopRequested.emit()
                        elif code in ("BTN_NORTH",):
                            self.homeRequested.emit()

            now = time.time()
            if self._enabled and (now - last_emit) >= (1 / 60):
                pitch_deg = self._ly * 30.0
                roll_deg = self._rx * 30.0
                yaw_deg = self._lx * 30.0
                self.anglesChanged.emit(pitch_deg, roll_deg, yaw_deg)
                last_emit = now

            time.sleep(self._dt)

        self._set_connected(False)

    def _hid_loop(self) -> None:
        if hid is None:
            self.debugEvent.emit("hidapi (hid) library not available; controller disabled.")
            return

        last_emit = 0.0

        while self._running:
            if self._device is None:
                self._open_device()
                if self._device is None:
                    self._set_connected(False)
                    time.sleep(0.5)
                    continue

            try:
                data = self._device.read(64, timeout_ms=int(max(1.0, self._dt * 1000)))
            except OSError as exc:
                self.debugEvent.emit(f"HID read failed: {exc}")
                self._close_device()
                self._set_connected(False)
                time.sleep(0.5)
                continue

            if not data:
                self._set_connected(True)
            else:
                report = self._prepare_report(bytes(data))
                if report:
                    processed = self._process_report(report)
                    if not processed and self._layout is None:
                        self._layout = HIDLayout.from_report(report)
                        self.debugEvent.emit(
                            f"Using HID layout with {len(report)}-byte reports: axes={list(self._layout.axes.keys())}"
                        )
                        processed = self._process_report(report)

                    if processed:
                        self._set_connected(True)

            now = time.time()
            if self._enabled and (now - last_emit) >= (1 / 60):
                pitch_deg = self._ly * 30.0
                roll_deg = self._rx * 30.0
                yaw_deg = self._lx * 30.0
                self.anglesChanged.emit(pitch_deg, roll_deg, yaw_deg)
                last_emit = now

            time.sleep(self._dt)

        self._close_device()
        self._set_connected(False)

    def _prepare_report(self, report: bytes) -> bytes:
        return report

    def _open_device(self) -> None:
        if hid is None:
            return

        try:
            devices = hid.enumerate()
        except Exception as exc:
            self.debugEvent.emit(f"hid.enumerate failed: {exc}")
            return

        selected = None
        for info in devices:
            path = info.get("path")
            if not path:
                continue

            path_str = path.decode("utf-8", errors="ignore") if isinstance(path, (bytes, bytearray)) else str(path)
            if self._preferred_path and path_str != self._preferred_path:
                continue

            vendor_id = info.get("vendor_id")
            product_id = info.get("product_id")

            if self._preferred_vendor is not None and vendor_id != self._preferred_vendor:
                continue
            if self._preferred_product is not None and product_id != self._preferred_product:
                continue

            usage_page = info.get("usage_page")
            usage = info.get("usage")
            if usage_page not in (0x01, None):
                continue
            if usage not in (0x04, 0x05, None):  # joystick or gamepad
                continue

            selected = info
            break

        if selected is None:
            return

        path_obj = selected["path"]
        try:
            device_cls = getattr(hid, "Device", None)
            if device_cls is not None:
                self._device = device_cls(path=path_obj)
            else:
                dev = hid.device()
                if hasattr(dev, "open_path"):
                    dev.open_path(path_obj)
                else:
                    dev.open(selected.get("vendor_id", 0), selected.get("product_id", 0))
                self._device = dev

            if hasattr(self._device, "set_nonblocking"):
                self._device.set_nonblocking(True)
            elif hasattr(self._device, "nonblocking"):
                self._device.nonblocking = True  # type: ignore[attr-defined]
            name_parts = []
            if selected.get("manufacturer_string"):
                name_parts.append(selected["manufacturer_string"])
            if selected.get("product_string"):
                name_parts.append(selected["product_string"])
            name = " ".join(name_parts) or "Unknown HID Gamepad"
            self.debugEvent.emit(f"Gamepad connected via HID: {name}")
            self._layout = None
            self._reset_state()
        except Exception as exc:
            self.debugEvent.emit(f"Failed to open HID device: {exc}")
            self._device = None

    def _close_device(self) -> None:
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
        self._device = None
        self._layout = None
        self._reset_state()

    def _process_report(self, report: bytes) -> bool:
        if self._process_xinput_style(report):
            return True

        if self._layout is None:
            return False

        self._lx = self._read_axis(report, self._layout.axes.get("lx"), self._lx)
        self._ly = self._read_axis(report, self._layout.axes.get("ly"), self._ly)
        self._rx = self._read_axis(report, self._layout.axes.get("rx"), self._rx)
        self._ry = self._read_axis(report, self._layout.axes.get("ry"), self._ry)

        self._lt = self._read_trigger(report, self._layout.triggers.get("lt"), self._lt)
        self._rt = self._read_trigger(report, self._layout.triggers.get("rt"), self._rt)

        for code, spec in self._layout.buttons.items():
            if spec.byte >= len(report):
                continue
            pressed = 1 if (report[spec.byte] & (1 << spec.bit)) else 0
            prev = self._buttons.get(code, 0)
            if pressed == prev:
                continue
            self._buttons[code] = pressed

            if pressed:
                if code == "BTN_SOUTH":
                    self.enableToggle.emit()
                elif code in ("BTN_EAST", "BTN_WEST"):
                    self.estopRequested.emit()
                elif code == "BTN_NORTH":
                    self.homeRequested.emit()

        self._debug_axes("hid")
        return True

    def _read_axis(self, report: bytes, spec: Optional[AxisSpec], fallback: float) -> float:
        if spec is None:
            return fallback
        end = spec.index + spec.size
        if end > len(report):
            return fallback

        raw = 0
        for i in range(spec.size):
            raw |= report[spec.index + i] << (8 * i)

        bits = spec.size * 8
        value = _normalize_unsigned(raw, bits)
        if spec.invert:
            value = -value
        return _apply_deadzone(value, self._dead)

    def _read_trigger(self, report: bytes, spec: Optional[TriggerSpec], fallback: float) -> float:
        if spec is None:
            return fallback

        if spec.axis is not None:
            end = spec.axis.index + spec.axis.size
            if end <= len(report):
                raw = 0
                for i in range(spec.axis.size):
                    raw |= report[spec.axis.index + i] << (8 * i)
                bits = spec.axis.size * 8
                value = _normalize_unsigned(raw, bits)
                return max(-1.0, min(1.0, value))

        if spec.button is not None and spec.button.byte < len(report):
            pressed = 1 if (report[spec.button.byte] & (1 << spec.button.bit)) else 0
            return 1.0 if pressed else -1.0

        return fallback

    def _reset_state(self) -> None:
        self._lx = self._ly = self._rx = self._ry = 0.0
        self._lt = self._rt = -1.0
        for key in self._buttons:
            self._buttons[key] = 0
        self._xinput_active = False
        self._last_axes_debug = 0.0
        self._xinput_center = None
        self._inputs_center.clear()
        self._inputs_span.clear()

    def _set_connected(self, on: bool) -> None:
        if on and not self._connected:
            self._connected = True
            self.connected.emit()
        elif not on and self._connected:
            self._connected = False
            self.disconnected.emit()

    def _process_xinput_style(self, report: bytes) -> bool:
        """Handle the packed HID reports used by many Xbox-compatible pads."""

        length = len(report)
        if length < 12:
            return False

        offsets = [9] if length >= 17 else []
        offsets += list(range(0, max(0, length - 12) + 1))

        seen_offsets: set[int] = set()
        for offset in offsets:
            if offset in seen_offsets:
                continue
            seen_offsets.add(offset)

            if offset < 2:
                continue

            try:
                buttons_lo = report[offset - 2]
                buttons_hi = report[offset - 1]
                # Raw triggers are present but Mac reports repurpose these bytes; ignore for now.
                lx, ly, rx, ry = struct.unpack_from("<hhhh", report, offset + 1)
            except (IndexError, struct.error):
                continue

            if not all(-32768 <= v <= 32767 for v in (lx, ly, rx, ry)):
                continue

            if self._xinput_center is None:
                self._xinput_center = (lx, ly, rx, ry)
                self.debugEvent.emit(
                    f"Calibrated XInput center: {self._xinput_center}"
                )

            cx, cy, crx, cry = self._xinput_center

            def _norm_axis(raw: int, center: int) -> float:
                return max(-1.0, min(1.0, (raw - center) / 32767.0))

            self._lx = _apply_deadzone(_norm_axis(lx, cx), self._dead)
            self._ly = _apply_deadzone(_norm_axis(ly, cy), self._dead)
            self._rx = _apply_deadzone(_norm_axis(rx, crx), self._dead)
            self._ry = _apply_deadzone(_norm_axis(ry, cry), self._dead)
            # Triggers are not decoded yet for this layout; keep defaults.
            self._lt = -1.0
            self._rt = -1.0

            buttons = buttons_lo | (buttons_hi << 8)
            mapping = {
                "BTN_SOUTH": 1 << 0,
                "BTN_EAST": 1 << 1,
                "BTN_WEST": 1 << 2,
                "BTN_NORTH": 1 << 3,
            }

            for code, mask in mapping.items():
                pressed = 1 if (buttons & mask) else 0
                prev = self._buttons.get(code, 0)
                if pressed == prev:
                    continue
                self._buttons[code] = pressed
                if pressed:
                    if code == "BTN_SOUTH":
                        self.enableToggle.emit()
                    elif code in ("BTN_EAST", "BTN_WEST"):
                        self.estopRequested.emit()
                    elif code == "BTN_NORTH":
                        self.homeRequested.emit()

            if not self._xinput_active:
                self._xinput_active = True
                self.debugEvent.emit(f"Using XInput HID layout at offset {offset}")
            self._debug_axes("xinput")
            return True

        return False

    def _debug_axes(self, tag: str) -> None:
        now = time.time()
        if now - self._last_axes_debug < 0.25:
            return
        self._last_axes_debug = now
        self.debugEvent.emit(
            f"[{tag}] LX={self._lx:.2f} LY={self._ly:.2f} RX={self._rx:.2f} RY={self._ry:.2f} LT={self._lt:.2f} RT={self._rt:.2f}"
        )

    def _normalize_inputs_axis(self, raw: int, axis: str) -> float:
        center = self._inputs_center.get(axis)
        span = self._inputs_span.get(axis)
        if center is None or span is None:
            center, span = self._guess_inputs_axis_calibration(raw)
            self._inputs_center[axis] = center
            self._inputs_span[axis] = span
            self.debugEvent.emit(
                f"Calibrated inputs {axis}: center={center:.1f} span={span:.1f}"
            )
        else:
            center = float(center)
            span = float(span)
            if span < 1000.0 and abs(float(raw) - center) > 1024.0:
                center, span = self._guess_inputs_axis_calibration(raw)
                self._inputs_center[axis] = center
                self._inputs_span[axis] = span
                self.debugEvent.emit(
                    f"Recalibrated inputs {axis}: center={center:.1f} span={span:.1f}"
                )

        if span == 0:
            return 0.0

        value = (float(raw) - center) / span
        value = max(-1.0, min(1.0, value))

        if abs(value) < 0.05:
            # Slowly recentre when stick returns home.
            self._inputs_center[axis] = 0.9 * center + 0.1 * float(raw)

        return value

    @staticmethod
    def _guess_inputs_axis_calibration(raw: int) -> Tuple[float, float]:
        if 0 <= raw <= 255:
            return 128.0, 127.0
        if 0 <= raw <= 1023:
            return 512.0, 511.0
        if -32768 <= raw <= 32767:
            return 0.0, 32767.0
        return 32768.0, 32767.0


def _parse_int_env(name: str) -> Optional[int]:
    value = os.getenv(name)
    if not value:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None
