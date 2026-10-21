import os
import tempfile
import time
import tomllib


class ConfigError(Exception):
    """Raised when the config file is missing, unreadable, or invalid."""


class Session:
    def __init__(self, config_path: str):
        self.config_path = os.path.abspath(config_path)
        self.config_dir = os.path.dirname(self.config_path)
        self.config = self.load_config(self.config_path)

        self.start_time = time.time()
        self._apply_stats(self.config.get("stats", {}))

        self.current_wpm = 0.0
        self.active_seconds = 0.0
        self.idle_seconds = 0.0
        self.last_activity_time = self.start_time
        self._last_sample = None
        self.is_active = False

    def load_config(self, config_path):
        if not os.path.isfile(config_path):
            raise ConfigError(f"Config file not found: {config_path}")
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Could not parse config {config_path}: {e}") from e
        except OSError as e:
            raise ConfigError(f"Could not read config {config_path}: {e}") from e
        return validate_config(config)

    def resolve_path(self, path: str) -> str:
        """Resolve a config path against the config file's directory.

        Absolute paths and ~/paths are expanded as-is. Relative paths are
        resolved from the directory that contains the config file.
        """
        expanded = os.path.expanduser(path)
        if os.path.isabs(expanded):
            return os.path.normpath(expanded)
        return os.path.normpath(os.path.join(self.config_dir, expanded))

    def _apply_stats(self, stats):
        self.total_chars = int(stats.get("total_chars", 0))
        self._seeded_chars = self.total_chars
        self.max_wpm = float(stats.get("max_wpm", 0))
        self.average_wpm = float(stats.get("average_wpm", 0))
        self.completed_sessions = int(stats.get("completed_sessions", 0))
        # Sample config uses the singular key; accept either spelling.
        if "completed_break" in stats:
            self.completed_breaks = int(stats.get("completed_break", 0))
        else:
            self.completed_breaks = int(stats.get("completed_breaks", 0))
        self._persisted_total_time = float(stats.get("total_time", 0))

    def add_char(self):
        self.total_chars += 1

    def update(self, wpm, now=None):
        now = time.time() if now is None else now
        if self._last_sample is None:
            delta = 0.0
        else:
            delta = max(0.0, now - self._last_sample)
        self._last_sample = now

        self.current_wpm = wpm
        if wpm > self.max_wpm:
            self.max_wpm = wpm

        if wpm > 0:
            self.last_activity_time = now
            self.is_active = True
        elif now - self.last_activity_time > 5:
            self.is_active = False

        if self.is_active:
            self.active_seconds += delta
        else:
            self.idle_seconds += delta

        session_chars = self.total_chars - self._seeded_chars
        if session_chars > 0 and self.active_seconds > 0:
            self.average_wpm = (session_chars / 5.0) / (self.active_seconds / 60.0)

    def typing_percent(self) -> float:
        total = self.active_seconds + self.idle_seconds
        if total <= 0:
            return 0.0
        return 100.0 * self.active_seconds / total

    def idle_percent(self) -> float:
        total = self.active_seconds + self.idle_seconds
        if total <= 0:
            return 0.0
        return 100.0 * self.idle_seconds / total

    def current_total_time(self, now=None) -> float:
        now = time.time() if now is None else now
        return self._persisted_total_time + max(0.0, now - self.start_time)

    def save(self, now=None):
        """Write lifetime stats back into the config file's [stats] section."""
        now = time.time() if now is None else now
        stats = {
            "total_chars": int(self.total_chars),
            "total_time": int(self.current_total_time(now)),
            "completed_sessions": int(self.completed_sessions),
            "completed_break": int(self.completed_breaks),
            "average_wpm": float(self.average_wpm),
            "max_wpm": float(self.max_wpm),
        }
        self.config["stats"] = stats
        try:
            update_stats_section(self.config_path, stats)
        except OSError as e:
            print(f"Error saving stats: {e}")

    def get_stats(self):
        elapsed = time.time() - self.start_time
        return {
            "elapsed": elapsed,
            "current_wpm": self.current_wpm,
            "average_wpm": self.average_wpm,
            "max_wpm": self.max_wpm,
            "total_chars": self.total_chars,
            "is_active": self.is_active,
            "typing_percent": self.typing_percent(),
            "idle_percent": self.idle_percent(),
        }


