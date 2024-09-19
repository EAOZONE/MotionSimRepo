from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QSlider, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPixmap
import sys


class widget(QWidget):
    def __init__(self):
        self.enabled = False
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setGeometry(QRect(0, 0, 800, 600))
        self.setWindowTitle("Widget")
        self.setStyleSheet("background-color: lightgray;")

        self.eStop = QPushButton(self)
        self.eStop.setGeometry(QRect(310, 400, 171, 71))
        self.eStop.setObjectName("pushButton")
        self.eStop.setText("E-Stop")
        self.eStop.setStyleSheet("background-color: red; color: white;")
        self.eStop.clicked.connect(self.estop_pressed)

        self.home = QPushButton(self)
        self.home.setGeometry(QRect(100, 340, 171, 71))
        self.home.setObjectName("pushButton")
        self.home.setStyleSheet("background-color: green; color: white;")
        self.home.setText("Home")

        self.home.clicked.connect(self.home_pressed)

        self.enableAll = QCheckBox(self)
        self.enableAll.setGeometry(QRect(310, 450, 171, 71))
        self.enableAll.setObjectName("checkBox")
        self.enableAll.setText("Enable All")
        self.enableAll.setStyleSheet("color: black;")
        self.enableAll.stateChanged.connect(self.toggle_enabled)

        self.scrollBox = QScrollArea(self)
        self.scrollBox.setGeometry(QRect(530, 210, 171, 191))
        self.scrollBox.setObjectName("scrollArea")
        self.scrollBox.setStyleSheet("background-color: white; color: black;")

        self.actuator1 = QSlider(Qt.Horizontal, self)
        self.actuator1.setGeometry(QRect(100, 280, 64, 50))
        self.actuator1.setObjectName("horizontalSlider")
        self.actuator1.valueChanged.connect(self.on_dial_rotate_actuator1)

        self.actuator2 = QSlider(Qt.Horizontal, self)
        self.actuator2.setGeometry(QRect(160, 240, 64, 50))
        self.actuator2.setObjectName("horizontalSlider")
        self.actuator2.valueChanged.connect(self.on_dial_rotate_actuator2)

        self.actuator3 = QSlider(Qt.Horizontal, self)
        self.actuator3.setGeometry(QRect(220, 280, 64, 50))
        self.actuator3.setObjectName("horizontalSlider")
        self.actuator3.valueChanged.connect(self.on_dial_rotate_actuator3)

        self.image = QGraphicsView(self)
        self.image.setGeometry(QRect(300,210,192,192))
        self.image.setObjectName("qGrpahicsView")

        self.scene = QGraphicsScene()
        pixmap = QPixmap("TPED-logo.jpg")
        pixmap = pixmap.scaled(186, 186)

        self.scene.addPixmap(pixmap)
        self.image.setScene(self.scene)
    def estop_pressed(self):
        print('Stop')
        if self.enabled:
            self.enableAll.setChecked(False)
    def home_pressed(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print('Home')
        self.actuator1.setValue(0)
        self.actuator2.setValue(0)
        self.actuator3.setValue(0)
    def on_dial_rotate_actuator1(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print(f"Dial rotated to: {self.actuator1.value()}")
    def on_dial_rotate_actuator2(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print(f"Dial rotated to: {self.actuator2.value()}")
    def on_dial_rotate_actuator3(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print(f"Dial rotated to: {self.actuator3.value()}")
    def toggle_enabled(self):
        self.enabled = not self.enabled
        print(self.enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = widget()
    widget.show()
    sys.exit(app.exec_())
