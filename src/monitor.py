import time
from collections import deque
from pynput import keyboard
import threading
from session import Session

class Monitor:
    def __init__(self,session):
        self.session = session
        self.window_seconds = session.config["monitor"]["window_seconds"]
        self.keys_ignored = session.config["monitor"]["keys_ignored"]
        self.keystrokes = deque()
        self.running = False
        self.listener = None
        self.callbacks = []

        self.start()

    def add_callback(self, callback):
        """Add a callback function to be called on key press."""
        self.callbacks.append(callback)

    def on_press(self, key):
        current_time = time.time()
        # Ignore keys in keys_ignored
        if str(key) in self.keys_ignored:
            return
        self.keystrokes.append(current_time)
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(key)
            except Exception as e:
                print(f"Error in callback: {e}")

    def on_release(self, key):
        if key == keyboard.Key.esc:
            # We don't stop here, let the main loop handle stop
            pass

    def calculate_wpm(self):
        current_time = time.time()

        # remove keystrokes from outside the time window
        cutoff_time = current_time - self.window_seconds
        while self.keystrokes and self.keystrokes[0] < cutoff_time:
            self.keystrokes.popleft()

        char_count = len(self.keystrokes)
        words = char_count / 5

        if self.keystrokes:
            time_elapsed = min(current_time - self.keystrokes[0], self.window_seconds)
            # Avoid division by zero and enforce a minimum window for smoothing
            # We use 5.0s so that WPM ramps up linearly over the first 5 seconds
            effective_time = max(time_elapsed, 5.0)
            wpm = (words / effective_time) * 60
        else:
            wpm = 0
            time_elapsed = 0
            
        return wpm, char_count, time_elapsed

    def tick(self):
        wpm, char_count, _ = self.calculate_wpm()
        self.session.update(wpm, char_count)

    def start(self):
        self.running = True
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        print(f"Monitor started. Window: {self.window_seconds}s")

    def stop(self):
        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None

if __name__ == "__main__":
    session = Session("../sampleConfig.toml")
    monitor = Monitor(session)
    monitor.start()
    time.sleep(100)
    monitor.stop()
