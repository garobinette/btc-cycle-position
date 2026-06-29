"""
The combined clock.

Blends the two independent clocks into a single 0-100 cycle-position score and
attaches a human-readable band. Also builds the "where are we right now"
snapshot from the most recent row.
"""

import pandas as pd

import config


def interpret(heat: float) -> str:
    """Map any 0-100 heat to its band label."""
    if pd.isna(heat):
        return "n/a (insufficient history)"
    for low, high, label in config.HEAT_BANDS:
        if low <= heat < high:
            return label
    return "n/a"


def compute_combined_clock(
    time_df: pd.DataFrame, valuation_df: pd.DataFrame
) -> pd.DataFrame:
    """Weighted blend of time_heat and valuation_heat per date."""
    w_t = config.COMBINED_WEIGHTS["time"]
    w_v = config.COMBINED_WEIGHTS["valuation"]

    out = pd.DataFrame(index=time_df.index)
    out["time_heat"] = time_df["time_heat"]
    out["valuation_heat"] = valuation_df["valuation_heat"]

    # Where valuation is missing (early history), fall back to time-only so the
    # combined series is still defined; otherwise use the weighted blend.
    blended = w_t * out["time_heat"] + w_v * out["valuation_heat"]
    out["combined_heat"] = blended.where(
        out["valuation_heat"].notna(), out["time_heat"]
    )
    out["band"] = out["combined_heat"].apply(interpret)
    return out


def current_snapshot(
    df: pd.DataFrame,
    time_df: pd.DataFrame,
    valuation_df: pd.DataFrame,
    combined_df: pd.DataFrame,
) -> dict:
    """A flat dict describing the latest date - drives the printed/Excel summary."""
    last = df.index[-1]
    return {
        "as_of": last.date().isoformat(),
        "close": round(float(df.loc[last, "close"]), 2),
        "days_since_halving": int(time_df.loc[last, "days_since_halving"]),
        "cycle_progress_pct": float(time_df.loc[last, "cycle_progress_pct"]),
        "phase": time_df.loc[last, "phase"],
        "time_heat": round(float(time_df.loc[last, "time_heat"]), 1),
        "valuation_heat": (
            round(float(valuation_df.loc[last, "valuation_heat"]), 1)
            if pd.notna(valuation_df.loc[last, "valuation_heat"]) else None
        ),
        "combined_heat": round(float(combined_df.loc[last, "combined_heat"]), 1),
        "band": combined_df.loc[last, "band"],
    }
