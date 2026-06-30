"""Tests for the valuation clock: scaling, indicator math, NaN-safe combine."""

import numpy as np
import pandas as pd

from src import valuation_clock as vc


def _ramp(n=1500, start=100.0, end=100000.0):
    """A monotonically rising synthetic price series of length n."""
    idx = pd.date_range("2019-01-01", periods=n, freq="D")
    close = np.linspace(start, end, n)
    return pd.DataFrame({"close": close}, index=idx)


def test_scale_clamps():
    assert vc._scale(0.6, 0.6, 2.4) == 0
    assert vc._scale(2.4, 0.6, 2.4) == 100
    assert vc._scale(5.0, 0.6, 2.4) == 100  # clamped above
    assert vc._scale(0.0, 0.6, 2.4) == 0    # clamped below


def test_drawdown_zero_at_new_high():
    df = _ramp()  # always making new highs -> drawdown ~ 0
    ind = vc.compute_indicators(df)
    assert abs(ind["drawdown_from_ath"].iloc[-1]) < 1e-9


def test_mayer_above_one_when_rising():
    df = _ramp()
    ind = vc.compute_indicators(df)
    # Price rising faster than its 200d average -> Mayer > 1.
    assert ind["mayer_multiple"].iloc[-1] > 1.0


def test_combine_handles_missing_indicators():
    # Row with only two of four indicators present should still produce a value.
    heat = pd.DataFrame(
        {"mayer_multiple": [80.0], "drawdown_from_ath": [60.0],
         "sma200w_ratio": [np.nan], "pi_cycle_ratio": [np.nan]}
    )
    combined = vc.combine_valuation_heat(heat)
    assert abs(combined.iloc[0] - 70.0) < 1e-9  # mean of the two present


def test_valuation_heat_bounded():
    df = _ramp()
    out = vc.compute_valuation_clock(df)
    v = out["valuation_heat"].dropna()
    assert (v >= 0).all() and (v <= 100).all()


def test_mvrv_flows_through_when_present():
    df = _ramp()
    df["mvrv"] = np.linspace(0.8, 3.5, len(df))  # bottom -> top range
    out = vc.compute_valuation_clock(df)
    # MVRV should appear as a raw column and a heat column.
    assert "mvrv" in out and "mvrv_heat" in out
    # Last row sits at the top of the MVRV range -> heat near 100.
    assert out["mvrv_heat"].iloc[-1] > 95


def test_pipeline_ignores_mvrv_when_absent():
    df = _ramp()  # no mvrv column
    out = vc.compute_valuation_clock(df)
    assert "mvrv" not in out
    assert out["valuation_heat"].dropna().between(0, 100).all()
