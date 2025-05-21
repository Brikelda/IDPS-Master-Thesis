# state_collector.py
import time
import threading
from collections import deque

class StateCollector:
    def __init__(self, max_buffer_size=30):
        # Stores the most recent system states
        self.state_buffer = deque(maxlen=max_buffer_size)  # Each item: (timestamp, state_dict)
        self.lock = threading.Lock()

    def update_state(self, state_dict):
        with self.lock:
            self.state_buffer.append((time.time(), state_dict))

    def collect(self):
        with self.lock:
            if not self.state_buffer:
                return None
            return self.state_buffer[-1][1]  # Latest state

    def collect_latest_timestamp(self):
        with self.lock:
            if not self.state_buffer:
                return None
            return self.state_buffer[-1][0]

    def check_stability(self, tolerance=0.05):
        with self.lock:
            if len(self.state_buffer) < 2:
                return False
            # Compare last two snapshots
            _, latest = self.state_buffer[-1]
            _, previous = self.state_buffer[-2]
            deviations = []
            for key in latest:
                if key in previous and isinstance(latest[key], (int, float)):
                    prev_val = previous[key]
                    curr_val = latest[key]
                    if prev_val == 0:
                        continue
                    deviation = abs(curr_val - prev_val) / abs(prev_val)
                    deviations.append(deviation < tolerance)
            return all(deviations) if deviations else False
