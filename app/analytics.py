from datetime import date, timedelta
import sqlite3
from app.pipeline import BASE, DB

NAMES = [
    "kpis",
    "monthly",
    "products",
    "countries",
    "repeat_customers",
    "rfm",
    "cohorts",
    "transactions",
]


def connect(path=DB):
    if not path.exists():
        raise ValueError("Run python -m app.bootstrap first.")
    c = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def query(name, start, end, country="All", path=DB):
    if name not in NAMES:
        raise ValueError("Unknown report.")
    a = date.fromisoformat(start)
    b = date.fromisoformat(end)
    if a > b:
        raise ValueError("Start date must be on or before end date.")
    if name == "cohorts" and country != "All":
        raise ValueError(
            "Cohorts use all countries to keep acquisition and denominator consistent. Select All."
        )
    params = {
        "start": a.isoformat(),
        "end": b.isoformat(),
        "until": (b + timedelta(days=1)).isoformat(),
        "country": country,
    }
    prefix = "WITH RECURSIVE filtered AS (SELECT * FROM fact_lines WHERE invoice_date>=:start AND invoice_date<:until AND (:country='All' OR country=:country)) "
    sql = (BASE / "sql" / f"{name}.sql").read_text()
    with connect(path) as c:
        return [dict(r) for r in c.execute(prefix + sql, params)]


def metadata(path=DB):
    with connect(path) as c:
        a, b = c.execute(
            "SELECT MIN(invoice_date),MAX(invoice_date) FROM invoices"
        ).fetchone()
        countries = [
            r[0]
            for r in c.execute("SELECT DISTINCT country FROM invoices ORDER BY country")
        ]
    return {
        "start": a[:10],
        "end": b[:10],
        "countries": countries,
        "reports": NAMES,
        "currency": "GBP",
    }
