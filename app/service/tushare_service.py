import pandas as pd
import tushare as ts
from app.config import settings
from datetime import datetime

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


def fetch_today_daily_basic(trade_date: str | None = None) -> pd.DataFrame:
    """
    从 tushare 获取当天 daily_basic 数据
    """
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y%m%d")

    df = pro.daily_basic(trade_date=trade_date)
    return df