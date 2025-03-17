import serial
import numpy as np
from serial.tools import list_ports
import logging

logging.basicConfig(level=logging.DEBUG)

VID = 0x0483
PID = 0x5740

def getport() -> str:
    device_list = list_ports.comports()
    for device in device_list:
        if device.vid == VID and device.pid == PID:
            return device.device
    raise OSError("Device not found")

class tinySA:
    def __init__(self, dev=None):
        self.dev = dev or getport()
        self.serial = None
        self.points = 101
        self._frequencies = np.linspace(1e6, 350e6, self.points)
    
    @property
    def frequencies(self):
        return self._frequencies

    def set_frequencies(self, start=1e6, stop=350e6, points=None):
        if points:
            self.points = points
        self._frequencies = np.linspace(start, stop, self.points)
        logging.debug(f"Frequencies set to range {start} - {stop} Hz with {self.points} points.")

    def open(self):
        if self.serial is None:
            self.serial = serial.Serial(self.dev)
            logging.debug(f"Opened serial port: {self.dev}")

    def close(self):
        if self.serial:
            self.serial.close()
            self.serial = None
            logging.debug("Closed serial port.")

    def send_command(self, cmd):
        self.open()
        self.serial.write(cmd.encode())
        self.serial.readline()  # discard empty line

    def fetch_data(self):
        result = ''
        line = ''
        while True:
            c = self.serial.read().decode('utf-8')
            if c == chr(13):
                continue
            line += c
            if c == chr(10):
                result += line
                line = ''
            if line.endswith('ch>'):
                break
        return result

    def data(self, array=2):
        self.send_command("data %d\r" % array)
        data_str = self.fetch_data()
        data = []
        for line in data_str.split('\n'):
            if line:
                try:
                    data.append(float(line))
                except ValueError as e:
                    logging.error(f"Conversion error for line: {line}, error: {e}")
        return np.array(data)

    def get_current_settings(self):
        """
        Query the spectrum analyzer for current settings.
        Assumes the SA returns settings as 'key: value' pairs.
        Modify parsing as needed for your device.
        """
        self.send_command("settings?\r")
        response = self.fetch_data()
        settings = {}
        for line in response.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                settings[key.strip()] = value.strip()
        logging.debug(f"Current SA settings: {settings}")
        return settings
