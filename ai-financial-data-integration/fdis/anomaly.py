"""Anomaly detection: robust (median/MAD) z-score on log-scaled expense amounts."""
import math
import statistics

EXEMPT = {"Rent", "Salary"}  # large but expected
THRESHOLD = 3.5


def flag_anomalies(txns: list[dict]) -> int:
    expenses = [t for t in txns if t["amount_base"] < 0 and t["category"] not in EXEMPT]
    for t in txns:
        t["anomaly"] = False
        t["anomaly_reason"] = None
    if len(expenses) < 5:
        return 0
    logs = [math.log1p(abs(t["amount_base"])) for t in expenses]
    med = statistics.median(logs)
    mad = statistics.median(abs(x - med) for x in logs) or 1e-9
    count = 0
    for t, x in zip(expenses, logs):
        z = 0.6745 * (x - med) / mad
        if z > THRESHOLD:
            t["anomaly"] = True
            t["anomaly_reason"] = f"unusually large expense (robust z={z:.1f})"
            count += 1
    return count
