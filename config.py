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

# Optional MVRV (on-chain market-value-to-realized-value ratio). Supply it
# either way - the loader handles both:
#   1. Add an MVRV column to your main btc_daily.xlsx (auto-detected), OR
#   2. Point MVRV_EXCEL at a separate export; it merges onto price by date.
# If neither is present the valuation clock just runs on the price-only
# indicators (the combine step renormalises weights automatically).
MVRV_COLUMN_CANDIDATES = [
    "mvrv", "mvrv ratio", "mvrv_ratio", "capmvrvcur",
    "market value to realized value",
]
MVRV_EXCEL = DATA_DIR / "mvrv.xlsx"   # set to None to disable the separate file
MVRV_SHEET = 0

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

# Cycle length in days. Protocol target is 1458 (210k blocks x 10 min), but the
# realised average halving-to-halving interval has been ~1388 days because
# blocks arrive slightly faster than 10 min on average. Used only for the
# progress %, so we use the empirical figure for consistency with the curve.
CYCLE_LENGTH_DAYS = 1388

# --------------------------------------------------------------------------
# Time clock anchoring.
# The clock stretches to fit each cycle's REALISED top rather than assuming a
# fixed day. Pre-top phases scale to the actual halving->top span; post-top
# phases scale to the average top->bottom span (~12-13 months). This keeps the
# clock in phase when a cycle tops early or late (2025 topped ~534 days out,
# well past the ~480-day average).
# Realised cycle tops (update the last entry if a new high forms):
CYCLE_TOPS = [
    "2013-11-30",   # ~$1.1k
    "2017-12-17",   # ~$19.7k
    "2021-11-10",   # ~$69k
    "2025-10-06",   # $124,824 (current cycle ATH)
]
# Fallbacks used when a cycle's top hasn't formed yet (no CYCLE_TOPS entry):
AVG_HALVING_TO_TOP_DAYS = 480   # average halving -> top (367/526/547)
AVG_TOP_TO_BOTTOM_DAYS = 380    # average top -> bottom (~12-13 months)

# Normalised heat curves. The four canonical phases live on three legs, and the
# cycle is bracketed by halvings on BOTH ends: halving -> top -> next halving.
# PRE-TOP: x = fraction of the halving->top span (0 = halving, 1.0 = top).
PRETOP_HEAT_CURVE = [
    (0.00,  20),   # halving: accumulation
    (0.30,  32),   # accumulation
    (0.55,  50),   # expansion begins
    (0.80,  72),   # expansion
    (0.92,  90),   # euphoria
    (1.00, 100),   # the top
]
# CORRECTION: x = fraction of the top->bottom span (0 = top, 1.0 = bottom).
# Bottom is derived as top + AVG_TOP_TO_BOTTOM_DAYS.
CORRECTION_HEAT_CURVE = [
    (0.00, 100),   # the top
    (0.50,  45),   # correction underway
    (0.80,  20),   # approaching the bottom
    (1.00,  10),   # the bottom
]
# RE-ACCUMULATION: x = fraction of the bottom->next-halving span (0 = bottom,
# 1.0 = next halving). This is the leg that re-anchors the tail to the halving.
REACCUM_HEAT_CURVE = [
    (0.00, 10),    # the bottom
    (0.40, 18),    # recovery / accumulation
    (1.00, 24),    # next halving: the cycle closes where it began
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
    "mvrv": {  # on-chain market cap / realized cap. <1 = bottom, >3.5 = top.
        # Weighted heavier than the price metrics on purpose: it's the only
        # indicator not derived from price, so it carries independent signal.
        "low": 0.8, "high": 3.5, "weight": 1.5,
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
