import pandas as pd
import tushare as ts
from app.config import settings
from datetime import datetime
from sqlalchemy.inspection import inspect
from app.models.models import FinaIndicator, Dividend, FinaAudit, FinaMainbz
from app.utils.tushare_utils import RateLimiter

token = settings.TUSHARE_TOKEN
ts.set_token(token)

pro = ts.pro_api()


def get_sw_industry(level="L1", src="SW2021"):
    """获取申万行业分类数据"""
    df = pro.index_classify(level=level, src=src)
    return df

#查询当前所有正常上市交易的股票列表
def get_stock_list():
    fields = (
        "ts_code,symbol,name,area,industry,fullname,ennname,cnspell,"
        "market,exchange,curr_type,list_status,list_date,delist_date,"
        "is_hs,act_name,act_ent_type"
    )

    df = pro.stock_basic(
        exchange="",
        list_status="L",
        fields=fields
    )

    return df

#上市公司基本信息
def get_stock_company(offset: int = 0, limit: int = 2000):
    return pro.stock_company(offset=offset, limit=limit)

def get_income_vip(period: str):
    """
    获取利润表（VIP）
    period: 报告期，如 20181231 / 20231231
    """
    fields = (
        "ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,end_type,"
        "basic_eps,diluted_eps,total_revenue,revenue,int_income,prem_earned,"
        "comm_income,n_commis_income,n_oth_income,n_oth_b_income,prem_income,"
        "out_prem,une_prem_reser,reins_income,n_sec_tb_income,n_sec_uw_income,"
        "n_asset_mg_income,oth_b_income,fv_value_chg_gain,invest_income,"
        "ass_invest_income,forex_gain,total_cogs,oper_cost,int_exp,comm_exp,"
        "biz_tax_surchg,sell_exp,admin_exp,fin_exp,assets_impair_loss,"
        "operate_profit,non_oper_income,non_oper_exp,nca_disploss,"
        "total_profit,income_tax,n_income,n_income_attr_p,minority_gain,"
        "oth_compr_income,t_compr_income,compr_inc_attr_p,compr_inc_attr_m_s,"
        "ebit,ebitda,rd_exp,update_flag"
    )

    df = pro.income_vip(
        period=period,
        fields=fields
    )
    return df

# 利润表
def get_income_all(ts_code: str):
    return pro.income(ts_code=ts_code)

# 资产负债表
def get_balancesheet_all(ts_code: str):
    return pro.balancesheet(ts_code=ts_code)

# 现金流量表
def get_cashflow_all(ts_code: str):
    return pro.cashflow(ts_code=ts_code)

def get_index_member(offset: int = 0, limit: int = 2000):
    """
    分页获取指数成分股
    :param offset: 偏移量，从第几条开始
    :param limit: 每页条数
    :return: DataFrame
    """
    return pro.index_member_all(offset=offset, limit=limit)

def get_daily_basic(
    trade_date=None,
    ts_code=None,
    start_date=None,
    end_date=None
):
    if trade_date and (start_date or end_date):
        raise ValueError("trade_date 不能与 start_date/end_date 同时使用")

    return pro.daily_basic(
        trade_date=trade_date,
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date
    )


def fetch_today_daily_basic(trade_date: str | None = None, offset: int = 0, limit: int = 6000) -> pd.DataFrame:
    """
    从 tushare 获取当天 daily_basic 数据
    """
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y%m%d")

    df = pro.daily_basic(trade_date=trade_date, offset=offset, limit=limit)
    return df

# 200 次 / 60 秒
tushare_limiter = RateLimiter(max_calls=200, period=60)
def fetch_fina_indicator(ts_code: str) -> pd.DataFrame:
    # ⭐ 限速
    tushare_limiter.acquire()
    cols = [c.key for c in inspect(FinaIndicator).mapper.column_attrs]
    fields = ",".join(cols)
    """
    从 tushare 获取财务指标数据
    """
    df = pro.fina_indicator(ts_code=ts_code, fields=fields)
    return df

# 60 次 / 60 秒
tushare_limiter_60 = RateLimiter(max_calls=60, period=60)
def fetch_fina_audit(ts_code: str) -> pd.DataFrame:
    tushare_limiter_60.acquire()
    df = pro.fina_audit(ts_code=ts_code, fields="ts_code,ann_date,end_date,audit_result,audit_fees,audit_agency,audit_sign")
    return df

tushare_limiter_300 = RateLimiter(max_calls=300, period=60)
def fetch_dividend(ts_code: str | None = None, limit: int | None = None, offset: int | None = None) -> pd.DataFrame:
    # ⭐ 限速
    tushare_limiter_300.acquire()
    cols = [c.key for c in inspect(Dividend).mapper.column_attrs]
    fields = ",".join(cols)
    """
    从 tushare 获取送股分红数据
    """
    df = pro.dividend(ts_code=ts_code, fields=fields, limit=limit, offset=offset)
    return df


# 文档要求 2000 积分可用，单次最多 100 行；为稳妥控制在 60 次/分钟。
tushare_limiter_mainbz = RateLimiter(max_calls=60, period=60)


def fetch_fina_mainbz(
    ts_code: str,
    bz_type: str = "P",
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    """
    获取主营业务构成（fina_mainbz）。

    说明：
    - 2000 积分可用（按 Tushare 文档）
    - 默认按单股 + type(P/D) 拉取
    - 单次建议 limit=100（接口上限）
    """
    tushare_limiter_mainbz.acquire()

    params: dict[str, str | int] = {
        "ts_code": ts_code,
        "type": bz_type,
        "limit": limit,
        "offset": offset,
    }
    if period:
        params["period"] = period
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    # 显式字段优先，失败后降级为接口默认字段。
    fields = "ts_code,end_date,type,bz_item,bz_sales,bz_profit,bz_cost,curr_type,update_flag"
    try:
        df = pro.fina_mainbz(fields=fields, **params)
    except Exception:
        df = pro.fina_mainbz(**params)

    if df is None or df.empty:
        return pd.DataFrame()

    # 若接口没返回 type 字段，使用请求参数补齐，保证入库主键完整。
    if "type" not in df.columns:
        df["type"] = bz_type

    # 对齐模型真实字段，避免接口字段漂移。
    cols = [c.key for c in inspect(FinaMainbz).mapper.column_attrs]
    keep = [c for c in df.columns if c in cols]
    return df[keep]
