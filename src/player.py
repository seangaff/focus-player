import os
import random

from just_playback import Playback

from session import Session


def list_audio_files(folder: str) -> list[str]:
    """Return mp3/wav filenames in a folder. Missing folders yield an empty list."""
    try:
        names = os.listdir(folder)
    except FileNotFoundError:
        print(f"Music folder not found: {folder}")
        return []
    except NotADirectoryError:
        print(f"Music folder is not a directory: {folder}")
        return []
    except OSError as e:
        print(f"Could not read music folder {folder}: {e}")
        return []
    return [name for name in names if name.lower().endswith((".mp3", ".wav"))]


def reorder_playlist(playlist, index, shuffle, rng=None):
    """Reorder a playlist, keeping the current track loaded.

    Shuffle moves the current track to the front and shuffles the rest.
    Turning shuffle off sorts the list and points the index at the current track.
    """
    if not playlist:
        return [], 0
    index = min(max(index, 0), len(playlist) - 1)
    current = playlist[index]
    if shuffle:
        others = [track for i, track in enumerate(playlist) if i != index]
        (rng or random).shuffle(others)
        return [current, *others], 0
    ordered = sorted(playlist)
    return ordered, ordered.index(current)


def target_volumes(wpm, fg_min, fg_max, bg_min, bg_max):
    """Map typing speed to foreground and background volumes on a 0..1 scale.

    0 WPM is silence for music and full ambience. 100 WPM (and above) is full
    music and the ambience floor. Each channel is scaled inside its own range.
    """
    intensity = min(max(wpm / 100.0, 0.0), 1.0)
    foreground = fg_min + intensity * (fg_max - fg_min)
    background = bg_max - intensity * (bg_max - bg_min)
    return _clamp01(foreground), _clamp01(background)


def approach(current, target, step):
    if current < target:
        return min(current + step, target)
    if current > target:
        return max(current - step, target)
    return current


def _clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _unit_volume(percent) -> float:
    return _clamp01(float(percent) / 100.0)


