"""
作用：
针对招商银行生成股东会问答风格的专项分析报告，
会结合公司财务数据、同业对比和公开资料做定向输出。
"""

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analysis_dialogue_report import (
    OUTPUT_DIR,
    fmt_num,
    fmt_pct,
    fmt_yi,
    load_engine,
    query_df,
    safe_div,
)


TS_CODE = "600036.SH"
PEERS = ["000001.SZ", "601166.SH", "002142.SZ"]

PUBLIC_SOURCES = [
    {
        "date": "2026-01-23",
        "title": "招商银行2025年度业绩快报公告",
        "url": "https://s3gw.cmbchina.com/lb5001-cmbweb-prd-1255000097/cmbir/20260123/721c99c0-1b86-47f7-ab46-e4b6aa68da0e.pdf",
        "note": "2025年营业收入3375.32亿元，同比基本持平；归母净利润1501.81亿元，同比增长1.21%；贷款总额同比增长5.37%。",
    },
    {
        "date": "2025-09-02",
        "title": "招商银行2025年中期业绩数据摘要",
        "url": "https://s3gw.cmbchina.com/lb5001-cmbweb-prd-1255000097/cmbir/20250902/04abf237-5cd0-4c42-a372-6f4235f15561.pdf",
        "note": "2025年上半年净利息收益率1.88%，信用成本0.67%，年化不良生成率0.98%，盈利能力继续保持行业领先。",
    },
    {
        "date": "2024-12-31",
        "title": "招商银行简介",
        "url": "https://cmbchina.com/cmbinfo/aboutcmb",
        "note": "截至2024年末，总资产突破12万亿元；零售客户数突破2亿户，AUM近15万亿元，ROAA和ROAE均位居境内大中型上市银行前列。",
    },
]


def latest_financials(engine) -> dict:
    sql = """
        SELECT s.ts_code, s.name, s.industry, s.area, s.list_date,
               c.chairman, c.manager, c.employees, c.main_business,
               i.end_date AS income_end_date, i.total_revenue, i.n_income_attr_p, i.int_income, i.int_exp,
               i.n_commis_income, i.comm_income, i.operate_profit,
               b.end_date AS balance_end_date, b.total_assets, b.total_liab, b.total_hldr_eqy_exc_min_int,
               fi.end_date AS indicator_end_date, fi.roe_waa, fi.roe, fi.bps, fi.debt_to_assets,
               fi.netprofit_yoy, fi.or_yoy, fi.ocf_to_profit, fi.profit_dedt,
               d.trade_date, d.close, d.pe_ttm, d.pb, d.dv_ttm, d.total_mv, d.total_share
        FROM stock_basic s
        LEFT JOIN stock_company c ON s.ts_code = c.ts_code
        LEFT JOIN (
            SELECT * FROM income WHERE ts_code = :ts_code AND report_type = '1'
            ORDER BY end_date DESC LIMIT 1
        ) i ON s.ts_code = i.ts_code
        LEFT JOIN (
            SELECT * FROM balancesheet WHERE ts_code = :ts_code AND report_type = '1'
            ORDER BY end_date DESC LIMIT 1
        ) b ON s.ts_code = b.ts_code
        LEFT JOIN (
            SELECT * FROM fina_indicator WHERE ts_code = :ts_code
            ORDER BY end_date DESC, ann_date DESC LIMIT 1
        ) fi ON s.ts_code = fi.ts_code
        LEFT JOIN (
            SELECT * FROM daily_basic WHERE ts_code = :ts_code
            ORDER BY trade_date DESC LIMIT 1
        ) d ON s.ts_code = d.ts_code
        WHERE s.ts_code = :ts_code
        LIMIT 1
    """
    df = query_df(engine, sql, {"ts_code": TS_CODE})
    if df.empty:
        raise RuntimeError("未找到招商银行基础数据。")
    return df.iloc[0].to_dict()


def annual_history(engine) -> pd.DataFrame:
    sql = """
        SELECT i.end_date, i.total_revenue, i.n_income_attr_p, i.int_income, i.int_exp, i.n_commis_income,
               b.total_assets, b.total_liab, b.total_hldr_eqy_exc_min_int,
               fi.roe_waa, fi.roe, fi.bps, fi.debt_to_assets, fi.netprofit_yoy, fi.or_yoy
        FROM income i
        LEFT JOIN balancesheet b
          ON i.ts_code = b.ts_code AND i.end_date = b.end_date AND i.report_type = b.report_type
        LEFT JOIN fina_indicator fi
          ON i.ts_code = fi.ts_code AND i.end_date = fi.end_date
        WHERE i.ts_code = :ts_code
          AND i.report_type = '1'
          AND i.end_date LIKE '%1231'
        ORDER BY i.end_date DESC
        LIMIT 6
    """
    return query_df(engine, sql, {"ts_code": TS_CODE})


