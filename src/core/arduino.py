# core/arduino.py
from PySide6.QtCore import QObject, QThread, Signal, Slot
import serial, serial.tools.list_ports, time, queue, threading


class ArduinoWorker(QObject):
    connected = Signal(str)
    disconnected = Signal(str)
    ack = Signal(str)
    error = Signal(str)

    def __init__(self, preferred_port: str | None = None, baud=9600, parent=None):
        super().__init__(parent)
        self._ser = None
        self._baud = baud
        self._port = preferred_port
        self._cmd_q = queue.Queue()
        self._stop = threading.Event()
        self._max_wait_s = 60.0  # how long to wait for "Finished"

    def start(self):
        self._open_serial()
        t = threading.Thread(target=self._pump, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()
        if self._ser:
            try: self._ser.close()
            except: pass
            self.disconnected.emit(self._port or "")

    def _detect_port(self) -> str | None:
        if self._port: return self._port
        for p in serial.tools.list_ports.comports():
            if "Arduino" in p.description or "usbmodem" in p.device or "wchusbserial" in p.device:
                return p.device
        return None

    def _open_serial(self):
        port = self._detect_port()
        if not port:
            self.error.emit("Arduino port not found")
            return
        try:
            self._ser = serial.Serial(port=port, baudrate=self._baud, timeout=0.2)
            self._port = port
            self.connected.emit(port)
            time.sleep(1.5)  # let Arduino reset
        except Exception as e:
            self.error.emit(f"Serial open failed: {e}")

    def _pump(self):
        while not self._stop.is_set():
            try:
                cmd = self._cmd_q.get(timeout=0.05)
            except queue.Empty:
                continue

            if not self._ser:
                self._open_serial()
                if not self._ser:
                    self.error.emit("No serial; dropping command")
                    continue

            try:
                # clear any stale output
                self._ser.reset_input_buffer()

                # send command
                self._ser.write((cmd + "\n").encode())

                # blocking wait for "Finished" with timeout
                t0 = time.time()
                finished = False
                while time.time() - t0 < self._max_wait_s:
                    line = self._ser.readline()
                    if not line:
                        continue
                    s = line.decode(errors="ignore").strip()

                    # optional: you can log/forward other messages here if desired
                    print("ARDUINO:", s)

                    if s == "Finished" or "Finished" in s:
                        self.ack.emit("Finished")
                        finished = True
                        break

                if not finished:
                    self.error.emit("Timeout waiting for 'Finished' from Arduino")

            except Exception as e:
                self.error.emit(f"Write/read failed: {e}")
                try:
                    self._ser.close()
                except:
                    pass
                self._ser = None

    @Slot(float, float, float)
    def send_angles(self, a1: float, a2: float, a3: float):
        # prepare clamped integer command once here
        a1, a2 = a1, a2
        cmd = f"{a1},{a2},{a3}"
        print(cmd)
        self._cmd_q.put(cmd)
