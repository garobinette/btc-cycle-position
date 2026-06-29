"""Smoke-test helper. Generates SYNTHETIC (fake) BTC-like daily data in
data/btc_daily.xlsx so you can verify the pipeline runs before plugging
in your own spreadsheet. The numbers are not real prices. Run:
    python make_sample_data.py
"""
import numpy as np, pandas as pd

idx = pd.date_range("2019-06-01", "2026-06-29", freq="D")
n = len(idx)

# Two halving-style cycles: peak ~Nov 2021 and ~Oct 2025, troughs between.
def cycle_price(dates):
    p = np.zeros(len(dates))
    anchors = {  # (peak_date, peak_price, trough_date, trough_price)
        0: ("2021-11-10", 69000, "2022-11-21", 16000),
        1: ("2025-10-06", 126000, "2026-10-15", 50000),
    }
    base = pd.Timestamp("2019-06-01")
    for i, d in enumerate(dates):
        # crude piecewise-ish shape via blended sines on the cycle clock
        t = (d - base).days
        # long uptrend with two humps
        hump1 = 60000*np.exp(-((t-900)/240)**2)
        hump2 = 118000*np.exp(-((t-2320)/250)**2)
        floor = 6000 + 9*t**0.92
        p[i] = floor + hump1 + hump2
    return p

close = cycle_price(idx)
rng = np.random.default_rng(42)
close *= (1 + rng.normal(0, 0.012, n)).cumprod()  # mild random walk noise
close = np.clip(close, 3000, None)

df = pd.DataFrame({"Date": idx, "PX_LAST": np.round(close, 2)})
df.to_excel("data/btc_daily.xlsx", index=False)
print(f"Wrote {len(df)} rows, {df.Date.min().date()} -> {df.Date.max().date()}, "
      f"price range ${df.PX_LAST.min():,.0f}-${df.PX_LAST.max():,.0f}")
