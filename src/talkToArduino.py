import math
import platform
import time
import serial
import serial.tools.list_ports
from serial.serialutil import SerialException

class ArdiunoTalk():
    def __init__(self):
        self.arduino_port_name = None  # Store the name of the Arduino port
        self.arduino = None  # The actual serial connection
        self.enabled = False
        self.arduino_port_name = "COM6"
        if self.arduino_port_name:
            try:
                self.arduino = serial.Serial(port=self.arduino_port_name, timeout=1)
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
    def calculateLength(self, angle1, angle2):
        A = 0.1
        B = 0.1
        actuator1 = 180*(A*math.tan(angle1*math.pi/180)+B*math.tan(angle2*math.pi/180))
        actuator2 = 180*(A*math.tan(angle1*math.pi/180)-B*math.tan(angle2*math.pi/180))
        return actuator1, actuator2
    def send_all_angles(self, angle1, angle2, angle3):
        # if not self.enabled:
        #     print("Action blocked: System is not enabled.")
        #     return
        actuator1, actuator2 = self.calculateLength(angle1, angle2)
        command = f"{int(actuator1)},{int(actuator2)},{angle3}"
        print(command)
        if self.arduino:
            self.arduino.flush()
            self.arduino.write(str(command).encode())
            while True:
                raw = self.arduino.readline()  # this is a bytes object
                print(raw)
                self.arduino.flush()
                if not raw:
                    continue  # timeout, try again
                if raw == b"DONE\r\n":  # compare against bytes
                    break

        else:
            print("Arduino not connected")
    def setEnable(self, enable):
        self.enabled = enable