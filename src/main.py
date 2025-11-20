import argparse
from monitor import Monitor
from player import Player
from session import Session
from tui import FocusApp

def main():
    parser = argparse.ArgumentParser(description="Focus Player")
    parser.add_argument("--music", help="Path to music file (high intensity)")
    parser.add_argument("--ambience", help="Path to ambience file (low intensity)")
    # parser.add_argument("--midi", help="Path to MIDI file for Note mode") # Disabled
    # parser.add_argument("--mode", choices=["background", "adaptive", "note"], default="adaptive", help="Playback mode") # Deprecated
    args = parser.parse_args()

    # Initialize modules
    monitor = Monitor(window_seconds=15)
    player = Player()
    session = Session()

    # Configure Player
    player.load_tracks(ambience_path=args.ambience, music_path=args.music)
    
    # Start Monitor
    monitor.start()

    # Run App
    app = FocusApp(monitor, player, session)
    app.run()

if __name__ == "__main__":
    main()
