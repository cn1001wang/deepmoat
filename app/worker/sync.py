# sync.py
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor

from app.db.session import Base, engine, SessionLocal
from app.crud.crud_industry import save_sw_industry, save_index_member
from app.crud.crud_stock import save_stock_basic
from app.crud.crud_company import save_stock_company, get_all_listed_companies_info
from app.service.finance_service import fetch_finance_for_stock_2
from ..service.tushare_service import get_sw_industry, get_stock_list, get_stock_company, get_index_member

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
            save_sw_industry(df)
    logging.info("申万行业抓取完成！")


def fetch_stock_basic():
    logging.info("开始抓取股票列表...")
    df = get_stock_list()
    logging.info(f"抓取 {df.shape[0]} 支股票")
    with get_db_session() as db:
        save_stock_basic(df)
    logging.info("股票列表抓取完成！")


def fetch_stock_company():
    logging.info("开始抓取股票公司信息...")
    df = get_stock_company()
    logging.info(f"抓取 {df.shape[0]} 支公司信息")
    with get_db_session() as db:
        save_stock_company(df)
    logging.info("股票公司信息抓取完成！")


def fetch_index_member():
    logging.info("开始抓取指数成分股...")
    page_size = 2000
    page_no = 0

    while True:
        df = get_index_member(page_no * page_size, page_size)
        if df.empty:
            logging.info("没有更多数据，结束抓取")
            break

        logging.info(f"抓取到 {df.shape[0]} 条成分股")
        with get_db_session() as db:
            save_index_member(db, df)

        if df.shape[0] < page_size:
            # 不足 page_size 条，说明是最后一页
            break

        page_no += 1

    logging.info("指数成分股抓取完成！")


def fetch_finance_data(max_workers=5):
    logging.info("开始抓取财务数据...")
    companies = get_all_listed_companies_info()
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tushare 数据同步脚本")
    parser.add_argument("--industry", action="store_true", help="抓取申万行业数据")
    parser.add_argument("--stock_basic", action="store_true", help="抓取股票列表")
    parser.add_argument("--stock_company", action="store_true", help="抓取公司信息")
    parser.add_argument("--index_member", action="store_true", help="抓取指数成分股")
    parser.add_argument("--finance", action="store_true", help="抓取财务数据")
    parser.add_argument("--workers", type=int, default=5, help="抓取财务数据线程数")
    args = parser.parse_args()

    run(args)
