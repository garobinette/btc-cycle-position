"""
The valuation clock (independent clock #2).

It knows nothing about the calendar. From the daily close it derives four
price-based stretch indicators, normalises each to a 0-100 heat, and combines
them into a weighted "observed heat". All four are computable from close
alone; on-chain metrics (MVRV, Puell) can be bolted on later via add_external().
"""

import numpy as np
import pandas as pd

import config


def _scale(value, low, high):
    """Linear map [low, high] -> [0, 100], clamped. Works element-wise."""
    pct = (value - low) / (high - low) * 100.0
    return np.clip(pct, 0.0, 100.0)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Raw indicator values (not yet heat-scaled)."""
    close = df["close"]
    out = pd.DataFrame(index=df.index)

    # Mayer Multiple: price relative to its 200-day average.
    sma_200d = close.rolling(200, min_periods=200).mean()
    out["mayer_multiple"] = close / sma_200d

    # Drawdown from the running all-time high (0 at ATH, negative below).
    running_ath = close.cummax()
    out["drawdown_from_ath"] = (close - running_ath) / running_ath

    # 200-week SMA ratio (the historic bear-market floor). 200 weeks ~ 1400 days.
    sma_200w = close.rolling(1400, min_periods=1400).mean()
    out["sma200w_ratio"] = close / sma_200w

    # Pi Cycle Top: 111-day SMA vs twice the 350-day SMA. Ratio ~1 flags tops.
    sma_111 = close.rolling(111, min_periods=111).mean()
    sma_350 = close.rolling(350, min_periods=350).mean()
    out["pi_cycle_ratio"] = sma_111 / (2.0 * sma_350)

    return out


def indicators_to_heat(indicators: pd.DataFrame) -> pd.DataFrame:
    """Scale each raw indicator to a 0-100 heat using config ranges."""
    heat = pd.DataFrame(index=indicators.index)
    for name, spec in config.VALUATION_INDICATORS.items():
        if name in indicators:
            heat[name] = _scale(indicators[name], spec["low"], spec["high"])
    return heat


def combine_valuation_heat(heat: pd.DataFrame) -> pd.Series:
    """Weighted mean across available indicators, renormalising per row.

    Early rows have NaN for slow indicators (e.g. the 200-week SMA needs ~4
    years of history). Those are skipped and the remaining weights renormalise,
    so the score is always built only from indicators that actually exist.
    """
    weights = {n: s["weight"] for n, s in config.VALUATION_INDICATORS.items()}
    cols = [c for c in heat.columns if c in weights]

    w = np.array([weights[c] for c in cols], dtype=float)
    values = heat[cols].to_numpy(dtype=float)

    mask = ~np.isnan(values)            # which indicators exist on each row
    weighted = np.where(mask, values * w, 0.0).sum(axis=1)
    weight_sum = (mask * w).sum(axis=1)

    with np.errstate(invalid="ignore", divide="ignore"):
        combined = np.where(weight_sum > 0, weighted / weight_sum, np.nan)
    return pd.Series(combined, index=heat.index)


def compute_valuation_clock(df: pd.DataFrame) -> pd.DataFrame:
    """Return raw indicators, their per-indicator heat, and combined valuation heat."""
    indicators = compute_indicators(df)
    heat = indicators_to_heat(indicators)

    out = indicators.copy()
    out = out.join(heat.add_suffix("_heat"))
    out["valuation_heat"] = combine_valuation_heat(heat)
    return out
