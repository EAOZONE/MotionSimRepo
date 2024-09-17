from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QDial
import sys

class widget(QWidget):
    def __init__(self):
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

        self.scrollBox = QScrollArea(self)
        self.scrollBox.setGeometry(QRect(530, 210, 171, 191))
        self.scrollBox.setObjectName("scrollArea")

        self.actuator1 = QDial(self)
        self.actuator1.setGeometry(QRect(70, 280, 50, 64))
        self.actuator1.setObjectName("qDial")

        self.actuator2 = QDial(self)
        self.actuator2.setGeometry(QRect(130, 240, 50, 64))
        self.actuator2.setObjectName("qDial")

        self.actuator3 = QDial(self)
        self.actuator3.setGeometry(QRect(190, 280, 50, 64))
        self.actuator3.setObjectName("qDial")
        # Function that will execute when the button is clicked
    def estop_pressed(self):
        print('Stop')

    def home_pressed(self):
        print('Home')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = widget()
    widget.show()
    sys.exit(app.exec_())
