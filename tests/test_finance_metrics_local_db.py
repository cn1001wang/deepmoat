import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.models import BalanceSheet, CashFlow, Dividend, FinaIndicator, Income
from app.service.finance_metrics import build_metrics_table


class FinanceMetricsLocalDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        for model in (Income, BalanceSheet, CashFlow, FinaIndicator, Dividend):
            model.__table__.create(self.engine)
        self.db = Session(self.engine)
        code = "000001.SZ"
        self.db.add_all([
            Income(ts_code=code, end_date="20251231", report_type="1", revenue=100, n_income=10),
            BalanceSheet(ts_code=code, end_date="20251231", report_type="1", total_assets=100),
            CashFlow(ts_code=code, end_date="20251231", report_type="1", n_cashflow_act=12),
            FinaIndicator(ts_code=code, end_date="20251231", ann_date="20260301", roe=10),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_builds_metrics_from_injected_database_session(self):
        result = build_metrics_table("000001.SZ", 6, self.db)
        self.assertIn("20251231", result["periods"])
        self.assertTrue(result["rows"])


if __name__ == "__main__":
    unittest.main()
