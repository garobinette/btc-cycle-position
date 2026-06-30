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

    # Optional: MVRV column living in the same file.
    mvrv_col = _find_column(raw.columns, config.MVRV_COLUMN_CANDIDATES)
    if mvrv_col is not None:
        df["mvrv"] = pd.to_numeric(raw[mvrv_col], errors="coerce")

    # Drop rows missing date or price (but NOT missing mvrv - it may be partial).
    df = df.dropna(subset=["date", "close"]).sort_values("date")
    df = df.drop_duplicates(subset="date", keep="last")
    df = df.set_index("date")

    # Strip any timezone so comparisons against naive halving dates are clean.
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    if df.empty:
        raise ValueError("After cleaning, no valid rows remained. Check the file.")

    mvrv_note = f", mvrv column '{mvrv_col}'" if mvrv_col is not None else ""
    print(
        f"Loaded {len(df):,} rows from {path.name} "
        f"({df.index.min().date()} -> {df.index.max().date()}), "
        f"price column '{close_col}'{mvrv_note}."
    )
    return df


def load_mvrv_file(path=None, sheet=None) -> pd.Series:
    """Load a separate MVRV export into a date-indexed Series named 'mvrv'.

    Returns None if MVRV_EXCEL isn't configured or the file is absent, so the
    pipeline silently runs price-only in that case.
    """
    path = config.MVRV_EXCEL if path is None else path
    if path is None:
        return None

    path = Path(path)
    if not path.exists():
        print(f"MVRV file {path.name} not found - running without MVRV.")
        return None

    sheet = config.MVRV_SHEET if sheet is None else sheet
    try:
        raw = pd.read_excel(path, sheet_name=sheet)
    except PermissionError:
        raise PermissionError(
            f"Could not read {path.name} - it's open in Excel. Close it and rerun."
        )

    date_col = _find_column(raw.columns, config.DATE_COLUMN_CANDIDATES)
    mvrv_col = _find_column(raw.columns, config.MVRV_COLUMN_CANDIDATES)
    if date_col is None or mvrv_col is None:
        raise ValueError(
            f"MVRV file needs a date column and an MVRV column. Found: "
            f"{list(raw.columns)}"
        )

    s = pd.DataFrame({
        "date": pd.to_datetime(raw[date_col], errors="coerce"),
        "mvrv": pd.to_numeric(raw[mvrv_col], errors="coerce"),
    }).dropna().sort_values("date").drop_duplicates("date", keep="last")
    s = s.set_index("date")["mvrv"]
    if s.index.tz is not None:
        s.index = s.index.tz_localize(None)

    print(f"Loaded {len(s):,} MVRV rows from {path.name} "
          f"({s.index.min().date()} -> {s.index.max().date()}).")
    return s


def attach_mvrv(price_df: pd.DataFrame, mvrv_series: pd.Series) -> pd.DataFrame:
    """Align an MVRV Series onto the price frame by date (left join)."""
    if mvrv_series is None:
        return price_df
    out = price_df.copy()
    out["mvrv"] = mvrv_series.reindex(out.index)
    return out
