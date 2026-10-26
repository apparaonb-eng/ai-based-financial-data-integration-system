"""Cross-source duplicate detection: same date + same base amount + a shared description word."""
import re


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def deduplicate(txns: list[dict]) -> tuple[list[dict], int]:
    """Keep the first record seen (source order in config = priority) and merge sources."""
    kept: list[dict] = []
    index: dict[tuple, list[dict]] = {}
    dupes = 0
    for t in txns:
        key = (t["date"], round(t["amount_base"], 0))
        match = None
        for cand in index.get(key, []):
            if t["source"] in cand["sources"].split(","):
                continue  # same source: a genuine repeat purchase, not a duplicate
            if _tokens(t["description"]) & _tokens(cand["description"]):
                match = cand
                break
        if match:
            match["sources"] += "," + t["source"]
            dupes += 1
        else:
            t = {**t, "sources": t["source"]}
            kept.append(t)
            index.setdefault(key, []).append(t)
    return kept, dupes
