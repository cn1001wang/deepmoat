# sync.py
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor

from app.crud.crud_daily import save_daily_basic
from app.db.session import Base, engine, SessionLocal, get_db
from app.crud.crud_industry import save_sw_industry, save_index_member
from app.crud.crud_stock import save_stock_basic
from app.crud.crud_company import save_stock_company, get_all_listed_companies_info
from app.crud.crud_fina_indicator import save_fina_indicator
from app.service.finance_service import fetch_finance_for_stock_2
from app.utils.tushare_utils import fetch_paginated
from app.service.tushare_service import fetch_today_daily_basic, get_sw_industry, get_stock_list, get_stock_company, get_index_member, fetch_fina_indicator


# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# -----------------------------
# DB Session 上下文管理器
# -----------------------------
from contextlib import contextmanager

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# -----------------------------
# 抓取函数
# -----------------------------
def fetch_industry():
    logging.info("开始抓取申万行业数据...")
    for level in ["L1", "L2", "L3"]:
        df = get_sw_industry(level=level, src="SW2021")
        logging.info(f"{level} 行业数据：{df.shape[0]} 行")
        with get_db_session() as db:
            save_sw_industry(db, df)
    logging.info("申万行业抓取完成！")


def fetch_stock_basic():
    logging.info("开始抓取股票列表...")
    df = get_stock_list()
    logging.info(f"抓取 {df.shape[0]} 支股票")
    with get_db_session() as db:
        save_stock_basic(db, df)
    logging.info("股票列表抓取完成！")


def fetch_stock_company():
    fetch_paginated(fetch_func=get_stock_company, save_func=save_stock_company)


def fetch_index_member():
    fetch_paginated(fetch_func=get_index_member, save_func=save_index_member)


def fetch_finance_data(max_workers=5):
    logging.info("开始抓取财务数据...")
    with get_db_session() as db:
        companies = get_all_listed_companies_info(db)
        logging.info(f"共 {len(companies)} 支股票")

        def fetch_one(ts_code):
            try:
                fetch_finance_for_stock_2(ts_code)
                logging.info(f"{ts_code} 财务数据抓取成功")
            except Exception as e:
                logging.error(f"{ts_code} 财务数据抓取失败: {e}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ts_code, _ in companies:
                executor.submit(fetch_one, ts_code)

    logging.info("财务数据抓取完成！")

def sync_today_daily_basic():
    df = fetch_today_daily_basic()
    save_daily_basic(df)

def sync_fina_indicator(max_workers=5):
    logging.info("开始抓取财务指标数据...")
    with get_db_session() as db:
        companies = get_all_listed_companies_info(db)
        logging.info(f"共 {len(companies)} 支股票")

        def fetch_one(ts_code):
            try:
                df = fetch_fina_indicator(ts_code)
                save_fina_indicator(df)
                logging.info(f"{ts_code} 财务指标数据抓取成功")
            except Exception as e:
                logging.error(
                    "%s 财务指标写入失败: %s",
                    ts_code,
                    type(e).__name__
                )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ts_code, _ in companies:
                executor.submit(fetch_one, ts_code)

        logging.info("财务指标数据抓取完成！")

# -----------------------------
# 主函数
# -----------------------------
def run(args):
    # 创建表
    Base.metadata.create_all(bind=engine)

    if args.industry:
        fetch_industry()
    if args.stock_basic:
        fetch_stock_basic()
    if args.stock_company:
        fetch_stock_company()
    if args.index_member:
        fetch_index_member()
    if args.finance:
        fetch_finance_data(max_workers=args.workers)
    if args.daily:
        sync_today_daily_basic()
    if args.fina_indicator:
        sync_fina_indicator(max_workers=args.workers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tushare 数据同步脚本")
    parser.add_argument("--industry", action="store_true", help="抓取申万行业数据")
    parser.add_argument("--stock_basic", action="store_true", help="抓取股票列表")
    parser.add_argument("--stock_company", action="store_true", help="抓取公司信息")
    parser.add_argument("--index_member", action="store_true", help="抓取指数成分股")
    parser.add_argument("--finance", action="store_true", help="抓取财务数据")
    parser.add_argument("--daily", action="store_true", help="抓取今日指标")
    parser.add_argument("--workers", type=int, default=1, help="抓取财务数据线程数")
    parser.add_argument("--fina_indicator", action="store_true", help="抓取财务指标数据")
    args = parser.parse_args()

    run(args)
