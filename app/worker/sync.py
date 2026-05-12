# sync.py
import argparse
import logging
import time
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from sqlalchemy import func, text

from app.crud.crud_daily import save_daily_basic
from app.db.session import Base, engine, SessionLocal
from app.crud.crud_industry import save_sw_industry, save_index_member
from app.crud.crud_stock import save_stock_basic
from app.models.models import FinaIndicator, StockBasic
from app.crud.crud_company import save_stock_company
from app.crud.crud_fina_indicator import (
    save_fina_indicator,
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
from app.service.finance_service import (
    fetch_finance_for_stock_2,
    fetch_finance_for_stock_overwrite,
)
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


def get_active_stock_codes_for_sync(db) -> list[str]:
    """
    获取财务类同步任务使用的股票池。

    优先读取 Tushare 最新在市名单，避免把已经退市的股票继续纳入同步。
    如果远端拉取失败，再回退到本地 stock_basic(list_status='L')。
    若两者都不可用，则直接返回空，避免误用 stock_company 全量历史池。
    """
    try:
        df = get_stock_list()
        if df is not None and not df.empty and "ts_code" in df.columns:
            codes = [
                ts_code.strip().upper()
                for ts_code in df["ts_code"].tolist()
                if isinstance(ts_code, str) and ts_code.strip()
            ]
            if codes:
                logging.info("股票池来源: tushare stock_basic(list_status='L')")
                return list(dict.fromkeys(codes))
        logging.warning("Tushare 在市股票池为空，回退到本地 stock_basic")
    except Exception as e:
        logging.warning(
            "获取 Tushare 在市股票池失败，回退到本地 stock_basic: %s | %s",
            type(e).__name__,
            str(e),
        )

    codes = [
        row[0].strip().upper()
        for row in db.query(StockBasic.ts_code)
        .filter(StockBasic.list_status == "L")
        .all()
        if row and isinstance(row[0], str) and row[0].strip()
    ]
    if codes:
        logging.info("股票池来源: 本地 stock_basic(list_status='L')")
        return list(dict.fromkeys(codes))

    logging.warning(
        "未找到可用的在市股票池，跳过本轮同步以避免抓取已退市股票；可先执行 --stock_basic 刷新股票列表"
    )
    return []


def is_tushare_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc)
    return "频率超限" in msg or "频次" in msg or "rate limit" in msg.lower()


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
        listed_codes = get_active_stock_codes_for_sync(db)
        if ts_codes:
            listed_codes = [code for code in listed_codes if code in ts_codes]
        logging.info(f"共 {len(listed_codes)} 支股票")

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
                            wait_s = (
                                65.0
                                if is_tushare_rate_limit_error(e)
                                else 1.5 * retries
                            )
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
            for ts_code in listed_codes:
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
        stock_codes = get_active_stock_codes_for_sync(db)
        logging.info(f"共 {len(stock_codes)} 支股票")

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
            for ts_code in stock_codes:
                if not check_dividend_exists(db, ts_code):
                    executor.submit(fetch_one, ts_code)

    logging.info("送股分红数据抓取完成！")


def sync_fina_audit_data(**_):
    logging.info("开始抓取财报审计意见数据...")
    with get_db_session() as db:
        stock_codes = get_active_stock_codes_for_sync(db)
        logging.info(f"共 {len(stock_codes)} 支股票")

        for ts_code in stock_codes:
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

