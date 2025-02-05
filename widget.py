import time
import threading
from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QSlider, QGraphicsView, QVBoxLayout, QGraphicsScene
from PySide6.QtGui import QPixmap, QKeyEvent
import sys
from readCSV import saveFileAsArr
from talkToArduino import ArdiunoTalk

class Widget(QWidget):

    def __init__(self):
        self.stop_loop = None
        self.actuator1 = 0
        self.actuator2 = 0
        self.enabled = False
        super().__init__()
        self.setupUi()
        self.arduinoTalker = ArdiunoTalk()

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

        self.angle1 = QSlider(Qt.Horizontal, self)
        self.angle1.setGeometry(QRect(100, 280, 64, 50))
        self.angle1.setObjectName("horizontalSlider")
        self.angle1.valueChanged.connect(self.on_dial_rotate_actuator1)
        self.angle1.setMinimum(-45)
        self.angle1.setMaximum(45)

        self.angle2 = QSlider(Qt.Horizontal, self)
        self.angle2.setGeometry(QRect(160, 240, 64, 50))
        self.angle2.setObjectName("horizontalSlider")
        self.angle2.valueChanged.connect(self.on_dial_rotate_actuator2)
        self.angle2.setMinimum(-45)
        self.angle2.setMaximum(45)

        self.angle3 = QSlider(Qt.Horizontal, self)
        self.angle3.setGeometry(QRect(220, 280, 64, 50))
        self.angle3.setObjectName("horizontalSlider")
        self.angle3.valueChanged.connect(self.on_dial_rotate_actuator3)
        self.angle3.setMinimum(0)
        self.angle3.setMaximum(180)

        self.image = QGraphicsView(self)
        self.image.setGeometry(QRect(300,210,192,192))
        self.image.setObjectName("qGrpahicsView")

        self.scene = QGraphicsScene()
        pixmap = QPixmap("TPED-logo.jpg")
        pixmap = pixmap.scaled(186, 186)

        self.scene.addPixmap(pixmap)
        self.image.setScene(self.scene)
        self.setup_scrollbox()

    def setup_scrollbox(self):
        self.scrollBox = QScrollArea(self)
        self.scrollBox.setGeometry(QRect(530, 210, 171, 191))
        self.scrollBox.setObjectName("scrollArea")
        self.scrollBox.setStyleSheet("background-color: white; color: black;")

        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.name_buttons = []
        for name in ['Name1', 'Name2', 'Name3', 'Name4']:  # Replace with your names
                button = QPushButton(name)
                button.clicked.connect(lambda checked, n=name: self.on_name_clicked(n))  # Connect button click to function
                self.scrollLayout.addWidget(button)
                self.name_buttons.append(button)
        self.scrollBox.setWidget(self.scrollWidget)

    def estop_pressed(self):
        t = threading.Thread(target=self.stop_execution)
        t.start()

    def stop_execution(self):
        print('Stop')
        self.stop_loop = True
        if self.enabled:
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
        for button in self.name_buttons:
            button.setEnabled(False)
        print("Name buttons disabled")

    def enable_name_buttons(self):
        for button in self.name_buttons:
            button.setEnabled(True)
        print("Name buttons enabled")

    def home_pressed(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print('Home')
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
            # Check if spacebar is pressed
            if event.key() == Qt.Key_Space:
                self.estop_pressed()  # Call the E-Stop function
            else:
                super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())
