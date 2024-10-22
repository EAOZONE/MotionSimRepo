from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QSlider, QGraphicsView, QVBoxLayout, QGraphicsScene
from PySide6.QtGui import QPixmap, QKeyEvent
import serial
import serial.tools.list_ports  # Import this module to list available ports
import time
import sys
import platform

from serial.serialutil import SerialException


class widget(QWidget):
    def __init__(self):
        self.enabled = False
        super().__init__()
        self.setupUi()
        self.arduino_port_name = None  # Store the name of the Arduino port
        self.arduino = None  # The actual serial connection

        self.arduino_port_name = self.detect_arduino_port()
        if self.arduino_port_name:
            try:
                self.arduino = serial.Serial(port=self.arduino_port_name, baudrate=115200, timeout=.1)
                print(f"Connected to Arduino on Port: {self.arduino_port_name}")
            except SerialException as e:
                print(f"Failed to connect to Arduino: {e}")
                self.arduino = None
        else:
            print("No arduino port detected")


    def detect_arduino_port(self):
        system_platform = platform.system()
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if system_platform == "Windows" and "Arduino" in port.description:
                return port.device
            elif system_platform == "Darwin":
                if port.device.startswith("/dev/cu.usbmodem"):
                    return port.device
        return None

    def setupUi(self):
        self.setGeometry(QRect(0, 0, 800, 600))
        self.setWindowTitle("Widget")
        self.setStyleSheet("background-color: lightgray;")

        self.eStop = QPushButton(self)
        self.eStop.setGeometry(QRect(310, 400, 171, 100))
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
        self.enableAll.setGeometry(QRect(310, 500, 171, 71))
        self.enableAll.setObjectName("checkBox")
        self.enableAll.setText("Enable All")
        self.enableAll.stateChanged.connect(self.toggle_enabled)

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
        self.setup_scrollbox()

    def write_read(self, x):
        self.arduino.write(bytes(str(x), 'utf-8'))
        print(x)
        time.sleep(0.05)
        data = self.arduino.readline()
        return data

    def setup_scrollbox(self):
        self.scrollBox = QScrollArea(self)
        self.scrollBox.setGeometry(QRect(530, 210, 171, 191))
        self.scrollBox.setObjectName("scrollArea")
        self.scrollBox.setStyleSheet("background-color: white; color: black;")

        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)

        for name in ['Name1', 'Name2', 'Name3', 'Name4']:  # Replace with your names
                button = QPushButton(name)
                button.clicked.connect(lambda checked, n=name: self.on_name_clicked(n))  # Connect button click to function
                self.scrollLayout.addWidget(button)
        self.scrollBox.setWidget(self.scrollWidget)
    def estop_pressed(self):
        print('Stop')
        if self.enabled:
            self.enableAll.setChecked(False)
    def on_name_clicked(self, name):
        print(f"{name} clicked")
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
        #print(self.write_read("1"+str(self.actuator1.value())))
        print(f"Dial rotated to: {self.actuator1.value()}")
    def on_dial_rotate_actuator2(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        #print(self.write_read("2"+str(self.actuator2.value())))
        print(f"Dial rotated to: {self.actuator2.value()}")
    def on_dial_rotate_actuator3(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        #print(self.write_read("3"+str(self.actuator3.value())))
        print(f"Dial rotated to: {self.actuator3.value()}")
    def toggle_enabled(self):
        self.enabled = not self.enabled
        print(self.enabled)
    def keyPressEvent(self, event: QKeyEvent):
            # Check if spacebar is pressed
            if event.key() == Qt.Key_Space:
                self.estop_pressed()  # Call the E-Stop function
            else:
                super().keyPressEvent(event)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = widget()
    widget.show()
    sys.exit(app.exec_())
