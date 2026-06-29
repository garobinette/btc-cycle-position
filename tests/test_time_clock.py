"""Tests for the time clock: halving anchoring, heat curve, phase labels."""

import pandas as pd

from src import time_clock


def test_days_since_halving_picks_most_recent():
    # A date a week after the 2024-04-20 halving should read ~7 days.
    idx = pd.to_datetime(["2024-04-27"])
    days = time_clock.days_since_halving(idx)
    assert int(days.iloc[0]) == 7


def test_days_since_halving_across_cycles():
    # Just before the 2024 halving, the anchor is still the 2020 halving.
    idx = pd.to_datetime(["2024-04-19"])
    days = time_clock.days_since_halving(idx)
    assert int(days.iloc[0]) > 1400  # ~4 years since 2020-05-11


def test_time_heat_is_bounded():
    idx = pd.to_datetime(["2024-04-20", "2025-10-06", "2026-12-01"])
    days = time_clock.days_since_halving(idx)
    heat = time_clock.time_heat_from_days(days)
    assert (heat >= 0).all() and (heat <= 100).all()


def test_top_window_runs_hotter_than_bottom():
    days = pd.Series([610, 1218], index=[0, 1])  # ~20 mo vs ~40 mo
    heat = time_clock.time_heat_from_days(days)
    assert heat.iloc[0] > heat.iloc[1]


def test_phase_labels():
    assert "Accumulation" in time_clock.phase_label(100)
    assert "Top" in time_clock.phase_label(600)
    assert "Bottom" in time_clock.phase_label(1100)
