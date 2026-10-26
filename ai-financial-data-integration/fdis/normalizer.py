"""Normalise raw records into one transaction schema in a base currency."""
from datetime import datetime

# Static demo rates to the base currency (INR). Replace with a live FX feed in production.
DEFAULT_RATES = {"INR": 1.0, "USD": 83.0, "EUR": 90.0, "GBP": 105.0}


def parse_amount(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")  # accounting style (123.45)
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_date(value, fmt: str) -> str | None:
    try:
        return datetime.strptime(str(value).strip(), fmt).strftime("%Y-%m-%d")
    except ValueError:
        return None


def normalise(records: list[dict], src: dict, rates: dict, base: str) -> tuple[list[dict], list[str]]:
    """Return (transactions, warnings)."""
    m = src["mapping"]
    out, warnings = [], []
    for i, r in enumerate(records, 1):
        date = parse_date(r.get(m["date"]), src.get("date_format", "%Y-%m-%d"))
        amount = parse_amount(r.get(m["amount"]))
        ccy = (str(r.get(m["currency"])).strip().upper() if "currency" in m and r.get(m["currency"])
               else src.get("default_currency", base))
        if date is None or amount is None or ccy not in rates:
            warnings.append(f"{src['name']} row {i}: skipped (bad date/amount/currency)")
            continue
        if src.get("expenses_positive"):  # some systems store spend as positive numbers
            amount = -amount
        out.append({
            "source": src["name"],
            "source_ref": str(r.get(m.get("ref", ""), "")) or None,
            "date": date,
            "description": str(r.get(m["description"], "")).strip(),
            "amount": round(amount, 2),
            "currency": ccy,
            "amount_base": round(amount * rates[ccy], 2),
        })
    return out, warnings
