from pynput import keyboard
import time
import threading
from collections import deque
from just_playback import Playback
from tqdm import tqdm


class Monitor:
    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.keystrokes = deque()
        self.print_interval = 1
        self.running = True

        self.playback = Playback()
        self.playback.load_file("/Users/seangaffney/Music/vibes/Smolder (Synthwave - Retrowave - Electronic Mix) [OvYeYtujzjQ].mp3")
        self.playback.play()
        self.playback.loop_at_end(True)
        # self.pbar = tqdm(total=self.playback.duration)


    def on_press(self, key):
        # try:
        #     print('alphanumeric key {0} pressed'.format(
        #         key.char))
        # except AttributeError:
        #     print('special key {0} pressed'.format(
        #         key))
        #     if key == keyboard.Key.esc:
        #         raise SystemExit
        current_time = time.time()
        self.keystrokes.append(current_time)

    def on_release(self, key):
        if key == keyboard.Key.esc:
            self.running = False
            return False

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
            # time_elapsed = self.window_seconds
            wpm = (words / time_elapsed) * 60
        else:
            wpm = 0
            time_elapsed = 0
        return wpm, char_count, time_elapsed

    def print_loop(self):
        while self.running:
            wpm, chars, elapsed = self.calculate_wpm()
            volume = min(max(wpm / 100, 0), 1)  # Normalize WPM to [0, 1] range
            
            # print(f"\r \n\n", end='', flush=True)
            # self.pbar.update(self.playback.curr_pos)
            print(f"\rCurrent WPM: {wpm:.1f} | Characters: {chars} | Window: {elapsed:.1f}s | Volume: {volume:.2f}", end='', flush=True)


            # Slow down music start
            # calculate fade-in factor based on WPM
            # calculate average WPM over the last 20 seconds
            # longer range allows for smoother transitions
            # try different time windows for averaging

            if self.playback.active:
                self.playback.set_volume(volume)

            time.sleep(self.print_interval)
    
    def start(self):
        print(f"WPM Monitor started: measuring over {self.window_seconds}s window. \n PRess ECS to stop \n")

        print_thread = threading.Thread(target=self.print_loop, daemon=True)
        print_thread.start()

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


if __name__ == "__main__":
    monitor = Monitor(window_seconds=15)
    monitor.start()
# playback = Playback()
# playback.load_file("/Users/seangaffney/Music/tunes/Let's Begin [ne7d4T3LQMU].mp3")
# playback.play()
# print(playback.duration)
# while playback.active:
#     print(playback.curr_pos)
#     time.sleep(1)