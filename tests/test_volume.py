import pytest

from player import target_volumes


def test_volume_tracks_wpm_inside_channel_ranges():
    assert target_volumes(0, 0, 1, 0, 0.8) == pytest.approx((0.0, 0.8))
    assert target_volumes(50, 0, 1, 0, 0.8) == pytest.approx((0.5, 0.4))
    assert target_volumes(100, 0, 1, 0, 0.8) == pytest.approx((1.0, 0.0))


def test_volume_clamps_outside_zero_to_one_hundred_wpm():
    assert target_volumes(250, 0, 1, 0, 0.8) == pytest.approx((1.0, 0.0))
    assert target_volumes(-20, 0, 1, 0, 0.8) == pytest.approx((0.0, 0.8))


def test_nonzero_floors():
    foreground, background = target_volumes(0, 0.1, 0.9, 0.2, 0.8)
    assert foreground == pytest.approx(0.1)
    assert background == pytest.approx(0.8)
    foreground, background = target_volumes(100, 0.1, 0.9, 0.2, 0.8)
    assert foreground == pytest.approx(0.9)
    assert background == pytest.approx(0.2)
