from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QDial, QGraphicsView, QGraphicsScene
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

        self.eStop = QPushButton(self)
        self.eStop.setGeometry(QRect(310, 400, 171, 71))
        self.eStop.setObjectName("pushButton")
        self.eStop.setText("E-Stop")
        # Connect the pushButton to a function on click
        self.eStop.clicked.connect(self.estop_pressed)

        self.home = QPushButton(self)
        self.home.setGeometry(QRect(100, 340, 171, 71))
        self.home.setObjectName("pushButton")
        self.home.setText("Home")

        self.home.clicked.connect(self.home_pressed)

        self.enableAll = QCheckBox(self)
        self.enableAll.setGeometry(QRect(310, 450, 171, 71))
        self.enableAll.setObjectName("checkBox")
        self.enableAll.setText("Enable All")
        self.enableAll.stateChanged.connect(self.toggle_enabled)

        self.scrollBox = QScrollArea(self)
        self.scrollBox.setGeometry(QRect(530, 210, 171, 191))
        self.scrollBox.setObjectName("scrollArea")

        self.actuator1 = QDial(self)
        self.actuator1.setGeometry(QRect(100, 280, 50, 64))
        self.actuator1.setObjectName("qDial")
        self.actuator1.valueChanged.connect(self.on_dial_rotate_actuator1)

        self.actuator2 = QDial(self)
        self.actuator2.setGeometry(QRect(160, 240, 50, 64))
        self.actuator2.setObjectName("qDial")
        self.actuator2.valueChanged.connect(self.on_dial_rotate_actuator2)

        self.actuator3 = QDial(self)
        self.actuator3.setGeometry(QRect(220, 280, 50, 64))
        self.actuator3.setObjectName("qDial")
        self.actuator3.valueChanged.connect(self.on_dial_rotate_actuator3)

        self.image = QGraphicsView(self)
        self.image.setGeometry(QRect(270,210,256,192))
        self.image.setObjectName("qGrpahicsView")

        self.scene = QGraphicsScene()
        pixmap = QPixmap("TPED-Logo.png")
        pixmap = pixmap.scaled(186, 186)

        self.scene.addPixmap(pixmap)
        self.image.setScene(self.scene)
    def estop_pressed(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print('Stop')
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
