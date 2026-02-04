from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, ProgressBar, Label
from textual.widgets import Header, Footer, Static, ProgressBar, Label, Button, Input
from textual.reactive import reactive
from textual.containers import Container, Vertical, Horizontal
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
    
    #volume-container {
        width: 60%;
        height: auto;
        border: solid blue;
        padding: 1 2;
        margin-bottom: 2;
    }

    #pomodoro-container {
        width: 60%;
        height: auto;
        border: solid red;
        padding: 1 2;
    }

    #timer-display {
        text-align: center;
        text-style: bold;
        color: yellow;
        height: 3;
        content-align: center middle;
        text-opacity: 100%; 
        border: heavy white;
    }
    
    .timer-controls {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
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

    def __init__(self, monitor, player, session, pomodoro):
        super().__init__()
        self.monitor = monitor
        self.player = player
        self.session = session
        self.pomodoro = pomodoro

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
            Label("Music Progress"),
            ProgressBar(total=100.0, show_eta=False, id="music-progress"),
            
            Label("Ambience Volume"),
            ProgressBar(total=1.0, show_eta=False, id="ambience-bar"),
            Label("Ambience Progress"),
            ProgressBar(total=100.0, show_eta=False, id="ambience-progress"),
            id="volume-container"
        )
        yield Container(
            Label("Pomodoro Timer"),
            Static("25:00", id="timer-display"),
            Horizontal(
                Button("Start", id="pomo-start", variant="success"),
                Button("Pause", id="pomo-pause", variant="warning"),
                Button("Reset", id="pomo-reset", variant="error"),
                Button("Switch Mode", id="pomo-switch", variant="primary"),
                classes="timer-controls"
            ),
            Label("Work (min):", classes="stat-label"), 
            Input(value="25", id="work-input", type="integer"),
            Label("Break (min):", classes="stat-label"),
            Input(value="5", id="break-input", type="integer"),
            id="pomodoro-container"
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
        intensity = min(max(wpm / 100, 0), 1)
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
        
        # Update Progress Bars
        progress = self.player.get_progress()
        
        music_prog = self.query_one("#music-progress", ProgressBar)
        m_curr = progress["music"]["current"]
        m_total = progress["music"]["total"]
        if m_total > 0:
            music_prog.update(total=m_total, progress=m_curr)
            
        amb_prog = self.query_one("#ambience-progress", ProgressBar)
        a_curr = progress["ambience"]["current"]
        a_total = progress["ambience"]["total"]

        if a_total > 0:
            amb_prog.update(total=a_total, progress=a_curr)

        # 5. Update Pomodoro
        self.pomodoro.tick()
        self.query_one("#timer-display", Static).update(self.pomodoro.get_time_display())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "pomo-start":
            self.pomodoro.start()
        elif button_id == "pomo-pause":
            self.pomodoro.pause()
        elif button_id == "pomo-reset":
            self.pomodoro.reset()
        elif button_id == "pomo-switch":
            self.pomodoro.toggle_mode()
            
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "work-input":
            try:
                val = int(event.value)
                self.pomodoro.set_duration(work_mins=val)
            except ValueError:
                pass
        elif event.input.id == "break-input":
            try:
                val = int(event.value)
                self.pomodoro.set_duration(break_mins=val)
            except ValueError:
                pass

    def on_unmount(self) -> None:
        """Called when app exits."""
        self.monitor.stop()
        self.player.cleanup()