def validate_config(config: dict) -> dict:
    if not isinstance(config, dict):
        raise ConfigError("Config file must contain a TOML table")

    player = _require_table(config, "player")
    foreground = _require_table(player, "foreground", "player.foreground")
    background = _require_table(player, "background", "player.background")
    monitor = _require_table(config, "monitor")
    pomodoro = _require_table(config, "pomodoro")
    config.setdefault("stats", {})

    _require_str(player, "alert_sound", "player.alert_sound")
    mode = player.setdefault("mode", "adaptive")
    if not isinstance(mode, str) or not mode:
        raise ConfigError("player.mode must be a non-empty string")

    player["smoothing_step"] = _require_number(
        player, "smoothing_step", default=0.05, minimum=0.001, maximum=1.0,
        label="player.smoothing_step",
    )
    _apply_channel_defaults(foreground, "player.foreground")
    _apply_channel_defaults(background, "player.background")

    monitor["window_seconds"] = _require_number(
        monitor, "window_seconds", minimum=0.1, label="monitor.window_seconds",
    )
    keys = monitor.setdefault("keys_ignored", [])
    if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
        raise ConfigError("monitor.keys_ignored must be a list of strings")

    pomodoro["work_interval"] = _require_number(
        pomodoro, "work_interval", minimum=0.01, label="pomodoro.work_interval",
    )
    pomodoro["break_interval"] = _require_number(
        pomodoro, "break_interval", minimum=0.01, label="pomodoro.break_interval",
    )
    alert = pomodoro.setdefault("alert_on_complete", True)
    if not isinstance(alert, bool):
        raise ConfigError("pomodoro.alert_on_complete must be true or false")

    return config


def _require_table(parent: dict, key: str, label: str | None = None) -> dict:
    label = label or key
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Config missing [{label}] section")
    return value


def _require_str(parent: dict, key: str, label: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} must be a non-empty string")
    return value


def _require_number(parent, key, label, default=None, minimum=None, maximum=None) -> float:
    if key not in parent or parent[key] is None:
        if default is None:
            raise ConfigError(f"Config missing {label}")
        parent[key] = default
    value = parent[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{label} must be a number")
    value = float(value)
    if minimum is not None and value < minimum:
        raise ConfigError(f"{label} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{label} must be <= {maximum}")
    parent[key] = value
    return value


def _apply_channel_defaults(channel: dict, label: str) -> None:
    _require_str(channel, "folder", f"{label}.folder")
    channel.setdefault("default_song", "")
    if not isinstance(channel["default_song"], str):
        raise ConfigError(f"{label}.default_song must be a string")
    for flag in ("shuffle", "loop"):
        channel.setdefault(flag, False)
        if not isinstance(channel[flag], bool):
            raise ConfigError(f"{label}.{flag} must be true or false")
    _require_number(channel, "min_volume", default=0, minimum=0, maximum=100, label=f"{label}.min_volume")
    _require_number(channel, "max_volume", default=100, minimum=0, maximum=100, label=f"{label}.max_volume")


def update_stats_section(path: str, stats: dict) -> None:
    """Replace values in the [stats] table without rewriting the rest of the file."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()

    start = None
    for index, line in enumerate(lines):
        if line.strip() == "[stats]":
            start = index
            break

    formatted = {key: _toml_value(value) for key, value in stats.items()}
    if start is None:
        block = ["", "[stats]"] + [f"{key} = {value}" for key, value in formatted.items()]
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(block)
        _write_lines(path, lines, newline)
        return

    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            end = index
            break

    remaining = dict(formatted)
    section = []
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            section.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in remaining:
            section.append(f"{key} = {remaining.pop(key)}")
        else:
            section.append(line)
    for key, value in remaining.items():
        section.append(f"{key} = {value}")

    lines[start + 1:end] = section
    _write_lines(path, lines, newline)


def _write_lines(path: str, lines: list[str], newline: str) -> None:
    body = newline.join(lines)
    if not body.endswith(newline):
        body += newline
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.4f}".rstrip("0").rstrip(".")
    raise ConfigError(f"Cannot write stats value {value!r}")
