from pathlib import Path
import tempfile, unittest, sqlite3
import pandas as pd
from app.pipeline import build
from app.analytics import query


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.sqlite"
        self.rows = [
            ["1", "A", "Apple", 2, "2021-01-01", 10, 1, "UK"],
            ["2", "A", "Apple", 1, "2021-02-01", 10, 1, "UK"],
            ["C3", "A", "Apple", -1, "2021-02-02", 10, 1, "UK"],
            ["4", "B", "Book", 1, "2021-02-03", 20, None, "France"],
        ]
        self.columns = [
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
        ]
        self.quality = build(
            pd.DataFrame(self.rows + [self.rows[0]], columns=self.columns), self.db
        )

    def tearDown(self):
        self.temp.cleanup()

    def q(self, n, c="All"):
        return query(n, "2021-01-01", "2021-02-28", c, self.db)

    def test_financial_reconciliation(self):
        r = self.q("kpis")[0]
        self.assertEqual(r["gross_sales"], 50)
        self.assertEqual(r["returns"], 10)
        self.assertEqual(r["net_revenue"], 40)
        self.assertEqual(r["sales_orders"], 3)

    def test_duplicate_and_anonymous(self):
        self.assertEqual(self.quality["duplicate_rows_removed"], 1)
        self.assertEqual(self.quality["anonymous_line_rows"], 1)
        self.assertEqual(self.q("kpis")[0]["known_buyers"], 1)

    def test_repeat_customer(self):
        self.assertEqual(self.q("repeat_customers")[0]["repeat_purchase_rate"], 1)

    def test_cohorts(self):
        r = self.q("cohorts")
        self.assertEqual([x["month_index"] for x in r], [0, 1])
        self.assertEqual(r[1]["retention"], 1)

    def test_bound_country_parameter(self):
        self.assertEqual(self.q("kpis", "UK' OR 1=1 --")[0]["sales_orders"], 0)

    def test_country_filter(self):
        self.assertEqual(self.q("kpis", "UK")[0]["net_revenue"], 20)

    def test_date_validation(self):
        with self.assertRaises(ValueError):
            query("kpis", "2021-03-01", "2021-01-01", path=self.db)

    def test_all_queries_execute(self):
        for n in ["monthly", "products", "countries", "rfm", "transactions"]:
            self.assertTrue(self.q(n))

    def test_inconsistent_invoice_rejected(self):
        bad = self.rows + [["1", "B", "Book", 1, "2021-01-01", 20, 99, "UK"]]
        with self.assertRaises(ValueError):
            build(pd.DataFrame(bad, columns=self.columns), self.db)

    def test_line_timestamps_preserved(self):
        rows = self.rows + [["1", "B", "Book", 1, "2021-01-01 00:01:00", 3, 1, "UK"]]
        report = build(pd.DataFrame(rows, columns=self.columns), self.db)
        self.assertEqual(report["invoices_with_multiple_timestamps"], 1)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(
                c.execute(
                    "SELECT COUNT(DISTINCT line_timestamp) FROM invoice_lines WHERE invoice_no='1'"
                ).fetchone()[0],
                2,
            )

    def test_invalid_prices_quarantined(self):
        rows = self.rows + [
            ["5", "B", "Book", 1, "2021-02-04", -20, 2, "UK"],
            ["6", "B", "Book", 0, "2021-02-04", 20, 2, "UK"],
        ]
        r = build(pd.DataFrame(rows, columns=self.columns), self.db)
        self.assertEqual(r["invalid_rows_removed"], 2)

    def test_idempotent_rebuild(self):
        build(pd.DataFrame(self.rows, columns=self.columns), self.db)
        self.assertEqual(self.q("kpis")[0]["net_revenue"], 40)


if __name__ == "__main__":
    unittest.main()