class Player:
    def __init__(self, session):
        self.session = session

        self.foreground_playback = Playback()
        self.background_playback = Playback()
        self.alert_playback = Playback()

        configured_mode = self.session.config["player"].get("mode", "adaptive")
        if configured_mode != "adaptive":
            print(f"Player mode {configured_mode!r} is not implemented; using adaptive.")
        self.mode = "adaptive"

        foreground = self.session.config["player"]["foreground"]
        background = self.session.config["player"]["background"]

        self.fg_playlist = []
        self.fg_index = 0
        self.fg_shuffle = foreground.get("shuffle", False)
        self.fg_loop = foreground.get("loop", False)
        self.fg_is_playing = False
        self.fg_loaded = False

        self.bg_playlist = []
        self.bg_index = 0
        self.bg_shuffle = background.get("shuffle", False)
        self.bg_loop = background.get("loop", False)
        self.bg_is_playing = False
        self.bg_loaded = False
        self.alert_loaded = False

        self.fg_min = _unit_volume(foreground.get("min_volume", 0))
        self.fg_max = _unit_volume(foreground.get("max_volume", 100))
        if self.fg_min > self.fg_max:
            self.fg_min, self.fg_max = self.fg_max, self.fg_min

        self.bg_min = _unit_volume(background.get("min_volume", 0))
        self.bg_max = _unit_volume(background.get("max_volume", 80))
        if self.bg_min > self.bg_max:
            self.bg_min, self.bg_max = self.bg_max, self.bg_min

        self.smoothing_step = min(max(float(self.session.config["player"].get("smoothing_step", 0.05)), 0.001), 1.0)

        self.foreground_volume = self.fg_min
        self.target_foreground_volume = self.fg_min
        self.background_volume = self.bg_max
        self.target_background_volume = self.bg_max
        self.is_playing = False

        self.load_default_tracks()

    def play_alert(self):
        if not self.alert_loaded:
            return
        self.alert_playback.play()

    def build_playlist(self, folder, shuffle):
        playlist = list_audio_files(folder)
        if shuffle:
            random.shuffle(playlist)
        else:
            playlist.sort()
        return playlist

    def load_default_tracks(self):
        fg_cfg = self.session.config["player"]["foreground"]
        bg_cfg = self.session.config["player"]["background"]
        self.fg_folder = self.session.resolve_path(fg_cfg["folder"])
        self.bg_folder = self.session.resolve_path(bg_cfg["folder"])

        self.fg_playlist = self.build_playlist(self.fg_folder, self.fg_shuffle)
        default_fg = fg_cfg.get("default_song", "")
        if default_fg in self.fg_playlist:
            self.fg_index = self.fg_playlist.index(default_fg)
        else:
            self.fg_index = 0

        self.bg_playlist = self.build_playlist(self.bg_folder, self.bg_shuffle)
        default_bg = bg_cfg.get("default_song", "")
        if default_bg in self.bg_playlist:
            self.bg_index = self.bg_playlist.index(default_bg)
        else:
            self.bg_index = 0

        self.fg_loaded = False
        if self.fg_playlist:
            self.fg_loaded = self.load_track(
                self.foreground_playback,
                self.get_abs_path(self.fg_folder, self.fg_playlist[self.fg_index]),
            )
        self.bg_loaded = False
        if self.bg_playlist:
            self.bg_loaded = self.load_track(
                self.background_playback,
                self.get_abs_path(self.bg_folder, self.bg_playlist[self.bg_index]),
            )

        alert_path = self.session.resolve_path(self.session.config["player"]["alert_sound"])
        self.alert_loaded = self.load_track(self.alert_playback, alert_path)

    def get_abs_path(self, folder, filename):
        return os.path.join(folder, filename)

    def load_track(self, playback: Playback, path: str) -> bool:
        try:
            playback.load_file(path)
            return True
        except Exception as e:
            print(f"Error loading track: {e}")
            return False

    def play(self):
        if self.fg_loaded and not self.fg_is_playing:
            self.foreground_playback.play()
            self.fg_is_playing = True
        if self.bg_loaded and not self.bg_is_playing:
            self.background_playback.play()
            self.bg_is_playing = True
        self.update_volumes()

    def toggle_fg_play(self):
        self.fg_is_playing = self._toggle(self.foreground_playback, self.fg_loaded, self.fg_is_playing)

    def toggle_bg_play(self):
        self.bg_is_playing = self._toggle(self.background_playback, self.bg_loaded, self.bg_is_playing)

    def _toggle(self, playback, loaded, is_playing) -> bool:
        if not loaded:
            return False
        if is_playing:
            playback.pause()
            return False
        if playback.paused:
            playback.resume()
        else:
            playback.play()
        return True

    def set_fg_shuffle(self, enabled: bool) -> None:
        self.fg_shuffle = enabled
        self.fg_playlist, self.fg_index = reorder_playlist(self.fg_playlist, self.fg_index, enabled)

    def set_bg_shuffle(self, enabled: bool) -> None:
        self.bg_shuffle = enabled
        self.bg_playlist, self.bg_index = reorder_playlist(self.bg_playlist, self.bg_index, enabled)

    def fg_next(self):
        if not self.fg_playlist:
            return
        self.fg_index += 1
        if self.fg_index >= len(self.fg_playlist):
            if self.fg_loop:
                self.fg_index = 0
            else:
                self.fg_index = len(self.fg_playlist) - 1
                self.foreground_playback.stop()
                self.fg_is_playing = False
                return
        self._load_fg_current()

    def bg_next(self):
        if not self.bg_playlist:
            return
        self.bg_index += 1
        if self.bg_index >= len(self.bg_playlist):
            if self.bg_loop:
                self.bg_index = 0
            else:
                self.bg_index = len(self.bg_playlist) - 1
                self.background_playback.stop()
                self.bg_is_playing = False
                return
        self._load_bg_current()

    def fg_last(self):
        if not self.fg_playlist:
            return
        self.fg_index = max(0, self.fg_index - 1)
        self._load_fg_current()

    def bg_last(self):
        if not self.bg_playlist:
            return
        self.bg_index = max(0, self.bg_index - 1)
        self._load_bg_current()

    def _load_fg_current(self):
        path = self.get_abs_path(self.fg_folder, self.fg_playlist[self.fg_index])
        self.fg_loaded = self.load_track(self.foreground_playback, path)
        if self.fg_is_playing and self.fg_loaded:
            self.foreground_playback.play()
        elif not self.fg_loaded:
            self.fg_is_playing = False

    def _load_bg_current(self):
        path = self.get_abs_path(self.bg_folder, self.bg_playlist[self.bg_index])
        self.bg_loaded = self.load_track(self.background_playback, path)
        if self.bg_is_playing and self.bg_loaded:
            self.background_playback.play()
        elif not self.bg_loaded:
            self.bg_is_playing = False

    def stop(self):
        self.background_playback.stop()
        self.foreground_playback.stop()
        self.alert_playback.stop()
        self.fg_is_playing = False
        self.bg_is_playing = False

    def tick(self):
        """Advance finished tracks and ease volumes toward the typing target."""
        if self.fg_is_playing and self.fg_loaded and not self.foreground_playback.active:
            self.fg_next()
        if self.bg_is_playing and self.bg_loaded and not self.background_playback.active:
            self.bg_next()

        # Adaptive is the only implemented mode: volume follows WPM.
        foreground, background = target_volumes(
            self.session.current_wpm,
            self.fg_min,
            self.fg_max,
            self.bg_min,
            self.bg_max,
        )
        self.target_foreground_volume = foreground
        self.target_background_volume = background
        self.update_volumes()

    def update_volumes(self):
        """Ease both channels toward their targets by smoothing_step."""
        self.foreground_volume = approach(
            self.foreground_volume, self.target_foreground_volume, self.smoothing_step
        )
        self.background_volume = approach(
            self.background_volume, self.target_background_volume, self.smoothing_step
        )
        self.foreground_playback.set_volume(self.foreground_volume)
        self.background_playback.set_volume(self.background_volume)

    def get_progress(self):
        """Returns progress info for tracks."""
        fg_curr = self.foreground_playback.curr_pos
        fg_tot = self.foreground_playback.duration
        if fg_curr < 0:
            fg_curr = 0
        if fg_tot <= 0:
            fg_tot = 1

        bg_curr = self.background_playback.curr_pos
        bg_tot = self.background_playback.duration
        if bg_curr < 0:
            bg_curr = 0
        if bg_tot <= 0:
            bg_tot = 1

        fg_name = self.fg_playlist[self.fg_index] if self.fg_playlist else "No Track"
        bg_name = self.bg_playlist[self.bg_index] if self.bg_playlist else "No Track"

        return {
            "ambience": {
                "name": bg_name,
                "current": bg_curr,
                "total": bg_tot,
                "is_playing": self.bg_is_playing,
                "shuffle": self.bg_shuffle,
                "loop": self.bg_loop,
            },
            "music": {
                "name": fg_name,
                "current": fg_curr,
                "total": fg_tot,
                "is_playing": self.fg_is_playing,
                "shuffle": self.fg_shuffle,
                "loop": self.fg_loop,
            },
        }

    def cleanup(self):
        self.stop()


if __name__ == "__main__":
    from pathlib import Path

    config = Path(__file__).resolve().parent.parent / "sampleConfig.toml"
    session = Session(config)
    player = Player(session)
    player.play_alert()
    print(list_audio_files(player.fg_folder))
