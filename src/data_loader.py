"""
Load daily BTC/USD data from an Excel file into a clean, sorted DataFrame.

Output contract: a DataFrame indexed by a tz-naive DatetimeIndex (daily,
ascending) with at least a float column named "close". Extra columns are
preserved if present but never required.
"""

from pathlib import Path

import pandas as pd

import config


def _find_column(columns, candidates):
    """Return the actual column whose lowercased name matches a candidate."""
    lookup = {str(c).strip().lower(): c for c in columns}
    for cand in candidates:
        if cand in lookup:
            return lookup[cand]
    return None


def load_price_data(path: Path = None, sheet=None) -> pd.DataFrame:
    """Read the Excel workbook and normalise it.

    Raises a clear error if the file is missing, open in Excel (Windows lock),
    or missing a usable date/price column.
    """
    path = Path(path or config.INPUT_EXCEL)
    sheet = config.INPUT_SHEET if sheet is None else sheet

    if not path.exists():
        raise FileNotFoundError(
            f"No input file at {path}\n"
            f"Put your spreadsheet in the data/ folder and set INPUT_EXCEL "
            f"in config.py to its filename."
        )

    try:
        raw = pd.read_excel(path, sheet_name=sheet)
    except PermissionError:
        # The classic Windows gotcha: the workbook is open in Excel.
        raise PermissionError(
            f"Could not read {path.name} - it looks like the file is open in "
            f"Excel. Close it and run again."
        )

    date_col = _find_column(raw.columns, config.DATE_COLUMN_CANDIDATES)
    close_col = _find_column(raw.columns, config.CLOSE_COLUMN_CANDIDATES)

    if date_col is None:
        raise ValueError(
            f"Couldn't find a date column. Looked for "
            f"{config.DATE_COLUMN_CANDIDATES}. Columns present: "
            f"{list(raw.columns)}"
        )
    if close_col is None:
        raise ValueError(
            f"Couldn't find a price column. Looked for "
            f"{config.CLOSE_COLUMN_CANDIDATES}. Columns present: "
            f"{list(raw.columns)}"
        )

    df = pd.DataFrame()
    df["date"] = pd.to_datetime(raw[date_col], errors="coerce")
    df["close"] = pd.to_numeric(raw[close_col], errors="coerce")

    # Drop unparseable rows, sort, de-duplicate dates, set the index.
    df = df.dropna(subset=["date", "close"]).sort_values("date")
    df = df.drop_duplicates(subset="date", keep="last")
    df = df.set_index("date")

    # Strip any timezone so comparisons against naive halving dates are clean.
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    if df.empty:
        raise ValueError("After cleaning, no valid rows remained. Check the file.")

    print(
        f"Loaded {len(df):,} rows from {path.name} "
        f"({df.index.min().date()} -> {df.index.max().date()}), "
        f"price column '{close_col}'."
    )
    return df
