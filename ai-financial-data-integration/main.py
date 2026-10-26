"""CLI entry point.

Usage:
    python setup_sample_data.py
    python main.py                 # uses Claude if ANTHROPIC_API_KEY is set
    python main.py --no-ai         # keyword rules only
"""
import argparse
import json

from fdis.pipeline import run


def main():
    ap = argparse.ArgumentParser(description="AI-Based Financial Data Integration System")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--db", default="finance.db")
    ap.add_argument("--out", default="output")
    ap.add_argument("--no-ai", action="store_true", help="Skip Claude, use keyword rules")
    a = ap.parse_args()

    with open(a.config, encoding="utf-8") as f:
        config = json.load(f)

    s = run(config, a.db, a.out, use_ai=not a.no_ai)

    print(f"\n=== Summary ({s['base_currency']}) ===")
    print(f"Transactions: {s['transactions']}  (duplicates merged: {s['duplicates_merged']})")
    print(f"Income: {s['total_income']:,.2f}   Spend: {s['total_spend']:,.2f}   Net: {s['net']:,.2f}")
    print("By category:")
    for cat, v in s["by_category"].items():
        print(f"  {cat:<14}{v:>14,.2f}")
    if s["anomalies"]:
        print("Anomalies:")
        for an in s["anomalies"]:
            print(f"  {an['date']}  {an['description']}  {an['amount_base']:,.2f}  ({an['anomaly_reason']})")
    for w in s["warnings"]:
        print("Warning:", w)


if __name__ == "__main__":
    main()
