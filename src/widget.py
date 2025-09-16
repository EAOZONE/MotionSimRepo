import sys, time, threading
from pathlib import Path

from PySide6 import QtUiTools, QtCore
from PySide6.QtCore import QRect, Qt, QPoint
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QSlider,
    QGraphicsView, QVBoxLayout, QGraphicsScene, QGraphicsTextItem, QLabel
)
from PySide6.QtGui import QPixmap, QKeyEvent, QFont

from readCSV import saveFileAsArr
from talkToArduino import ArdiunoTalk


class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.eStop = None
        self.stop_loop = None
        self.actuator1 = 0
        self.actuator2 = 0
        self.enabled = False
        self.arduinoTalker = ArdiunoTalk()

        self._load_ui()
        self._apply_qss()
        self._init_graphics_scene()
        self._setup_scrollbox()
        self._connect_signals()

    # --- UI / QSS loading ---
    def _load_ui(self):
        loader = QtUiTools.QUiLoader()
        ui_file = QtCore.QFile("form.ui")
        if not ui_file.open(QtCore.QFile.ReadOnly):
            raise RuntimeError("Could not open form.ui")
        root = loader.load(ui_file, self)  # parent = self
        ui_file.close()

        # Put the loaded form inside this Widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(root)

        # Grab references by objectName
        self.image: QGraphicsView = root.findChild(QGraphicsView, "graphicsView")
        self.eStop: QPushButton = root.findChild(QPushButton, "eStopButton")
        self.home: QPushButton = root.findChild(QPushButton, "homeButton")
        self.enableAll: QCheckBox = root.findChild(QCheckBox, "enableAllCheck")
        self.angle1: QSlider = root.findChild(QSlider, "angle1Slider")
        self.angle2: QSlider = root.findChild(QSlider, "angle2Slider")
        self.angle3: QSlider = root.findChild(QSlider, "angle3Slider")
        self.scrollBox: QScrollArea = root.findChild(QScrollArea, "scrollArea")

        # Ensure fixed size as before
        self.setFixedSize(800, 600)

    def _apply_qss(self):
        qss_path = Path("styles.qss")
        if qss_path.exists():
            QApplication.instance().setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # --- GraphicsView background + overlay text ---
    def _init_graphics_scene(self):
        self.scene = QGraphicsScene()
        self.image.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 800, 600)

        self._bg_pix = QPixmap("../images/background.png")  # or robust disk path
        self._bg_item = self.scene.addPixmap(self._bg_pix)

        # Logo (adjust path or move to :/resources)
        pixmap = QPixmap("../images/TPED-logo-cropped.png").scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item = self.scene.addPixmap(pixmap)
        item.setPos(-50, -60)

        # Title overlay
        text_item = QGraphicsTextItem("Motion Simulator Design Team")
        text_item.setDefaultTextColor(Qt.white)
        text_item.setFont(QFont("Anton", 30))
        text_item.setPos(200, 60)
        self.scene.addItem(text_item)

    # --- Scroll area with sequence buttons ---
    def _setup_scrollbox(self):
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollLayout.setContentsMargins(35, 10, 10, 10)

        self.name_buttons = []
        for name in ["Sequence 1", "Sequence 2", "Sequence 3", "Sequence 4"]:
            button = QPushButton(name)
            button.setMinimumHeight(35)
            button.setMinimumWidth(125)
            # Inherit global QSS; optional per-button tweaks:
            # button.setStyleSheet("font-size: 12px;")
            button.clicked.connect(lambda checked=False, n=name: self.on_name_clicked(n))
            self.scrollLayout.addWidget(button)
            self.name_buttons.append(button)

        self.scrollBox.setWidget(self.scrollWidget)

    # --- Signal wiring ---
    def _connect_signals(self):
        self.eStop.clicked.connect(self.estop_pressed)
        self.home.clicked.connect(self.home_pressed)
        self.enableAll.stateChanged.connect(self.toggle_enabled)
        self.angle1.valueChanged.connect(self.on_dial_rotate_actuator1)
        self.angle2.valueChanged.connect(self.on_dial_rotate_actuator2)
        self.angle3.valueChanged.connect(self.on_dial_rotate_actuator3)

    # --- Original logic (unchanged) ---
    def estop_pressed(self):
        t = threading.Thread(target=self.stop_execution, daemon=True)
        t.start()

    def stop_execution(self):
        print("Stop")
        self.stop_loop = True
        if self.enabled:
            # This will also trigger toggle_enabled via stateChanged
            self.enableAll.setChecked(False)

    def on_name_clicked(self, name):
        print(f"{name} clicked")
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        arr = saveFileAsArr("test.csv")
        self.disable_name_buttons()
        for i in range(len(arr)):
            if self.stop_loop:
                self.stop_loop = False
                break
            self.arduinoTalker.send_all_angles(arr[i][0], arr[i][1], arr[i][2])
            print(f"Dial rotated to: {arr[i][0]}, {arr[i][1]}, {arr[i][2]}")
            QApplication.processEvents()
            time.sleep(0.5)
        self.enable_name_buttons()

    def disable_name_buttons(self):
        for b in self.name_buttons: b.setEnabled(False)
        print("Name buttons disabled")

    def enable_name_buttons(self):
        for b in self.name_buttons: b.setEnabled(True)
        print("Name buttons enabled")

    def home_pressed(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print("Home")
        self.angle1.setValue(0)
        self.angle2.setValue(0)
        self.angle3.setValue(0)

    def on_dial_rotate_actuator1(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        self.arduinoTalker.send_all_angles(self.angle1.value(), self.angle2.value(), self.angle3.value())
        print(f"Dial rotated to: {self.angle1.value()}")

    def on_dial_rotate_actuator2(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        self.arduinoTalker.send_all_angles(self.angle1.value(), self.angle2.value(), self.angle3.value())
        print(f"Dial rotated to: {self.angle2.value()}")

    def on_dial_rotate_actuator3(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        self.arduinoTalker.send_all_angles(self.angle1.value(), self.angle2.value(), self.angle3.value())
        print(f"Dial rotated to: {self.angle3.value()}")

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
    w = Widget()
    w.show()
    sys.exit(app.exec())
