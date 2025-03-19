import threading
import time
import os
import numpy as np
from spectrum_analyzer import tinySA
import logging

logging.basicConfig(level=logging.DEBUG)

class DataService:
    def __init__(self):
        self.sa = tinySA()
        self.latest_data = None
        self._running = False
        self._lock = threading.Lock()
        
        self.recording = False
        self.record_file_path = None
        self.record_thread = None
        self._record_lock = threading.Lock()

    # Continuous sweep acquisition
    def _sweep_loop(self):
        while self._running:
            try:
                data = self.sa.data(0)
                logging.debug(f"Sweep data acquired: {data[:5]}...")
            except Exception as e:
                logging.error(f"Error during sweep: {e}")
                data = None
            with self._lock:
                self.latest_data = data
            time.sleep(1)

    def start_sweep(self):
        if not self._running:
            self._running = True
            threading.Thread(target=self._sweep_loop, daemon=True).start()
            logging.info("Sweep started.")

    def pause_sweep(self):
        self._running = False
        logging.info("Sweep paused.")

    def get_latest_data(self):
        with self._lock:
            return self.latest_data

    # Recording functionality with configurable interval and duration
    def start_recording(self, record_duration=None, dest_folder="tinySA_data", record_interval=1.0, freq_range=None):
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
            logging.debug(f"Created folder: {dest_folder}")
        timestamp = time.strftime("%H%M")
        file_name = f"sweep_{timestamp}.csv"
        self.record_file_path = os.path.join(dest_folder, file_name)
        
        data = self.get_latest_data()
        if data is not None:
            num_points = len(data)
        else:
            num_points = self.sa.points
        
        if freq_range is not None:
            start_freq, stop_freq = freq_range
            freqs = [f"{int(f)}" for f in np.linspace(start_freq, stop_freq, num_points)]
        else:
            freqs = [f"{int(f)}" for f in self.sa.frequencies[:num_points]]
        
        # Write metadata as a comment in the CSV header.
        header = ""
        if freq_range is not None:
            header += f"# Frequency Range: {freq_range[0]} Hz to {freq_range[1]} Hz\n"
        header += "time," + ",".join(freqs) + "\n"
        
        with open(self.record_file_path, "w") as f:
            f.write(header)
        logging.info(f"Recording started: {self.record_file_path}")
        
        self.recording = True
        self.record_thread = threading.Thread(target=self._record_loop, args=(record_duration, record_interval), daemon=True)
        self.record_thread.start()

    def _record_loop(self, record_duration, record_interval):
        counter = 0
        while self.recording:
            t = counter * record_interval  # fixed timestamp based on counter and interval
            # Force a fresh capture for each record
            data = self.sa.data(0)
            with self._lock:
                self.latest_data = data
            if data is not None:
                row = f"{t:.1f}," + ",".join(f"{d:.2f}" for d in data) + "\n"
                with self._record_lock:
                    with open(self.record_file_path, "a") as f:
                        f.write(row)
                logging.debug(f"Recorded row at t={t:.1f} sec")
            counter += 1
            if record_duration is not None and t >= record_duration:
                self.recording = False
                logging.info("Recording duration reached. Stopping recording.")
                break
            time.sleep(record_interval)

    def stop_recording(self):
        self.recording = False
        if self.record_thread is not None:
            self.record_thread.join(timeout=5)
        logging.info("Recording stopped.")

    # --- Additional instrument commands from the manufacturer ---

    def set_sweep(self, start, stop):
        self.sa.set_sweep(start, stop)

    def set_span(self, span):
        self.sa.set_span(span)

    def set_center(self, center):
        self.sa.set_center(center)

    def set_level(self, level):
        self.sa.set_level(level)

    def set_output(self, on):
        self.sa.set_output(on)

    def set_low_output(self):
        self.sa.set_low_output()

    def set_low_input(self):
        self.sa.set_low_input()

    def set_high_input(self):
        self.sa.set_high_input()

    def set_frequency(self, freq):
        self.sa.set_frequency(freq)

    def measure(self, freq):
        return self.sa.measure(freq)

    def temperature(self):
        return self.sa.temperature()

    def rbw(self, value=0):
        self.sa.rbw(value)

    def resume(self):
        self.sa.resume()

    def pause(self):
        self.sa.pause()

    def marker_value(self, nr=1):
        return self.sa.marker_value(nr)

    def fetch_frequencies(self):
        self.sa.fetch_frequencies()
        return self.sa.frequencies

    def send_scan(self, start, stop, points=None):
        self.sa.send_scan(start, stop, points)

    def scan(self):
        return self.sa.scan()

    def capture(self):
        return self.sa.capture()

    def logmag(self, x):
        self.sa.logmag(x)

    def writeCSV(self, x, name):
        self.sa.writeCSV(x, name)

    def cmd(self, text):
        return self.sa.cmd(text)
