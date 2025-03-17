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
        self.record_start_time = None
        self.record_file_path = None
        self.record_thread = None
        self._record_lock = threading.Lock()

    def _sweep_loop(self):
        while self._running:
            try:
                data = self.sa.data(0)
                logging.debug(f"Sweep data acquired: {data[:5]}...")  # log first 5 data points
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

    def start_recording(self, record_duration=None, dest_folder="tinySA_data"):
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
            logging.debug(f"Created folder: {dest_folder}")
        timestamp = time.strftime("%H%M")
        file_name = f"sweep_{timestamp}.csv"
        self.record_file_path = os.path.join(dest_folder, file_name)
        
        data = self.get_latest_data()
        num_points = len(data) if data is not None else self.sa.points
        # Use SA frequencies for header labels.
        freqs = [f"{int(f)}" for f in self.sa.frequencies]
        header = "time," + ",".join(freqs) + "\n"
        with open(self.record_file_path, "w") as f:
            f.write(header)
        logging.info(f"Recording started: {self.record_file_path}")
        
        self.recording = True
        self.record_start_time = time.time()
        self.record_thread = threading.Thread(target=self._record_loop, args=(record_duration,), daemon=True)
        self.record_thread.start()

    def _record_loop(self, record_duration):
        while self.recording:
            t = time.time() - self.record_start_time
            data = self.get_latest_data()
            if data is not None:
                row = f"{t:.2f}," + ",".join(f"{d:.2f}" for d in data) + "\n"
                with self._record_lock:
                    with open(self.record_file_path, "a") as f:
                        f.write(row)
                logging.debug(f"Recorded row at {t:.2f} sec")
            if record_duration is not None and t >= record_duration:
                self.recording = False
                logging.info("Recording duration reached. Stopping recording.")
                break
            time.sleep(1)

    def stop_recording(self):
        self.recording = False
        if self.record_thread is not None:
            self.record_thread.join(timeout=5)
        logging.info("Recording stopped.")
