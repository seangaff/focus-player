import pytest

from monitor import Monitor
from session import Session
from support import write_config


def make_monitor(tmp_path):
    return Monitor(Session(write_config(tmp_path)), start_listener=False)


def test_empty_window_is_zero(tmp_path):
    monitor = make_monitor(tmp_path)
    assert monitor.calculate_wpm(now=100) == (0, 0, 0)


def test_ramps_over_first_five_seconds(tmp_path):
    monitor = make_monitor(tmp_path)
    monitor.keystrokes.extend([99, 99, 99, 99, 99])
    wpm, count, elapsed = monitor.calculate_wpm(now=100)
    assert count == 5
    assert elapsed == pytest.approx(1)
    # 5 chars = 1 word, spread across the 5s ramp floor.
    assert wpm == pytest.approx(12)


def test_uses_elapsed_time_after_the_ramp(tmp_path):
    monitor = make_monitor(tmp_path)
    monitor.keystrokes.extend([90] * 10)
    wpm, count, elapsed = monitor.calculate_wpm(now=100)
    assert count == 10
    assert elapsed == pytest.approx(10)
    assert wpm == pytest.approx(12)


def test_drops_keystrokes_outside_the_window(tmp_path):
    monitor = make_monitor(tmp_path)
    monitor.keystrokes.extend([80, 90, 100])
    wpm, count, elapsed = monitor.calculate_wpm(now=100)
    assert count == 2
    assert list(monitor.keystrokes) == [90, 100]
    assert elapsed == pytest.approx(10)
    assert wpm == pytest.approx((2 / 5) / 10 * 60)
