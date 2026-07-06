"""Tests for the top-anchored time clock: anchoring, canonical phases, heat."""

import pandas as pd

from src import time_clock as tc

HALVING = pd.Timestamp("2024-04-20")
TOP = pd.Timestamp("2025-10-06")   # realised top, ~534 days after the halving


def test_days_since_halving_picks_most_recent():
    idx = pd.to_datetime(["2024-04-27"])
    assert int(tc.days_since_halving(idx).iloc[0]) == 7


def test_days_since_halving_across_cycles():
    idx = pd.to_datetime(["2024-04-19"])           # day before the 2024 halving
    assert int(tc.days_since_halving(idx).iloc[0]) > 1400


def test_heat_is_bounded():
    idx = pd.to_datetime(["2024-04-20", "2025-10-06", "2026-06-29", "2026-12-01"])
    df = pd.DataFrame({"close": [1, 2, 3, 4]}, index=idx)
    heat = tc.compute_time_clock(df)["time_heat"]
    assert (heat >= 0).all() and (heat <= 100).all()


def test_top_date_reads_peak_euphoria():
    heat, phase = tc._heat_and_phase(TOP)
    assert heat > 99 and phase == "Euphoria"


def test_euphoria_hotter_than_correction():
    top_heat, _ = tc._heat_and_phase(TOP)
    corr_heat, _ = tc._heat_and_phase(TOP + pd.Timedelta(days=250))
    assert top_heat > corr_heat


def test_four_canonical_phases_present():
    cases = {
        "Accumulation": HALVING + pd.Timedelta(days=30),
        "Expansion":    HALVING + pd.Timedelta(days=350),
        "Euphoria":     TOP,
        "Correction":   TOP + pd.Timedelta(days=150),
    }
    for expected, d in cases.items():
        _, phase = tc._heat_and_phase(d)
        assert phase == expected, f"{d.date()} -> {phase}, expected {expected}"


def test_reaccumulation_after_bottom():
    # Bottom = top + 380 days; well past it we should be in re-accumulation
    # (labelled Accumulation), with heat rising back toward the next halving.
    bottom = TOP + pd.Timedelta(days=380)
    heat_bottom, _ = tc._heat_and_phase(bottom)
    heat_later, phase_later = tc._heat_and_phase(bottom + pd.Timedelta(days=300))
    assert phase_later == "Accumulation"
    assert heat_later > heat_bottom            # heat climbs off the bottom


def test_tail_brackets_to_next_halving():
    # Just before the next halving, heat should sit near the curve's closing
    # value (~24), i.e. the cycle closes where it began rather than drifting.
    next_halving = pd.Timestamp("2028-04-17")
    heat, phase = tc._heat_and_phase(next_halving - pd.Timedelta(days=5))
    assert 18 <= heat <= 26 and phase == "Accumulation"


def test_reanchor_uses_actual_late_top():
    # The 2025 cycle topped ~534 days out. At day 480 (the old average-top day)
    # we should NOT be at peak heat, because the realised top is later.
    heat, phase = tc._heat_and_phase(HALVING + pd.Timedelta(days=480))
    assert heat < 100 and phase in ("Expansion", "Euphoria")


def test_days_since_top_sign():
    pre = tc.days_since_top(pd.to_datetime([TOP - pd.Timedelta(days=10)])).iloc[0]
    post = tc.days_since_top(pd.to_datetime([TOP + pd.Timedelta(days=10)])).iloc[0]
    assert pre < 0 and post > 0
