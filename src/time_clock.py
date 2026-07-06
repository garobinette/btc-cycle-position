"""
The time clock (independent clock #1).

It knows nothing about price magnitude. It locates position within the cycle
using three calendar anchors, so the cycle is bracketed by halvings on both
ends: the most recent halving (start), that cycle's realised top (interior
peak), and the next halving (end). The four canonical phases run across three
legs: Accumulation -> Expansion -> Euphoria (halving -> top), Correction
(top -> bottom), then Accumulation again (bottom -> next halving).

Anchoring to the realised top keeps the clock in phase when a cycle tops early
or late (2025 topped ~534 days after its halving, past the ~480-day average),
while bracketing the tail to the next halving ties the re-accumulation leg back
to the 4-year rhythm rather than letting it float off the top.
"""

import numpy as np
import pandas as pd

import config


_HALVINGS = pd.to_datetime(config.HALVINGS).sort_values()
_TOPS = pd.to_datetime(config.CYCLE_TOPS).sort_values()

_PRE_X = np.array([p[0] for p in config.PRETOP_HEAT_CURVE], dtype=float)
_PRE_Y = np.array([p[1] for p in config.PRETOP_HEAT_CURVE], dtype=float)
_COR_X = np.array([p[0] for p in config.CORRECTION_HEAT_CURVE], dtype=float)
_COR_Y = np.array([p[1] for p in config.CORRECTION_HEAT_CURVE], dtype=float)
_REA_X = np.array([p[0] for p in config.REACCUM_HEAT_CURVE], dtype=float)
_REA_Y = np.array([p[1] for p in config.REACCUM_HEAT_CURVE], dtype=float)


def _most_recent_halving(date: pd.Timestamp) -> pd.Timestamp:
    """The latest halving on or before `date`."""
    past = _HALVINGS[_HALVINGS <= date]
    return past[-1] if len(past) else _HALVINGS[0]


def _next_halving(halving: pd.Timestamp) -> pd.Timestamp:
    """The halving after `halving`, or a far-future sentinel if none is known."""
    later = _HALVINGS[_HALVINGS > halving]
    return later[0] if len(later) else halving + pd.Timedelta(days=10000)


def _cycle_top(halving: pd.Timestamp) -> pd.Timestamp:
    """The realised top belonging to this cycle, or an expected top if none yet.

    A cycle's top is the first known top that falls after its halving and before
    the next halving. If none exists (the top hasn't formed), fall back to the
    average halving->top span so the clock still resolves.
    """
    nxt = _next_halving(halving)
    tops = _TOPS[(_TOPS > halving) & (_TOPS < nxt)]
    if len(tops):
        return tops[0]
    return halving + pd.Timedelta(days=config.AVG_HALVING_TO_TOP_DAYS)


def _heat_and_phase(date: pd.Timestamp):
    """(heat 0-100, phase name) for a single date.

    Three legs, bracketed by halvings on both ends:
      halving -> top          : Accumulation -> Expansion -> Euphoria
      top     -> bottom       : Correction        (bottom = top + avg span)
      bottom  -> next halving : Accumulation      (re-accumulation)
    """
    halving = _most_recent_halving(date)
    top = _cycle_top(halving)
    bottom = top + pd.Timedelta(days=config.AVG_TOP_TO_BOTTOM_DAYS)
    nxt = _next_halving(halving)

    pre_span = (top - halving).days
    if pre_span <= 0:                  # guard against a mis-entered top date
        pre_span = config.AVG_HALVING_TO_TOP_DAYS

    if date <= top:
        f = (date - halving).days / pre_span
        heat = float(np.interp(f, _PRE_X, _PRE_Y))
        if f < 0.30:
            phase = "Accumulation"
        elif f < 0.75:
            phase = "Expansion"
        else:
            phase = "Euphoria"
    elif date <= bottom:
        c = (date - top).days / config.AVG_TOP_TO_BOTTOM_DAYS
        heat = float(np.interp(c, _COR_X, _COR_Y))
        phase = "Correction"
    else:
        reacc_span = (nxt - bottom).days
        if reacc_span <= 0:            # bottom at/after next halving: clamp
            reacc_span = 1
        r = (date - bottom).days / reacc_span
        heat = float(np.interp(r, _REA_X, _REA_Y))
        phase = "Accumulation"

    return heat, phase


def days_since_halving(dates: pd.DatetimeIndex) -> pd.Series:
    """Vectorised days-since-most-recent-halving for a DatetimeIndex."""
    anchors = pd.Series([_most_recent_halving(d) for d in dates], index=dates)
    return (pd.Series(dates, index=dates) - anchors).dt.days


def days_since_top(dates: pd.DatetimeIndex) -> pd.Series:
    """Days since this cycle's (realised or expected) top; negative if pre-top."""
    out = []
    for d in dates:
        top = _cycle_top(_most_recent_halving(d))
        out.append((d - top).days)
    return pd.Series(out, index=dates)


def cycle_progress_pct(days: float) -> float:
    """Where in the ~4-year cycle, as a percentage (0% halving, 100% next)."""
    return round(100.0 * days / config.CYCLE_LENGTH_DAYS, 1)


def compute_time_clock(df: pd.DataFrame) -> pd.DataFrame:
    """Return days_since_halving, days_since_top, progress %, heat, and phase."""
    out = pd.DataFrame(index=df.index)
    out["days_since_halving"] = days_since_halving(df.index)
    out["days_since_top"] = days_since_top(df.index)
    out["cycle_progress_pct"] = out["days_since_halving"].apply(cycle_progress_pct)

    heat_phase = [_heat_and_phase(d) for d in df.index]
    out["time_heat"] = [hp[0] for hp in heat_phase]
    out["phase"] = [hp[1] for hp in heat_phase]
    return out
