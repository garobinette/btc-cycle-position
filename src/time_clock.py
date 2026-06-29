"""
The time clock (independent clock #1).

It knows nothing about price. For each date it computes days since the most
recent halving, then maps that onto an "expected heat" curve that encodes the
historical phase shape (accumulation -> bull -> top -> markdown -> bottom).
"""

import numpy as np
import pandas as pd

import config


# Parse halving anchors once.
_HALVINGS = pd.to_datetime(config.HALVINGS).sort_values()

# Pre-split the heat curve into x (days) and y (heat) arrays for np.interp.
_CURVE_X = np.array([pt[0] for pt in config.TIME_HEAT_CURVE], dtype=float)
_CURVE_Y = np.array([pt[1] for pt in config.TIME_HEAT_CURVE], dtype=float)


def _most_recent_halving(date: pd.Timestamp) -> pd.Timestamp:
    """The latest halving that occurred on or before `date`."""
    past = _HALVINGS[_HALVINGS <= date]
    if len(past) == 0:
        # Date precedes the first halving; anchor to it so days come out negative-safe.
        return _HALVINGS[0]
    return past[-1]


def days_since_halving(dates: pd.DatetimeIndex) -> pd.Series:
    """Vectorised days-since-most-recent-halving for a DatetimeIndex."""
    anchors = pd.Series(
        [_most_recent_halving(d) for d in dates], index=dates
    )
    return (pd.Series(dates, index=dates) - anchors).dt.days


def time_heat_from_days(days: pd.Series) -> pd.Series:
    """Map days-since-halving onto the expected-heat curve via interpolation."""
    # np.interp clamps to the endpoints outside the curve range, which is the
    # behaviour we want for the rare day > 1458 (next cycle hasn't been retuned).
    heat = np.interp(days.to_numpy(dtype=float), _CURVE_X, _CURVE_Y)
    return pd.Series(heat, index=days.index)


def phase_label(days: float) -> str:
    """Coarse phase name from days-since-halving (months in parentheses)."""
    if days < 365:
        return "Accumulation (0-12 mo)"
    if days < 548:
        return "Bull / markup (12-18 mo)"
    if days < 640:
        return "Top window (18-21 mo)"
    if days < 913:
        return "Markdown (21-30 mo)"
    if days < 1218:
        return "Bottom zone (30-40 mo)"
    return "Re-accumulation (40+ mo)"


def cycle_progress_pct(days: float) -> float:
    """Where in the ~4-year cycle, as a percentage (0% halving, 100% next)."""
    return round(100.0 * days / config.CYCLE_LENGTH_DAYS, 1)


def compute_time_clock(df: pd.DataFrame) -> pd.DataFrame:
    """Return a frame with days_since_halving, time_heat, and phase per date."""
    out = pd.DataFrame(index=df.index)
    out["days_since_halving"] = days_since_halving(df.index)
    out["cycle_progress_pct"] = out["days_since_halving"].apply(cycle_progress_pct)
    out["time_heat"] = time_heat_from_days(out["days_since_halving"])
    out["phase"] = out["days_since_halving"].apply(phase_label)
    return out
