# sync.py
import argparse
import logging
import time
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from sqlalchemy import text

from app.crud.crud_daily import save_daily_basic
from app.db.session import Base, engine, SessionLocal
from app.crud.crud_industry import save_sw_industry, save_index_member
from app.crud.crud_stock import save_stock_basic
from app.models.models import StockBasic
from app.crud.crud_company import save_stock_company, get_all_listed_companies_info
from app.crud.crud_fina_indicator import (
    save_fina_indicator,
    check_fina_indicator_exists,
)
from app.crud.crud_fina_audit import (
    save_fina_audit,
    check_fina_audit_exists,
)
from app.crud.crud_dividend import (
    save_dividend,
    check_dividend_exists,
)
from app.crud.crud_fina_mainbz import (
    save_fina_mainbz,
    check_fina_mainbz_exists,
)
from app.service.finance_service import fetch_finance_for_stock_2
from app.utils.tushare_utils import fetch_paginated
from app.service.tushare_service import (
    fetch_today_daily_basic,
    get_sw_industry,
    get_stock_list,
    get_stock_company,
    get_index_member,
    fetch_fina_indicator,
    fetch_fina_audit,
    fetch_dividend,
    fetch_fina_mainbz,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


# -----------------------------
# DB Session 上下文管理器
# -----------------------------


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


def ensure_fina_mainbz_schema():
    """
    修复/对齐 fina_mainbz 表结构：
    1) 补齐 type 列
    2) 主键改为 (ts_code, end_date, type, bz_item)

    说明：旧结构主键仅 (ts_code, end_date)，会导致同一期多条主营构成无法入库。
    """
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE fina_mainbz ADD COLUMN IF NOT EXISTS type VARCHAR(10)")
        )

        conn.execute(
            text("UPDATE fina_mainbz SET type='P' WHERE type IS NULL OR type = ''")
        )
        conn.execute(
            text(
                "UPDATE fina_mainbz SET bz_item='UNKNOWN' "
                "WHERE bz_item IS NULL OR bz_item = ''"
            )
        )

        conn.execute(text("ALTER TABLE fina_mainbz ALTER COLUMN type SET NOT NULL"))
        conn.execute(text("ALTER TABLE fina_mainbz ALTER COLUMN bz_item SET NOT NULL"))

        pk_rows = conn.execute(
            text(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = 'fina_mainbz'
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
                """
            )
        ).fetchall()

        current_pk = [row[0] for row in pk_rows]
        target_pk = ["ts_code", "end_date", "type", "bz_item"]

        if current_pk != target_pk:
            pk_name_row = conn.execute(
                text(
                    """
                    SELECT tc.constraint_name
                    FROM information_schema.table_constraints tc
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = 'fina_mainbz'
                      AND tc.constraint_type = 'PRIMARY KEY'
                    """
                )
            ).fetchone()
            if pk_name_row:
                conn.exec_driver_sql(
                    f'ALTER TABLE fina_mainbz DROP CONSTRAINT "{pk_name_row[0]}"'
                )

            conn.execute(
                text(
                    """
                    ALTER TABLE fina_mainbz
                    ADD CONSTRAINT fina_mainbz_pkey
                    PRIMARY KEY (ts_code, end_date, type, bz_item)
                    """
                )
            )

        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_fina_mainbz_ts_type_end_date
                ON fina_mainbz (ts_code, type, end_date DESC)
                """
            )
        )

    logging.info("fina_mainbz 表结构已校验/修复完成")


def parse_mainbz_types(raw: str) -> list[str]:
    allowed = {"P", "D", "I"}
    parts = [p.strip().upper() for p in raw.split(",") if p.strip()]
    if not parts:
        return ["P", "D"]
    invalid = [p for p in parts if p not in allowed]
    if invalid:
        raise ValueError(f"mainbz type 非法: {invalid}，仅支持 P/D/I")
    # 去重并保持顺序
    out: list[str] = []
    for p in parts:
        if p not in out:
            out.append(p)
    return out


