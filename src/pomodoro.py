import time

class PomodoroTimer:
    def __init__(self, session):
        self.session = session
        self.work_seconds = self.session.config["pomodoro"]["work_interval"] * 60
        self.break_seconds = self.session.config["pomodoro"]["break_interval"] * 60
        
        self.state = "Work" # "Work", "Break"
        self.remaining_seconds = self.work_seconds
        self.is_running = False
        self.last_tick_time = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.last_tick_time = time.time()

    def pause(self):
        self.is_running = False
        self.last_tick_time = None

    def reset(self):
        self.is_running = False
        self.last_tick_time = None
        if self.state == "Work":
            self.remaining_seconds = self.work_seconds
        else:
            self.remaining_seconds = self.break_seconds

    def toggle_mode(self):
        self.reset()
        if self.state == "Work":
            self.state = "Break"
            self.remaining_seconds = self.break_seconds
        else:
            self.state = "Work"
            self.remaining_seconds = self.work_seconds

    def set_duration(self, work_mins=None, break_mins=None):
        if work_mins is not None:
            self.work_seconds = int(work_mins * 60)
            if self.state == "Work" and not self.is_running:
                self.remaining_seconds = self.work_seconds
                
        if break_mins is not None:
            self.break_seconds = int(break_mins * 60)
            if self.state == "Break" and not self.is_running:
                self.remaining_seconds = self.break_seconds

    def tick(self):
        if not self.is_running:
            return
            
        current_time = time.time()
        if self.last_tick_time:
            delta = current_time - self.last_tick_time
            if delta >= 1.0:
                # Decrement by whole seconds passed
                seconds_passed = int(delta)
                self.remaining_seconds = max(0, self.remaining_seconds - seconds_passed)
                self.last_tick_time += seconds_passed # Keep precision
                
                if self.remaining_seconds == 0:
                    self.is_running = False
                    self.last_tick_time = None
        else:
            self.last_tick_time = current_time

    def get_time_display(self):
        mins = int(self.remaining_seconds // 60)
        secs = int(self.remaining_seconds % 60)
        return f"{mins:02d}:{secs:02d}"