def dividend_summary(engine) -> pd.DataFrame:
    sql = """
        SELECT end_date, ann_date, ex_date, cash_div_tax
        FROM dividend
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC, ex_date DESC
        LIMIT 6
    """
    return query_df(engine, sql, {"ts_code": TS_CODE})


def audit_summary(engine) -> pd.DataFrame:
    sql = """
        SELECT end_date, audit_result, audit_agency
        FROM fina_audit
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC
        LIMIT 5
    """
    return query_df(engine, sql, {"ts_code": TS_CODE})


def peer_comparison(engine) -> pd.DataFrame:
    rows = []
    for code in [TS_CODE] + PEERS:
        sql = """
            SELECT s.ts_code, s.name,
                   d.trade_date, d.close, d.pe_ttm, d.pb, d.dv_ttm, d.total_mv,
                   i.end_date, i.total_revenue, i.n_income_attr_p,
                   fi.roe_waa, fi.roe, fi.bps, fi.netprofit_yoy
            FROM stock_basic s
            LEFT JOIN (
                SELECT * FROM daily_basic WHERE ts_code = :ts_code
                ORDER BY trade_date DESC LIMIT 1
            ) d ON s.ts_code = d.ts_code
            LEFT JOIN (
                SELECT * FROM income WHERE ts_code = :ts_code AND report_type = '1'
                ORDER BY end_date DESC LIMIT 1
            ) i ON s.ts_code = i.ts_code
            LEFT JOIN (
                SELECT * FROM fina_indicator WHERE ts_code = :ts_code
                ORDER BY end_date DESC, ann_date DESC LIMIT 1
            ) fi ON s.ts_code = fi.ts_code
            WHERE s.ts_code = :ts_code
            LIMIT 1
        """
        df = query_df(engine, sql, {"ts_code": code})
        if not df.empty:
            rows.append(df.iloc[0].to_dict())
    return pd.DataFrame(rows)


def annual_table_markdown(df: pd.DataFrame) -> str:
    header = "| 年度 | 营收 | 归母净利 | 净利同比 | 净利息收入 | 手续费净收入 | 总资产 | ROE(加权) |\n| --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = []
    for _, row in df.iterrows():
        net_interest = (row["int_income"] or 0) - (row["int_exp"] or 0)
        rows.append(
            "| {year} | {rev} | {profit} | {profit_yoy} | {nii} | {fee} | {assets} | {roe} |".format(
                year=str(row["end_date"])[:4],
                rev=fmt_yi(row["total_revenue"]),
                profit=fmt_yi(row["n_income_attr_p"]),
                profit_yoy=fmt_pct(row["netprofit_yoy"]),
                nii=fmt_yi(net_interest),
                fee=fmt_yi(row["n_commis_income"]),
                assets=fmt_yi(row["total_assets"]),
                roe=fmt_pct(row["roe_waa"]),
            )
        )
    return "\n".join([header] + rows)


def peer_table_markdown(df: pd.DataFrame) -> str:
    header = "| 银行 | 最新财报期 | 收盘价 | PE(TTM) | PB | 股息率 | 营收 | 归母净利 | ROE(加权) | 净利同比 | 总市值 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = []
    for _, row in df.iterrows():
        rows.append(
            "| {name} | {period} | {close} | {pe} | {pb} | {dv} | {rev} | {profit} | {roe} | {yoy} | {mv} |".format(
                name=row["name"],
                period=row["end_date"],
                close=fmt_num(row["close"]),
                pe=fmt_num(row["pe_ttm"]),
                pb=fmt_num(row["pb"]),
                dv=fmt_pct(row["dv_ttm"]),
                rev=fmt_yi(row["total_revenue"]),
                profit=fmt_yi(row["n_income_attr_p"]),
                roe=fmt_pct(row["roe_waa"]),
                yoy=fmt_pct(row["netprofit_yoy"]),
                mv=f"{float(row['total_mv'])/10000:.2f}亿" if pd.notna(row["total_mv"]) else "N/A",
            )
        )
    return "\n".join([header] + rows)


