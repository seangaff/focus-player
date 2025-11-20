from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, ProgressBar, Label
from textual.reactive import reactive
import time

class FocusApp(App):
    """A Textual app for Focus Player."""

    CSS = """
    Screen {
        align: center middle;
    }

    #stats-container {
        width: 60%;
        height: auto;
        border: solid green;
        padding: 1 2;
        margin-bottom: 2;
    }

    #wpm-display {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .stat-label {
        width: 100%;
        text-align: center;
    }

    #volume-container {
        width: 60%;
        height: auto;
        border: solid blue;
        padding: 1 2;
    }

    ProgressBar {
        margin-bottom: 1;
    }
    
    Label {
        margin-bottom: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    wpm = reactive(0.0)
    elapsed = reactive(0.0)
    music_vol = reactive(0.0)
    ambience_vol = reactive(0.0)

    def __init__(self, monitor, player, session):
        super().__init__()
        self.monitor = monitor
        self.player = player
        self.session = session

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("WPM", classes="stat-label"),
            Static("0.0", id="wpm-display"),
            Static("Time: 0s", id="time-display", classes="stat-label"),
            id="stats-container"
        )
        yield Container(
            Label("Music Volume"),
            ProgressBar(total=1.0, show_eta=False, id="music-bar"),
            Label("Ambience Volume"),
            ProgressBar(total=1.0, show_eta=False, id="ambience-bar"),
            id="volume-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.set_interval(0.1, self.update_loop)
        self.player.play()

    def update_loop(self) -> None:
        """Main update loop."""
        # 1. Get stats from Monitor
        wpm, chars, elapsed = self.monitor.calculate_wpm()
        self.session.update(wpm, chars)
        
        # 2. Update Player logic
        # Cap at 100 WPM for max intensity
        intensity = min(max(wpm / 60, 0), 1)
        self.player.set_intensity(intensity)
        self.player.update_volumes()

        # 3. Update UI Reactive variables
        self.wpm = wpm
        self.elapsed = elapsed
        self.music_vol = self.player.music_volume
        self.ambience_vol = self.player.ambience_volume

        # 4. Update Widgets directly (reactive watchers can also be used but direct update is fine for simple cases)
        self.query_one("#wpm-display", Static).update(f"{wpm:.1f}")
        self.query_one("#time-display", Static).update(f"Time: {elapsed:.1f}s")
        
        music_bar = self.query_one("#music-bar", ProgressBar)
        music_bar.progress = self.music_vol
        
        ambience_bar = self.query_one("#ambience-bar", ProgressBar)
        ambience_bar.progress = self.ambience_vol

    def on_unmount(self) -> None:
        """Called when app exits."""
        self.monitor.stop()
        self.player.cleanup()
