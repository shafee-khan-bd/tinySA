import threading
import time
import os
import numpy as np
from spectrum_analyzer import tinySA

class DataService:
    def __init__(self):
        self.sa = tinySA()  # Instantiate the spectrum analyzer
        self.latest_data = None
        self._running = False
        self._lock = threading.Lock()
        
        # Recording state
        self.recording = False
        self.record_start_time = None
        self.record_file_path = None
        self.record_thread = None
        self._record_lock = threading.Lock()

    def _sweep_loop(self):
        while self._running:
            try:
                data = self.sa.data(0)  # Acquire current sweep data
            except Exception as e:
                print("Error during sweep:", e)
                data = None

            with self._lock:
                self.latest_data = data

            time.sleep(1)

    def start_sweep(self):
        if not self._running:
            self._running = True
            threading.Thread(target=self._sweep_loop, daemon=True).start()

    def pause_sweep(self):
        self._running = False

    def get_latest_data(self):
        with self._lock:
            return self.latest_data

    def save_data(self, filename):
        data = self.get_latest_data()
        if data is not None:
            try:
                with open(filename, "w") as f:
                    for i, d in enumerate(data):
                        f.write(f"{i},{d}\n")
                return True
            except Exception as e:
                print("Error saving data:", e)
        return False

    # ----------- Recording Functionality -----------
    def start_recording(self, record_duration=None, dest_folder="tinySA_data"):
        # Create destination folder if it doesn't exist
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        # Create unique file name with current hour & minute
        timestamp = time.strftime("%H%M")
        file_name = f"sweep_{timestamp}.csv"
        self.record_file_path = os.path.join(dest_folder, file_name)
        
        # Write header row: "time, f0, f1, ..., fN"
        # Use the latest data length if available, otherwise a default (e.g., 101)
        data = self.get_latest_data()
        num_points = len(data) if data is not None else 101
        freqs = [f"{int(f)}" for f in np.linspace(50e3, 3e6, num_points)]
        header = "time," + ",".join(freqs) + "\n"
        with open(self.record_file_path, "w") as f:
            f.write(header)
        
        self.recording = True
        self.record_start_time = time.time()
        self.record_thread = threading.Thread(target=self._record_loop, args=(record_duration,), daemon=True)
        self.record_thread.start()

    def _record_loop(self, record_duration):
        while self.recording:
            t = time.time() - self.record_start_time  # relative time (seconds)
            data = self.get_latest_data()
            if data is not None:
                row = f"{t:.2f}," + ",".join(f"{d:.2f}" for d in data) + "\n"
                with self._record_lock:
                    with open(self.record_file_path, "a") as f:
                        f.write(row)
            # If a record duration was set, stop when reached
            if record_duration is not None and t >= record_duration:
                self.recording = False
                break
            time.sleep(1)

    def stop_recording(self):
        self.recording = False
        if self.record_thread is not None:
            self.record_thread.join(timeout=5)
