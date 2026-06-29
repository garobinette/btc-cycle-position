# BTC Cycle Position

Estimates where Bitcoin sits in its ~4-year halving cycle by combining two
*independent clocks* into a single 0–100 **cycle-position score**.

- **Time clock** — calendar only. Days since the most recent halving, mapped
  onto an expected-heat curve that encodes the historical phase shape
  (accumulation → bull → top window → markdown → bottom).
- **Valuation clock** — price only. Four stretch indicators
  (Mayer Multiple, drawdown from ATH, 200-week SMA ratio, Pi Cycle ratio),
  each normalised to a 0–100 heat, then weighted into one observed-heat number.
- **Combined clock** — a weighted blend of the two. Default 35% time / 65%
  valuation, because the calendar is only a prior; price is what's actually
  happening.

A heat of **0** ≈ cycle bottom (deep value), **100** ≈ cycle top (euphoria).

## Setup (Windows)

```bat
cd btc-cycle-position
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Your data

Put a daily BTC/USD spreadsheet in `data\` and point `INPUT_EXCEL` in
`config.py` at it. The loader only needs:

- a **date** column (any of: Date, Timestamp, Day, ...)
- a **close/price** column (any of: Close, Price, PX_LAST, BTC/USD, ...)

Column names are matched case-insensitively, so a Bloomberg `PX_LAST` pull
works out of the box. Daily frequency, oldest-to-newest or newest-to-oldest
both fine (it sorts). For the 200-week SMA to populate you need ~4 years of
history; rows before that simply build the score from the indicators that are
available.

## Run

```bat
python main.py
```

Produces:

- `output\cycle_position.xlsx` — Summary + Time Clock + Valuation Clock +
  Combined Clock sheets
- `output\cycle_position.png` — all three heat series on one chart
- a printed snapshot of the current cycle position

## Tune it

Everything adjustable lives in `config.py`: halving dates, the time-heat
curve control points, each indicator's normalisation range and weight, and the
combined time/valuation split.

## Tests

```bat
pytest
```

## Extending: on-chain indicators

The valuation clock is built so MVRV, Puell Multiple, NUPL, etc. can be added
later. Add the raw series in `valuation_clock.compute_indicators` and a
matching entry in `config.VALUATION_INDICATORS`. Free daily source:
CoinMetrics community API.

## Layout

```
btc-cycle-position/
├── config.py              # all tunable settings
├── main.py                # pipeline entry point
├── requirements.txt
├── .gitignore
├── data/                  # your input spreadsheet (git-ignored)
├── output/                # generated workbook + chart (git-ignored)
├── src/
│   ├── data_loader.py     # Excel -> clean DataFrame
│   ├── time_clock.py      # calendar-based heat
│   ├── valuation_clock.py # price-based heat
│   ├── combined_clock.py  # blend + interpretation + snapshot
│   ├── excel_writer.py    # multi-sheet workbook
│   └── plotting.py        # three-line chart
└── tests/
    ├── test_time_clock.py
    └── test_valuation_clock.py
```

> Not investment advice. Cycle position is a probabilistic reference, not a
> timing signal — and the 4-year cycle itself is increasingly debated as ETFs
> and corporate treasuries reshape demand.