def parse_ts_codes(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


def sync_fina_mainbz(
    max_workers=1,
    types: list[str] | None = None,
    force: bool = False,
    ts_codes: set[str] | None = None,
):
    if types is None:
        types = ["P", "D"]

    logging.info("开始抓取主营业务构成数据 fina_mainbz...")
    logging.info("同步类型: %s", ",".join(types))

    with get_db_session() as db:
        # 优先使用 stock_basic 在市股票，避免 stock_company 全量历史导致任务过大。
        listed_codes = [
            row[0]
            for row in db.query(StockBasic.ts_code)
            .filter(StockBasic.list_status == "L")
            .all()
            if row and row[0]
        ]

        if listed_codes:
            companies = [(code, None) for code in listed_codes]
            logging.info("股票池来源: stock_basic(list_status='L')")
        else:
            companies = get_all_listed_companies_info(db)
            logging.info("股票池来源: stock_company(回退)")

        if ts_codes:
            companies = [row for row in companies if row[0] in ts_codes]
        logging.info(f"共 {len(companies)} 支股票")

        def fetch_one(ts_code: str, missing_types: list[str]):
            for bz_type in missing_types:
                total = 0
                page = 0
                while True:
                    retries = 0
                    df = None
                    while retries < 3:
                        try:
                            df = fetch_fina_mainbz(
                                ts_code=ts_code,
                                bz_type=bz_type,
                                limit=100,
                                offset=page * 100,
                            )
                            break
                        except Exception as e:
                            retries += 1
                            wait_s = 1.5 * retries
                            logging.warning(
                                "%s[%s] 第%s次拉取失败（offset=%s）: %s | %s，%.1fs后重试",
                                ts_code,
                                bz_type,
                                retries,
                                page * 100,
                                type(e).__name__,
                                str(e),
                                wait_s,
                            )
                            time.sleep(wait_s)

                    if df is None:
                        logging.error(
                            "%s[%s] 主营构成抓取终止（连续重试失败，offset=%s）",
                            ts_code,
                            bz_type,
                            page * 100,
                        )
                        break

                    if df.empty:
                        break

                    try:
                        save_fina_mainbz(df)
                    except Exception as e:
                        logging.error(
                            "%s[%s] 主营构成写入失败（offset=%s）: %s | %s",
                            ts_code,
                            bz_type,
                            page * 100,
                            type(e).__name__,
                            str(e),
                        )
                        logging.debug(traceback.format_exc())
                        break

                    total += len(df)
                    if len(df) < 100:
                        break

                    page += 1
                    time.sleep(0.05)

                logging.info("%s[%s] 主营构成抓取成功 (%s条)", ts_code, bz_type, total)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ts_code, _ in companies:
                if force:
                    missing_types = types
                else:
                    missing_types = [
                        t for t in types if not check_fina_mainbz_exists(db, ts_code, t)
                    ]
                if missing_types:
                    executor.submit(fetch_one, ts_code, missing_types)

    logging.info("fina_mainbz 抓取完成！")

def sync_dividend():
    """
    抓取送股分红数据
    由于 Tushare 接口限制必须指定 ts_code 或 ann_date，且 ann_date 不支持范围查询效率低，
    因此回退到按股票代码循环抓取。
    """
    logging.info("开始抓取送股分红数据 (按股票代码)...")
    # fetch_paginated(
    #     fetch_func=fetch_dividend,
    #     save_func=lambda db, df: save_dividend(df),
    #     page_size=2000
    # )

    with get_db_session() as db:
        companies = get_all_listed_companies_info(db)
        logging.info(f"共 {len(companies)} 支股票")

        def fetch_one(ts_code):
            try:
                # fetch_dividend 内部已经处理了 limit/offset，但这里我们只需要全量，
                # 对于单只股票，数据量很小，不需要分页。
                df = fetch_dividend(ts_code=ts_code)
                
                if not df.empty:
                    save_dividend(df)
                logging.info(f"{ts_code} 送股分红数据抓取成功 ({len(df)}条)")
            except Exception as e:
                logging.error("%s 送股分红数据写入失败: %s", ts_code, e)
        # fetch_one('600132.SH')
        # 使用线程池并发抓取
        with ThreadPoolExecutor(max_workers=5) as executor:
            for ts_code, _ in companies:
                if not check_dividend_exists(db, ts_code):
                    executor.submit(fetch_one, ts_code)

    logging.info("送股分红数据抓取完成！")


def sync_fina_audit_data(**_):
    logging.info("开始抓取财报审计意见数据...")
    with get_db_session() as db:
        companies = get_all_listed_companies_info(db)
        logging.info(f"共 {len(companies)} 支股票")

        for ts_code, _ in companies:
            if check_fina_audit_exists(db, ts_code):
                continue
            try:
                df = fetch_fina_audit(ts_code)
                if not df.empty:
                    save_fina_audit(df)
                logging.info(f"{ts_code} 审计意见数据抓取成功 ({len(df)}条)")
            except Exception as e:
                logging.error("%s 审计意见数据写入失败: %s", ts_code, e)

    logging.info("财报审计意见数据抓取完成！")


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
    now = datetime.now()
    # 如果当前时间早于15点，截止日期为昨天
    if now.hour < 15:
        end_date = now - timedelta(days=1)
    else:
        end_date = now

    # 往前推6天，总共7天
    start_date = end_date - timedelta(days=6)

    current_date = start_date
    while current_date <= end_date:
        trade_date_str = current_date.strftime("%Y%m%d")
        logging.info(f"正在同步 {trade_date_str} 的 daily_basic 数据...")

        fetch_paginated(
            fetch_func=fetch_today_daily_basic,
            save_func=lambda db, df: save_daily_basic(df),
            trade_date=trade_date_str,
            page_size=6000,
        )

        current_date += timedelta(days=1)


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
                logging.error("%s 财务指标写入失败: %s", ts_code, type(e).__name__)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ts_code, _ in companies:
                if not check_fina_indicator_exists(db, ts_code):
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
    if args.dividend:
        sync_dividend()
    if args.fina_audit:
        sync_fina_audit_data(max_workers=args.workers)
    if args.fina_mainbz:
        ensure_fina_mainbz_schema()
        sync_fina_mainbz(
            max_workers=args.workers,
            types=parse_mainbz_types(args.mainbz_types),
            force=args.fina_mainbz_force,
            ts_codes=parse_ts_codes(args.mainbz_ts_codes),
        )


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
    parser.add_argument("--dividend", action="store_true", help="抓取送股分红")
    parser.add_argument("--fina_audit", action="store_true", help="抓取财报审计意见")
    parser.add_argument("--fina_mainbz", action="store_true", help="抓取主营业务构成")
    parser.add_argument("--mainbz_types", type=str, default="P,D", help="主营构成类型，逗号分隔：P,D,I")
    parser.add_argument("--mainbz_ts_codes", type=str, default="", help="仅同步指定股票，逗号分隔：如 600600.SH,000001.SZ")
    parser.add_argument("--fina_mainbz_force", action="store_true", help="强制重刷已存在的主营构成数据")
    args = parser.parse_args()

    run(args)
