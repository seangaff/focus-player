import argparse
from monitor import Monitor
from player import Player
from session import Session
from pomodoro import PomodoroTimer
from tui import FocusApp


def main():
    parser = argparse.ArgumentParser(description="Focus Player")
    parser.add_argument("--config", default="../sampleConfig.toml", help="Path to config file")
    args = parser.parse_args()

    if args.config is None:
        print("Error Loading config, programed exited")
        return

    # Initialize modules
    session = Session(args.config)

    monitor = Monitor(session)
    player = Player(session)
    pomodoro = PomodoroTimer(session)
    

    # Run App
    app = FocusApp(monitor, player, session, pomodoro)
    app.run()

if __name__ == "__main__":
    main()
