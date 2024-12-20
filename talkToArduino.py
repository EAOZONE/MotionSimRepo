import math
import platform
import time
import serial
import serial.tools.list_ports
from serial.serialutil import SerialException
from readCSV import saveFileAsArr

class ArdiunoTalk():
    def __init__(self):
        self.arduino_port_name = None  # Store the name of the Arduino port
        self.arduino = None  # The actual serial connection
        self.enabled = False
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
    def write_read(self, x):
        self.arduino.write(bytes(str(x), 'utf-8'))
        print(x)
        time.sleep(0.05)
        data = self.arduino.readline()
        return data
    def calculateLength(self, angle1, angle2):
        A = 1
        B = 1
        actuator1 = 180*(A*math.tan(angle1.value()*math.pi/180)+B*math.tan(angle2.value()*math.pi/180))
        actuator2 = 180*(A*math.tan(angle1.value()*math.pi/180)-B*math.tan(angle2.value()*math.pi/180))
        return actuator1, actuator2
    def send_all_angles(self, angle1, angle2, angle3):
        if not self.enabled:
            print("Action blocked: System is not enabled.")
            return
        actuator1, actuator2 = self.calculateLength(angle1, angle2)
        command = f"A{actuator1},{actuator2},{angle3.value()}"
        if self.arduino:
            print(self.write_read(command))
        else:
            print("Arduino not connected")
    def runThroughFile(self, fileName):
        arr = saveFileAsArr(fileName)
        for i in range(len(arr)):
            self.send_all_angles(arr[i][0], arr[i][1], arr[i][2])
    def setEnable(self, enable):
        self.enabled = enable