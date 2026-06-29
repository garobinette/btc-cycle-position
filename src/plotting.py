"""
Chart the three heat series on one figure so the two independent clocks and
their blend are visible together. Saved as a PNG in output/.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless / no display needed
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import config


def plot_clocks(time_df, valuation_df, combined_df, path: Path = None) -> Path:
    path = Path(path or config.OUTPUT_CHART)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(13, 6))

    # Faint band shading for context (bottom / mid / top zones).
    band_colors = ["#1d9e75", "#9fe1cb", "#fac775", "#ef9f27", "#e24b4a"]
    for (low, high, _label), color in zip(config.HEAT_BANDS, band_colors):
        ax.axhspan(low, min(high, 100), color=color, alpha=0.08)

    ax.plot(time_df.index, time_df["time_heat"],
            label="Time clock (calendar)", color="#378add", linewidth=1.3)
    ax.plot(valuation_df.index, valuation_df["valuation_heat"],
            label="Valuation clock (price)", color="#d85a30", linewidth=1.3)
    ax.plot(combined_df.index, combined_df["combined_heat"],
            label="Combined cycle position", color="#26215c", linewidth=2.2)

    ax.set_ylim(0, 100)
    ax.set_ylabel("Cycle heat (0 = bottom, 100 = top)")
    ax.set_title("BTC cycle position - time vs valuation vs combined")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)

    print(f"Wrote chart -> {path}")
    return path
