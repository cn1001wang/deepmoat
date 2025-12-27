from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class FinanceSyncLogRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    table_name: str = Field(..., alias="tableName")
    last_sync_end_date: Optional[str] = Field(None, alias="lastSyncEndDate")

class IncomeRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    end_date: str = Field(..., alias="endDate")
    report_type: str = Field(..., alias="reportType")
    ann_date: Optional[str] = Field(None, alias="annDate")
    f_ann_date: Optional[str] = Field(None, alias="fAnnDate")
    comp_type: Optional[str] = Field(None, alias="compType")
    end_type: Optional[str] = Field(None, alias="endType")
    basic_eps: Optional[float] = Field(None, alias="basicEps")
    diluted_eps: Optional[float] = Field(None, alias="dilutedEps")
    total_revenue: Optional[float] = Field(None, alias="totalRevenue")
    revenue: Optional[float] = None
    operate_profit: Optional[float] = Field(None, alias="operateProfit")
    total_profit: Optional[float] = Field(None, alias="totalProfit")
    n_income: Optional[float] = Field(None, alias="nIncome")
    n_income_attr_p: Optional[float] = Field(None, alias="nIncomeAttrP")
    rd_exp: Optional[float] = Field(None, alias="rdExp")
    # ... (篇幅原因省略中间类似字段，你可以根据 models.py 补全所有 Float 字段)
    update_flag: Optional[str] = Field(None, alias="updateFlag")

class BalanceSheetRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    end_date: str = Field(..., alias="endDate")
    report_type: str = Field(..., alias="reportType")
    total_share: Optional[float] = Field(None, alias="totalShare")
    money_cap: Optional[float] = Field(None, alias="moneyCap")
    total_assets: Optional[float] = Field(None, alias="totalAssets")
    total_liab: Optional[float] = Field(None, alias="totalLiab")
    total_hldr_eqy_exc_min_int: Optional[float] = Field(None, alias="totalHldrEqyExcMinInt")
    # ... (根据 models.py 补全所有字段)
    update_flag: Optional[str] = Field(None, alias="updateFlag")

class CashFlowRead(BaseSchema):
    ts_code: str = Field(..., alias="tsCode")
    end_date: str = Field(..., alias="endDate")
    report_type: str = Field(..., alias="reportType")
    net_profit: Optional[float] = Field(None, alias="netProfit")
    n_cashflow_act: Optional[float] = Field(None, alias="nCashflowAct")
    n_cashflow_inv_act: Optional[float] = Field(None, alias="nCashflowInvAct")
    n_cash_flows_fnc_act: Optional[float] = Field(None, alias="nCashFlowsFncAct")
    free_cashflow: Optional[float] = Field(None, alias="freeCashflow")
    # ... (根据 models.py 补全所有字段)
    update_flag: Optional[str] = Field(None, alias="updateFlag")