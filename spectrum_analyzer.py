#!/usr/bin/env python3
import serial
import numpy as np
import pylab as pl
import struct
from serial.tools import list_ports
import logging
from PIL import Image
import time

logging.basicConfig(level=logging.DEBUG)

# Vendor and Product IDs for tinySA
VID = 0x0483  # e.g., 1155 in decimal
PID = 0x5740  # e.g., 22336 in decimal

def getport() -> str:
    """
    Automatically detect and return the device port based on VID and PID.
    """
    device_list = list_ports.comports()
    for device in device_list:
        if device.vid == VID and device.pid == PID:
            logging.debug(f"Device found: {device.device}")
            return device.device
    raise OSError("Device not found")

REF_LEVEL = (1 << 9)

class tinySA:
    """
    Class for interfacing with the tinySA spectrum analyzer.
    """
    def __init__(self, dev=None):
        """
        Initialize the tinySA device.
        :param dev: Optional device port. If None, auto-detect.
        """
        self.dev = dev or getport()
        self.serial = None
        self.points = 101
        self._frequencies = np.linspace(1e6, 350e6, self.points)

    @property
    def frequencies(self):
        """
        Get the current frequency array.
        """
        return self._frequencies

    def set_frequencies(self, start=1e6, stop=350e6, points=None):
        """
        Set the frequency sweep parameters.
        :param start: Start frequency in Hz.
        :param stop: Stop frequency in Hz.
        :param points: Number of points (if provided, updates self.points).
        """
        if points:
            self.points = points
        self._frequencies = np.linspace(start, stop, self.points)
        logging.debug(f"Frequencies set to range {start} - {stop} Hz with {self.points} points.")

    def open(self):
        """
        Open the serial connection if it is not already open.
        """
        if self.serial is None:
            self.serial = serial.Serial(self.dev)
            logging.debug(f"Opened serial port: {self.dev}")

    def close(self):
        """
        Close the serial connection.
        """
        if self.serial:
            self.serial.close()
            self.serial = None
            logging.debug("Closed serial port.")

    def send_command(self, cmd):
        """
        Send a command string to the device.
        :param cmd: The command string to send.
        """
        self.open()
        self.serial.write(cmd.encode())
        self.serial.readline()  # discard empty line

    def cmd(self, text):
        """
        Send a raw command (with appended carriage return) and return the fetched data.
        :param text: Command text.
        :return: Response from device.
        """
        self.open()
        self.serial.write((text + "\r").encode())
        self.serial.readline()  # discard empty line
        data = self.fetch_data()
        return data

    def set_sweep(self, start, stop):
        """
        Set the sweep start and stop frequencies on the device.
        :param start: Start frequency in Hz.
        :param stop: Stop frequency in Hz.
        """
        if start is not None:
            self.send_command("sweep start %d\r" % start)
        if stop is not None:
            self.send_command("sweep stop %d\r" % stop)

    def set_span(self, span):
        """
        Set the sweep span.
        :param span: Span value in Hz.
        """
        if span is not None:
            self.send_command("sweep span %d\r" % span)

    def set_center(self, center):
        """
        Set the center frequency.
        :param center: Center frequency in Hz.
        """
        if center is not None:
            self.send_command("sweep center %d\r" % center)

    def set_level(self, level):
        """
        Set the reference level.
        :param level: Level in dBm.
        """
        if level is not None:
            self.send_command("level %d\r" % level)

    def set_output(self, on):
        """
        Enable or disable output.
        :param on: Boolean indicating output state.
        """
        if on is not None:
            if on:
                self.send_command("output on\r")
            else:
                self.send_command("output off\r")

    def set_low_output(self):
        """
        Set the device to low output mode.
        """
        self.send_command("mode low output\r")

    def set_low_input(self):
        """
        Set the device to low input mode.
        """
        self.send_command("mode low input\r")

    def set_high_input(self):
        """
        Set the device to high input mode.
        """
        self.send_command("mode high input\r")

    def set_frequency(self, freq):
        """
        Set the device to a specific frequency.
        :param freq: Frequency in Hz.
        """
        if freq is not None:
            self.send_command("freq %d\r" % freq)

    def measure(self, freq):
        """
        Measure at a specific frequency.
        :param freq: Frequency in Hz.
        :return: The measured value.
        """
        if freq is not None:
            self.send_command("hop %d 2\r" % freq)
            data = self.fetch_data()
            for line in data.split('\n'):
                if line:
                    return float(line)

    def temperature(self):
        """
        Read the device temperature.
        :return: Temperature reading.
        """
        self.send_command("k\r")
        data = self.fetch_data()
        for line in data.split('\n'):
            if line:
                return float(line)

    def rbw(self, data=0):
        """
        Set the resolution bandwidth (RBW).
        :param data: RBW value. If 0, auto mode is used.
        """
        if data == 0:
            self.send_command("rbw auto\r")
        elif data < 1:
            self.send_command("rbw %f\r" % data)
        else:
            self.send_command("rbw %d\r" % data)
        if self.serial is not None:
            time.sleep(0.1)
            self.serial.reset_input_buffer()
            
        
    def fetch_data(self):
        """
        Fetch raw data from the device until the prompt is reached.
        :return: The fetched data as a string.
        """
        result = ''
        line = ''
        while True:
            c = self.serial.read().decode('utf-8')
            if c == chr(13):
                continue  # ignore carriage return
            line += c
            if c == chr(10):
                result += line
                line = ''
            if line.endswith('ch>'):
                # stop on prompt
                break
        return result

    def marker_value(self, nr=1):
        """
        Set a marker on the device and return its value.
        :param nr: Marker number.
        :return: Marker value.
        """
        self.send_command("marker %d\r" % nr)
        data = self.fetch_data()
        line = data.split('\n')[0]
        if line:
            dl = line.strip().split(' ')
            if len(dl) >= 4:
                d = dl[3]
                return float(d)
        return 0

    def data(self, array=2):
        """
        Acquire sweep data.
        :param array: Data array selection.
        :return: NumPy array of sweep data.
        """
        self.send_command("data %d\r" % array)
        data = self.fetch_data()
        x = []
        for line in data.split('\n'):
            if line:
                try:
                    x.append(float(line))
                except Exception as e:
                    logging.error(f"Conversion error for line: {line}, error: {e}")
        return np.array(x)

    def fetch_frequencies(self):
        """
        Query the device for the frequency list.
        """
        self.send_command("frequencies\r")
        data = self.fetch_data()
        x = []
        for line in data.split('\n'):
            if line:
                try:
                    x.append(float(line))
                except Exception as e:
                    logging.error(f"Conversion error for frequency line: {line}, error: {e}")
        self._frequencies = np.array(x)

    def send_scan(self, start=1e6, stop=900e6, points=None):
        """
        Initiate a scan over a frequency range.
        :param start: Start frequency in Hz.
        :param stop: Stop frequency in Hz.
        :param points: Number of scan points.
        """
        if points:
            self.send_command("scan %d %d %d\r" % (start, stop, points))
        else:
            self.send_command("scan %d %d\r" % (start, stop))

    def scan(self):
        """
        Perform a complete scan by dividing the frequency range into segments.
        :return: A tuple of arrays (array0, array1) containing the scan data.
        """
        segment_length = 101
        array0 = []
        array1 = []
        if self._frequencies is None:
            self.fetch_frequencies()
        freqs = self._frequencies
        while len(freqs) > 0:
            seg_start = freqs[0]
            seg_stop = freqs[segment_length-1] if len(freqs) >= segment_length else freqs[-1]
            length = segment_length if len(freqs) >= segment_length else len(freqs)
            self.send_scan(seg_start, seg_stop, length)
            array0.extend(self.data(0))
            array1.extend(self.data(1))
            freqs = freqs[segment_length:]
        self.resume()
        return (array0, array1)
    
    def capture(self):
        """
        Capture an image of the current display.
        :return: PIL Image of the display.
        """
        self.send_command("capture\r")
        b = self.serial.read(320 * 240 * 2)
        x = struct.unpack(">76800H", b)
        # Convert pixel format from 565 (RGB) to 8888 (RGBA)
        arr = np.array(x, dtype=np.uint32)
        arr = 0xFF000000 + ((arr & 0xF800) >> 8) + ((arr & 0x07E0) << 5) + ((arr & 0x001F) << 19)
        return Image.frombuffer('RGBA', (320, 240), arr, 'raw', 'RGBA', 0, 1)

    def logmag(self, x):
        """
        Plot the log magnitude of the sweep data using pylab.
        :param x: Sweep data.
        """
        pl.grid(True)
        pl.xlim(self.frequencies[0], self.frequencies[-1])
        pl.plot(self.frequencies, x)
        
    def writeCSV(self, x, name):
        """
        Write sweep data to a CSV file.
        :param x: Sweep data.
        :param name: Output file name.
        """
        with open(name, "w") as f:
            for i in range(len(x)):
                print("%d, %2.2f" % (self.frequencies[i], x[i]), file=f)

    def resume(self):
        """
        Resume sweep after a pause.
        """
        self.send_command("resume\r")
	
    def pause(self):
        """
        Pause the sweep.
        """
        self.send_command("pause\r")
	
    def fetch_array(self, sel):
        """
        Fetch a complex data array from the device.
        :param sel: Array selection.
        :return: Complex NumPy array.
        """
        self.send_command("data %d\r" % sel)
        data = self.fetch_data()
        x = []
        for line in data.split('\n'):
            if line:
                try:
                    x.extend([float(d) for d in line.strip().split(' ')])
                except Exception as e:
                    logging.error(f"Error parsing complex data: {line} with error {e}")
        return np.array(x[0::2]) + np.array(x[1::2]) * 1j

    def fetch_gamma(self, freq=None):
        """
        Fetch the gamma value from the device.
        :param freq: Optional frequency in Hz to set before fetching.
        :return: Gamma as a complex number, normalized by REF_LEVEL.
        """
        if freq:
            self.set_frequency(freq)
        self.send_command("gamma\r")
        data = self.serial.readline()
        d = data.strip().split(b' ')
        try:
            real = int(d[0])
            imag = int(d[1])
            return (real + imag * 1j) / REF_LEVEL
        except Exception as e:
            logging.error(f"Error parsing gamma data: {data}, error: {e}")
            return None


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="%prog: [options]")
    parser.add_option("-p", "--plot", dest="plot",
                      action="store_true", default=False,
                      help="plot rectangular", metavar="PLOT")
    parser.add_option("-c", "--scan", dest="scan",
                      action="store_true", default=False,
                      help="scan by script", metavar="SCAN")
    parser.add_option("-S", "--start", dest="start",
                      type="float", default=1e6,
                      help="start frequency", metavar="START")
    parser.add_option("-E", "--stop", dest="stop",
                      type="float", default=900e6,
                      help="stop frequency", metavar="STOP")
    parser.add_option("-N", "--points", dest="points",
                      type="int", default=101,
                      help="scan points", metavar="POINTS")
    parser.add_option("-P", "--port", type="int", dest="port",
                      help="port", metavar="PORT")
    parser.add_option("-d", "--dev", dest="device",
                      help="device node", metavar="DEV")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="verbose output")
    parser.add_option("-C", "--capture", dest="capture",
                      help="capture current display to FILE", metavar="FILE")
    parser.add_option("-e", dest="command", action="append",
                      help="send raw command", metavar="COMMAND")
    parser.add_option("-o", dest="save",
                      help="write CSV file", metavar="SAVE")
    (opt, args) = parser.parse_args()

    nv = tinySA(opt.device or getport())

    if opt.command:
        print(opt.command)
        for c in opt.command:
            nv.send_command(c + "\r")
        data = nv.fetch_data()
        print(data)

    if opt.capture:
        print("capturing...")
        img = nv.capture()
        img.save(opt.capture)
        exit(0)

    if opt.start or opt.stop or opt.points:
        nv.set_frequencies(opt.start, opt.stop, opt.points)
    if opt.plot or opt.save or opt.scan:
        p = int(opt.port) if opt.port else 0
        if opt.scan or opt.points > 101:
            s = nv.scan()
            s = s[p]
        else:
            if opt.start or opt.stop:
                nv.set_sweep(opt.start, opt.stop)
            nv.fetch_frequencies()
            s = nv.data(p)
    if opt.save:
        nv.writeCSV(s, opt.save)
    if opt.plot:
        nv.logmag(s)
        pl.show()
