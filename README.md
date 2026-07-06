# BTC Cycle Position

Estimates where Bitcoin sits in its ~4-year halving cycle by combining two
*independent clocks* into a single 0–100 **cycle-position score**.

- **Time clock** — calendar only, in four canonical phases across three legs
  bracketed by halvings on both ends: **Accumulation → Expansion → Euphoria**
  (halving → top), **Correction** (top → bottom), then **Accumulation** again
  (bottom → next halving). It anchors on three events — the most recent halving,
  that cycle's *realised* top (`CYCLE_TOPS` in config), and the next halving —
  and stretches each leg to fit. Anchoring to the realised top keeps it in
  phase when a cycle tops early or late (2025 topped ~534 days out, past the
  ~480-day average); bracketing the tail to the next halving ties the
  re-accumulation leg back to the 4-year rhythm rather than letting it drift.
  The bottom is derived as top + the average top→bottom span (~12–13 months).
- **Valuation clock** — how stretched price is. Five indicators: four derived
  from price (Mayer Multiple, drawdown from ATH, 200-week SMA ratio, Pi Cycle
  ratio) plus **MVRV** (on-chain market-value-to-realized-value), each
  normalised to a 0–100 heat and weighted into one observed-heat number. MVRV
  is the only input not derived from price, so it carries independent signal
  and is weighted accordingly.
- **Combined clock** — a weighted blend of the two. Default 35% time / 65%
  valuation, because the calendar is only a prior; price and on-chain value are
  what's actually happening.

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

## MVRV (on-chain valuation)

MVRV is supplied as data rather than derived from price. Two ways to provide it,
and the loader handles both:

1. **Separate file (recommended).** Pull it with the included fetcher:

   ```bat
   python fetch_mvrv.py
   ```

   This downloads the full daily history of `CapMVRVCur` from the CoinMetrics
   community API (no API key required) and writes `data\mvrv.xlsx`. Then point
   `config.py` at it:

   ```python
   MVRV_EXCEL = DATA_DIR / "mvrv.xlsx"
   ```

   It merges onto the price history by date; where MVRV is missing (it usually
   starts later than the earliest price), those rows simply score on the
   price-only indicators.

2. **Column in your main file.** If your own workflow already exports MVRV,
   add an `MVRV` column to `btc_daily.xlsx` and the loader auto-detects it
   (leave `MVRV_EXCEL = None`).

If no MVRV is present at all, the valuation clock just runs on the four
price indicators — the combine step renormalises the weights automatically.

## Run

```bat
python main.py
```

Produces:

- `output\cycle_position.xlsx` — Summary + Time Clock + Valuation Clock +
  Combined Clock sheets
- `output\cycle_position.png` — all three heat series on one chart
- a printed snapshot of the current cycle position

A successful run with MVRV enabled prints **two** load lines — one for the
price file and one for `mvrv.xlsx`.

## Tune it

Everything adjustable lives in `config.py`: halving dates, the time-heat curve
control points, each indicator's normalisation range and weight (including
MVRV's `low`/`high`/`weight`), and the combined time/valuation split.

## Tests

```bat
pytest
```

## Extending: more on-chain indicators

MVRV is wired in; the same pattern adds others (Puell Multiple, NUPL, realized
price, ...). Add the raw series in `valuation_clock.compute_indicators` and a
matching entry in `config.VALUATION_INDICATORS`. Free daily source: the
CoinMetrics community API (see `fetch_mvrv.py` for the request pattern).

## Layout

```
btc-cycle-position/
├── config.py              # all tunable settings
├── main.py                # pipeline entry point
├── fetch_mvrv.py          # pull MVRV from CoinMetrics -> data/mvrv.xlsx
├── make_sample_data.py    # synthetic data for smoke-testing the install
├── requirements.txt
├── .gitignore
├── data/                  # input spreadsheets (git-ignored)
├── output/                # generated workbook + chart (git-ignored)
├── src/
│   ├── data_loader.py     # Excel -> clean DataFrame (+ optional MVRV merge)
│   ├── time_clock.py      # calendar-based heat
│   ├── valuation_clock.py # price + MVRV heat
│   ├── combined_clock.py  # blend + interpretation + snapshot
│   ├── excel_writer.py    # multi-sheet workbook
│   └── plotting.py        # three-line chart
└── tests/
    ├── test_time_clock.py
    └── test_valuation_clock.py
```

> Not investment advice. Cycle position is a probabilistic reference, not a
> timing signal. The time clock anchors to each cycle's realised top, which
> keeps it in phase, but it is still shaped by only three completed cycles and
> assumes a top→bottom span (~12–13 months) that may not repeat. A time curve
> also can't see *amplitude* — the 2025 top was the calmest on record even
> though its timing was textbook — so the valuation/on-chain clock is the more
> robust half. The 4-year cycle itself is increasingly debated as ETFs and
> corporate treasuries reshape demand. Treat the score as one input, not an
> oracle.
