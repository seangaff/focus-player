import time

class Session:
    def __init__(self):
        self.start_time = time.time()
        self.total_chars = 0
        self.current_wpm = 0
        self.max_wpm = 0
        self.breaks_taken = 0
        self.last_activity_time = time.time()
        self.is_active = False

    def update(self, wpm, char_count):
        self.current_wpm = wpm
        if wpm > self.max_wpm:
            self.max_wpm = wpm
        
        # This is a bit simplified, total_chars should probably be cumulative
        # But Monitor gives us windowed chars. 
        # Let's trust Monitor for instantaneous, but we might need to track total separately if we want session total.
        # For now, let's just store what Monitor gives us for display.
        
        current_time = time.time()
        if char_count > 0:
            self.last_activity_time = current_time
            self.is_active = True
        else:
            # If no activity for 5 seconds, consider it a break or idle
            if current_time - self.last_activity_time > 5:
                self.is_active = False

    def get_stats(self):
        elapsed = time.time() - self.start_time
        return {
            "elapsed": elapsed,
            "current_wpm": self.current_wpm,
            "max_wpm": self.max_wpm,
            "is_active": self.is_active
        }
