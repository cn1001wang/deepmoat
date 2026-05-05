import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.crud.crud_daily import get_daily_basic
from app.crud.crud_fina_indicator import get_fina_indicator
from app.models.models import DailyBasic, FinaIndicator


class CrudLatestFallbackTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        DailyBasic.__table__.create(self.engine)
        FinaIndicator.__table__.create(self.engine)
        self.session = Session(self.engine)

        self.session.add_all(
            [
                DailyBasic(ts_code="000001.SZ", trade_date="20260429", total_mv=100),
                DailyBasic(ts_code="000002.SZ", trade_date="20260429", total_mv=200),
                DailyBasic(ts_code="000001.SZ", trade_date="20260430", total_mv=110),
                DailyBasic(ts_code="000002.SZ", trade_date="20260430", total_mv=220),
                FinaIndicator(ts_code="000001.SZ", ann_date="20260401", end_date="20251231", roe=9),
                FinaIndicator(ts_code="000001.SZ", ann_date="20260428", end_date="20260331", roe=10),
                FinaIndicator(ts_code="000002.SZ", ann_date="20260401", end_date="20251231", roe=20),
            ]
        )
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_daily_basic_falls_back_to_latest_market_date_before_requested_date(self):
        rows = get_daily_basic("20260505", None, self.session)

        self.assertEqual({row.ts_code for row in rows}, {"000001.SZ", "000002.SZ"})
        self.assertEqual({row.trade_date for row in rows}, {"20260430"})

    def test_fina_indicator_falls_back_to_latest_period_per_stock(self):
        rows = get_fina_indicator(None, "20260331", None, self.session)

        by_code = {row.ts_code: row for row in rows}
        self.assertEqual(by_code["000001.SZ"].end_date, "20260331")
        self.assertEqual(by_code["000002.SZ"].end_date, "20251231")


if __name__ == "__main__":
    unittest.main()
