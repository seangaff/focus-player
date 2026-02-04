import argparse
from monitor import Monitor
from player import Player
from session import Session
from pomodoro import PomodoroTimer
from tui import FocusApp
import tomllib

def load_config(config_path="./sampleConfig.toml"):
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    # TODO: Add config validation and specifc error handling, assume config correct for now
    except Exception as e:
        print(f"Error loading config: {e}")
        return None
    return config

def main():
    parser = argparse.ArgumentParser(description="Focus Player")
    parser.add_argument("--config", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    if config is None:
        print("Error Loading config, programed exited")
        return


    # Initialize modules
    session = Session(config)
    
    monitor = Monitor(session)
    player = Player(session)
    pomodoro = PomodoroTimer(session)
    # Configure Player
    player.load_tracks()
    
    # Start Monitor
    monitor.start()

    # Run App
    app = FocusApp(monitor, player, session, pomodoro)
    app.run()

if __name__ == "__main__":
    main()
