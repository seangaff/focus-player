# focus-player

TUI music player that rewards typing. Music volume rises with your typing speed and fades when you stop, so the quiet stretches stay available for thinking. A second ambience track moves the other way: louder while you pause, quieter while you type.

## How volume works

Keystrokes are counted in a sliding window (`monitor.window_seconds`, default 15). Words are `characters / 5`. For the first 5 seconds of a burst, WPM ramps up instead of spiking. Speed is capped at 100 WPM for full intensity.

Music volume is scaled between that channel's `min_volume` and `max_volume` (percent). Ambience is scaled in the opposite direction between its own min and max, so a background max of 80 never reaches full volume. Both channels ease toward the target by `player.smoothing_step` on each UI tick (a 0.0–1.0 step, not a percent).

Only `player.mode = "adaptive"` is implemented. Any other mode falls back to adaptive.

## Install

Python 3.11+ is required. On macOS the key listener needs an Accessibility permission for the terminal you launch from (System Settings → Privacy & Security → Accessibility). Enable Terminal, iTerm, or Cursor, then restart that app.

```bash
./setup.sh
# or, once dependencies are available:
pip install -e .
```

`setup.sh` creates a pyenv virtualenv and installs [requirements.txt](requirements.txt). The editable install also adds a `focus-player` command.

MIDI experiments under `experiments/` are not part of the app. Install them only if you want those prototypes:

```bash
pip install -e ".[midi]"
```

## Run

```bash
make run
# or
focus-player --config sampleConfig.toml
```

Copy [sampleConfig.toml](sampleConfig.toml) to your own file if you want a private setup. On quit, the app writes lifetime stats back into the `[stats]` table of whichever config you passed.

## Config

Paths are resolved from the config file's directory. `~/...` and absolute paths are left alone.

```toml
[player]
alert_sound = "sounds/notification.mp3"   # ships in sounds/
mode = "adaptive"
smoothing_step = 0.05

[player.foreground]
folder = "~/Music/sets"       # mp3/wav files; missing folders are skipped
max_volume = 100

[player.background]
folder = "~/Music/ambience"
max_volume = 80

[pomodoro]
work_interval = 25            # minutes
break_interval = 5
alert_on_complete = true      # plays alert_sound, then starts the next interval
```

The pomodoro timer switches Work → Break → Work on its own and keeps running until you pause it. The timer label shows the mode (`Work 24:59`).

Shuffle rebuilds the playlist: the current track stays put, and the rest are shuffled. Turning shuffle off sorts the folder alphabetically.

## Stats

The panel shows current, average, and max WPM, characters typed, completed work intervals and breaks, and the share of the session spent typing versus idle. Average WPM uses characters typed this session divided by time you were actually typing (including the short grace period after you pause), not the whole wall clock.

## Tests

```bash
pip install -e ".[dev]"
make test
```

## Not in this version

These ideas are still only notes or `experiments/` prototypes:

- Note-per-key and MIDI playback
- DJ / energy-based playlist switching
- In-app song browser
- Pausing when other system audio is playing
