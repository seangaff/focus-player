import time


class PomodoroTimer:
    def __init__(self, session):
        self.session = session
        pomodoro = self.session.config["pomodoro"]
        self.work_seconds = pomodoro["work_interval"] * 60
        self.break_seconds = pomodoro["break_interval"] * 60
        self.alert_on_complete = pomodoro.get("alert_on_complete", True)

        self.state = "Work"  # "Work", "Break"
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
        if work_mins is not None and work_mins > 0:
            self.work_seconds = int(work_mins * 60)
            if self.state == "Work" and not self.is_running:
                self.remaining_seconds = self.work_seconds

        if break_mins is not None and break_mins > 0:
            self.break_seconds = int(break_mins * 60)
            if self.state == "Break" and not self.is_running:
                self.remaining_seconds = self.break_seconds

    def tick(self, now=None) -> bool:
        """Advance the clock. Returns True when an interval finishes."""
        if not self.is_running:
            return False

        current_time = time.time() if now is None else now
        if self.last_tick_time is None:
            self.last_tick_time = current_time
            return False

        delta = current_time - self.last_tick_time
        if delta < 1.0:
            return False

        seconds_passed = int(delta)
        self.remaining_seconds = max(0, self.remaining_seconds - seconds_passed)
        self.last_tick_time += seconds_passed

        if self.remaining_seconds == 0:
            return self._advance_interval(current_time)
        return False

    def _advance_interval(self, now) -> bool:
        if self.state == "Work":
            self.session.completed_sessions += 1
            self.state = "Break"
            self.remaining_seconds = self.break_seconds
        else:
            self.session.completed_breaks += 1
            self.state = "Work"
            self.remaining_seconds = self.work_seconds
        # Keep the cycle going; the user can pause if they want to stop.
        self.is_running = True
        self.last_tick_time = now
        return True

    def get_time_display(self):
        mins = int(self.remaining_seconds // 60)
        secs = int(self.remaining_seconds % 60)
        return f"{self.state} {mins:02d}:{secs:02d}"
