"""
Write results to a multi-sheet workbook:

  Summary           - the current-date snapshot (one row of headline numbers)
  Time Clock        - daily days-since-halving, progress %, time heat, phase
  Valuation Clock   - daily raw indicators + per-indicator heat + valuation heat
  Combined Clock    - daily time / valuation / combined heat + band
"""

from pathlib import Path

import pandas as pd

import config


def _summary_frame(snapshot: dict) -> pd.DataFrame:
    """Turn the snapshot dict into a tidy two-column (Metric, Value) frame."""
    labels = {
        "as_of": "As of",
        "close": "Close price (USD)",
        "days_since_halving": "Days since halving",
        "cycle_progress_pct": "Cycle progress (%)",
        "phase": "Calendar phase",
        "time_heat": "Time clock heat (0-100)",
        "valuation_heat": "Valuation clock heat (0-100)",
        "combined_heat": "Combined cycle position (0-100)",
        "band": "Interpretation",
    }
    rows = [(labels[k], snapshot.get(k)) for k in labels]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def write_workbook(snapshot, time_df, valuation_df, combined_df,
                   path: Path = None) -> Path:
    path = Path(path or config.OUTPUT_EXCEL)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(path, engine="openpyxl") as xl:
            _summary_frame(snapshot).to_excel(xl, sheet_name="Summary", index=False)
            time_df.to_excel(xl, sheet_name="Time Clock")
            valuation_df.to_excel(xl, sheet_name="Valuation Clock")
            combined_df.to_excel(xl, sheet_name="Combined Clock")
            _autosize(xl)
    except PermissionError:
        raise PermissionError(
            f"Could not write {path.name} - it's probably open in Excel. "
            f"Close it and run again."
        )

    print(f"Wrote workbook -> {path}")
    return path


def _autosize(xl):
    """Best-effort column width fit so the output is readable on open."""
    for ws in xl.book.worksheets:
        for col in ws.columns:
            width = max(
                (len(str(c.value)) for c in col if c.value is not None),
                default=10,
            )
            letter = col[0].column_letter
            ws.column_dimensions[letter].width = min(width + 2, 40)
