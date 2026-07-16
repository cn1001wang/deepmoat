import ast
from datetime import date
from pathlib import Path
import unittest


class FinanceServiceDateTest(unittest.TestCase):
    def test_available_periods_use_database_date_format(self):
        # Keep this test independent from Tushare configuration at import time.
        source = Path("app/service/finance_service.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "get_latest_available_end_date")
        namespace = {"date": date}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "finance_service.py", "exec"), namespace)
        get_period = namespace["get_latest_available_end_date"]

        self.assertEqual(get_period(date(2026, 4, 1)), "20260331")
        self.assertEqual(get_period(date(2026, 10, 1)), "20260930")
