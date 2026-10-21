VALID_CONFIG = """\
# keep this comment
[stats]
total_chars = 100
total_time = 10
completed_sessions = 2
completed_break = 1
average_wpm = 40
max_wpm = 80

[player]
# player stays
alert_sound = "sounds/notification.mp3"
mode = "adaptive"
smoothing_step = 0.05

[player.foreground]
folder = "music"
default_song = ""
shuffle = false
loop = false
min_volume = 0
max_volume = 100

[player.background]
folder = "ambience"
default_song = ""
shuffle = false
loop = true
min_volume = 0
max_volume = 80

[monitor]
window_seconds = 15
keys_ignored = ["Key.cmd"]

[pomodoro]
work_interval = 25
break_interval = 5
alert_on_complete = true
"""


def write_config(directory, text=VALID_CONFIG, name="config.toml"):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path
