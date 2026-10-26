"""Transaction categorisation.

Uses Claude when ANTHROPIC_API_KEY is set (one batched call over unique descriptions);
otherwise (or on any failure) falls back to keyword rules. AI output is validated against
a fixed category list.
"""
import json
import os

CATEGORIES = ["Salary", "Rent", "Groceries", "Dining", "Transport", "Utilities",
              "Shopping", "Entertainment", "Healthcare", "Transfer", "Other"]

MODEL = "claude-sonnet-5-5"

KEYWORDS = {
    "Salary": ["salary", "payroll"],
    "Rent": ["rent", "landlord"],
    "Groceries": ["bigbasket", "grocery", "supermarket", "dmart"],
    "Dining": ["swiggy", "zomato", "restaurant", "cafe", "starbucks"],
    "Transport": ["uber", "ola", "metro", "fuel", "petrol"],
    "Utilities": ["electricity", "broadband", "airtel", "water bill", "gas"],
    "Shopping": ["amazon", "flipkart", "myntra"],
    "Entertainment": ["netflix", "spotify", "cinema", "movie"],
    "Healthcare": ["pharmacy", "hospital", "clinic", "apollo"],
    "Transfer": ["transfer", "wire", "neft", "imps", "upi"],
}


def rule_category(description: str) -> str:
    d = description.lower()
    for cat, words in KEYWORDS.items():
        if any(w in d for w in words):
            return cat
    return "Other"


def _claude_categories(descriptions: list[str]) -> dict[str, str]:
    import anthropic

    prompt = (
        "Categorise each bank transaction description into exactly one of: "
        f"{CATEGORIES}.\nReturn ONLY a JSON object mapping each description to its category.\n"
        f"Descriptions:\n{json.dumps(descriptions)}"
    )
    msg = anthropic.Anthropic().messages.create(
        model=MODEL, max_tokens=2000, messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    raw = json.loads(text)
    return {d: c for d, c in raw.items() if d in descriptions and c in CATEGORIES}


def categorise(txns: list[dict], use_ai: bool = True) -> str:
    """Adds 'category' and 'category_by' to each transaction. Returns 'claude' or 'rules'."""
    unique = sorted({t["description"] for t in txns})
    ai_map: dict[str, str] = {}
    method = "rules"
    if use_ai and os.getenv("ANTHROPIC_API_KEY"):
        try:
            ai_map = _claude_categories(unique)
            method = "claude"
        except Exception as e:
            print(f"  [categoriser] AI call failed ({e}); using rules.")
    for t in txns:
        if t["description"] in ai_map:
            t["category"], t["category_by"] = ai_map[t["description"]], "claude"
        else:
            t["category"], t["category_by"] = rule_category(t["description"]), "rules"
    return method
