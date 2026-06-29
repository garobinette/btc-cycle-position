"""
Central configuration for the BTC cycle-position project.

Everything you might want to tweak lives here so the logic modules in src/
stay clean. Nothing in src/ hard-codes a path, a weight, or a date.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths  (pathlib keeps these Windows-safe: no backslash-escaping headaches)
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Drop your spreadsheet in data/ and put its filename here.
INPUT_EXCEL = DATA_DIR / "btc_daily.xlsx"
INPUT_SHEET = 0  # 0 = first sheet, or a sheet name string like "Prices"

OUTPUT_EXCEL = OUTPUT_DIR / "cycle_position.xlsx"
OUTPUT_CHART = OUTPUT_DIR / "cycle_position.png"

# --------------------------------------------------------------------------
# Column mapping
# --------------------------------------------------------------------------
# The loader auto-detects from these candidate names (case-insensitive).
# PX_LAST is included because that's the Bloomberg mnemonic you already use.
DATE_COLUMN_CANDIDATES = ["date", "dates", "timestamp", "day", "time"]
CLOSE_COLUMN_CANDIDATES = [
    "close", "close price", "px_last", "last price", "price",
    "btc", "btc/usd", "btcusd", "adj close",
]

# --------------------------------------------------------------------------
# Time clock: halving dates (UTC).
# The most recent halving <= a given date defines that date's "days since
# halving". The future entry just marks where the current cycle is expected
# to end; it is not used as a "past" anchor until it actually occurs.
# --------------------------------------------------------------------------
HALVINGS = [
    "2012-11-28",
    "2016-07-09",
    "2020-05-11",
    "2024-04-20",
    "2028-04-17",  # projected; update when the real date is known
]

# Nominal cycle length in days (~4 years). Used only for the progress %.
CYCLE_LENGTH_DAYS = 1458

# Expected-heat curve as (days_since_halving, heat 0-100) control points.
# This encodes the historical phase shape: quiet accumulation -> bull ->
# top window ~18-20 months -> markdown -> bottom ~32-40 months. np.interp
# draws a smooth line through these. Tune freely.
TIME_HEAT_CURVE = [
    (0,    25),   # halving day, accumulation begins
    (180,  35),   # ~6 months
    (365,  50),   # ~12 months, bull starting
    (480,  78),   # ~16 months
    (550,  95),   # ~18 months, top window opens
    (610, 100),   # ~20 months, peak zone
    (700,  82),   # markdown underway
    (820,  55),   # ~27 months
    (913,  38),   # ~30 months
    (1100, 20),   # ~36 months, bottom zone
    (1218, 12),   # ~40 months, capitulation trough
    (1458, 24),   # next halving approaches, re-accumulation
]

# --------------------------------------------------------------------------
# Valuation clock: each indicator maps a raw value to a 0-100 heat via a
# (low, high) range. low -> heat 0 (cheap / bottom), high -> heat 100
# (expensive / top). Values are clamped to [0, 100].
# Weights need not sum to 1; they are normalised across whichever indicators
# are available on a given row (early rows lack the 200-week SMA, etc.).
# --------------------------------------------------------------------------
VALUATION_INDICATORS = {
    "mayer_multiple": {  # close / 200-day SMA
        "low": 0.6, "high": 2.4, "weight": 1.0,
    },
    "drawdown_from_ath": {  # 0 at ATH, negative below. -0.85 ~ deep bear low
        "low": -0.85, "high": 0.0, "weight": 1.0,
    },
    "sma200w_ratio": {  # close / 200-week SMA (the historic bear floor)
        "low": 1.0, "high": 4.0, "weight": 1.0,
    },
    "pi_cycle_ratio": {  # 111d SMA / (2 * 350d SMA); ~1.0 flags a top
        "low": 0.5, "high": 1.0, "weight": 1.0,
    },
}

# --------------------------------------------------------------------------
# Combined clock: blend of time (calendar prior) and valuation (observed).
# Valuation carries more weight by default since the calendar is only a prior.
# --------------------------------------------------------------------------
COMBINED_WEIGHTS = {"time": 0.35, "valuation": 0.65}

# Shared interpretation bands for any 0-100 heat score.
HEAT_BANDS = [
    (0,   20, "Deep value / bottom zone"),
    (20,  40, "Accumulation / early cycle"),
    (40,  60, "Mid-cycle / markup"),
    (60,  80, "Late bull / elevated"),
    (80, 101, "Euphoria / top zone"),
]
