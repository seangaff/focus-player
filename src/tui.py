from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Footer, Static, ProgressBar, Label, Button, Input
from textual.reactive import reactive
from textual.containers import Container, Vertical, Horizontal
import time

class FocusApp(App):
    """A Textual app for Focus Player."""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr 1fr;
        padding: 0 1;
        /* Textual automatically reserves space for the docked Footer */
        height: 100%;
        width: 100%;
    }

    #stats-container {
        border: solid green;
        padding: 0 1;
        height: 100%;
    }

    #volume-container {
        border: solid blue;
        padding: 0 1;
        row-span: 2;
        height: 100%;
    }

    #pomodoro-container {
        border: solid red;
        padding: 0 1;
        height: 100%;
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
        layout: horizontal;
        align: center middle;
        height: auto;
        margin-top: 1;
        width: 100%;
    }
    
    Button {
        margin: 0 1;
        width: auto;
        min-width: 8;
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
        with Container(id="main-container"):
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
        # 1. Run agent ticks to update their state and the session
        self.monitor.tick()
        self.player.tick()
        self.pomodoro.tick()

        # 2. Extract state from session for UI components
        wpm = self.session.current_wpm
        elapsed = time.time() - self.session.start_time

        # 3. Update UI Reactive variables
        self.wpm = wpm
        self.elapsed = elapsed
        self.music_vol = self.player.foreground_volume
        self.ambience_vol = self.player.background_volume

        # 4. Update Widgets
        self.query_one("#wpm-display", Static).update(f"{wpm:.1f}")
        self.query_one("#time-display", Static).update(f"Time: {elapsed:.1f}s")
        
        music_bar = self.query_one("#music-bar", ProgressBar)
        music_bar.progress = self.music_vol # Changed from foreground_vol to music_vol
        
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

        # 5. Update Pomodoro display
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
