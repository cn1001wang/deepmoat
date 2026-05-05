import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.models import FinaIndicator
from app.worker.sync import should_sync_fina_indicator


class SyncFinaIndicatorTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        FinaIndicator.__table__.create(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_syncs_existing_stock_when_indicator_is_older_than_target_period(self):
        self.session.add(
            FinaIndicator(
                ts_code="000895.SZ",
                ann_date="20251029",
                end_date="20250930",
            )
        )
        self.session.commit()

        self.assertTrue(
            should_sync_fina_indicator(self.session, "000895.SZ", "20260331")
        )

    def test_skips_existing_stock_when_indicator_reaches_target_period(self):
        self.session.add(
            FinaIndicator(
                ts_code="000895.SZ",
                ann_date="20260429",
                end_date="20260331",
            )
        )
        self.session.commit()

        self.assertFalse(
            should_sync_fina_indicator(self.session, "000895.SZ", "20260331")
        )

    def test_syncs_stock_with_no_indicator_history(self):
        self.assertTrue(
            should_sync_fina_indicator(self.session, "000895.SZ", "20260331")
        )


if __name__ == "__main__":
    unittest.main()
