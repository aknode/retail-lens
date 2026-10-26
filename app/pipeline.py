"""Idempotent normalized retail warehouse build with an atomic publish."""

from pathlib import Path
import sqlite3, os
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[1]
DB = BASE / "artifacts/retail.sqlite"
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE customers(customer_id TEXT PRIMARY KEY);
CREATE TABLE products(stock_code TEXT PRIMARY KEY,description TEXT NOT NULL);
CREATE TABLE invoices(invoice_no TEXT PRIMARY KEY,customer_id TEXT REFERENCES customers,
 invoice_date TEXT NOT NULL,country TEXT NOT NULL,is_cancellation INTEGER NOT NULL CHECK(is_cancellation IN (0,1)));
CREATE TABLE invoice_lines(line_id INTEGER PRIMARY KEY,invoice_no TEXT NOT NULL REFERENCES invoices,
 stock_code TEXT NOT NULL REFERENCES products,quantity INTEGER NOT NULL CHECK(quantity<>0),
 unit_price REAL NOT NULL CHECK(unit_price>0),line_timestamp TEXT NOT NULL);
CREATE INDEX idx_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_invoice_customer ON invoices(customer_id);
CREATE INDEX idx_invoice_country ON invoices(country);
CREATE INDEX idx_lines_invoice ON invoice_lines(invoice_no);
CREATE VIEW fact_lines AS SELECT l.*,i.customer_id,l.line_timestamp AS invoice_date,i.country,i.is_cancellation,p.description,
 CASE WHEN i.is_cancellation=1 OR l.quantity<0 THEN -ABS(l.quantity*l.unit_price)
 ELSE l.quantity*l.unit_price END AS net_amount,
 CASE WHEN i.is_cancellation=0 AND l.quantity>0 THEN l.quantity*l.unit_price ELSE 0 END AS gross_amount,
 CASE WHEN i.is_cancellation=1 OR l.quantity<0 THEN ABS(l.quantity*l.unit_price) ELSE 0 END AS return_amount
 FROM invoice_lines l JOIN invoices i USING(invoice_no) JOIN products p USING(stock_code);
"""


def build(frame, db_path=DB):
    required = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]
    if set(required) - set(frame):
        raise ValueError("Missing retail source columns.")
    raw = frame[required].copy()
    total = len(raw)
    duplicates = int(raw.duplicated().sum())
    raw = raw.drop_duplicates()
    raw["InvoiceDate"] = pd.to_datetime(
        raw.InvoiceDate, errors="coerce", format="mixed"
    )
    for c in ["Quantity", "UnitPrice"]:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    valid = (
        raw.InvoiceNo.notna()
        & raw.StockCode.notna()
        & raw.Country.notna()
        & raw.InvoiceDate.notna()
        & np.isfinite(raw.Quantity)
        & np.isfinite(raw.UnitPrice)
        & raw.Quantity.ne(0)
        & raw.UnitPrice.gt(0)
        & raw.Quantity.eq(raw.Quantity.round())
    )
    invalid = int((~valid).sum())
    raw = raw[valid].copy()
    if raw.empty:
        raise ValueError("No valid transactions remain.")
    raw["InvoiceNo"] = raw.InvoiceNo.astype(str)
    raw["StockCode"] = raw.StockCode.astype(str)
    raw["customer_id"] = raw.CustomerID.map(
        lambda v: (
            None
            if pd.isna(v)
            else str(int(v))
            if isinstance(v, (int, float))
            else str(v)
        )
    )
    raw["invoice_date"] = raw.InvoiceDate.dt.strftime("%Y-%m-%d %H:%M:%S")
    raw["Description"] = (
        raw.Description.fillna("Description unavailable").astype(str).str.strip()
    )
    raw["Country"] = raw.Country.astype(str)
    # Source invoices can span several line timestamps. Preserve those timestamps;
    # the header records the earliest one. Customer and country must be consistent.
    checks = raw.groupby("InvoiceNo")[["customer_id", "Country"]].nunique(dropna=False)
    if (checks > 1).any().any():
        raise ValueError("Inconsistent invoice dimensions in source.")
    timestamp_counts = raw.groupby("InvoiceNo").invoice_date.nunique()
    first_timestamp = raw.groupby("InvoiceNo").invoice_date.min()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    try:
        with sqlite3.connect(tmp) as con:
            con.executescript(SCHEMA)
            con.executemany(
                "INSERT INTO customers VALUES (?)",
                [(v,) for v in raw.customer_id.dropna().unique()],
            )
            products = raw.groupby("StockCode", sort=False).Description.agg(
                lambda s: (
                    s.mode().iloc[0]
                    if not s.mode().empty
                    else "Description unavailable"
                )
            )
            con.executemany("INSERT INTO products VALUES (?,?)", list(products.items()))
            inv = raw.drop_duplicates("InvoiceNo")
            con.executemany(
                "INSERT INTO invoices VALUES (?,?,?,?,?)",
                [
                    (
                        r.InvoiceNo,
                        r.customer_id,
                        first_timestamp[r.InvoiceNo],
                        r.Country,
                        int(r.InvoiceNo.upper().startswith("C")),
                    )
                    for r in inv.itertuples()
                ],
            )
            con.executemany(
                "INSERT INTO invoice_lines(invoice_no,stock_code,quantity,unit_price,line_timestamp) VALUES (?,?,?,?,?)",
                [
                    (
                        r.InvoiceNo,
                        r.StockCode,
                        int(r.Quantity),
                        float(r.UnitPrice),
                        r.invoice_date,
                    )
                    for r in raw.itertuples()
                ],
            )
            con.commit()
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Foreign key violations.")
            stats = dict(
                zip(
                    ["gross_sales", "returns", "net_revenue"],
                    con.execute(
                        "SELECT SUM(gross_amount),SUM(return_amount),SUM(net_amount) FROM fact_lines"
                    ).fetchone(),
                )
            )
            if not np.isclose(
                stats["gross_sales"] - stats["returns"], stats["net_revenue"], atol=0.01
            ):
                raise ValueError("Revenue reconciliation failed.")
            report = {
                "source_rows": total,
                "duplicate_rows_removed": duplicates,
                "invalid_rows_removed": invalid,
                "loaded_rows": len(raw),
                "invoices": len(inv),
                "customers": int(raw.customer_id.nunique()),
                "products": len(products),
                "invoices_with_multiple_timestamps": int((timestamp_counts > 1).sum()),
                "anonymous_line_rows": int(raw.customer_id.isna().sum()),
                "date_min": str(raw.InvoiceDate.min()),
                "date_max": str(raw.InvoiceDate.max()),
                "reconciliation": stats,
                "foreign_key_violations": 0,
                "currency": "GBP",
                "data": "UCI Online Retail historical transactions",
                "checks": [
                    "exact duplicate removal",
                    "positive finite unit price",
                    "nonzero integer quantity",
                    "valid invoice dimensions",
                    "foreign keys",
                    "gross minus returns equals net",
                ],
            }
        os.replace(tmp, db_path)
        return report
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
