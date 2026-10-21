from pomodoro import PomodoroTimer
from session import Session
from support import write_config


def make_timer(tmp_path):
    session = Session(write_config(tmp_path))
    session.completed_sessions = 0
    session.completed_breaks = 0
    return PomodoroTimer(session), session


def test_sub_second_tick_does_not_move(tmp_path):
    timer, _session = make_timer(tmp_path)
    timer.remaining_seconds = 10
    timer.is_running = True
    timer.last_tick_time = 100
    assert timer.tick(now=100.4) is False
    assert timer.remaining_seconds == 10
    assert timer.state == "Work"


def test_work_interval_advances_to_break_and_keeps_running(tmp_path):
    timer, session = make_timer(tmp_path)
    timer.remaining_seconds = 2
    timer.is_running = True
    timer.last_tick_time = 100
    assert timer.tick(now=102) is True
    assert timer.state == "Break"
    assert timer.remaining_seconds == 5 * 60
    assert timer.is_running is True
    assert session.completed_sessions == 1
    assert session.completed_breaks == 0
    assert timer.get_time_display() == "Break 05:00"
    assert timer.alert_on_complete is True


def test_break_interval_advances_to_work(tmp_path):
    timer, session = make_timer(tmp_path)
    timer.state = "Break"
    timer.remaining_seconds = 1
    timer.is_running = True
    timer.last_tick_time = 50
    assert timer.tick(now=51) is True
    assert timer.state == "Work"
    assert timer.remaining_seconds == 25 * 60
    assert timer.get_time_display() == "Work 25:00"
    assert session.completed_breaks == 1
    assert session.completed_sessions == 0


def test_paused_timer_does_not_complete(tmp_path):
    timer, session = make_timer(tmp_path)
    timer.remaining_seconds = 0
    timer.is_running = False
    assert timer.tick(now=10) is False
    assert session.completed_sessions == 0
