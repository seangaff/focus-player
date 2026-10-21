import argparse
import sys
from pathlib import Path

from monitor import Monitor
from player import Player
from pomodoro import PomodoroTimer
from session import ConfigError, Session
from tui import FocusApp


def default_config_path() -> str:
    cwd_candidate = Path.cwd() / "sampleConfig.toml"
    if cwd_candidate.is_file():
        return str(cwd_candidate)
    return str(Path(__file__).resolve().parent.parent / "sampleConfig.toml")


def main():
    parser = argparse.ArgumentParser(description="Focus Player")
    parser.add_argument("--config", default=default_config_path(), help="Path to config file")
    args = parser.parse_args()

    try:
        session = Session(args.config)
    except ConfigError as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return 1

    monitor = Monitor(session)
    player = Player(session)
    pomodoro = PomodoroTimer(session)

    app = FocusApp(monitor, player, session, pomodoro)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
