from __future__ import annotations

import logging
from functools import partial
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, Slot, QThread
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QCheckBox, QSlider, QDial, QSpinBox, QDoubleSpinBox, QGroupBox, QProgressBar,
    QLineEdit, QListWidget, QFileDialog, QStatusBar, QTextEdit, QComboBox, QSizePolicy
)

from core.arduino import ArduinoWorker
from core.controller import ControllerWorker
from core.sequence import SequenceWorker

MODULE_DIR = Path(__file__).resolve().parent
APP_ROOT = MODULE_DIR.parent
REPO_ROOT = APP_ROOT.parent.parent
LOGGER = logging.getLogger(__name__)


def hline() -> QtWidgets.QFrame:
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.HLine)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)
    return frame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motion Simulator Control")
        self.setMinimumSize(1024, 700)

        self._enabled = False
        self._drive_manual = True
        self._sequence_buttons: list[QPushButton] = []
        self._teardown_done = False
        self._csv_path: Optional[Path] = None
        self.seq_thread: Optional[QThread] = None
        self.seq: Optional[SequenceWorker] = None
        self._sequence_aborted = False

        preset_mapping = {
            "Sequence 1": "src/test.csv",
            "Sequence 2": "Name1.csv",
            "Sequence 3": "src/test.csv",
            "Sequence 4": "src/test.csv",
        }
        self._preset_sequences: dict[str, Optional[Path]] = {}
        for name, rel in preset_mapping.items():
            path = (REPO_ROOT / rel).resolve()
            self._preset_sequences[name] = path if path.exists() else None

        central = QWidget(self)
        central.setObjectName("centralWidget")
        central.setAttribute(Qt.WA_StyledBackground, True)  # ensure background paints

        bg = "../images/background.png"
        self.setStyleSheet(f"""
        QMainWindow, QWidget#centralWidget {{
            background-image: url('{bg}');
            background-attachment: fixed;
            background-size: cover;
        }}
        """)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 18)
        main_layout.setSpacing(18)

        # ---- Top command bar -------------------------------------------------
        cmd_bar = QHBoxLayout()
        cmd_bar.setSpacing(12)
        self.btn_open_csv_top = QPushButton("Open CSV")
        self.btn_play_top = QPushButton("Play")
        self.btn_stop_top = QPushButton("Stop")
        self.btn_stop_top.setEnabled(False)
        self.btn_gamepad_toggle = QPushButton("Gamepad ON")
        self.btn_gamepad_toggle.setCheckable(True)
        self.btn_gamepad_toggle.setChecked(True)
        self.btn_enable_toggle = QPushButton("Enable")
        self.btn_enable_toggle.setCheckable(True)
        cmd_bar.addWidget(self.btn_open_csv_top)
        cmd_bar.addWidget(self.btn_play_top)
        cmd_bar.addWidget(self.btn_stop_top)
        cmd_bar.addWidget(self.btn_gamepad_toggle)
        cmd_bar.addWidget(self.btn_enable_toggle)

        self.dock_ard = QtWidgets.QDockWidget("Arduino", self)
        self.dock_ard.hide()
        self.dock_ard.setObjectName("dockArduino")  # needed for saveState/restoreState
        self.dock_ard.setFloating(True)
        self.dock_ard.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable |
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.dock_ard.setMaximumHeight(260)
        self.cb_show_arduino = QCheckBox("Arduino")
        self.cb_show_arduino.setChecked(False)  # visible by default
        self.cb_show_arduino.toggled.connect(self.dock_ard.setVisible)

        cmd_bar.addWidget(self.cb_show_arduino)

        self.dock_log = QtWidgets.QDockWidget("Log", self)
        self.dock_log.hide()
        self.dock_log.setObjectName("dockLog")  # needed for saveState/restoreState
        self.dock_log.setFloating(True)
        self.dock_log.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable |
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.dock_log.setMaximumHeight(260)
        self.cb_show_log = QCheckBox("Log")
        self.cb_show_log.setChecked(False)  # visible by default
        self.cb_show_log.toggled.connect(self.dock_log.setVisible)

        cmd_bar.addWidget(self.cb_show_log)
        cmd_bar.addStretch(1)
        self.cb_show_arduino.setProperty("pill", True)
        self.cb_show_log.setProperty("pill", True)

        main_layout.addLayout(cmd_bar)

        # ---- Main content layout ---------------------------------------------
        content = QHBoxLayout()
        content.setSpacing(18)
        main_layout.addLayout(content, 1)

        # -------- Left column: safety + manual controls --------
        left_widget = QWidget()
        left_widget.setObjectName("leftColumn")
        left_col = QVBoxLayout(left_widget)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(12)

        g_safety = QGroupBox("Safety")
        g_safety.setObjectName("safetyGroup")
        v_safety = QVBoxLayout(g_safety)
        v_safety.setSpacing(8)
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setObjectName("estop")
        self.btn_estop.setMinimumSize(180, 110)
        self.btn_estop.setCheckable(True)
        self.chk_enable = QCheckBox("Enable / Arm system")
        self.chk_enable.setChecked(False)
        v_safety.addWidget(self.btn_estop)
        v_safety.addWidget(self.chk_enable)
        v_safety.addWidget(hline())
        left_col.addWidget(g_safety)

        g_angles = QGroupBox("Manual Control (°)")
        g_angles.setObjectName("manualGroup")
        self.g_angles = g_angles
        self.g_angles.setEnabled(False)
        grid = QGridLayout(g_angles)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        def angle_row(row: int, label: str):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(-30, 30)
            dial = QDial()
            dial.setRange(-30, 30)
            dial.setNotchesVisible(True)
            spin = QSpinBox()
            spin.setRange(-30, 30)
            sld.valueChanged.connect(dial.setValue)
            sld.valueChanged.connect(spin.setValue)
            dial.valueChanged.connect(sld.setValue)
            dial.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(sld.setValue)
            spin.valueChanged.connect(self._send_all_angles)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(sld, row, 1)
            grid.addWidget(dial, row, 2)
            grid.addWidget(spin, row, 3)
            return sld, dial, spin

        self.pitch_sld, self.pitch_dial, self.pitch_spn = angle_row(0, "Pitch")
        self.roll_sld, self.roll_dial, self.roll_spn = angle_row(1, "Roll")
        self.yaw_sld, self.yaw_dial, self.yaw_spn = angle_row(2, "Yaw")

        jog_row = QHBoxLayout()
        jog_row.setSpacing(8)
        for text, delta in (("-5°", -5), ("-1°", -1), ("+1°", 1), ("+5°", 5)):
            btn = QPushButton(text)
            btn.clicked.connect(partial(self._jog_selected, delta))
            jog_row.addWidget(btn)
        grid.addLayout(jog_row, 3, 0, 1, 4)

        left_col.addWidget(g_angles, 1)
        left_col.addStretch(1)
        left_widget.setMinimumWidth(280)
        content.addWidget(left_widget, 0)

        # -------- Centre column: display + quick sequences --------
        center_widget = QWidget()
        center_widget.setObjectName("centerColumn")
        center_col = QVBoxLayout(center_widget)
        center_col.setContentsMargins(0, 0, 0, 0)
        center_col.setSpacing(12)

        sequence_box = QGroupBox("Sequences")
        sequence_box.setObjectName("sequenceBox")
        seq_layout = QVBoxLayout(sequence_box)
        seq_layout.setContentsMargins(18, 12, 18, 16)
        seq_layout.setSpacing(10)
        for name in ("Sequence 1", "Sequence 2", "Sequence 3", "Sequence 4"):
            btn = QPushButton(name)
            btn.setProperty("sequence", True)
            btn.setMinimumHeight(40)
            btn.clicked.connect(partial(self._run_sequence_preset, name))
            seq_layout.addWidget(btn)
            self._sequence_buttons.append(btn)
        center_col.addWidget(sequence_box, 0, alignment=Qt.AlignHCenter)
        g_log = QGroupBox("Log")
        v_log = QVBoxLayout(g_log)
        v_log.setSpacing(4)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMinimumHeight(150)
        v_log.addWidget(self.txt_log)
        self.dock_log.setWidget(g_log)
        self.dock_log.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_log)

        hint = QLabel("Gamepad mapping: LX → Yaw, LY → Pitch, RX → Roll")
        hint.setObjectName("hintLabel")
        hint.setAlignment(Qt.AlignCenter)
        center_col.addWidget(hint)
        content.addWidget(center_widget, 1)

        # -------- Right column: automation / controller --------
        right_widget = QWidget()
        right_widget.setObjectName("rightColumn")
        right_col = QVBoxLayout(right_widget)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(12)

        g_seq = QGroupBox("Sequence Runner")
        v_seq = QVBoxLayout(g_seq)
        v_seq.setSpacing(8)
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self.btn_load_csv = QPushButton("Load CSV")
        self.le_csv = QLineEdit()
        self.le_csv.setPlaceholderText("No file loaded")
        self.le_csv.setReadOnly(True)
        self.le_dt = QDoubleSpinBox()
        self.le_dt.setPrefix("dt ")
        self.le_dt.setSuffix(" s")
        self.le_dt.setRange(0.01, 10.0)
        self.le_dt.setSingleStep(0.05)
        self.le_dt.setValue(0.50)
        top_row.addWidget(self.btn_load_csv)
        top_row.addWidget(self.le_csv, 1)
        top_row.addWidget(self.le_dt)
        v_seq.addLayout(top_row)
        self.seq_list = QListWidget()
        self.seq_list.setMinimumHeight(160)
        v_seq.addWidget(self.seq_list)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
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
        v_ctrl.setSpacing(15)
        self.lbl_ctrl_status = QLabel("Controller: Disconnected")
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

        self.cb_show_arduino.setProperty("pill", True)
        self.pb_lx.setProperty("controller", True)
        self.pb_ly.setProperty("controller", True)
        self.pb_rx.setProperty("controller", True)
        self.pb_ry.setProperty("controller", True)
        v_ctrl.addWidget(self.pb_lx)
        v_ctrl.addWidget(self.pb_ly)
        v_ctrl.addWidget(self.pb_rx)
        v_ctrl.addWidget(self.pb_ry)
        right_col.addWidget(g_ctrl)

        g_ard = QGroupBox("Arduino")
        v_ard = QVBoxLayout(g_ard)
        v_ard.setSpacing(8)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.cb_port = QComboBox()
        self.cb_port.setEditable(True)
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
        self.dock_ard.setWidget(g_ard)
        self.dock_ard.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_ard)


        right_col.addStretch(1)
        right_widget.setMinimumWidth(320)
        content.addWidget(right_widget, 0)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.lbl_status = QLabel("Ready")
        self.status.addPermanentWidget(self.lbl_status)

        # State + workers
        self._start_workers()
        self.destroyed.connect(self.teardown)

        # Wire signals
        self.btn_open_csv_top.clicked.connect(self._choose_csv)
        self.btn_play_top.clicked.connect(self._seq_run)
        self.btn_stop_top.clicked.connect(self._seq_abort)
        self.btn_enable_toggle.toggled.connect(self.chk_enable.setChecked)
        self.btn_gamepad_toggle.toggled.connect(self._on_gamepad_toggled)

        self.btn_estop.clicked.connect(self._on_estop)
        self.chk_enable.toggled.connect(self._on_enable_changed)
        self.chk_ctrl_drive.toggled.connect(self._on_drive_manual_toggled)

        self.btn_load_csv.clicked.connect(self._choose_csv)
        self.btn_seq_run.clicked.connect(self._seq_run)
        self.btn_seq_pause.clicked.connect(self._seq_pause)
        self.btn_seq_abort.clicked.connect(self._seq_abort)
        self.btn_connect.clicked.connect(self._arduino_connect_clicked)

        self._set_sequence_running(False)

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
        self.controller.estopRequested.connect(self._on_estop)
        self.controller.enableToggle.connect(self.chk_enable.toggle)
        self.controller.homeRequested.connect(self._on_home_requested)
        self.ctrl_thread.start()

    # --- Slots -------------------------------------------------------
    @Slot()
    def _on_estop(self):
        self.chk_enable.setChecked(False)
        self.lbl_status.setText("E-STOP engaged")
        self._log("E-STOP engaged")

    @Slot(bool)
    def _on_enable_changed(self, enabled: bool):
        self._enabled = enabled
        with QtCore.QSignalBlocker(self.btn_enable_toggle):
            self.btn_enable_toggle.setChecked(enabled)
            self.btn_enable_toggle.setText("Disable" if enabled else "Enable")
        if not enabled:
            self.btn_estop.setChecked(False)
        self.lbl_status.setText("Enabled" if enabled else "Disabled")
        self._log("System enabled" if enabled else "System disabled")
        self.g_angles.setEnabled(enabled)

    def _on_drive_manual_toggled(self, enabled: bool):
        self._drive_manual = enabled

    def _jog_selected(self, delta: int):
        if not self._enabled:
            self._log("Enable the system before jogging.")
            return
        target = None
        focus = self.focusWidget()
        for widget in (self.pitch_spn, self.roll_spn, self.yaw_spn):
            if widget is focus:
                target = widget
                break
        if target is None:
            target = self.pitch_spn
        target.setValue(target.value() + delta)

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

        if self._drive_manual:
            self._sync_manual_controls(int(pitch), int(roll), int(yaw))
            if self._enabled:
                self._send_all_angles()

    def _set_ctrl_status(self, connected: bool):
        self.lbl_ctrl_status.setText(
            "Controller: Connected" if connected else "Controller: Disconnected"
        )
        if not connected and self.btn_gamepad_toggle.isChecked():
            self.btn_gamepad_toggle.setChecked(False)

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

    def _run_sequence_path(self, path: Path):
        if not self._enabled:
            self._log("Enable the system before running sequences.")
            return
        if not path.exists():
            self._log(f"Sequence file not found: {path}")
            return
        if self.seq is not None or (self.seq_thread is not None and self.seq_thread.isRunning()):
            self._seq_abort()
            if self.seq_thread is not None:
                try:
                    self.seq_thread.wait(2000)
                except Exception:
                    pass
            self.seq = None
            self.seq_thread = None

        self._log(f"Running sequence: {path.name}")
        thread = QThread(self)
        self._sequence_aborted = False
        worker = SequenceWorker(str(path), dt=float(self.le_dt.value()))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.stepEmitted.connect(self.arduino.send_angles)
        worker.finished.connect(thread.quit)
        worker.aborted.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.aborted.connect(self._on_sequence_aborted)
        worker.finished.connect(self._on_sequence_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self.seq_thread = thread
        self.seq = worker
        self._set_sequence_running(True)

    def _run_sequence_preset(self, name: str):
        self._log(f"{name} selected")
        path = self._preset_sequences.get(name)
        if path is None:
            self._log(f"No CSV configured for {name}.")
            return
        self._run_sequence_path(path)

    def _seq_run(self):
        if self._csv_path is None:
            self._log("Load a CSV file first.")
            return
        self._run_sequence_path(self._csv_path)

    def _seq_pause(self):
        self._log("Pause requested (implement in SequenceWorker if desired)")

    def _seq_abort(self):
        if self.seq is None:
            self._log("No active sequence to abort.")
            return
        try:
            self.seq.stop()
            self._log("Abort requested")
        except Exception:
            pass
        finally:
            self._set_sequence_running(False)

    def _arduino_connect_clicked(self):
        self._log(f"Connect clicked to port: {self.cb_port.currentText()}")

    def _on_gamepad_toggled(self, checked: bool):
        self.controller.set_enabled(checked)
        with QtCore.QSignalBlocker(self.chk_ctrl_drive):
            self.chk_ctrl_drive.setEnabled(checked)
            if checked:
                self.chk_ctrl_drive.setChecked(self._drive_manual)
            else:
                self.chk_ctrl_drive.setChecked(False)
        self.btn_gamepad_toggle.setText("Gamepad ON" if checked else "Gamepad OFF")
        state = "enabled" if checked else "disabled"
        self._log(f"Gamepad {state}")

    def _on_home_requested(self):
        if not self._enabled:
            return
        self.pitch_spn.setValue(0)
        self.roll_spn.setValue(0)
        self.yaw_spn.setValue(0)
        self._log("Home requested")

    def _set_sequence_running(self, running: bool):
        self.btn_seq_run.setEnabled(not running)
        self.btn_seq_pause.setEnabled(running)
        self.btn_seq_abort.setEnabled(running)
        self.btn_play_top.setEnabled(not running)
        self.btn_stop_top.setEnabled(running)
        for btn in self._sequence_buttons:
            btn.setEnabled(not running)

    # --- Logging / teardown -----------------------------------------
    def _on_sequence_aborted(self):
        self._sequence_aborted = True
        self._log("Sequence aborted")

    def _on_sequence_finished(self):
        if not self._sequence_aborted:
            self._log("Sequence finished")
        self.seq = None
        if self.seq_thread is not None:
            try:
                self.seq_thread.wait(2000)
            except Exception:
                pass
            self.seq_thread = None
        self._set_sequence_running(False)

    def _log(self, message: str):
        LOGGER.info(message)
        self.txt_log.append(message)
        self.lbl_status.setText(message)

    def teardown(self):
        if self._teardown_done:
            return
        self._teardown_done = True

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

    def closeEvent(self, event):
        self.teardown()
        super().closeEvent(event)