def ensure_stock_company_schema():
    """
    Keep DB schema compatible with upstream data.

    Postgres won't auto-migrate when SQLAlchemy models change; we do a minimal
    ALTER for columns that have grown beyond their original sizes.
    """
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'stock_company' AND column_name = 'office'
                """
            )
        ).fetchone()
        if row and row[0] is not None and int(row[0]) < 500:
            conn.execute(text("ALTER TABLE stock_company ALTER COLUMN office TYPE varchar(500)"))


def fetch_index_member():
    fetch_paginated(fetch_func=get_index_member, save_func=save_index_member)


def fetch_finance_data(max_workers=5, overwrite: bool = False):
    mode = "完全覆盖" if overwrite else "增量"
    logging.info("开始抓取财务数据（%s）...", mode)
    with get_db_session() as db:
        stock_codes = get_active_stock_codes_for_sync(db)
        logging.info(f"共 {len(stock_codes)} 支股票")

        def fetch_one(ts_code):
            try:
                if overwrite:
                    fetch_finance_for_stock_overwrite(ts_code)
                else:
                    fetch_finance_for_stock_2(ts_code)
                logging.info(f"{ts_code} 财务数据抓取成功")
            except Exception as e:
                logging.error(f"{ts_code} 财务数据抓取失败: {e}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ts_code in stock_codes:
                executor.submit(fetch_one, ts_code)

    logging.info("财务数据抓取完成！")


def sync_today_daily_basic():
    sync_daily_basic_range()


def parse_yyyymmdd(raw: str) -> datetime:
    try:
        return datetime.strptime(raw, "%Y%m%d")
    except ValueError as exc:
        raise ValueError(f"日期格式非法: {raw}，应为 YYYYMMDD，如 20160101") from exc


def get_default_daily_end_date() -> datetime:
    now = datetime.now()
    # 如果当前时间早于15点，截止日期为昨天
    if now.hour < 15:
        return now - timedelta(days=1)
    return now


def sync_daily_basic_range(
    start_date: str | None = None,
    end_date: str | None = None,
):
    if end_date:
        end_dt = parse_yyyymmdd(end_date)
    else:
        end_dt = get_default_daily_end_date()

    if start_date:
        start_dt = parse_yyyymmdd(start_date)
    else:
        # 往前推6天，总共7天，保持 --daily 原有默认行为。
        start_dt = end_dt - timedelta(days=6)

    if start_dt > end_dt:
        raise ValueError(
            f"daily_basic 起始日期不能晚于结束日期: {start_dt:%Y%m%d} > {end_dt:%Y%m%d}"
        )

    logging.info(
        "开始同步 daily_basic，日期范围 %s 至 %s",
        start_dt.strftime("%Y%m%d"),
        end_dt.strftime("%Y%m%d"),
    )

    total_days = 0
    current_date = start_dt
    while current_date <= end_dt:
        trade_date_str = current_date.strftime("%Y%m%d")
        logging.info(f"正在同步 {trade_date_str} 的 daily_basic 数据...")

        fetch_paginated(
            fetch_func=fetch_today_daily_basic,
            save_func=lambda db, df: save_daily_basic(df),
            trade_date=trade_date_str,
            page_size=6000,
        )

        total_days += 1
        current_date += timedelta(days=1)

    logging.info("daily_basic 同步完成，共扫描 %s 个自然日", total_days)


def iter_month_end_sample_dates(
    start_dt: datetime,
    end_dt: datetime,
    window_days: int = 7,
):
    if window_days < 1:
        raise ValueError("monthly sample window_days 必须大于等于 1")

    month = datetime(start_dt.year, start_dt.month, 1)
    while month <= end_dt:
        if month.month == 12:
            next_month = datetime(month.year + 1, 1, 1)
        else:
            next_month = datetime(month.year, month.month + 1, 1)

        month_end = min(next_month - timedelta(days=1), end_dt)
        sample_start = max(start_dt, month_end - timedelta(days=window_days - 1))

        current = sample_start
        while current <= month_end:
            yield current
            current += timedelta(days=1)

        month = next_month


def sync_daily_basic_dates(dates, label: str):
    total_days = 0
    for current_date in dates:
        trade_date_str = current_date.strftime("%Y%m%d")
        logging.info("正在同步 %s 的 daily_basic 数据（%s）...", trade_date_str, label)

        fetch_paginated(
            fetch_func=fetch_today_daily_basic,
            save_func=lambda db, df: save_daily_basic(df),
            trade_date=trade_date_str,
            page_size=6000,
        )

        total_days += 1

    logging.info("daily_basic %s同步完成，共扫描 %s 个自然日", label, total_days)


def sync_daily_basic_hybrid(
    start_date: str = "20160101",
    end_date: str | None = None,
    recent_years: int = 3,
    sample_window_days: int = 7,
):
    if recent_years < 1:
        raise ValueError("recent_years 必须大于等于 1")

    start_dt = parse_yyyymmdd(start_date)
    end_dt = parse_yyyymmdd(end_date) if end_date else get_default_daily_end_date()
    if start_dt > end_dt:
        raise ValueError(
            f"daily_basic 起始日期不能晚于结束日期: {start_dt:%Y%m%d} > {end_dt:%Y%m%d}"
        )

    recent_start_dt = max(start_dt, end_dt - timedelta(days=365 * recent_years - 1))
    older_end_dt = recent_start_dt - timedelta(days=1)

    logging.info(
        "开始 hybrid daily_basic 同步：近 %s 年逐日 %s 至 %s；历史抽样 %s 至 %s（月末前 %s 天）",
        recent_years,
        recent_start_dt.strftime("%Y%m%d"),
        end_dt.strftime("%Y%m%d"),
        start_dt.strftime("%Y%m%d"),
        older_end_dt.strftime("%Y%m%d") if older_end_dt >= start_dt else "无",
        sample_window_days,
    )

    # 先同步最近 3 年完整数据，保证最常用的筛选和分析窗口优先可用。
    sync_daily_basic_range(
        start_date=recent_start_dt.strftime("%Y%m%d"),
        end_date=end_dt.strftime("%Y%m%d"),
    )

    if older_end_dt >= start_dt:
        sampled_dates = iter_month_end_sample_dates(
            start_dt=start_dt,
            end_dt=older_end_dt,
            window_days=sample_window_days,
        )
        sync_daily_basic_dates(sampled_dates, label="历史月末抽样")


def sync_fina_indicator(max_workers=5):
    logging.info("开始抓取财务指标数据...")
    target_end_date = get_latest_indicator_target_end_date()
    logging.info("财务指标目标报告期：%s", target_end_date)
    with get_db_session() as db:
        stock_codes = get_active_stock_codes_for_sync(db)
        logging.info(f"共 {len(stock_codes)} 支股票")

        def fetch_one(ts_code):
            try:
                df = fetch_fina_indicator(ts_code)
                save_fina_indicator(df)
                logging.info(f"{ts_code} 财务指标数据抓取成功")
            except Exception as e:
                logging.error("%s 财务指标写入失败: %s", ts_code, type(e).__name__)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ts_code in stock_codes:
                if should_sync_fina_indicator(db, ts_code, target_end_date):
                    executor.submit(fetch_one, ts_code)

        logging.info("财务指标数据抓取完成！")


def get_latest_indicator_target_end_date(today=None):
    if today is None:
        today = datetime.now()

    year = today.year
    md = today.month * 100 + today.day

    if md >= 1231:
        return f"{year}1231"
    if md >= 930:
        return f"{year}0930"
    if md >= 630:
        return f"{year}0630"
    return f"{year}0331"


def should_sync_fina_indicator(db, ts_code, target_end_date):
    max_end_date = (
        db.query(func.max(FinaIndicator.end_date))
        .filter(FinaIndicator.ts_code == ts_code)
        .scalar()
    )
    return not max_end_date or max_end_date < target_end_date


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
        ensure_stock_company_schema()
        fetch_stock_company()
    if args.index_member:
        fetch_index_member()
    if args.finance:
        fetch_finance_data(max_workers=args.workers, overwrite=args.finance_overwrite)
    if args.daily:
        if args.daily_hybrid:
            sync_daily_basic_hybrid(
                start_date=args.daily_start_date or "20160101",
                end_date=args.daily_end_date,
                recent_years=args.daily_recent_years,
                sample_window_days=args.daily_sample_window_days,
            )
        else:
            sync_daily_basic_range(
                start_date=args.daily_start_date,
                end_date=args.daily_end_date,
            )
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
    parser.add_argument(
        "--finance_overwrite",
        action="store_true",
        help="完全覆盖同步财务数据：删除旧 income/balancesheet/cashflow 后重拉",
    )
    parser.add_argument("--daily", action="store_true", help="抓取 daily_basic 指标")
    parser.add_argument("--daily_start_date", type=str, default=None, help="daily_basic 起始日期，格式 YYYYMMDD；不传则同步最近 7 天")
    parser.add_argument("--daily_end_date", type=str, default=None, help="daily_basic 结束日期，格式 YYYYMMDD；不传则按当前时间自动取今天/昨天")
    parser.add_argument("--daily_hybrid", action="store_true", help="daily_basic hybrid 模式：近几年逐日同步，更早数据按月末抽样")
    parser.add_argument("--daily_recent_years", type=int, default=3, help="hybrid 模式下逐日同步最近几年，默认 3")
    parser.add_argument("--daily_sample_window_days", type=int, default=7, help="hybrid 模式下历史月末抽样窗口天数，默认 7")
    parser.add_argument("--workers", type=int, default=1, help="抓取财务数据线程数")
    parser.add_argument("--fina_indicator", action="store_true", help="抓取财务指标数据")
    parser.add_argument("--dividend", action="store_true", help="抓取送股分红")
    parser.add_argument("--fina_audit", action="store_true", help="抓取财报审计意见")
    parser.add_argument("--fina_mainbz", action="store_true", help="抓取主营业务构成")
    parser.add_argument("--mainbz_types", type=str, default="P,D,I", help="主营构成类型，逗号分隔：P,D,I")
    parser.add_argument("--mainbz_ts_codes", type=str, default="", help="仅同步指定股票，逗号分隔：如 600600.SH,000001.SZ")
    parser.add_argument("--fina_mainbz_force", action="store_true", help="强制重刷已存在的主营构成数据")
    args = parser.parse_args()

    run(args)
