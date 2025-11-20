import time
from collections import deque
from pynput import keyboard
import threading

class Monitor:
    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.keystrokes = deque()
        self.running = False
        self.listener = None
        self.callbacks = []

    def add_callback(self, callback):
        """Add a callback function to be called on key press."""
        self.callbacks.append(callback)

    def on_press(self, key):
        current_time = time.time()
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
            # Avoid division by zero
            if time_elapsed < 1:
                time_elapsed = 1
            wpm = (words / time_elapsed) * 60
        else:
            wpm = 0
            time_elapsed = 0
            
        return wpm, char_count, time_elapsed

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
