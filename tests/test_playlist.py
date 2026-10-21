import random

from player import list_audio_files, reorder_playlist


def test_missing_folder_is_empty():
    assert list_audio_files("/no/such/focus-player-folder") == []


def test_lists_only_audio_files(tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"")
    (tmp_path / "b.WAV").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("nope", encoding="utf-8")
    assert sorted(list_audio_files(str(tmp_path))) == ["a.mp3", "b.WAV"]


def test_shuffle_keeps_current_track_first():
    playlist, index = reorder_playlist(["a", "b", "c", "d"], 2, True, random.Random(0))
    assert playlist[0] == "c"
    assert index == 0
    assert sorted(playlist) == ["a", "b", "c", "d"]


def test_disabling_shuffle_sorts_and_keeps_current_track():
    playlist, index = reorder_playlist(["c", "a", "b"], 0, False)
    assert playlist == ["a", "b", "c"]
    assert index == 2
