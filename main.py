"""
Run the whole pipeline:

    python main.py

Steps: load the Excel data, run both independent clocks, blend them, write the
workbook and chart, and print the current cycle-position snapshot.
"""

from src import data_loader, time_clock, valuation_clock, combined_clock
from src import excel_writer, plotting


def run():
    # 1. Load
    df = data_loader.load_price_data()

    # 2. Independent clocks
    time_df = time_clock.compute_time_clock(df)
    valuation_df = valuation_clock.compute_valuation_clock(df)

    # 3. Combined clock
    combined_df = combined_clock.compute_combined_clock(time_df, valuation_df)
    snapshot = combined_clock.current_snapshot(df, time_df, valuation_df, combined_df)

    # 4. Outputs
    excel_writer.write_workbook(snapshot, time_df, valuation_df, combined_df)
    plotting.plot_clocks(time_df, valuation_df, combined_df)

    # 5. Console summary
    _print_snapshot(snapshot)
    return snapshot


def _print_snapshot(s: dict):
    val = s["valuation_heat"]
    val_str = f"{val:>5}" if val is not None else "  n/a"
    print("\n" + "=" * 48)
    print(f"  BTC cycle position as of {s['as_of']}")
    print("=" * 48)
    print(f"  Close price            ${s['close']:,.2f}")
    print(f"  Days since halving      {s['days_since_halving']:>5}  "
          f"({s['cycle_progress_pct']}% through cycle)")
    print(f"  Calendar phase          {s['phase']}")
    print("-" * 48)
    print(f"  Time clock heat         {s['time_heat']:>5}")
    print(f"  Valuation clock heat   {val_str}")
    print(f"  Combined position       {s['combined_heat']:>5}")
    print(f"  Interpretation          {s['band']}")
    print("=" * 48 + "\n")


if __name__ == "__main__":
    run()
