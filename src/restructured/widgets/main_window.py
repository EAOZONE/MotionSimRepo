# widgets/main_window.py
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, Slot, QThread
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QCheckBox, QSlider, QDial, QSpinBox, QDoubleSpinBox, QGroupBox, QProgressBar,
    QLineEdit, QListWidget, QFileDialog, QStatusBar, QTextEdit, QComboBox, QToolBar,
    QSizePolicy
)

from core.arduino import ArduinoWorker
from core.controller import ControllerWorker
from core.sequence import SequenceWorker


def hline() -> QtWidgets.QFrame:
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.HLine)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)
    return frame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motion Simulator Control")
        self.setMinimumSize(1000, 680)

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(16)

        # -------- Left column: safety + manual controls --------
        left_widget = QWidget()
        left_col = QVBoxLayout(left_widget)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(12)

        g_safety = QGroupBox("Safety")
        v_safety = QVBoxLayout(g_safety)
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setObjectName("estop")
        self.btn_estop.setMinimumHeight(96)
        self.btn_estop.setCheckable(True)
        self.chk_enable = QCheckBox("Enable / Arm system")
        v_safety.addWidget(self.btn_estop)
        v_safety.addWidget(self.chk_enable)
        v_safety.addWidget(hline())
        left_col.addWidget(g_safety)

        g_angles = QGroupBox("Manual Control (°)")
        grid = QGridLayout(g_angles)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        def angle_row(row: int, label: str):
            lbl = QLabel(label)
            sld = QSlider(Qt.Horizontal); sld.setRange(-30, 30)
            dial = QDial(); dial.setRange(-30, 30); dial.setNotchesVisible(True)
            spin = QSpinBox(); spin.setRange(-30, 30)
            sld.valueChanged.connect(dial.setValue)
            sld.valueChanged.connect(spin.setValue)
            dial.valueChanged.connect(sld.setValue)
            dial.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(sld.setValue)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(sld, row, 1)
            grid.addWidget(dial, row, 2)
            grid.addWidget(spin, row, 3)
            return sld, dial, spin

        self.pitch_sld, self.pitch_dial, self.pitch_spn = angle_row(0, "Pitch")
        self.roll_sld, self.roll_dial, self.roll_spn = angle_row(1, "Roll")
        self.yaw_sld, self.yaw_dial, self.yaw_spn = angle_row(2, "Yaw")

        jog_row = QHBoxLayout()
        for text, delta in (("-5°", -5), ("-1°", -1), ("+1°", +1), ("+5°", +5)):
            btn = QPushButton(text)
            btn.clicked.connect(lambda _=False, d=delta: self._jog_selected(d))
            jog_row.addWidget(btn)
        grid.addLayout(jog_row, 3, 1, 1, 3)
        left_col.addWidget(g_angles, 1)
        left_col.addStretch(1)
        left_widget.setMinimumWidth(280)
        root.addWidget(left_widget, 0)

        # -------- Middle column: simple display image --------
        center_widget = QWidget()
        center_col = QVBoxLayout(center_widget)
        center_col.setContentsMargins(0, 0, 0, 0)
        center_col.setSpacing(8)

        self.display_img = QLabel()
        self.display_img.setAlignment(Qt.AlignCenter)
        self.display_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._base_pixmap: Optional[QPixmap] = None
        self._load_display_image()
        center_col.addWidget(self.display_img, 1)

        hint = QLabel("Gamepad mapping: LX → Yaw, LY → Pitch, RX → Roll")
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("hintLabel")
        center_col.addWidget(hint)
        root.addWidget(center_widget, 1)

        # -------- Right column: automation / controller --------
        right_widget = QWidget()
        right_col = QVBoxLayout(right_widget)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(12)

        g_seq = QGroupBox("Sequence")
        v_seq = QVBoxLayout(g_seq)
        top_row = QHBoxLayout()
        self.btn_load_csv = QPushButton("Load CSV")
        self.le_csv = QLineEdit(); self.le_csv.setPlaceholderText("No file loaded")
        self.le_dt = QDoubleSpinBox(); self.le_dt.setPrefix("dt "); self.le_dt.setSuffix(" s")
        self.le_dt.setRange(0.01, 10.0); self.le_dt.setSingleStep(0.05); self.le_dt.setValue(0.50)
        top_row.addWidget(self.btn_load_csv)
        top_row.addWidget(self.le_csv, 1)
        top_row.addWidget(self.le_dt)
        v_seq.addLayout(top_row)
        self.seq_list = QListWidget(); self.seq_list.setMinimumHeight(140)
        v_seq.addWidget(self.seq_list)
        btn_row = QHBoxLayout()
        self.btn_seq_run = QPushButton("Run")
        self.btn_seq_pause = QPushButton("Pause")
        self.btn_seq_abort = QPushButton("Abort")
        btn_row.addWidget(self.btn_seq_run)
        btn_row.addWidget(self.btn_seq_pause)
        btn_row.addWidget(self.btn_seq_abort)
        v_seq.addLayout(btn_row)
        right_col.addWidget(g_seq)

        g_ctrl = QGroupBox("Controller")
        v_ctrl = QVBoxLayout(g_ctrl)
        self.lbl_ctrl_status = QLabel("Disconnected")
        self.chk_ctrl_drive = QCheckBox("Drive manual controls")
        self.chk_ctrl_drive.setChecked(True)
        self.pb_lx = QProgressBar()
        self.pb_ly = QProgressBar()
        self.pb_rx = QProgressBar()
        self.pb_ry = QProgressBar()
        for bar, name in ((self.pb_lx, "LX"), (self.pb_ly, "LY"), (self.pb_rx, "RX"), (self.pb_ry, "RY")):
            bar.setRange(-100, 100)
            bar.setFormat(f"{name} %v")
        v_ctrl.addWidget(self.lbl_ctrl_status)
        v_ctrl.addWidget(self.chk_ctrl_drive)
        v_ctrl.addWidget(self.pb_lx)
        v_ctrl.addWidget(self.pb_ly)
        v_ctrl.addWidget(self.pb_rx)
        v_ctrl.addWidget(self.pb_ry)
        right_col.addWidget(g_ctrl)

        g_ard = QGroupBox("Arduino")
        v_ard = QVBoxLayout(g_ard)
        row = QHBoxLayout()
        self.cb_port = QComboBox(); self.cb_port.setEditable(True)
        self.btn_connect = QPushButton("Connect")
        row.addWidget(QLabel("Port:"))
        row.addWidget(self.cb_port, 1)
        row.addWidget(self.btn_connect)
        self.lbl_ard_status = QLabel("Disconnected")
        self.lbl_ack = QLabel("ACK: —")
        self.lbl_err = QLabel("ERR: —")
        v_ard.addLayout(row)
        v_ard.addWidget(self.lbl_ard_status)
        v_ard.addWidget(self.lbl_ack)
        v_ard.addWidget(self.lbl_err)
        right_col.addWidget(g_ard)

        g_log = QGroupBox("Log")
        v_log = QVBoxLayout(g_log)
        self.txt_log = QTextEdit(); self.txt_log.setReadOnly(True); self.txt_log.setMinimumHeight(120)
        v_log.addWidget(self.txt_log)
        right_col.addWidget(g_log, 1)
        right_col.addStretch(1)
        right_widget.setMinimumWidth(300)
        root.addWidget(right_widget, 0)

        # Toolbar and status bar
        tb = QToolBar("Main"); tb.setIconSize(QtCore.QSize(16, 16)); self.addToolBar(tb)
        action_open = QAction("Open CSV", self)
        action_play = QAction("Play", self)
        action_stop = QAction("Stop", self)
        action_toggle_ctrl = QAction("Gamepad ON/OFF", self)
        action_enable = QAction("Enable", self); action_enable.setCheckable(True)
        for act in (action_open, None, action_play, action_stop, None, action_toggle_ctrl, None, action_enable):
            if act is None:
                tb.addSeparator()
            else:
                tb.addAction(act)

        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.lbl_status = QLabel("Ready")
        self.status.addPermanentWidget(self.lbl_status)

        # State + workers
        self._enabled = False
        self._csv_path: Optional[Path] = None
        self._start_workers()

        # Wire signals
        action_open.triggered.connect(self._choose_csv)
        action_play.triggered.connect(self._seq_run)
        action_stop.triggered.connect(self._seq_abort)
        action_enable.toggled.connect(self.chk_enable.setChecked)
        action_toggle_ctrl.triggered.connect(self._toggle_controller)

        self.btn_estop.clicked.connect(self._on_estop)
        self.chk_enable.toggled.connect(self._on_enable_changed)

        for widget in (self.pitch_spn, self.roll_spn, self.yaw_spn):
            widget.valueChanged.connect(self._send_all_angles)

        self.btn_load_csv.clicked.connect(self._choose_csv)
        self.btn_seq_run.clicked.connect(self._seq_run)
        self.btn_seq_pause.clicked.connect(self._seq_pause)
        self.btn_seq_abort.clicked.connect(self._seq_abort)
        self.btn_connect.clicked.connect(self._arduino_connect_clicked)

        self._update_display_pixmap()

    # --- Helpers -----------------------------------------------------
    def _load_display_image(self):
        for path in ("images/GUI-img.png", "images/background.png", "images/img.png"):
            pix = QPixmap(path)
            if not pix.isNull():
                self._base_pixmap = pix
                self.display_img.setPixmap(pix)
                return
        self._base_pixmap = None
        self.display_img.clear()

    def _update_display_pixmap(self):
        if self._base_pixmap is None or self.display_img.width() <= 0:
            return
        scaled = self._base_pixmap.scaled(
            self.display_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.display_img.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display_pixmap()

    # --- Worker setup ------------------------------------------------
    def _start_workers(self):
        # Arduino worker
        self.ard_thread = QThread(self)
        self.arduino = ArduinoWorker(preferred_port=None)
        self.arduino.moveToThread(self.ard_thread)
        self.ard_thread.started.connect(self.arduino.start)
        self.destroyed.connect(self.arduino.stop)
        self.arduino.connected.connect(lambda p: self._set_arduino_status(f"Connected: {p}"))
        self.arduino.disconnected.connect(lambda _="": self._set_arduino_status("Disconnected"))
        self.arduino.ack.connect(self._set_ack)
        self.arduino.error.connect(self._set_error)
        self.ard_thread.start()

        # Controller worker
        self.ctrl_thread = QThread(self)
        self.controller = ControllerWorker()
        self.controller.moveToThread(self.ctrl_thread)
        self.ctrl_thread.started.connect(self.controller.start)
        self.destroyed.connect(self.controller.stop)
        self.controller.connected.connect(lambda: self._set_ctrl_status(True))
        self.controller.disconnected.connect(lambda: self._set_ctrl_status(False))
        self.controller.anglesChanged.connect(self._ctrl_angles_changed)
        self.controller.debugEvent.connect(lambda msg: self._log(f"[CTRL] {msg}"))
        self.ctrl_thread.start()

    # --- Slots -------------------------------------------------------
    @Slot()
    def _on_estop(self):
        self.chk_enable.setChecked(False)
        self.lbl_status.setText("E-STOP engaged")

    @Slot(bool)
    def _on_enable_changed(self, enabled: bool):
        self._enabled = enabled
        self.lbl_status.setText("Enabled" if enabled else "Disabled")

    def _jog_selected(self, delta: int):
        if not self._enabled:
            return
        self.pitch_spn.setValue(self.pitch_spn.value() + delta)

    @Slot()
    def _send_all_angles(self):
        if not self._enabled:
            return
        self.arduino.send_angles(
            self.pitch_spn.value(), self.roll_spn.value(), self.yaw_spn.value()
        )

    @Slot(float, float, float)
    def _ctrl_angles_changed(self, pitch, roll, yaw):
        self.pb_lx.setValue(int(max(-100, min(100, getattr(self.controller, "_lx", 0.0) * 100))))
        self.pb_ly.setValue(int(max(-100, min(100, getattr(self.controller, "_ly", 0.0) * 100))))
        self.pb_rx.setValue(int(max(-100, min(100, getattr(self.controller, "_rx", 0.0) * 100))))
        self.pb_ry.setValue(int(max(-100, min(100, getattr(self.controller, "_ry", 0.0) * 100))))

        if self.chk_ctrl_drive.isChecked():
            self._sync_manual_controls(int(pitch), int(roll), int(yaw))
            if self._enabled:
                self._send_all_angles()

    def _set_ctrl_status(self, connected: bool):
        self.lbl_ctrl_status.setText(
            "Controller: Connected" if connected else "Controller: Disconnected"
        )

    def _set_arduino_status(self, text: str):
        self.lbl_ard_status.setText(text)
        self._log(text)

    def _set_ack(self, msg: str):
        self.lbl_ack.setText(f"ACK: {msg}")

    def _set_error(self, msg: str):
        self.lbl_err.setText(f"ERR: {msg}")
        self._log(f"[ERR] {msg}")

    def _sync_manual_controls(self, pitch: int, roll: int, yaw: int) -> None:
        def apply_triplet(attrs, value):
            value = max(-30, min(30, value))
            blockers = [QtCore.QSignalBlocker(widget) for widget in attrs]
            slider, dial, spin = attrs
            slider.setValue(value)
            dial.setValue(value)
            spin.setValue(value)
            del blockers

        apply_triplet((self.pitch_sld, self.pitch_dial, self.pitch_spn), pitch)
        apply_triplet((self.roll_sld, self.roll_dial, self.roll_spn), roll)
        apply_triplet((self.yaw_sld, self.yaw_dial, self.yaw_spn), yaw)

    # --- Sequence / Automation --------------------------------------
    def _choose_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        self._csv_path = Path(path)
        self.le_csv.setText(path)
        try:
            import csv
            self.seq_list.clear()
            with open(self._csv_path, "r", newline="") as fh:
                reader = csv.reader(fh)
                for idx, row in enumerate(reader):
                    self.seq_list.addItem(", ".join(row[:3]))
                    if idx > 200:
                        break
        except Exception as exc:
            self._log(f"CSV read error: {exc}")

    def _seq_run(self):
        if not self._enabled or not self._csv_path:
            return
        self._log(f"Running sequence: {self._csv_path.name}")
        self.seq_thread = QThread(self)
        self.seq = SequenceWorker(str(self._csv_path), dt=float(self.le_dt.value()))
        self.seq.moveToThread(self.seq_thread)
        self.seq_thread.started.connect(self.seq.run)
        self.seq.stepEmitted.connect(lambda a, b, c: self.arduino.send_angles(a, b, c))
        self.seq.finished.connect(self.seq_thread.quit)
        self.seq.aborted.connect(self.seq_thread.quit)
        self.seq_thread.start()

    def _seq_pause(self):
        self._log("Pause requested (implement in SequenceWorker if desired)")

    def _seq_abort(self):
        try:
            self.seq.stop()
            self._log("Abort requested")
        except Exception:
            pass

    def _arduino_connect_clicked(self):
        self._log(f"Connect clicked to port: {self.cb_port.currentText()}")

    def _toggle_controller(self):
        self.controller.toggle_enabled()
        state = "enabled" if getattr(self.controller, "_enabled", True) else "disabled"
        self._log(f"Gamepad {state}")

    # --- Logging / teardown -----------------------------------------
    def _log(self, message: str):
        self.txt_log.append(message)
        self.lbl_status.setText(message)

    def teardown(self):
        seq = getattr(self, "seq", None)
        if seq is not None:
            try:
                seq.stop()
            except Exception:
                pass
        seq_thread = getattr(self, "seq_thread", None)
        if seq_thread is not None:
            try:
                seq_thread.quit()
                seq_thread.wait(3000)
            except Exception:
                pass

        if hasattr(self, "controller"):
            try:
                self.controller.stop()
            except Exception:
                pass
        if hasattr(self, "ctrl_thread"):
            try:
                self.ctrl_thread.quit()
                self.ctrl_thread.wait(3000)
            except Exception:
                pass

        if hasattr(self, "arduino"):
            try:
                self.arduino.stop()
            except Exception:
                pass
        if hasattr(self, "ard_thread"):
            try:
                self.ard_thread.quit()
                self.ard_thread.wait(3000)
            except Exception:
                pass
