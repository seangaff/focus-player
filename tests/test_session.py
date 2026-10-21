import os
from pathlib import Path

import pytest

from session import ConfigError, Session
from support import VALID_CONFIG, write_config


def test_sample_config_resolves_alert_sound():
    root = Path(__file__).resolve().parents[1]
    session = Session(str(root / "sampleConfig.toml"))
    alert = session.resolve_path(session.config["player"]["alert_sound"])
    assert alert == str(root / "sounds" / "notification.mp3")
    assert os.path.isfile(alert)
    assert session.config["player"]["smoothing_step"] == pytest.approx(0.05)


def test_resolve_relative_home_and_absolute(tmp_path):
    session = Session(write_config(tmp_path))
    assert session.resolve_path("sounds/notification.mp3") == os.path.normpath(
        tmp_path / "sounds" / "notification.mp3"
    )
    assert session.resolve_path("/tmp/song.mp3") == "/tmp/song.mp3"
    assert session.resolve_path("~/Music/sets") == os.path.expanduser("~/Music/sets")


def test_seeds_stats_from_config(tmp_path):
    session = Session(write_config(tmp_path))
    assert session.total_chars == 100
    assert session.max_wpm == pytest.approx(80)
    assert session.average_wpm == pytest.approx(40)
    assert session.completed_sessions == 2
    assert session.completed_breaks == 1
    assert session._persisted_total_time == pytest.approx(10)


def test_average_wpm_uses_active_time_and_percents(tmp_path):
    session = Session(write_config(tmp_path))
    session.start_time = 1000
    session.update(30, now=1000)
    for _ in range(50):
        session.add_char()
    session.update(30, now=1060)
    assert session.active_seconds == pytest.approx(60)
    assert session.average_wpm == pytest.approx(10)
    assert session.max_wpm == pytest.approx(80)

    session.update(90, now=1066)
    assert session.is_active is True

    session.update(0, now=1072)
    assert session.is_active is False
    assert session.active_seconds == pytest.approx(66)
    assert session.idle_seconds == pytest.approx(6)
    assert session.typing_percent() == pytest.approx(100 * 66 / 72)
    assert session.idle_percent() == pytest.approx(100 * 6 / 72)
    assert session.max_wpm == pytest.approx(90)


def test_save_updates_stats_without_dropping_other_sections(tmp_path):
    path = write_config(tmp_path)
    session = Session(path)
    session.start_time = 1000
    session.total_chars = 150
    session.max_wpm = 90
    session.average_wpm = 12.5
    session.completed_sessions = 3
    session.completed_breaks = 2

    session.save(now=1060)
    session.save(now=1060)
    text = path.read_text(encoding="utf-8")
    assert "total_chars = 150" in text
    assert "total_time = 70" in text
    assert "completed_sessions = 3" in text
    assert "completed_break = 2" in text
    assert "average_wpm = 12.5" in text
    assert "max_wpm = 90" in text
    assert text.count("total_time = 70") == 1
    assert "# player stays" in text
    assert 'alert_sound = "sounds/notification.mp3"' in text

    reloaded = Session(path)
    assert reloaded.total_chars == 150
    assert reloaded.completed_sessions == 3
    assert reloaded.completed_breaks == 2
    assert reloaded._persisted_total_time == pytest.approx(70)
    assert reloaded.average_wpm == pytest.approx(12.5)


def test_missing_config_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        Session(tmp_path / "missing.toml")


def test_invalid_toml(tmp_path):
    path = tmp_path / "bad.toml"
    path.write_text("[player\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="parse"):
        Session(path)


def test_missing_required_section(tmp_path):
    text = VALID_CONFIG.replace("[pomodoro]\n", "[not_pomodoro]\n")
    path = write_config(tmp_path, text)
    with pytest.raises(ConfigError, match="pomodoro"):
        Session(path)
