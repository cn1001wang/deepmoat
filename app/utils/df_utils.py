def dedup_finance_df(df):
    """
    对财务数据做“公告级去重”

    Tushare 的财务接口有以下特点：
    1. 同一个 (ts_code, end_date) 可能会返回多条记录
    2. 不同 report_type（合并报表 / 母公司报表）
    3. update_flag = "1" 表示更正公告（应覆盖旧数据）

    设计目标：
    - 对 (ts_code, end_date, report_type) 作为唯一键
    - 如果同一期有多条，保留 update_flag 最大的一条
      （即优先保留更正公告）

    为什么先排序再 drop_duplicates：
    - pandas 的 drop_duplicates 只能保留 first / last
    - 所以先按 update_flag 排序，再保留 last
    """
    if df is None or df.empty:
        return df

    return (
        df.sort_values("update_flag")
          .drop_duplicates(
              subset=["ts_code", "end_date", "report_type"],
              keep="last"
          )
    )
