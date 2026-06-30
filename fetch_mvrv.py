"""
Fetch BTC MVRV (CapMVRVCur) from the CoinMetrics community API and write it to
data/mvrv.xlsx, ready for the valuation clock to merge by date.

Run:
    python fetch_mvrv.py

Then make sure MVRV_EXCEL in config.py points at the file (it defaults the
output to data/mvrv.xlsx) and run main.py. No API key is needed - CapMVRVCur
is a free community metric.
"""

import sys
import time

import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("Missing dependency 'requests'. Run: pip install -r requirements.txt")

import config

API_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ASSET = "btc"
METRIC = "CapMVRVCur"   # market value / realized value (the MVRV ratio)


def fetch_rows() -> list:
    """Pull all daily MVRV rows, following pagination until exhausted."""
    params = {
        "assets": ASSET,
        "metrics": METRIC,
        "frequency": "1d",
        "page_size": 10000,
    }
    rows, page = [], 1
    resp = requests.get(API_URL, params=params, timeout=30)
    while True:
        resp.raise_for_status()
        payload = resp.json()

        # The API reports problems in a "error" field rather than always via HTTP status.
        if "error" in payload:
            raise RuntimeError(f"CoinMetrics error: {payload['error']}")

        data = payload.get("data", [])
        rows.extend(data)
        print(f"  page {page}: +{len(data)} rows (total {len(rows)})")

        next_url = payload.get("next_page_url")
        if not next_url:
            break
        time.sleep(0.25)  # be polite to the community endpoint
        resp = requests.get(next_url, timeout=30)
        page += 1

    return rows


def to_frame(rows: list) -> pd.DataFrame:
    """Normalise the raw API rows to a tidy (date, mvrv) frame, tz-stripped."""
    df = pd.DataFrame(rows)
    if df.empty or METRIC not in df.columns:
        raise RuntimeError(
            f"No '{METRIC}' values returned. Got columns: {list(df.columns)}"
        )

    out = pd.DataFrame({
        # API times look like 2010-07-19T00:00:00.000000000Z (UTC).
        "date": pd.to_datetime(df["time"], utc=True).dt.tz_localize(None).dt.normalize(),
        "mvrv": pd.to_numeric(df[METRIC], errors="coerce"),
    })
    out = out.dropna().sort_values("date").drop_duplicates("date", keep="last")
    return out.reset_index(drop=True)


def write_excel(out: pd.DataFrame):
    """Write to the configured MVRV path (default data/mvrv.xlsx)."""
    path = config.MVRV_EXCEL or (config.DATA_DIR / "mvrv.xlsx")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.to_excel(path, index=False)
    except PermissionError:
        sys.exit(f"Could not write {path.name} - it's open in Excel. Close it and rerun.")
    print(
        f"Wrote {len(out):,} MVRV rows -> {path} "
        f"({out['date'].min().date()} -> {out['date'].max().date()})"
    )
    if config.MVRV_EXCEL is None:
        print('Reminder: set MVRV_EXCEL = DATA_DIR / "mvrv.xlsx" in config.py, '
              "then run main.py.")


def main():
    print("Fetching BTC MVRV (CapMVRVCur) from CoinMetrics community API...")
    try:
        rows = fetch_rows()
    except requests.exceptions.RequestException as exc:
        sys.exit(f"Network error talking to CoinMetrics: {exc}")
    out = to_frame(rows)
    write_excel(out)


if __name__ == "__main__":
    main()
