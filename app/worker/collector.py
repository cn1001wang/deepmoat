# Tushare 抓取逻辑

from common.service.tushare_service import get_sw_industry, get_stock_list, get_stock_company, get_index_member
from app.crud.crud_industry import save_sw_industry, save_index_member
from app.crud.crud_stock import save_stock_basic
from app.db.session import Base, engine
from app.crud.crud_company import save_stock_company
from app.crud.crud_company import get_all_listed_companies
from common.service.finance_service import fetch_finance_for_stock,fetch_finance_for_stock_2
from app.utils.date_utils import generate_periods

def get_save_sw_industry():
    # print("获取申万行业分类数据 L1 ...")
    df = get_sw_industry(level="L1", src="SW2021")
    print(df.head())

    # print("写入数据库...")
    save_sw_industry(df)

    # print("获取申万行业分类数据 L2 ...")
    df = get_sw_industry(level="L2", src="SW2021")


    # print("写入数据库...")
    save_sw_industry(df)

    # print("获取申万行业分类数据 L3 ...")
    df = get_sw_industry(level="L3", src="SW2021")


    # print("写入数据库...")
    save_sw_industry(df)

    # print("完成！")

def get_save_index_member():
    df = get_index_member()
    print(df.head())
    save_index_member(df)

def get_save_stock():
    print("获取股票列表...")
    df = get_stock_list()
    save_stock_basic(df)

def get_save_stock_company():
    print("获取股票公司信息...")
    df = get_stock_company()
    save_stock_company(df)

def get_save_finance_for_stock():

    companies = get_all_listed_companies()

    for ts_code, setup_date in companies:
        print(f"拉取 {ts_code}")
        fetch_finance_for_stock(ts_code)

def check_finance_tables():
    # 检查所有股票的财务数据是否存在
    for ts_code, setup_date in get_all_listed_companies():
        print(f"检查 {ts_code} 的财务数据是否存在...")
        fetch_finance_for_stock_2(ts_code)

def run():
    # print("创建表（如果不存在）...")
    Base.metadata.create_all(bind=engine)
    # get_save_sw_industry()
    # get_save_stock()
    # get_save_stock_company()
    # get_save_finance_for_stock()
    # get_save_index_member()
    check_finance_tables()

if __name__ == "__main__":
    run()
