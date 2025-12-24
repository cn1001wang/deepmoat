from common.service.tushare_service import (
    get_income_all,
    get_balancesheet_all,
    get_cashflow_all,
)
from common.crud.crud_income import save_income_bulk
from common.crud.crud_balancesheet import save_balancesheet_bulk
from common.crud.crud_cashflow import save_cashflow_bulk
from common.crud.crud_sync_log import get_db_max_end_date, update_sync_log
from common.utils.df_utils import dedup_finance_df
import time


TABLES = {
    "income": (get_income_all, save_income_bulk),
    "balancesheet": (get_balancesheet_all, save_balancesheet_bulk),
    "cashflow": (get_cashflow_all, save_cashflow_bulk),
}


def fetch_finance_for_stock(ts_code: str):
    """
    同步某只股票的所有财务数据（增量 + 更正）

    整体策略：
    1. 全量拉取 tushare 财务数据
    2. 在内存中完成去重和增量过滤
    3. 只入库：
       - 数据库中不存在的新期数
       - 或 update_flag = 1 的更正公告
    4. 每张表维护独立的同步断点（end_date）

    这是一个“可反复执行、可恢复、可长期跑”的同步函数
    """
    
    for table_name, (fetch, save) in TABLES.items():

        # ① 读取数据库中该股票、该表的最大 end_date
        #    作为断点，避免每次全量入库
        last_end_date = get_db_max_end_date(ts_code, table_name)

        # ② 从 tushare 拉取该股票的全部财务数据
        #   （是否增量由后续逻辑统一处理）
        df = fetch(ts_code)
        if df is None or df.empty:
            continue

        # ③ 对 tushare 返回的数据做公告级去重
        #    保证同一期只保留最新版本
        df = dedup_finance_df(df)

        # ④ 增量过滤：
        #    - end_date >= last_end_date → 新数据
        #    - update_flag == "1"        → 更正公告（即使是旧期）
        if last_end_date:
            df = df[
                (df["end_date"] >= last_end_date) |
                (df["update_flag"] == "1")
            ]

        # 如果过滤后没有需要入库的数据，直接跳过
        if df.empty:
            continue

        # ⑤ 批量入库（通常是 bulk upsert）
        save(df)

        # ⑥ 更新同步断点
        #    使用本次成功入库数据的最大 end_date
        max_end_date = df["end_date"].max()
        update_sync_log(ts_code, table_name, max_end_date)

        # ⑦ 控制 tushare 接口频率，避免被限流
        time.sleep(0.35)


from datetime import date

def get_latest_available_end_date(today: date | None = None) -> str:
    if today is None:
        today = date.today()

    year = today.year
    md = today.month * 100 + today.day

    if md >= 1231:
        return f"{year}-12-31"
    elif md >= 930:
        return f"{year}-09-30"
    elif md >= 630:
        return f"{year}-06-30"
    else:
        return f"{year}-03-31"

from sqlalchemy import func
from common.database import SessionLocal
from common.models import Income, BalanceSheet, CashFlow

TABLE_MODEL_MAP = {
    "income": Income,
    "balancesheet": BalanceSheet,
    "cashflow": CashFlow,
}

def fetch_finance_for_stock_2(ts_code: str):
    """
    新版逻辑：
    1. 先查数据库
    2. 如果三张表 end_date 都 >= 当年最新一期 → 直接跳过
    3. 否则打印 ts_code，并同步缺失数据
    """

    latest_end_date = get_latest_available_end_date()

    # ① 先检查数据库是否已经是“今年最新一期”
    all_up_to_date = True

    for table_name in TABLES.keys():
        db_end_date = get_db_max_end_date(ts_code, table_name)

        if not db_end_date or db_end_date < latest_end_date:
            all_up_to_date = False
            break

    # ② 如果已经齐全，直接返回
    if all_up_to_date:
        return

    # ③ 否则打印并开始同步
    print(f"[SYNC] {ts_code} 财务数据不完整，开始同步…")

    for table_name, (fetch, save) in TABLES.items():

        last_end_date = get_db_max_end_date(ts_code, table_name)

        df = fetch(ts_code)
        if df is None or df.empty:
            continue

        # 公告级去重
        df = dedup_finance_df(df)

        # 增量 + 更正
        if last_end_date:
            df = df[
                (df["end_date"] > last_end_date) |
                (df["update_flag"] == "1")
            ]

        if df.empty:
            continue

        save(df)

        max_end_date = df["end_date"].max()
        update_sync_log(ts_code, table_name, max_end_date)

        time.sleep(0.35)