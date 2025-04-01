import time
import threading
from PySide6.QtCore import QRect, Qt, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QScrollArea, QSlider, QGraphicsView, QVBoxLayout, QGraphicsScene, QGraphicsTextItem
from PySide6.QtGui import QPixmap, QKeyEvent, QFont
import sys
from readCSV import saveFileAsArr
from talkToArduino import ArdiunoTalk

class Widget(QWidget):

    #Defining widget
    def __init__(self):
        super().__init__()
        self.eStop = None
        self.stop_loop = None
        self.actuator1 = 0
        self.actuator2 = 0
        self.enabled = False
        self.setupUi()
        self.arduinoTalker = ArdiunoTalk()




    #Setup UI
    def setupUi(self):
        self.setFixedSize(800, 600)
        self.setWindowTitle("Motion Simulator User Interface")

        self.image = QGraphicsView(self)
        self.image.setGeometry(QRect(0, 0, 800, 600))
        self.image.setObjectName("qGraphicsView")
        self.image.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scene = QGraphicsScene()
        self.image.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 800, 600)

        pixmap = QPixmap("TPED-logo-cropped.png").scaled(300, 300)
        item = self.scene.addPixmap(pixmap)
        item.setPos(-50, -60)

        self.image.setFrameShape(QGraphicsView.NoFrame)
        self.image.setScene(self.scene)

        text_item = QGraphicsTextItem("Motion Simulator Design Team")
        text_item.setDefaultTextColor(Qt.white)
        text_item.setFont(QFont("Anton", 30))
        text_item.setPos(200, 60)
        self.scene.addItem(text_item)

        stylesheet = """
        QWidget {
            background-image: url('background - resized.png');
            background-repeat: no-repeat;
            background-position: center;
        }
        QPushButton {
                background-color: #3853a4; 
                color: white;              
                border: 3px solid orange;     
                border-radius: 10px;        
                padding: 8px;               
                font-size: 16px;            
            }

        QPushButton:hover {
            background-color: #4f6cc2; 
        }

        QPushButton:pressed {
            background-color: #2a3b80;
        }
        QCheckBox {
            background-color: #3853a4; 
            color: white;              
            border: 3px solid orange;     
            padding: 5px; 
            border-radius: 10px;        
            padding: 8px;               
            font-size: 16px;                 
        }

        QCheckBox::indicator {
            width: 20px;                                 
            height: 20px;
            border: 2px solid white;      
            background-color: white;      
        }

        QCheckBox::indicator:checked {
            background-color: #ffa500;    
            border: 2px solid white;
        }
        QSlider::groove:horizontal {
            border: 2px solid white;    
            height: 8px;                
            background: #3853a4;        
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: transparent;
            image: url('Gear Image.PNG');  
            width: 32px;   
            height: 32px;
            margin: -12px 0; 
        }

        QSlider::sub-page:horizontal {
            background: #ffa500;
            border-radius: 4px;
        }

        QSlider::add-page:horizontal {
            background: #4f6cc2; 
            border-radius: 4px;
        }
        """

        self.setStyleSheet(stylesheet)

        self.eStop = QPushButton(self)
        self.eStop.setGeometry(550, 390, 175, 75)
        self.eStop.setObjectName("pushButton")
        self.eStop.setText("E-Stop")
        self.eStop.clicked.connect(self.estop_pressed)

        self.home = QPushButton(self)
        self.home.setGeometry(QRect(550, 190, 175, 75))
        self.home.setObjectName("homeButton")
        self.home.setText("Return to Home")
        self.home.clicked.connect(self.home_pressed)

        self.enableAll = QCheckBox(self)
        self.enableAll.setGeometry(QRect(550, 290, 175, 75))
        self.enableAll.setObjectName("checkBox")
        self.enableAll.setText("Enable All Motors")
        self.enableAll.stateChanged.connect(self.toggle_enabled)

        self.add_label("Actuator Controls:", 60, 190, 15)

        self.add_label("Actuator 1 Angle:", 100, 230, 8)
        self.angle1 = QSlider(Qt.Horizontal, self)
        self.angle1.setGeometry(QRect(100, 250, 140, 50))
        self.angle1.setObjectName("horizontalSlider")
        self.angle1.valueChanged.connect(self.on_dial_rotate_actuator1)
        self.angle1.setMinimum(-45)
        self.angle1.setMaximum(45)

        self.add_label("Actuator 2 Angle:", 100, 305, 8)
        self.angle2 = QSlider(Qt.Horizontal, self)
        self.angle2.setGeometry(QRect(100, 325, 140, 50))
        self.angle2.setObjectName("horizontalSlider")
        self.angle2.valueChanged.connect(self.on_dial_rotate_actuator2)
        self.angle2.setMinimum(-45)
        self.angle2.setMaximum(45)

        self.add_label("Actuator 3 Angle:", 100, 380, 8)
        self.angle3 = QSlider(Qt.Horizontal, self)
        self.angle3.setGeometry(QRect(100, 400, 140, 50))
        self.angle3.setObjectName("horizontalSlider")
        self.angle3.valueChanged.connect(self.on_dial_rotate_actuator3)
        self.angle3.setMinimum(0)
        self.angle3.setMaximum(180)

        self.add_label("Sequences:", 300, 190, 15)
        self.setup_scrollbox()

    def add_label(self, text, x, y, font_size, color=Qt.white):
        item = QGraphicsTextItem(text)
        item.setDefaultTextColor(color)
        item.setFont(QFont("Anton", font_size))
        item.setPos(x, y)
        self.scene.addItem(item)
        return item

    #Set up presets
    def setup_scrollbox(self):
        self.scrollBox = QScrollArea(self)
        self.scrollBox.setGeometry(QRect(300, 230, 200, 200))
        self.scrollBox.setObjectName("scrollArea")
        self.scrollBox.setStyleSheet("""
        QScrollArea {
            border: 3px solid orange;
            border-radius: 8px;
        }
        QScrollBar::vertical {
            background-color: #3853a4;
            color: white;
            border: 3px solid orange;
            border-radius: 10px;
            padding: 8px;
        }
        """)

        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollLayout.setContentsMargins(35, 10, 10, 10)

        self.name_buttons = []
        for name in ['Sequence 1', 'Sequence 2', 'Sequence 3', 'Sequence 4']:
                button = QPushButton(name)
                button.setMinimumHeight(35)
                button.setMinimumWidth(125)
                button.setStyleSheet("""
                QPushButton {
                    background-color: #3853a4; 
                    color: white;              
                    border: 3px solid orange;     
                    border-radius: 10px;        
                    padding: 8px;               
                    font-size: 12px;
                    text-align: center;           
                }

                QPushButton:hover {
                    background-color: #4f6cc2; 
                }

                QPushButton:pressed {
                    background-color: #2a3b80;
                }
                """)
                button.clicked.connect(lambda checked, n=name: self.on_name_clicked(n))  # Connect button click to function
                self.scrollLayout.addWidget(button)
                self.name_buttons.append(button)
        self.scrollBox.setWidget(self.scrollWidget)

    # estop button
    def estop_pressed(self):
        t = threading.Thread(target=self.stop_execution)
        t.start()

    # estop method
    def stop_execution(self):
        print('Stop')
        self.stop_loop = True
        if self.enabled:
            self.enableAll.setChecked(False)
    # preset buttons
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

    # disabling name buttons
    def disable_name_buttons(self):
        for button in self.name_buttons:
            button.setEnabled(False)
        print("Name buttons disabled")
    # enabling name buttons
    def enable_name_buttons(self):
        for button in self.name_buttons:
            button.setEnabled(True)
        print("Name buttons enabled")

    # Sets to origin
    def home_pressed(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        print('Home')
        self.angle1.setValue(0)
        self.angle2.setValue(0)
        self.angle3.setValue(0)
    # rotating actuator 1
    def on_dial_rotate_actuator1(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        self.arduinoTalker.send_all_angles(self.angle1.value(), self.angle2.value(), self.angle3.value())
        print(f"Dial rotated to: {self.angle1.value()}")

    # rotating actuator 2
    def on_dial_rotate_actuator2(self):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        self.arduinoTalker.send_all_angles(self.angle1.value(), self.angle2.value(), self.angle3.value())
        print(f"Dial rotated to: {self.angle2.value()}")

    # rotating actuator 3
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