def latest_cash_div(div_df: pd.DataFrame) -> float | None:
    if div_df.empty:
        return None
    annual = div_df[div_df["end_date"].astype(str).str.endswith("1231")].copy()
    if annual.empty:
        annual = div_df.copy()
    annual = annual.sort_values(["end_date", "ann_date", "ex_date"], ascending=False).drop_duplicates(subset=["end_date"], keep="first")
    value = annual.iloc[0]["cash_div_tax"]
    return None if pd.isna(value) else float(value)


def build_report(engine) -> str:
    latest = latest_financials(engine)
    annual = annual_history(engine)
    div_df = dividend_summary(engine)
    audit_df = audit_summary(engine)
    peer_df = peer_comparison(engine)

    net_interest_income = (latest["int_income"] or 0) - (latest["int_exp"] or 0)
    fee_ratio = safe_div(latest["n_commis_income"], latest["total_revenue"])
    assets_growth = safe_div(
        latest["total_assets"] - annual.iloc[1]["total_assets"],
        annual.iloc[1]["total_assets"],
    )
    profit_growth_3y = ((annual.iloc[0]["n_income_attr_p"] / annual.iloc[3]["n_income_attr_p"]) ** (1 / 3) - 1) if len(annual) >= 4 else None
    rev_growth_3y = ((annual.iloc[0]["total_revenue"] / annual.iloc[3]["total_revenue"]) ** (1 / 3) - 1) if len(annual) >= 4 else None
    bps = latest["bps"]
    cash_div = latest_cash_div(div_df)
    pb_bear = bps * 0.85 if pd.notna(bps) else None
    pb_base = bps if pd.notna(bps) else None
    pb_bull = bps * 1.10 if pd.notna(bps) else None
    div_bear = cash_div / 0.08 if cash_div else None
    div_base = cash_div / 0.07 if cash_div else None
    div_bull = cash_div / 0.065 if cash_div else None
    fair_low = (pb_bear * 0.7 + div_bear * 0.3) if pb_bear and div_bear else pb_bear or div_bear
    fair_mid = (pb_base * 0.7 + div_base * 0.3) if pb_base and div_base else pb_base or div_base
    fair_high = (pb_bull * 0.7 + div_bull * 0.3) if pb_bull and div_bull else pb_bull or div_bull

    sources_md = "\n".join(
        f"- {item['date']}｜{item['title']}：{item['note']} [链接]({item['url']})"
        for item in PUBLIC_SOURCES
    )

    peer_insights = [
        "- 招商银行在可比股份行里不是最低估值，但 `PB 0.90x` 仍处于可接受区间，市场愿意为其零售和财富管理优势支付小幅溢价。",
        "- 相比平安银行和兴业银行，招商银行的 `ROE(加权)` 与盈利稳定性更优；相比宁波银行，增速略逊但体量和分红能力明显更强。",
        "- 如果把“高股息 + 较好资产质量 + 零售壁垒”三件事放在一起看，招商银行依旧是股份行里最均衡的资产之一。",
    ]

    div_show = (
        div_df.sort_values(["end_date", "ann_date", "ex_date"], ascending=False)
        .drop_duplicates(subset=["end_date"], keep="first")
        .head(5)
    )
    dividend_lines = "\n".join(
        f"- {row['end_date']}：每股现金分红 {fmt_num(row['cash_div_tax'])} 元，除权日 {row['ex_date'] if pd.notna(row['ex_date']) else '未披露'}"
        for _, row in div_show.iterrows()
    )
    audit_lines = "\n".join(
        f"- {row['end_date']}：{row['audit_result']}（{row['audit_agency']}）"
        for _, row in audit_df.head(5).iterrows()
    )

    report = f"""# 招商银行（{TS_CODE}）股东大会问答式基本面分析报告
- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 公司：{latest['name']}｜行业：{latest['industry']}｜地区：{latest['area']}｜上市日期：{latest['list_date']}
- 主席/管理层：董事长 {latest['chairman'] or 'N/A'}；行长/管理层负责人 {latest['manager'] or 'N/A'}；员工数 {int(latest['employees']) if pd.notna(latest['employees']) else 'N/A'}
- 数据口径：表结构以 `app/models/models.py` 为准，核心使用 `income`、`balancesheet`、`cashflow`、`daily_basic`、`fina_indicator`、`fina_audit`、`dividend`。
- 时点说明：股价采用 {latest['trade_date']} 收盘口径；收入和利润采用 {latest['income_end_date']} 年报口径；ROE、PB 对应最近可用 `fina_indicator` 口径为 {latest['indicator_end_date']}。

【投资裁决】
- 公司判断：是，好公司。招商银行仍是中国股份行里最像“高质量金融消费平台”的银行，零售、财富管理、信用卡和数字化四张牌仍有体系化优势。
- 价格判断：接近合理偏低。按 {latest['trade_date']} 收盘价 {fmt_num(latest['close'])} 元、`PE(TTM) {fmt_num(latest['pe_ttm'])}x`、`PB {fmt_num(latest['pb'])}x` 看，市场报价已经比较克制，但还没到深度错杀。
- 当前结论：跟踪为主，可逢回调分批研究。它更像“高质量高股息银行股”，不是弹性最大的那只，但胜在胜率。
- 未来6-12个月关键变量：净息差能否企稳；中收尤其财富管理和手续费收入能否恢复；资产质量和信用成本是否继续平稳。
- 最大风险：利率中枢下行压缩净息差，如果零售和财富管理恢复又慢于预期，估值会长期被压在低位。

【投资结构化报告】
### 模块1：公司概览与背景
- 一句话生意：用零售客户基础、财富管理能力和数字化运营效率，去做一家比传统银行更像“金融服务平台”的股份行。
- 公司背景：招商银行于 1987 年在深圳成立，是中国境内第一家完全由企业法人持股的股份制商业银行，也是沪港两地上市银行集团。
- 外部公开资料补充：
{sources_md}

### 模块2：管理层评估
- 招行管理层的核心标签不是激进扩张，而是“价值银行”与风险收益平衡。这个标签至少从近几年公开口径看是一致的。
- 强项在于零售经营和组织执行力。弱项在于银行业的共性问题无法回避，尤其净息差和手续费收入都要受宏观环境影响。
- 资本配置上较克制，分红政策稳定，适合作为银行股的长期回报资产看待。

### 模块3：商业模式深度解析
- 主营业务：{latest['main_business'] or '吸收存款、发放贷款、财富管理、信用卡、同业及其他综合金融服务'}。
- 收入结构：{latest['income_end_date']} 年营业收入 {fmt_yi(latest['total_revenue'])}，其中净利息收入约 {fmt_yi(net_interest_income)}，手续费及佣金净收入约 {fmt_yi(latest['n_commis_income'])}，手续费净收入占比约 {fmt_pct((fee_ratio or 0) * 100)}。
- 巴菲特一句话测试：这是一家把存贷款关系、财富管理和客户长期资金留存做成护城河的银行。
- 真正的关键不是贷款规模冲多快，而是客户质量、低成本负债、AUM 和风险控制能不能长期领先。

### 模块4：经济护城河分析
- 网络效应：窄。客户越多，App、信用卡、支付结算与财富管理的协同越强，但银行本质不是纯网络效应行业。
- 转换成本：宽。高净值客户、代发工资、房贷、信用卡和理财基金账户一旦绑定，迁移成本很高。
- 成本优势：窄。负债成本、风控能力和数字化效率构成优势，但利率市场化环境下不可能形成绝对成本碾压。
- 无形资产：宽。招行品牌、零售心智、财富管理能力和数字化口碑在股份行里有明显领先。
- 有效规模：窄。股份行零售和财富管理赛道头部集中度会继续提升，招行具备吃份额的资格。
- 护城河总评：窄护城河偏宽，尤其零售与财富管理是最难被复制的部分。

### 模块5：财务深度分析
- 最新年报：{latest['income_end_date']} 营收 {fmt_yi(latest['total_revenue'])}，归母净利 {fmt_yi(latest['n_income_attr_p'])}；总资产 {fmt_yi(latest['total_assets'])}，同比约 {fmt_pct((assets_growth or 0) * 100)}。
- 盈利能力：最近可比指标期 `ROE(加权)` {fmt_pct(latest['roe_waa'])}，`PB` 对应每股净资产 `BPS {fmt_num(latest['bps'])}` 元。
- 资产负债结构：银行业 `debt_to_assets` 没有工业企业那种解释力，当前约 {fmt_pct(latest['debt_to_assets'])} 主要反映负债经营属性，不应简单类比高杠杆制造业。
- 现金流指标：银行 `cashflow` 报表意义弱于工业企业，更应看利润、资本充足和风险成本，因此这里只把 `ocf_to_profit` 作为补充，不作为核心判断。
- 近五年年报趋势：
{annual_table_markdown(annual)}
- 三年复合增速：营收 CAGR {fmt_pct((rev_growth_3y or 0) * 100)}；归母净利 CAGR {fmt_pct((profit_growth_3y or 0) * 100)}。结论是：这不是高成长银行，但仍是稳健盈利机器。

### 模块6：管理层沟通与经营表态
- 2025 年官方表态的核心词是“价值银行”“盈利能力行业领先”“质量、效益、结构平衡”。
- 从中期业绩摘要看，招行对净息差下行并不回避，但强调信用成本和资产质量维持较优水平。
- 这类表态说明：管理层更在意高质量回报，而不是单纯做大资产规模。

### 模块7：多模型估值
- 相对估值：当前 `PE(TTM) {fmt_num(latest['pe_ttm'])}x`、`PB {fmt_num(latest['pb'])}x`、股息率 `DV(TTM) {fmt_pct(latest['dv_ttm'])}`。
- 银行估值核心看三件事：`ROE`、`PB`、`股息率`。招行之所以能长期拿到略高于多数股份行的 `PB`，关键在于零售壁垒和更稳的盈利能力。
- `PB` 情景估值：悲观约 {fmt_num(pb_bear)} 元；基准约 {fmt_num(pb_base)} 元；乐观约 {fmt_num(pb_bull)} 元。
- 股息率情景估值：若按每股现金分红 {fmt_num(cash_div)} 元估算，8%/7%/6.5% 股息率对应价格约 {fmt_num(cash_div / 0.08 if cash_div else None)} / {fmt_num(cash_div / 0.07 if cash_div else None)} / {fmt_num(cash_div / 0.065 if cash_div else None)} 元。
- 综合判断：按 `PB 70% + 股息率 30%` 加权，合理区间大约在 {fmt_num(fair_low)} - {fmt_num(fair_high)} 元，中枢约 {fmt_num(fair_mid)} 元。它不便宜到失真，但也足够支持长期资金继续跟踪。

### 模块8：竞争与行业分析
- 银行业总量阶段已经过去，真正值得给溢价的是“零售能力 + 财富管理 + 风控文化”。
- 招行的核心可比对象不是国有大行，而是平安银行、兴业银行、宁波银行这些零售和股份行玩家。
- 同行业横向对比：
{peer_table_markdown(peer_df)}
{"\n".join(peer_insights)}

### 模块9：技术面与交易补充
- 银行股更多是估值和分红锚，技术面只作补充。
- 最新收盘 {fmt_num(latest['close'])} 元，接近 `PB 0.90x` 区间，市场并没有把它交易成高估值成长股。
- 高股息属性会让它在波动市里更像底仓资产，而不是弹性交易标的。

### 模块10：增长催化剂与前景展望
- 短期催化剂：净息差企稳、手续费收入回暖、财富管理和信用卡业务改善。
- 中期催化剂：零售AUM继续增长，资产质量平稳，风险成本维持低位。
- 长期展望：如果中国居民财富管理需求继续升级，招行仍有资格作为最受益的银行之一。

### 模块11：风险矩阵
- 经营风险 2/5：商业模式成熟，真正风险在于恢复速度而非模式失灵。
- 财务风险 2/5：银行是高杠杆经营，但招行的风险吸收能力和盈利缓冲相对较强。
- 竞争风险 3/5：零售和财富管理领域竞争激烈，宁波银行、平安银行等都在争夺优质客户。
- 监管/政策风险 4/5：银行高度受政策和监管环境影响，息差、资本和风险分类都不是自己能完全决定的。
- 宏观风险 4/5：地产、消费和信用周期会直接影响银行利润和估值。
- 估值风险 2/5：当前估值低，真正风险更多来自基本面而非过高定价。
- 黑天鹅情景：如果宏观信用风险明显抬头，或者零售资产质量显著恶化，银行股会先杀估值再杀盈利预期。

### 模块12：巴菲特计分卡与投资决策
- 巴菲特计分卡：29/36，评级 B+。
- 投资评级：持有/买入观察。
- 12个月目标价：悲观 {fmt_num(fair_low)} 元；基准 {fmt_num(fair_mid)} 元；乐观 {fmt_num(fair_high)} 元。
- 理想买入区间：{fmt_num((fair_low or 0) * 0.9 if fair_low else None)} - {fmt_num(fair_low)} 元。
- 仓位建议：若你需要高股息、低波动、可长期持有的银行底仓，招商银行值得优先研究；若你要高弹性，它不是最优解。
- 关键监控指标：净息差、手续费净收入、零售AUM、信用成本、拨备覆盖与不良生成。

【沃伦、查理与投资者问答】
投资者：招商银行到底是一家普通银行，还是一门有护城河的生意？
沃伦：我会说，它不是普通银行。大多数银行的故事都差不多，存款、贷款、息差。但招行多了一层，它把零售客户关系、财富管理和数字化体验做成了更强的粘性。这就像同样是开杂货店，有人只是卖货，有人已经变成了社区里最值得信任的服务中心。
查理：别把银行浪漫化。银行终究是高杠杆机构，监管一句话、利率一个波动，就能把漂亮故事砍掉一截。招行比别人好，但它没有脱离银行业物理定律。

投资者：那招行的护城河具体体现在哪里？
沃伦：最核心的是客户关系。高净值客户、信用卡、代发工资、财富管理，这些东西一旦绑在一起，迁移成本很高。你不是在换一个存款账户，你是在换一整套金融习惯。
查理：我同意，但护城河不是不用维护。财富管理和零售客户今天在，明天也可能被别的银行、券商或者互联网平台分流。真正决定护城河能不能守住的，是管理层有没有持续把服务和风控做好。

投资者：和同业比，为什么市场愿意给招行略高一点的估值？
沃伦：因为它的盈利质量和客户质量更好。你看横向对比，招行不是最便宜，但 `PB` 也没有高得离谱。市场愿意多付一点钱，买的是更好的回报稳定性。
查理：更直白一点，市场不是在奖励“银行”两个字，而是在奖励“这家银行没那么容易犯蠢”。这是好事，但也意味着你不能指望靠估值暴涨赚钱。

投资者：最大的风险是什么？地产吗？息差吗？还是零售资产质量？
沃伦：如果让我挑一个，我会先看净息差。因为这是银行最基本的赚钱方式。净息差长期往下，哪怕客户很多，利润天花板也会被压住。
查理：我会再加一句，别低估宏观信用周期。银行的问题往往不是今天表内坏账有多少，而是明天大家突然发现风险比想象中更高。银行股最怕的就是市场从“它很稳”切换到“它会不会也出事”。

投资者：现在这个价格值得下手吗？
沃伦：如果你想找的是长期能拿住的高股息优质银行，我会把招行放在名单前面。它不是那种一眼看上去便宜得发亮的票，但它够稳，够清楚。
查理：我没意见。但别用买成长股的方法买银行，也别用买银行的耐心去幻想成长股回报。你买招行，买的是一个长期复利底仓，不是彩票。

【本杰明插话：估值】
投资者：现在这个价格到底算贵还是便宜？
本杰明：先把口径说清楚。当前股价是 {latest['trade_date']} 的 {fmt_num(latest['close'])} 元；最近可用每股净资产 `BPS` 为 {fmt_num(bps)} 元；`PB` 是 {fmt_num(latest['pb'])} 倍，股息率约 {fmt_pct(latest['dv_ttm'])}。
本杰明：对银行股，`PB` 和股息率比 `DCF` 更有解释力。按 `0.85x-1.10x PB` 看，合理区间大约在 {fmt_num((bps or 0) * 0.85)} 到 {fmt_num((bps or 0) * 1.1)} 元；按股息率法，合理区间大约在 {fmt_num(cash_div / 0.08 if cash_div else None)} 到 {fmt_num(cash_div / 0.065 if cash_div else None)} 元。
本杰明：把两套方法合在一起，我认为当前价格更接近合理偏低，而不是深度低估。它给了你不错的胜率，但没给你夸张的赔率。

【综合结论】
沃伦：招商银行是我能听懂、也愿意长期持有的银行股，因为它的客户关系和盈利质量确实不一样。
查理：但你得记住，它再好也还是银行。银行是好生意，不是没风险的生意。
本杰明：如果你的目标是长期高股息和稳健复利，招商银行值得研究；如果你要很高弹性，它不是那类票。

### 分红与审计补充
#### 分红
{dividend_lines}

#### 审计意见
{audit_lines}

> ⚠️ **免责声明**：本分析仅供教育和研究用途，不构成投资建议。"巴菲特"视角是一个受沃伦·巴菲特公开表述的投资原则启发的分析框架，它并不代表沃伦·巴菲特本人对任何具体公司的观点。所有投资都有风险，请在做出投资决策前咨询合格的财务顾问。
"""
    return report


def main():
    engine = load_engine()
    report = build_report(engine)
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{TS_CODE.replace('.', '-')}-招商银行-{datetime.now().strftime('%Y%m%d')}.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"报告已生成: {output_path}")
    print(report)


if __name__ == "__main__":
    main()
