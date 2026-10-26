"""Pipeline: extract -> normalise -> dedupe -> categorise -> anomaly check -> load + report."""
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from .anomaly import flag_anomalies
from .categorizer import categorise
from .connectors import fetch
from .dedupe import deduplicate
from .normalizer import DEFAULT_RATES, normalise

COLUMNS = ["date", "description", "amount", "currency", "amount_base", "category",
           "category_by", "sources", "anomaly", "anomaly_reason"]


def run(config: dict, db_path: str, out_dir: str, use_ai: bool = True) -> dict:
    base = config.get("base_currency", "INR")
    rates = {**DEFAULT_RATES, **config.get("rates", {})}
    all_txns, warnings = [], []

    print("[1/5] Extracting and normalising")
    for src in config["sources"]:
        raw = fetch(src)
        txns, warn = normalise(raw, src, rates, base)
        print(f"      {src['name']:<8} {len(raw):>3} raw -> {len(txns):>3} valid")
        all_txns += txns
        warnings += warn
    all_txns.sort(key=lambda t: t["date"])

    print("[2/5] Removing cross-source duplicates")
    txns, dupes = deduplicate(all_txns)
    print(f"      {dupes} duplicates merged")

    print("[3/5] Categorising")
    method = categorise(txns, use_ai)
    print(f"      method: {method}")

    print("[4/5] Detecting anomalies")
    n_anom = flag_anomalies(txns)
    print(f"      {n_anom} flagged")

    print("[5/5] Loading")
    Path(out_dir).mkdir(exist_ok=True)
    csv_path = Path(out_dir) / "transactions.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(txns)

    with sqlite3.connect(db_path) as db:
        db.execute("DROP TABLE IF EXISTS transactions")
        db.execute("CREATE TABLE transactions (date TEXT, description TEXT, amount REAL, currency TEXT, "
                   "amount_base REAL, category TEXT, category_by TEXT, sources TEXT, anomaly INTEGER, "
                   "anomaly_reason TEXT)")
        db.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?)",
                       [tuple(t.get(c) for c in COLUMNS) for t in txns])

    by_cat = defaultdict(float)
    for t in txns:
        by_cat[t["category"]] += t["amount_base"]
    income = sum(t["amount_base"] for t in txns if t["amount_base"] > 0)
    spend = -sum(t["amount_base"] for t in txns if t["amount_base"] < 0)
    summary = {
        "base_currency": base,
        "transactions": len(txns),
        "duplicates_merged": dupes,
        "total_income": round(income, 2),
        "total_spend": round(spend, 2),
        "net": round(income - spend, 2),
        "by_category": {k: round(v, 2) for k, v in sorted(by_cat.items(), key=lambda kv: kv[1])},
        "anomalies": [{k: t[k] for k in ("date", "description", "amount_base", "anomaly_reason")}
                      for t in txns if t["anomaly"]],
        "warnings": warnings,
        "categoriser": method,
    }
    (Path(out_dir) / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary
