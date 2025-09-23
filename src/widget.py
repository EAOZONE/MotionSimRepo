# widget.py
# -*- coding: utf-8 -*-
import sys
import time
import threading
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QSlider,
    QGraphicsScene, QVBoxLayout, QDial
)

from ui_form import Ui_Widget  # generated from form.ui
from readCSV import saveFileAsArr
from talkToArduino import ArdiunoTalk


def load_stylesheet(app: QApplication, qss_filename: str):
    base_dir = Path(__file__).resolve().parent

    # First try local dir (src/)
    qss_path = base_dir / qss_filename

    # Then try src/styles/
    if not qss_path.exists():
        qss_path = base_dir / "styles" / qss_filename

    # Then try repo-level styles/
    if not qss_path.exists():
        qss_path = base_dir.parent / "styles" / qss_filename

    if not qss_path.exists():
        raise FileNotFoundError(f"Could not find {qss_filename} near {base_dir}")

    qss = qss_path.read_text(encoding="utf-8")
    app.setStyleSheet(qss)

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Load UI built in Designer ---
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # --- State / hardware ---
        self.stop_loop = False
        self.enabled = False
        self.arduinoTalker = ArdiunoTalk()

        # --- Build scene contents in the QGraphicsView (background + logo + title text if you want it as vector) ---
        self.scene = QGraphicsScene(self)
        self.ui.qGraphicsView.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 800, 600)

        # --- Wire controls ---
        self.eStop: QPushButton = self.findChild(QPushButton, "pushButton")
        self.home: QPushButton = self.findChild(QPushButton, "homeButton")
        self.enableAll: QCheckBox = self.findChild(QCheckBox, "checkBox")
        self.angle1: QSlider = self.findChild(QSlider, "angle1")
        self.angle2: QSlider = self.findChild(QSlider, "angle2")
        self.angle3: QDial = self.findChild(QDial, "angle3")
        self.scrollArea: QScrollArea = self.findChild(QScrollArea, "scrollArea")

        # Signals
        self.eStop.clicked.connect(self.estop_pressed)
        self.home.clicked.connect(self.home_pressed)
        self.enableAll.stateChanged.connect(self.toggle_enabled)

        # Sliders send in one place
        self.angle1.valueChanged.connect(self.on_dial_rotate_any)
        self.angle2.valueChanged.connect(self.on_dial_rotate_any)
        self.angle3.valueChanged.connect(self.on_dial_rotate_any)

        # Build the sequence buttons inside the scroll area’s vertical layout from the .ui
        self.name_buttons = []
        inner = self.scrollArea.widget()  # scrollAreaWidgetContents
        vlayout: QVBoxLayout = inner.layout()  # verticalLayout from form.ui
        for name in ["Sequence 1", "Sequence 2", "Sequence 3", "Sequence 4"]:
            btn = QPushButton(name, self)
            btn.setProperty("sequence", True)  # styled by QSS: QPushButton[sequence="true"] { ... }
            btn.clicked.connect(lambda _, n=name: self.on_name_clicked(n))
            vlayout.addWidget(btn)
            self.name_buttons.append(btn)

        # Keyboard focus for spacebar E-Stop
        self.setFocusPolicy(Qt.StrongFocus)

    # ----------------- Actions / Slots -----------------

    def estop_pressed(self):
        t = threading.Thread(target=self.stop_execution, daemon=True)
        t.start()

    def stop_execution(self):
        print("Stop")
        self.stop_loop = True
        if self.enabled:
            self.enableAll.setChecked(False)

    def on_name_clicked(self, name: str):
        print(f"{name} clicked")
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        arr = saveFileAsArr("test.csv")
        self.disable_name_buttons()
        try:
            for row in arr:
                if self.stop_loop:
                    self.stop_loop = False
                    break
                a1, a2, a3 = row[0], row[1], row[2]
                self.arduinoTalker.send_all_angles(a1, a2, a3)
                print(f"Sequence -> {a1}, {a2}, {a3}")
                QApplication.processEvents()
                time.sleep(0.5)
            print("Hi")
        finally:
            self.enable_name_buttons()

    def disable_name_buttons(self):
        for b in self.name_buttons:
            b.setEnabled(False)
        print("Name buttons disabled")

    def enable_name_buttons(self):
        for b in self.name_buttons:
            b.setEnabled(True)
        print("Name buttons enabled")

    def home_pressed(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print("Home")
        self.angle1.setValue(0)
        self.angle2.setValue(0)
        self.angle3.setValue(0)

    def on_dial_rotate_any(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        self.arduinoTalker.send_all_angles(
            self.angle1.value(), self.angle2.value(), self.angle3.value()
        )
        print(f"Angles: {self.angle1.value()}, {self.angle2.value()}, {self.angle3.value()}")

    def toggle_enabled(self):
        self.enabled = not self.enabled
        self.arduinoTalker.setEnable(self.enabled)
        print(self.enabled)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.estop_pressed()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load your .qss (rename if yours is app.qss vs styles/app.qss)
    load_stylesheet(app, "app.qss")  # or "styles/app.qss"

    w = Widget()
    w.setWindowTitle("Motion Simulator User Interface")
    w.setFixedSize(800, 600)
    w.show()

    sys.exit(app.exec())
