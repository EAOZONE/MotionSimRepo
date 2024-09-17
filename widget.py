from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
import sys

class widget(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setGeometry(QRect(0, 0, 800, 600))
        self.setWindowTitle("Widget")

        self.pushButton = QPushButton(self)
        self.pushButton.setGeometry(QRect(310, 400, 171, 71))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("E-Stop")

        # Connect the pushButton to a function on click
        self.pushButton.clicked.connect(self.estop_pressed)

    # Function that will execute when the button is clicked
    def estop_pressed(self):
        print('Stop')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = widget()
    widget.show()
    sys.exit(app.exec_())
