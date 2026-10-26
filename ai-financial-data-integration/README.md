# AI-Based Financial Data Integration System (base)

Integrates financial data from several systems into one clean, categorised transaction table.

```
bank CSV ─┐
card JSON ─┼─> normalise (dates, amounts, currency -> base) -> dedupe across sources
ledger DB ─┘      -> AI categorise (Claude or rules) -> anomaly detection -> SQLite + CSV + summary
```

## Run
```bash
python setup_sample_data.py
python main.py --no-ai                 # keyword rules, no dependencies
pip install -r requirements.txt        # optional
export ANTHROPIC_API_KEY=...           # enables Claude categorisation
python main.py
```
Outputs: `finance.db` (table `transactions`), `output/transactions.csv`, `output/summary.json`.

## What each part does
- `fdis/connectors.py` reads CSV / JSON / SQLite sources (configured in `config.json`).
- `fdis/normalizer.py` parses dates and amounts (including `1,234.00` and `(123.00)`), converts to the base currency using static demo rates, and skips bad rows with a warning.
- `fdis/dedupe.py` merges the same transaction reported by different systems (same date, same amount, shared description word).
- `fdis/categorizer.py` asks Claude to categorise unique descriptions in one call; the answer is validated against a fixed category list, and keyword rules cover anything it misses or if no API key is set.
- `fdis/anomaly.py` flags unusually large expenses with a robust (median/MAD) z-score.

## Notes
- FX rates in `config.json` are static demo values; plug in a live rates API for real use.
- Only descriptions are sent to Claude (no account numbers or balances). Review your data policy before using real financial data with any external API.
- Add a source by adding an entry to `sources` with its field mapping.
