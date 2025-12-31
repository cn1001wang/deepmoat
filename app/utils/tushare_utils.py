
from typing import Callable
from contextlib import contextmanager
import pandas as pd
import logging
from app.db.session import Base, engine, SessionLocal

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

def fetch_paginated(
    fetch_func: Callable[..., pd.DataFrame],
    save_func: Callable[[any, pd.DataFrame], None],
    db_session_func: Callable[[], any] = get_db_session,
    page_size: int = 3000,
    **kwargs
):
    """
    通用分页抓取模板
    :param fetch_func: 数据抓取函数，必须返回 DataFrame，支持 offset, limit 参数
    :param save_func: 数据保存函数，接受 (db, df)
    :param db_session_func: 获取数据库 session 的函数
    :param page_size: 每页抓取数量
    :param kwargs: 传给 fetch_func 的其他参数
    """
    logging.info(f"开始抓取数据，page_size={page_size}")
    page_no = 0
    while True:
        logging.info(f"抓取第 {page_no + 1} 页数据...")
        df = fetch_func(offset=page_no * page_size, limit=page_size, **kwargs)
        if df.empty:
            logging.info("抓取到空数据，结束。")
            break

        logging.info(f"抓取到 {df.shape[0]} 条数据")
        with db_session_func() as db:
            save_func(db, df)

        if df.shape[0] < page_size:
            logging.info("最后一页数据已抓取完成")
            break

        page_no += 1
    logging.info("数据抓取完成！")