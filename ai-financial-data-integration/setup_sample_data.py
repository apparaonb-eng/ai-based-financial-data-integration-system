"""Creates sample bank, card and ledger data (with overlaps, a foreign-currency item,
a bad row and one suspicious large payment)."""
import json
import sqlite3
from pathlib import Path

d = Path("sample_data")
d.mkdir(exist_ok=True)

(d / "bank_statement.csv").write_text(
    "Date,RefNo,Narration,Amount\n"
    "01/10/2026,B1,SALARY ACME CORP,\"85,000.00\"\n"
    "02/10/2026,B2,RENT TRANSFER LANDLORD,\"-25,000.00\"\n"
    "03/10/2026,B3,BIGBASKET GROCERY,-1850.40\n"
    "05/10/2026,B4,SWIGGY ORDER,-420.00\n"
    "07/10/2026,B5,UBER TRIP,-310.50\n"
    "09/10/2026,B6,AIRTEL BROADBAND,-999.00\n"
    "12/10/2026,B7,SWIGGY ORDER,-380.00\n"
    "15/10/2026,B8,WIRE TRANSFER UNKNOWN BENEFICIARY,\"-450,000.00\"\n"
    "18/10/2026,B9,BIGBASKET GROCERY,-2210.75\n"
    "20/10/2026,B10,APOLLO PHARMACY,-640.00\n"
    "not-a-date,B11,BROKEN ROW,-100\n"
)

(d / "card_statement.json").write_text(json.dumps({"transactions": [
    {"id": "K1", "posted": "2026-10-04", "merchant": "NETFLIX", "amt": 649.0, "ccy": "INR"},
    {"id": "K2", "posted": "2026-10-10", "merchant": "AMAZON MARKETPLACE", "amt": 3499.0, "ccy": "INR"},
    {"id": "K3", "posted": "2026-10-14", "merchant": "STARBUCKS CAFE", "amt": 6.5, "ccy": "USD"},
    {"id": "K4", "posted": "2026-10-16", "merchant": "SPOTIFY", "amt": 119.0, "ccy": "INR"},
    {"id": "K5", "posted": "2026-10-22", "merchant": "CINEMA TICKETS", "amt": 900.0, "ccy": "INR"},
]}, indent=2))

db = d / "ledger.db"
db.unlink(missing_ok=True)
with sqlite3.connect(db) as c:
    c.execute("CREATE TABLE entries (entry_id INTEGER PRIMARY KEY, entry_date TEXT, memo TEXT, value REAL)")
    c.executemany("INSERT INTO entries VALUES (?,?,?,?)", [
        (1, "2026-10-01", "Salary Acme Corp October", 85000.00),   # duplicate of bank B1
        (2, "2026-10-03", "BigBasket grocery order", -1850.40),   # duplicate of bank B3
        (3, "2026-10-21", "Electricity bill", -1420.00),
        (4, "2026-10-05", "Swiggy dinner", -420.00),               # duplicate of bank B4
    ])
print("Sample data created in sample_data/")
