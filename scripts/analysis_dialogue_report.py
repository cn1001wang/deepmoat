import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"

PUBLIC_CONTEXT = {
    "600887.SH": [
        {
            "date": "2025-04-29",
            "source": "伊利官网/2024年年报及2025年一季报解读",
            "url": "https://www.yili.com/uploads/2025-04-29/478095e5-22ea-40f7-87eb-7d55651a0ad51745927217322.pdf",
            "note": "2024年营收1157.80亿元，剔除商誉减值后净利润115.39亿元；2024年度拟分红77.26亿元，叠加回购后股东回报总额占利润比例约100.4%。",
        },
        {
            "date": "2025-08-28",
            "source": "伊利官网/2025年半年度报告",
            "url": "https://www.yili.com/uploads/2025-08-28/501a4412-a5b8-47fa-ae5f-3ce48eadb2911756372681806.pdf",
            "note": "2025年上半年营收619.33亿元，同比增长3.37%；扣非归母净利润70.16亿元，同比增长31.78%。",
        },
        {
            "date": "2025-10-30",
            "source": "伊利官网/2025年前三季度业绩解读",
            "url": "https://www.yili.com/news/company/5214",
            "note": "公司披露低温白奶营收及市场份额双增长，奶粉业务份额继续扩大，创新与渠道协同仍是经营主轴。",
        },
        {
            "date": "2026-02-28",
            "source": "国家统计局/2025年国民经济和社会发展统计公报",
            "url": "https://www.stats.gov.cn/zwfwck/sjfb/202602/t20260228_1962662.html",
            "note": "2025年全国牛奶产量4091万吨，同比增长0.3%；年末全国人口140489万人，全年出生人口792万人，乳品需求总量增长偏缓但结构升级继续。",
        },
    ],
    "605499.SH": [
        {
            "date": "2026-02-03",
            "source": "东鹏饮料官网/香港主板上市新闻",
            "url": "https://www.szeastroc.com/news/218.html",
            "note": "公司披露过去5年业绩复合增长率超30%，2025年营收突破200亿元；东鹏补水啦上市三年跃升为中国电解质饮料第一品牌，2025年前三季度营收28.47亿元，同比增长134.78%。",
        },
        {
            "date": "2026-01-31",
            "source": "东鹏饮料官网/印尼三林集团战略合作",
            "url": "https://www.szeastroc.com/news/216.html",
            "note": "公司宣布与印尼三林集团合作，东鹏饮料拟投资不超过2亿美元，推进印尼生产基地和销售体系建设，国际化进入实质落地阶段。",
        },
        {
            "date": "2025-09-16",
            "source": "东鹏饮料官网/凯度BrandZ中国品牌百强",
            "url": "https://www.szeastroc.com/news/187.html",
            "note": "东鹏饮料连续第四年登榜凯度BrandZ中国品牌百强，排名升至第44位，品牌价值42.18亿美元，同比增长73%。",
        },
        {
            "date": "2026-03-16",
            "source": "国家统计局/2026年1-2月社会消费品零售总额",
            "url": "https://www.stats.gov.cn/sj/zxfb/202603/t20260316_1962786.html",
            "note": "2026年1-2月饮料类零售额同比增长6.0%，消费总盘子仍在增长，但饮料赛道竞争对新品与渠道效率的要求更高。",
        },
    ],
    "300274.SZ": [
        {
            "date": "2025-04-26",
            "source": "阳光电源官网/2024年年度报告",
            "url": "https://cn.sungrowpower.com/storage/notice/iXCWPvAKdPMskX1nig8hGmY30qPWz5W19blFWDE9.pdf",
            "note": "2024年营收778.57亿元，同比增长7.76%；其中储能收入249.59亿元，同比增长40.21%，储能系统毛利率36.69%。",
        },
        {
            "date": "2025-07-16",
            "source": "阳光电源官网/沙特7.8GWh全球最大储能项目",
            "url": "https://cn.sungrowpower.com/news/1556.html",
            "note": "公司签约沙特ALGIHAZ 7.8GWh储能项目，项目于2025年全容量并网运行，进一步验证其全球大储交付与构网能力。",
        },
        {
            "date": "2025-09-30",
            "source": "阳光电源官网/2025大事件",
            "url": "https://cn.sungrowpower.com/news_key/1677/2.html",
            "note": "公司2025年持续围绕光、风、储、电、氢布局，构网储能、风电变流器和全球化交付是全年经营主轴之一。",
        },
        {
            "date": "2026-01-08",
            "source": "阳光电源官网/2026全球合作伙伴大会",
            "url": "https://cn.sungrowpower.com/news/1678.html",
            "note": "公司披露2025年各项业务稳健增长，并明确2026-2030年继续聚焦光风储电氢五大赛道，强调全球化协同与供应链韧性。",
        },
    ],
}

COMPANY_PROFILES = {
    "600887.SH": {
        "latest_notice": "按今天 2026-04-14 的时点，伊利尚未在本地库中体现 2025 年年报，因此最新定期财务判断以 2025 年三季报为主。",
        "company_quality": "伊利仍是中国乳业里最容易理解、现金流最扎实、品牌和渠道最成体系的龙头之一。",
        "price_desc": "市场给的是稳健消费龙头估值，不是困境甩卖价。",
        "judgement_desc": "适合长线组合当作消费防守核心跟踪，不适合把它幻想成高增长弹性票。",
        "key_vars": "液体乳价格战是否缓和；奶粉和功能营养品能否继续提升利润结构；原奶与渠道库存周期是否继续改善。",
        "max_risk": "人口与出生数下行压制行业天花板，若公司为了守份额持续高促销，高ROE会继续缓慢下台阶。",
        "one_line_business": "把奶做成全国性高频消费品牌，再靠渠道、冷链、研发和品类扩张赚取规模利润。",
        "background": "是A股乳业龙头，核心版图覆盖液体乳、冷饮、奶粉及奶制品，并尝试向健康饮品、功能营养和乳深加工延展。",
        "management_style": "管理层风格更像成熟消费品运营者，而不是激进资本玩家。",
        "shareholder_return": "股东友好度较高：2024年度拟分红77.26亿元，并配合回购计划，显示出较明确的资本回报意识。",
        "management_risk": "风险点在于：公开表达更多强调增长与创新，较少正面展开讨论液奶成熟期带来的长期估值天花板。",
        "main_business_fallback": "液体乳、冷饮、奶粉及奶制品",
        "revenue_engine": "常温液奶提供体量，冷饮提供品牌曝光与季节利润，奶粉和功能营养承担结构升级，海外与B2B渠道贡献增量。",
        "buffett_test": "这是一家把高频必需消费品品牌化、渠道化、全国化并持续做新品迭代的公司。",
        "unit_economics": "品牌广告、渠道覆盖和供应链规模决定利润中枢；一旦价格战激烈，毛利率和费用率会同时承压。",
        "moat": [
            ("网络效应", "无", "乳制品不是网络效应生意，规模大并不会让单个消费者对产品更依赖。"),
            ("转换成本", "窄", "家庭乳品消费具习惯性，但货架竞争强，转换成本更多来自品牌信任而非系统锁定。"),
            ("成本优势", "窄", "龙头采购、渠道、冷链、广告投放和供应链数字化带来规模优势，但原奶和促销仍会侵蚀利润。"),
            ("无形资产", "宽", "伊利品牌、质量心智、全国化渠道与冷链网络长期积累，尤其在常温奶、高端白奶、成人奶粉领域更强。"),
            ("有效规模", "窄", "全国乳业龙头寡头格局较稳，但细分赛道仍不断有区域和新品类玩家冲击。"),
        ],
        "moat_total": "窄护城河偏强，接近宽护城河边缘",
        "moat_trend": "整体稳定，但传统液奶品类面临人口与消费疲弱的慢性侵蚀，功能营养与奶粉是护城河续命点。",
        "comms_1": "2025年管理层主轴很清晰：守住液奶基本盘，继续押注奶粉、功能营养、乳深加工和渠道数字化。",
        "comms_2": "前后口径基本一致：从2024年主动调整，到2025年强调轻装上阵、新增长轨道，再到三季报强调低温白奶和奶粉份额提升，说明战略没有大幅摇摆。",
        "pe_comment": "乳业龙头但增长放缓，给16-22倍TTM PE较合适。",
        "reverse_dcf_note": "这说明市场对伊利并没有给出激进增长定价，但也要注意 2024 年现金流受营运资金回收提振，DCF 与所有者盈余法更适合作为上限参考。",
        "industry_lines": [
            "行业层面：乳业总量增长慢，结构升级快。原奶供需与出生率共同压制行业想象空间，但高端白奶、成人奶粉、功能营养和奶酪仍有结构性机会。",
            "竞争层面：伊利的全国渠道、品牌密度和冷链能力仍是最强武器；真正的对手不是单一公司，而是成熟行业下的促销竞争与新品类替代。",
            "波特五力简述：上游原奶价格波动中等；下游商超、电商、会员店议价力较强；新进入者做全国龙头难，但细分品类破局并不难；行业内竞争始终激烈。",
        ],
        "catalysts_short": "年报分红落地、原奶价格回落带来的毛利修复、功能营养新品放量、奶粉和低温奶份额变化。",
        "catalysts_mid": "乳深加工带来的原料国产化和高附加值突破，海外业务和B2B渠道继续扩张。",
        "long_term": "到2030年，伊利大概率还是中国乳业龙头，但估值重定价更依赖利润结构升级，而不是单纯收入规模扩张。",
        "black_swan": "若行业进入长期低价竞争且新品类扩张失败，伊利会从高质量消费龙头降级为低增长现金奶牛，估值中枢继续下移。",
        "monitoring": "液奶市占率、奶粉收入占比、经营现金流/净利润、毛利率、原奶价格、分红与回购执行。",
        "risk_matrix": [
            "经营风险 3/5：核心风险不在经营失控，而在成熟品类增长慢、促销投入高。",
            "财务风险 2/5：现金流总体稳，但流动比率偏低，需盯住短债与现金调度。",
            "竞争风险 4/5：护城河强但不绝对，行业价格战会持续磨利润。",
            "监管/政策风险 2/5：食品安全和广告合规是底线风险，一旦出事破坏力极大。",
            "宏观风险 3/5：出生率、消费信心和渠道去库存节奏都影响需求恢复。",
            "估值风险 3/5：当前估值并不昂贵，但已基本反映“龙头稳定”的预期。",
        ],
        "positioning": "若是防守型消费配置，可分三次布局；若追求高收益弹性，这只票不是最优解。",
        "dialogue": [
            "沃伦：先别看股价，先看生意。伊利这门生意不复杂，就是把消费者每天能喝、能吃、能记住的乳制品做成品牌，再把渠道铺到全国。这样的生意我愿意花时间看，因为它不是靠技术魔法赚钱，而是靠品牌、渠道、冷链、供应链和消费者心智赚钱。",
            "沃伦：护城河在哪里？最硬的一段在品牌和渠道。一个家庭换手机可能几年一次，换牛奶其实随时可以，但真正愿意长期复购的牌子不多。伊利把这件事做成了全国规模。你在县城、地级市、一线城市都能看到它，这是很难被复制的。",
            "查理：我同意它不是坏生意，但别把“全国都能看到”误解成“永远都能赚更多钱”。乳业是成熟行业，不是滚烫的新大陆。人口在下滑，出生数也不好看，行业总量增长慢，货架上竞争一点也不温柔。一个好品牌碰上一个增长慢的行业，回报率照样会下台阶。",
            "沃伦：这正是我为什么还愿意看它。成熟行业里，强者通常更强。别人难受时，龙头能活得更体面。看现金流就知道了，伊利不是纸面利润公司，过去几年经营现金流兑现得相当好，这一点我很看重。",
            "查理：现金流不错，我不反对。但你别忘了另一个事实，ROE从前些年的高位往下走了，流动比率也不高。它现在更像一台效率不错的现金机器，而不是一只还在快速加速的赛马。市场要是把它当高成长来定价，那就会犯愚蠢错误。",
            "沃伦：所以我不会把它当高成长。我把它看成高质量消费龙头，靠稳健现金流、分红和有限增长复利。要是价格对，就值得持有。",
            "查理：问题就在“要是价格对”。今天这个价，不便宜得让我兴奋，也没贵到让我厌烦。它卡在一个很麻烦的位置：够好，但不够便宜；够稳，但不够快。",
            "沃伦：那就别勉强挥棒。好公司不是任何价格都可以买。伊利值得放在名单里，等市场先生哪天心情差一点，再递给你更好的报价。",
            "查理：还有一件事。别只盯着液奶。真正决定它未来估值上不上去的，是奶粉、功能营养、乳深加工这些能不能把利润结构抬高。要是这些新故事最后只是更贵的宣传册，那就没什么意思了。",
        ],
        "benjamin_opening": "本杰明：两位先停一下。公司好不好是一回事，今天这个价格值不值是另一回事。我现在用 2024 年所有者盈余近似股权现金流，以 2026-04-14 的收盘价和总股本口径校准。",
        "benjamin_wrap": "本杰明：我不反对买好公司，我反对把“好公司”三个字当成忽略价格的许可证。伊利现在更像偏低位的优质资产，但还没低到让我失去纪律。",
        "closing": [
            "沃伦：伊利是中国乳业里少数我能看得懂、也愿意长期跟踪的公司，生意质量过关。",
            "查理：但我最大的保留意见也很简单，行业慢、人口慢、增长慢，任何对高增长的幻想都不值得付钱。",
            "本杰明：当前价格更接近合理偏低，而非深度低估。想要更舒服的安全边际，最好等它回到更便宜的区间。",
        ],
        "pe_range": (16, 19, 22),
        "owner_yield": (0.06, 0.055, 0.05),
        "dcf_assumptions": [(0.03, 0.09, 0.02), (0.05, 0.09, 0.025), (0.07, 0.085, 0.03)],
    },
    "605499.SH": {
        "latest_notice": "按今天 2026-04-14 的时点，本地库已覆盖到 2025 年年报三大表，但 `fina_indicator` 最新只到 2025-09-30，因此利润规模采用 2025 年年报，ROE、毛利率和周转效率等质量指标以最近一份可用的 2025 年三季报补充说明。",
        "company_quality": "东鹏饮料是A股少数仍在高增长的消费品公司，渠道下沉、单品爆款和多品类复制能力都比一般饮料公司更强。",
        "price_desc": "市场给的是高成长消费股估值，不是便宜资产价。",
        "judgement_desc": "适合列入高质量消费成长跟踪池，但更适合等波动给安全边际，而不是在情绪高位追价。",
        "key_vars": "东鹏特饮能否继续稳住份额；补水啦能否从爆品走向长青单品；国际化和多品类扩张是否能消化高估值预期。",
        "max_risk": "核心风险不是增长消失，而是增长从高位回落时，估值压缩速度可能比业绩增速更快。",
        "one_line_business": "把能量饮料打进全国低线城市和高密度终端，再沿着同一套渠道卖电解质水、茶饮、咖啡和更多高频即饮产品。",
        "background": "是A股功能饮料龙头，公司以东鹏特饮为核心现金牛，围绕“1+6”多品类战略推进补水啦、茶饮、咖啡和椰汁等新品扩张，并尝试走向海外。",
        "management_style": "管理层明显带有创始人驱动色彩，执行强、下沉深、讲究渠道效率和费用投放回报。",
        "shareholder_return": "股东回报并不吝啬，近几年现金分红积极，但公司本质上仍是成长型消费股，资金更该看再投资效率。",
        "management_risk": "风险点在于：创始人色彩浓、核心单品权重高，一旦新品复制不及预期，市场会迅速把它从成长股重估为单品公司。",
        "main_business_fallback": "能量饮料、电解质饮料、茶饮、咖啡及其他即饮饮料",
        "revenue_engine": "东鹏特饮贡献利润底座，补水啦贡献高增量，其他新品负责验证多品类复制能力，经销商体系和终端密度是放大的杠杆。",
        "buffett_test": "这是一家把一个爆款饮料做成全国渠道机器，再试图把第二个、第三个爆款塞进同一条分销管道的公司。",
        "unit_economics": "单位经济取决于终端密度、冰柜与陈列效率、经销商激励和广告投放回收。一旦新品转化率不够，费用率就会先抬头。",
        "moat": [
            ("网络效应", "无", "饮料消费不是网络效应，但高频购买和渠道陈列会放大头部品牌优势。"),
            ("转换成本", "窄", "消费者随时可以换别的饮料，但功能饮料场景和价格带习惯会形成弱粘性。"),
            ("成本优势", "窄", "PET包装、供应链规模、终端密度和经销商网络带来成本与执行优势，但原料和促销竞争会吞噬一部分红利。"),
            ("无形资产", "宽", "东鹏特饮在功能饮料里已经形成强认知，补水啦也在抢占电解质饮料心智。"),
            ("有效规模", "窄", "能量饮料和大众即饮赛道允许多家玩家共存，但全国化深分销网络并不容易复制。"),
        ],
        "moat_total": "窄护城河偏强，品牌与渠道已经形成组合壁垒",
        "moat_trend": "主品牌护城河仍在加固，真正决定护城河变宽还是变窄的，是补水啦和其他新品能否证明多品类复制成立。",
        "comms_1": "2025年管理层主轴很清晰：继续夯实东鹏特饮龙头地位，同时用补水啦和其他新品把“1+6”多品类战略做成第二增长曲线。",
        "comms_2": "外部公开表态从品牌升级、渠道下沉逐渐转向多品类与国际化，说明公司已经不满足于单一功能饮料标签。",
        "pe_comment": "成长型饮料龙头仍值得享受20-28倍TTM PE，但前提是高增长不能明显失速。",
        "reverse_dcf_note": "这说明市场已经把较高增长写进价格，但并没有预设夸张到失真的永续高增；问题在于，一旦增速降档，估值回撤会很快。",
        "industry_lines": [
            "行业层面：能量饮料和即饮饮料仍有结构性增长，县乡市场、运动补水场景和便利终端扩容都在给头部品牌机会。",
            "竞争层面：东鹏的核心对手不是单一上市公司，而是红牛、乐虎、魔爪以及一切想抢便利店冰柜和夫妻店货架的饮料品牌。",
            "波特五力简述：上游糖、PET、包装材料会影响毛利；下游经销商和终端资源决定放量效率；新品类进入门槛不高，但做成全国化深分销品牌很难。",
        ],
        "catalysts_short": "年报业绩兑现、补水啦延续高增、茶饮和咖啡新品动销、海外项目推进。",
        "catalysts_mid": "印尼等海外产能与渠道落地、多品类收入占比上升、品牌力继续外溢到更多即饮赛道。",
        "long_term": "到2030年，东鹏若能把东鹏特饮之外再养出两到三个十亿级品类，公司会从单品爆款企业进化成真正的多品类饮料集团。",
        "black_swan": "若核心大单品增速下台阶，而补水啦及其他新品又无法接棒，市场会迅速把东鹏从成长龙头估值打回传统饮料股估值。",
        "monitoring": "东鹏特饮收入增速、补水啦收入占比、全国终端数量、销售费用率、经营现金流/净利润、海外项目推进。",
        "risk_matrix": [
            "经营风险 3/5：核心风险在于东鹏特饮单品依赖仍高，新品矩阵的接棒速度需要持续验证。",
            "财务风险 2/5：现金流不错，但渠道扩张与新品推广会持续消耗营运资金。",
            "竞争风险 4/5：能量饮料、电解质水和即饮赛道都不缺强竞争者，货架与冰柜位置永远在争夺。",
            "监管/政策风险 2/5：食品安全、广告宣传和渠道合规是底线风险。",
            "宏观风险 2/5：大众即饮消费韧性较强，但消费降级会影响新品价格带扩张。",
            "估值风险 4/5：成长股估值对增速变化极敏感，业绩稍低于预期就可能触发杀估值。",
        ],
        "positioning": "若组合接受成长股波动，可小仓位跟踪；若偏绝对收益，最好等更深回撤后再动手。",
        "dialogue": [
            "沃伦：这家公司最吸引我的地方，是它不是先讲梦想，再找生意；它是先把一个爆款做透，再去扩第二个。东鹏特饮把渠道密度做出来后，整个公司就从一个产品，变成了一台饮料分发机器。",
            "沃伦：真正的价值不只在配方，而在货能不能铺到足够多的终端，冰柜能不能站住位置，经销商愿不愿意持续推。这样的生意一旦跑通，后来者就很难只靠一个广告抢回来。",
            "查理：别把渠道机器说得太浪漫。饮料行业的坏处在于，消费者一点也不忠诚，货架永远拥挤，今天是功能饮料，明天是电解质水，后天又是无糖茶。你必须不断证明自己，不然冰柜里的位置就会被别人拿走。",
            "沃伦：你说得对，所以我不会把它看成永远轻松的护城河。但我得承认，东鹏做下沉渠道的执行力非常强。很多公司有品牌，没有系统；很多公司有系统，没有第二增长曲线。东鹏现在两样都在尝试补齐。",
            "查理：我更关心另一件事。市场已经默认它不只是东鹏特饮了，默认补水啦、茶饮、咖啡都能长出来。只要其中两三个不达预期，估值就会先杀一轮。",
            "沃伦：这也是为什么价格很重要。公司好，不代表今天就一定好买。你要分清楚你买的是企业，还是买了别人对企业的热情。",
            "查理：还有创始人风险。创始人驱动的好处是打仗快，坏处是很多能力容易被误认成永远存在。只要组织复制没跟上，增长放缓时暴露得更明显。",
            "沃伦：所以我会继续跟。真要出手，我更想等市场把高增长打个折，再看这家公司还剩下多少真实护城河。",
            "查理：一句话，生意不错，价格不软。好球，但不一定是现在这一球。",
        ],
        "benjamin_opening": "本杰明：先把热情放一边。东鹏是成长股，不是债券替代品。我这里用 2025 年所有者盈余近似股权现金流，再用 2026-04-14 的收盘价和总股本口径校准。",
        "benjamin_wrap": "本杰明：我不怀疑公司质量，我怀疑的是买入价格是否给了足够犯错空间。成长股最怕的不是企业变坏，而是估值先不肯原谅你。",
        "closing": [
            "沃伦：东鹏饮料是一家我愿意持续跟踪的高质量消费成长股，尤其值得看它如何把第二曲线做成真生意。",
            "查理：我的保留意见很明确，单品依赖和高估值是双重考验，任何一头松动，股价都会先反应。",
            "本杰明：当前价格更接近合理偏上，而不是深度低估。等回调买，比在热度上头时追，更像理性的做法。",
        ],
        "pe_range": (20, 24, 28),
        "owner_yield": (0.05, 0.045, 0.04),
        "dcf_assumptions": [(0.08, 0.09, 0.03), (0.10, 0.09, 0.03), (0.12, 0.085, 0.035)],
    },
    "300274.SZ": {
        "latest_notice": "按今天 2026-04-14 的时点，本地库已覆盖到 2025 年年报三大表，但 `fina_indicator` 最新只到 2025-09-30，因此收入、利润和现金流采用 2025 年年报，ROE、毛利率与周转效率等质量指标以 2025 年三季报口径补充说明。",
        "company_quality": "阳光电源是光储逆变器与储能系统环节里最具全球竞争力的中国龙头之一，规模、盈利和现金流都明显强于多数可比公司。",
        "price_desc": "市场给的是龙头溢价，但没有把它炒到离谱的极端估值。",
        "judgement_desc": "适合放进新能源设备核心观察名单，若组合里本来就想配光储龙头，它比大多数同业更值得优先研究。",
        "key_vars": "海外大储项目交付节奏；储能系统毛利率能否维持；光伏逆变器竞争是否进一步加剧；新能源开发业务的波动是否拖累整体估值。",
        "max_risk": "最大风险不是公司失去竞争力，而是行业价格战和项目节奏波动让利润表阶段性大起大落，进而压缩估值。",
        "one_line_business": "把逆变器、电池管理、电网控制和系统集成做到全球领先，再用同一套电力电子能力去吃下光伏、储能、风电、充电和氢能的增量。",
        "background": "是全球光储龙头之一，核心业务包括光伏逆变器、储能系统、新能源投资开发及电站相关业务，并沿风电、充电和氢能延展。",
        "management_style": "管理层带有强技术和强工程交付特征，风格偏长期投入而不是短期讲故事。",
        "shareholder_return": "公司更像成长型制造科技龙头，股东回报要看资本配置效率和现金流沉淀，而不是单独盯住分红。",
        "management_risk": "风险点在于：业务线很多，报表里既有高质量设备收入，也有波动更大的开发业务，投资者如果只看总营收容易误判质量。",
        "main_business_fallback": "光伏逆变器、储能系统、新能源投资开发及其他新能源相关业务",
        "revenue_engine": "逆变器提供稳定全球份额，储能系统贡献高增量和更强技术壁垒，新能源开发业务放大收入体量但也会增加波动。",
        "buffett_test": "这是一家用电力电子技术做底座，把全球新能源基础设施里的关键设备和系统集成都吃下来的公司。",
        "unit_economics": "单位经济核心看设备毛利率、海外订单质量、系统集成能力和大项目交付回款效率，而不是只看出货规模。",
        "moat": [
            ("网络效应", "无", "这不是典型网络效应行业，但装机案例和客户认证会增强项目获取能力。"),
            ("转换成本", "窄", "大型电站和储能客户更看重长期可靠性、认证和服务体系，切换供应商成本高于普通制造业。"),
            ("成本优势", "窄", "规模采购、研发平台和全球化制造交付能力带来成本优势，但行业价格战会持续侵蚀一部分利润。"),
            ("无形资产", "宽", "Sungrow 品牌、全球认证体系、构网储能技术和历史项目案例构成明显壁垒。"),
            ("有效规模", "窄", "全球高端光储系统市场不可能无限容纳玩家，头部厂商会持续集中，但仍有华为、特斯拉等强敌。"),
        ],
        "moat_total": "窄护城河偏宽，技术、品牌和全球交付共同构成壁垒",
        "moat_trend": "护城河整体仍在加深，尤其储能系统和构网能力强化了差异化，但行业竞争会不断测试其价格纪律。",
        "comms_1": "2025年管理层主轴很清晰：在光、风、储、电、氢五大赛道继续强化技术领先、全球交付和数智化。",
        "comms_2": "公开口径持续强调构网储能、全球化与供应链韧性，说明公司希望市场按全球能源基础设施平台来理解它，而不是单一逆变器厂商。",
        "pe_comment": "光储龙头兼具周期与成长属性，给18-24倍TTM PE更合理，高于普通设备股但低于纯故事成长股。",
        "reverse_dcf_note": "这意味着市场要求的未来增长并不离谱，但新能源设备行业波动很大，任何项目延迟或价格战都会让这个增长假设被迅速下修。",
        "industry_lines": [
            "行业层面：光伏逆变器已经相对成熟，真正的增量来自全球储能、构网能力和新型电力系统建设。",
            "竞争层面：阳光电源的核心竞争对手包括华为以及固德威、锦浪科技、上能电气等逆变器与储能玩家，但在规模和全球大储能力上，阳光电源明显更强。",
            "波特五力简述：上游功率器件、电芯与原材料波动会影响成本；下游客户多为大型项目业主与渠道商，议价能力强；技术门槛不低，但行业竞争依旧激烈。",
        ],
        "catalysts_short": "海外储能大单交付、储能毛利率稳定、逆变器全球份额继续提升、构网产品商业化放量。",
        "catalysts_mid": "中东、欧洲、美国等重点市场的大储需求扩张，风电变流器、充电和氢能等新业务逐步贡献利润。",
        "long_term": "到2030年，阳光电源若能继续守住全球光储核心设备龙头位置，它的估值锚会越来越像能源基础设施平台，而不仅是设备制造商。",
        "black_swan": "若全球储能价格战失控、海外项目交付受阻或新能源开发业务出现明显减值，市场会重新按周期设备股而非全球平台股给估值。",
        "monitoring": "储能收入增速、储能毛利率、海外收入占比、经营现金流/净利润、应收与合同负债变化、同业估值差。",
        "risk_matrix": [
            "经营风险 3/5：设备业务优秀，但开发业务与大项目节奏会放大单季度波动。",
            "财务风险 2/5：现金流总体健康，但海外项目交付、应收与存货变化需要持续盯住。",
            "竞争风险 4/5：储能和逆变器赛道持续价格战，龙头也无法完全豁免。",
            "监管/政策风险 3/5：海外贸易政策、本地化要求和并网规则变化都会影响接单与盈利。",
            "宏观风险 3/5：全球利率、项目融资环境和新能源装机节奏都会影响需求兑现。",
            "估值风险 3/5：相对同行不贵，但市场对龙头稳定增长已有预期，一旦增速下修就会先压估值。",
        ],
        "positioning": "若想配新能源设备龙头，可分批观察；若偏低波动组合，应等待更明显的安全边际再加仓。",
        "dialogue": [
            "沃伦：这家公司不是卖单个零件，它卖的是新能源系统里的关键控制权。逆变器听上去像个部件，实际上它决定了电怎么变、怎么控、怎么并网，这就不是一个容易被替代的生意。",
            "沃伦：我喜欢它的一点是，它不是只押一个环节。光伏逆变器站稳后，它又把储能系统做起来，而且在全球大项目上开始证明自己。真正赚钱的企业，往往是技术和交付一起硬。",
            "查理：但别忘了，新能源设备行业从来不缺残酷竞争。今天你有技术，明天别人也能降价；今天你有订单，明天客户就逼你让利。这个行业最危险的地方，是大家都很聪明，也都很拼命。",
            "沃伦：对，所以我不把它看成公用事业，我把它看成高质量工业科技公司。关键是它有没有比同行更持久的盈利能力。看现在的规模、利润和现金流，它的确在同业里跑得更远。",
            "查理：我会盯紧两件事。第一，储能是不是会像光伏组件那样卷到几乎没有经济利润。第二，新能源开发业务会不会把本来很漂亮的设备生意搅浑。很多公司死，不是死在主业，而是死在“顺手多做一点”。",
            "沃伦：这正是为什么横向比较有意义。你会发现阳光电源不是最便宜的，但也不是最贵的；不是毛利最高的神话，但它的规模、ROE和现金流组合明显更扎实。",
            "查理：所以结论不复杂。它是这个赛道里少数值得认真研究的公司，但这个赛道的高波动决定了你不能用消费股的心态去买它。",
            "沃伦：如果价格给得合理，我愿意盯着这家公司，而不是盯着那些讲得更热闹、报表却更薄的同行。",
        ],
        "benjamin_opening": "本杰明：先把赛道热情放下。阳光电源是优秀公司，但优秀公司也要有价格纪律。我这里用 2025 年所有者盈余近似股权现金流，再用 2026-04-14 的收盘价和总股本口径校准。",
        "benjamin_wrap": "本杰明：我更愿意把它理解为“高质量龙头但不是白送”。若追求胜率，它比多数同业更优；若追求赔率，最好等行业情绪再差一点。",
        "closing": [
            "沃伦：阳光电源是新能源设备里少数兼具全球竞争力、规模和现金流的真龙头，值得长期跟踪。",
            "查理：但这个行业波动大、竞争狠，别因为公司优秀就忘了它仍然身处周期和价格战。",
            "本杰明：当前价格更接近合理而非便宜。相对同行它不贵，但绝不是随便闭眼买的低估值资产。",
        ],
        "pe_range": (18, 21, 24),
        "owner_yield": (0.055, 0.05, 0.045),
        "dcf_assumptions": [(0.04, 0.095, 0.025), (0.06, 0.09, 0.03), (0.08, 0.085, 0.03)],
        "peers": ["300763.SZ", "688390.SH", "300827.SZ", "002335.SZ"],
    },
}


@dataclass
class ValuationCase:
    name: str
    low: float | None
    base: float | None
    high: float | None
    weight: str
    comment: str


def load_engine():
    load_dotenv(dotenv_path=ROOT / ".env")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123456@localhost:5432/testdb",
    )
    db_url = database_url.replace("+psycopg2", "")
    return create_engine(db_url)


def query_df(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        return pd.read_sql(text(sql), engine, params=params or {})
    except SQLAlchemyError as exc:
        raise RuntimeError(f"SQL 执行失败: {exc}") from exc


def latest_by_end_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    sort_cols = [col for col in ["end_date", "ann_date"] if col in df.columns]
    ascending = [False] * len(sort_cols)
    return (
        df.sort_values(sort_cols, ascending=ascending)
        .drop_duplicates(subset=["end_date"], keep="first")
        .reset_index(drop=True)
    )


def fmt_yi(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value) / 1e8:.2f}亿"


def fmt_pct(value, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}%"


def fmt_num(value, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}"


def safe_div(a, b):
    if a is None or b is None or pd.isna(a) or pd.isna(b) or float(b) == 0:
        return None
    return float(a) / float(b)


def pct_change(current, previous):
    if current is None or previous is None or pd.isna(current) or pd.isna(previous) or float(previous) == 0:
        return None
    return (float(current) - float(previous)) / abs(float(previous)) * 100


def cagr(start, end, years):
    if (
        start is None
        or end is None
        or pd.isna(start)
        or pd.isna(end)
        or years <= 0
        or float(start) <= 0
        or float(end) <= 0
    ):
        return None
    return (float(end) / float(start)) ** (1 / years) - 1


def annual_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["end_date"].astype(str).str.endswith("1231")].copy()


def compute_rsi(close_series: pd.Series, period: int = 14) -> float | None:
    if len(close_series) < period + 1:
        return None
    delta = close_series.diff()
    up = delta.clip(lower=0).rolling(period).mean()
    down = (-delta.clip(upper=0)).rolling(period).mean()
    rs = up / down.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    value = rsi.iloc[-1]
    return None if pd.isna(value) else float(value)


def compute_macd(close_series: pd.Series) -> tuple[float | None, float | None, float | None]:
    if len(close_series) < 35:
        return None, None, None
    ema12 = close_series.ewm(span=12, adjust=False).mean()
    ema26 = close_series.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = (dif - dea) * 2
    last = (dif.iloc[-1], dea.iloc[-1], hist.iloc[-1])
    return tuple(None if pd.isna(x) else float(x) for x in last)


def present_value_of_stream(base_value: float, growth: float, discount: float, years: int, terminal_growth: float) -> float | None:
    if base_value <= 0 or discount <= terminal_growth:
        return None
    pv = 0.0
    value = base_value
    for year in range(1, years + 1):
        value *= 1 + growth
        pv += value / ((1 + discount) ** year)
    terminal = value * (1 + terminal_growth) / (discount - terminal_growth)
    pv += terminal / ((1 + discount) ** years)
    return pv


def reverse_growth_for_price(base_value: float, price_target_total: float, discount: float, years: int, terminal_growth: float) -> float | None:
    if base_value <= 0 or price_target_total <= 0 or discount <= terminal_growth:
        return None
    low = -0.1
    high = 0.2
    for _ in range(50):
        mid = (low + high) / 2
        pv = present_value_of_stream(base_value, mid, discount, years, terminal_growth)
        if pv is None:
            return None
        if pv > price_target_total:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def build_data_bundle(engine, ts_code: str) -> dict:
    stock_sql = """
        SELECT s.ts_code, s.name, s.industry, s.area, s.list_date, s.market, s.exchange,
               c.com_name, c.chairman, c.manager, c.secretary, c.reg_capital, c.setup_date,
               c.main_business, c.business_scope, c.employees, c.website
        FROM stock_basic s
        LEFT JOIN stock_company c ON s.ts_code = c.ts_code
        WHERE s.ts_code = :ts_code
        LIMIT 1
    """
    income_sql = """
        SELECT end_date, ann_date, total_revenue, revenue, oper_cost, operate_profit,
               n_income_attr_p, n_income, basic_eps, ebit, ebitda,
               sell_exp, admin_exp, fin_exp, rd_exp, total_profit, income_tax
        FROM income
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC, ann_date DESC
    """
    balance_sql = """
        SELECT end_date, ann_date, total_assets, total_liab, total_cur_assets, total_cur_liab,
               total_hldr_eqy_exc_min_int, total_hldr_eqy_inc_min_int,
               money_cap, inventories, accounts_receiv, notes_receiv,
               st_borr, lt_borr, bond_payable, fix_assets, cip
        FROM balancesheet
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC, ann_date DESC
    """
    cash_sql = """
        SELECT end_date, ann_date, n_cashflow_act, n_cashflow_inv_act, n_cash_flows_fnc_act,
               free_cashflow, c_pay_acq_const_fiolta, n_incr_cash_cash_equ,
               c_cash_equ_end_period
        FROM cashflow
        WHERE ts_code = :ts_code AND report_type = '1'
        ORDER BY end_date DESC, ann_date DESC
    """
    indicator_sql = """
        SELECT end_date, ann_date, eps, dt_eps, bps, current_ratio, quick_ratio, cash_ratio,
               arturn_days, invturn_days, assets_turn, grossprofit_margin, netprofit_margin,
               roe, roe_waa, roa, debt_to_assets, op_of_gr, expense_of_sales,
               ocf_to_or, ocf_to_profit, fcff, fcfe, interestdebt, netdebt,
               profit_dedt, or_yoy, netprofit_yoy
        FROM fina_indicator
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC
    """
    daily_sql = """
        SELECT trade_date, close, turnover_rate, volume_ratio, pe, pe_ttm, pb, ps_ttm,
               dv_ttm, total_share, total_mv, circ_mv
        FROM daily_basic
        WHERE ts_code = :ts_code
        ORDER BY trade_date DESC
    """
    dividend_sql = """
        SELECT end_date, ann_date, ex_date, cash_div_tax, stk_bo_rate, stk_co_rate
        FROM dividend
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC, ann_date DESC, ex_date DESC
    """
    audit_sql = """
        SELECT end_date, audit_result, audit_agency
        FROM fina_audit
        WHERE ts_code = :ts_code
        ORDER BY end_date DESC
    """

    stock_df = query_df(engine, stock_sql, {"ts_code": ts_code})
    if stock_df.empty:
        raise RuntimeError(f"未找到 {ts_code} 的基础信息。")

    income_df = latest_by_end_date(query_df(engine, income_sql, {"ts_code": ts_code}))
    balance_df = latest_by_end_date(query_df(engine, balance_sql, {"ts_code": ts_code}))
    cash_df = latest_by_end_date(query_df(engine, cash_sql, {"ts_code": ts_code}))
    indicator_df = latest_by_end_date(query_df(engine, indicator_sql, {"ts_code": ts_code}))
    daily_df = query_df(engine, daily_sql, {"ts_code": ts_code}).sort_values("trade_date").reset_index(drop=True)
    dividend_df = query_df(engine, dividend_sql, {"ts_code": ts_code})
    audit_df = query_df(engine, audit_sql, {"ts_code": ts_code})

    if income_df.empty or balance_df.empty or cash_df.empty or indicator_df.empty or daily_df.empty:
        raise RuntimeError(f"{ts_code} 的核心财务数据不完整，无法生成报告。")

    return {
        "stock": stock_df.iloc[0],
        "income": income_df,
        "balance": balance_df,
        "cash": cash_df,
        "indicator": indicator_df,
        "daily": daily_df,
        "dividend": dividend_df,
        "audit": audit_df,
    }


def build_quarter_table(bundle: dict) -> pd.DataFrame:
    income = bundle["income"][["end_date", "total_revenue", "n_income_attr_p", "operate_profit", "sell_exp", "admin_exp", "fin_exp", "rd_exp"]]
    balance = bundle["balance"][["end_date", "money_cap", "inventories", "accounts_receiv", "total_cur_liab", "total_assets", "total_liab"]]
    cash = bundle["cash"][["end_date", "n_cashflow_act", "free_cashflow", "c_pay_acq_const_fiolta"]]
    indicator = bundle["indicator"][["end_date", "grossprofit_margin", "netprofit_margin", "roe", "roa", "current_ratio", "quick_ratio", "debt_to_assets", "ocf_to_profit", "assets_turn", "arturn_days", "invturn_days"]]

    quarter = income.merge(balance, on="end_date", how="left").merge(cash, on="end_date", how="left").merge(indicator, on="end_date", how="left")
    quarter = quarter.sort_values("end_date", ascending=False).reset_index(drop=True)

    yoy_rev = []
    yoy_profit = []
    yoy_ocf = []
    for _, row in quarter.iterrows():
        prev_end = str(int(row["end_date"]) - 10000)
        prev = quarter[quarter["end_date"] == prev_end]
        prev_row = prev.iloc[0] if not prev.empty else None
        yoy_rev.append(pct_change(row["total_revenue"], prev_row["total_revenue"]) if prev_row is not None else None)
        yoy_profit.append(pct_change(row["n_income_attr_p"], prev_row["n_income_attr_p"]) if prev_row is not None else None)
        yoy_ocf.append(pct_change(row["n_cashflow_act"], prev_row["n_cashflow_act"]) if prev_row is not None else None)

    quarter["revenue_yoy"] = yoy_rev
    quarter["profit_yoy"] = yoy_profit
    quarter["ocf_yoy"] = yoy_ocf
    quarter["expense_ratio"] = quarter.apply(
        lambda row: safe_div(
            (row.get("sell_exp") or 0) + (row.get("admin_exp") or 0) + (row.get("fin_exp") or 0) + (row.get("rd_exp") or 0),
            row.get("total_revenue"),
        )
        * 100
        if safe_div(
            (row.get("sell_exp") or 0) + (row.get("admin_exp") or 0) + (row.get("fin_exp") or 0) + (row.get("rd_exp") or 0),
            row.get("total_revenue"),
        )
        is not None
        else None,
        axis=1,
    )
    quarter["cash_to_current_liab"] = quarter.apply(
        lambda row: safe_div(row.get("money_cap"), row.get("total_cur_liab")) * 100
        if safe_div(row.get("money_cap"), row.get("total_cur_liab")) is not None
        else None,
        axis=1,
    )
    quarter["owner_earnings"] = quarter.apply(
        lambda row: (row.get("n_cashflow_act") or 0) - (row.get("c_pay_acq_const_fiolta") or 0),
        axis=1,
    )
    return quarter


def build_annual_table(bundle: dict) -> pd.DataFrame:
    income = annual_only(
        bundle["income"][
            [
                "end_date",
                "total_revenue",
                "oper_cost",
                "operate_profit",
                "n_income_attr_p",
                "ebit",
                "fin_exp",
            ]
        ]
    )
    balance = annual_only(
        bundle["balance"][
            [
                "end_date",
                "total_assets",
                "total_liab",
                "total_cur_liab",
                "money_cap",
                "inventories",
                "accounts_receiv",
            ]
        ]
    )
    cash = annual_only(
        bundle["cash"][
            [
                "end_date",
                "n_cashflow_act",
                "free_cashflow",
                "c_pay_acq_const_fiolta",
            ]
        ]
    )
    indicator = annual_only(
        bundle["indicator"][
            [
                "end_date",
                "bps",
                "current_ratio",
                "quick_ratio",
                "assets_turn",
                "grossprofit_margin",
                "netprofit_margin",
                "roe",
                "roa",
                "debt_to_assets",
                "ocf_to_profit",
                "fcff",
                "fcfe",
                "interestdebt",
                "netdebt",
                "profit_dedt",
            ]
        ]
    )
    annual = (
        income.merge(balance, on="end_date", how="left")
        .merge(cash, on="end_date", how="left")
        .merge(indicator, on="end_date", how="left")
        .sort_values("end_date", ascending=False)
        .reset_index(drop=True)
    )

    annual["revenue_yoy"] = annual["total_revenue"].shift(-1)
    annual["profit_yoy"] = annual["n_income_attr_p"].shift(-1)
    annual["revenue_yoy"] = annual.apply(lambda row: pct_change(row["total_revenue"], row["revenue_yoy"]), axis=1)
    annual["profit_yoy"] = annual.apply(lambda row: pct_change(row["n_income_attr_p"], row["profit_yoy"]), axis=1)
    annual["ocf_profit_ratio"] = annual.apply(
        lambda row: safe_div(row["n_cashflow_act"], row["n_income_attr_p"]) * 100
        if safe_div(row["n_cashflow_act"], row["n_income_attr_p"]) is not None
        else None,
        axis=1,
    )
    annual["owner_earnings"] = annual.apply(
        lambda row: (row.get("n_cashflow_act") or 0) - (row.get("c_pay_acq_const_fiolta") or 0),
        axis=1,
    )
    annual["owner_earnings_yield"] = annual.apply(lambda row: row["owner_earnings"], axis=1)
    annual["cash_to_current_liab"] = annual.apply(
        lambda row: safe_div(row.get("money_cap"), row.get("total_cur_liab")) * 100
        if safe_div(row.get("money_cap"), row.get("total_cur_liab")) is not None
        else None,
        axis=1,
    )
    annual["interest_cover_proxy"] = annual.apply(
        lambda row: safe_div(row.get("ebit"), abs(row.get("fin_exp"))) if row.get("fin_exp") not in (None, 0) else None,
        axis=1,
    )
    return annual.head(8)


def build_market_view(bundle: dict) -> dict:
    daily = bundle["daily"].copy().sort_values("trade_date").reset_index(drop=True)
    latest = daily.iloc[-1]
    tail_250 = daily.tail(min(250, len(daily)))
    tail_60 = daily.tail(min(60, len(daily)))
    tail_20 = daily.tail(min(20, len(daily)))

    close = daily["close"].astype(float)
    ma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
    ma60 = float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None
    ma120 = float(close.rolling(120).mean().iloc[-1]) if len(close) >= 120 else None
    ma250 = float(close.rolling(250).mean().iloc[-1]) if len(close) >= 250 else None
    rsi14 = compute_rsi(close, 14)
    macd_dif, macd_dea, macd_hist = compute_macd(close)

    latest_pe = latest["pe_ttm"]
    latest_pb = latest["pb"]
    pe_hist = tail_250["pe_ttm"].dropna()
    pb_hist = tail_250["pb"].dropna()
    pe_pct = pe_hist.le(latest_pe).mean() * 100 if not pe_hist.empty and pd.notna(latest_pe) else None
    pb_pct = pb_hist.le(latest_pb).mean() * 100 if not pb_hist.empty and pd.notna(latest_pb) else None

    return {
        "latest": latest,
        "ma20": ma20,
        "ma60": ma60,
        "ma120": ma120,
        "ma250": ma250,
        "rsi14": rsi14,
        "macd_dif": macd_dif,
        "macd_dea": macd_dea,
        "macd_hist": macd_hist,
        "high_52w": float(tail_250["close"].max()) if not tail_250.empty else None,
        "low_52w": float(tail_250["close"].min()) if not tail_250.empty else None,
        "high_60d": float(tail_60["close"].max()) if not tail_60.empty else None,
        "low_60d": float(tail_60["close"].min()) if not tail_60.empty else None,
        "avg_turnover_20d": float(tail_20["turnover_rate"].mean()) if not tail_20.empty else None,
        "avg_volume_ratio_20d": float(tail_20["volume_ratio"].mean()) if not tail_20.empty else None,
        "pe_percentile_1y": pe_pct,
        "pb_percentile_1y": pb_pct,
    }


def latest_dividend_per_share(dividend_df: pd.DataFrame) -> float | None:
    if dividend_df.empty:
        return None
    annual = dividend_df[dividend_df["end_date"].astype(str).str.endswith("1231")].copy()
    if annual.empty:
        annual = dividend_df.copy()
    annual = annual.sort_values(["end_date", "ann_date", "ex_date"], ascending=False)
    row = annual.iloc[0]
    return None if pd.isna(row["cash_div_tax"]) else float(row["cash_div_tax"])


def build_valuations(bundle: dict, annual: pd.DataFrame, market: dict) -> tuple[list[ValuationCase], dict]:
    profile = COMPANY_PROFILES.get(bundle["stock"]["ts_code"], COMPANY_PROFILES["600887.SH"])
    latest = market["latest"]
    latest_indicator = annual.iloc[0]
    close = float(latest["close"])
    total_mv_yuan = float(latest["total_mv"]) * 10000 if pd.notna(latest["total_mv"]) else None
    total_share = float(latest["total_share"]) * 10000 if pd.notna(latest["total_share"]) else None
    eps_ttm = safe_div(close, latest["pe_ttm"])
    bps = latest_indicator.get("bps")
    owner_earnings = latest_indicator.get("owner_earnings")
    net_debt = latest_indicator.get("netdebt")
    if pd.isna(net_debt):
        net_debt = None
    else:
        net_debt = float(net_debt)

    pe_case = None
    pb_case = None
    dcf_case = None
    owner_case = None
    peg_case = None
    ddm_case = None
    nav_case = None
    sotp_case = None
    implied_growth = None

    if eps_ttm is not None:
        pe_low, pe_base, pe_high = profile["pe_range"]
        pe_case = ValuationCase(
            "相对估值(P/E)",
            round(eps_ttm * pe_low, 2),
            round(eps_ttm * pe_base, 2),
            round(eps_ttm * pe_high, 2),
            "高",
            profile["pe_comment"],
        )

    if bps is not None and not pd.isna(bps):
        pb_case = ValuationCase(
            "相对估值(P/B)",
            round(float(bps) * 2.5, 2),
            round(float(bps) * 3.0, 2),
            round(float(bps) * 3.4, 2),
            "中",
            "消费龙头具品牌溢价，PB主要用于校验安全边际。",
        )
        nav_case = ValuationCase(
            "NAV/净资产重估",
            round(float(bps) * 2.3, 2),
            round(float(bps) * 2.8, 2),
            round(float(bps) * 3.1, 2),
            "低",
            "对轻资产品牌消费品解释力一般，仅作底线参考。",
        )

    if owner_earnings is not None and not pd.isna(owner_earnings) and total_share:
        owner_ps = float(owner_earnings) / total_share
        yield_low, yield_base, yield_high = profile["owner_yield"]
        owner_case = ValuationCase(
            "所有者盈余收益率",
            round(owner_ps / yield_low, 2),
            round(owner_ps / yield_base, 2),
            round(owner_ps / yield_high, 2),
            "高",
            "按5.0%-6.0%的所有者盈余收益率反推合理价格。",
        )

        dcf_values = []
        for growth, discount, tg in profile["dcf_assumptions"]:
            total_value = present_value_of_stream(float(owner_earnings), growth, discount, 5, tg)
            if total_value is None or total_share == 0:
                dcf_values.append(None)
            else:
                equity_value = total_value - (net_debt or 0)
                dcf_values.append(equity_value / total_share)
        dcf_case = ValuationCase(
            "DCF/Owner Earnings",
            round(dcf_values[0], 2) if dcf_values[0] else None,
            round(dcf_values[1], 2) if dcf_values[1] else None,
            round(dcf_values[2], 2) if dcf_values[2] else None,
            "高",
            "以所有者盈余近似FCFE，折现率8.5%-9.0%，终值增长2%-3%。",
        )

        if total_mv_yuan:
            implied_growth = reverse_growth_for_price(float(owner_earnings), total_mv_yuan + (net_debt or 0), 0.09, 5, 0.025)

    profit_cagr = None
    if len(annual) >= 4:
        latest_profit = annual.iloc[0]["n_income_attr_p"]
        older_profit = annual.iloc[min(3, len(annual) - 1)]["n_income_attr_p"]
        profit_cagr = cagr(older_profit, latest_profit, min(3, len(annual) - 1))
        if eps_ttm is not None and profit_cagr is not None and profit_cagr > 0:
            fair_pe = min(22, max(14, profit_cagr * 100 * 1.2))
            peg_case = ValuationCase(
                "PEG",
                round(eps_ttm * max(14, fair_pe - 2), 2),
                round(eps_ttm * fair_pe, 2),
                round(eps_ttm * min(24, fair_pe + 2), 2),
                "中",
                "按近三年利润复合增速估算成长匹配PE。",
            )

    dividend_ps = latest_dividend_per_share(bundle["dividend"])
    if dividend_ps is not None:
        ddm_values = []
        for growth, discount in [(0.02, 0.085), (0.03, 0.085), (0.04, 0.08)]:
            if discount <= growth:
                ddm_values.append(None)
            else:
                ddm_values.append(dividend_ps * (1 + growth) / (discount - growth))
        ddm_case = ValuationCase(
            "DDM",
            round(ddm_values[0], 2) if ddm_values[0] else None,
            round(ddm_values[1], 2) if ddm_values[1] else None,
            round(ddm_values[2], 2) if ddm_values[2] else None,
            "中",
            "高分红适配该方法，但分红可持续性仍受行业周期影响。",
        )

    if pe_case and pb_case:
        sotp_case = ValuationCase(
            "SOTP(简化)",
            round(pe_case.low * 0.7 + pb_case.low * 0.3, 2),
            round(pe_case.base * 0.7 + pb_case.base * 0.3, 2),
            round(pe_case.high * 0.7 + pb_case.high * 0.3, 2),
            "低",
            "分部利润口径缺失，用主业PE与品牌资产PB做简化加总。",
        )

    cases = [case for case in [pe_case, pb_case, dcf_case, owner_case, peg_case, ddm_case, nav_case, sotp_case] if case is not None]
    summary = {
        "current_price": close,
        "implied_growth": implied_growth,
        "profit_cagr_3y": profit_cagr,
    }
    return cases, summary


def valuation_table(cases: list[ValuationCase]) -> str:
    header = "| 方法 | 悲观(元) | 基准(元) | 乐观(元) | 权重 | 备注 |\n| --- | --- | --- | --- | --- | --- |"
    rows = []
    for case in cases:
        rows.append(
            f"| {case.name} | {fmt_num(case.low)} | {fmt_num(case.base)} | {fmt_num(case.high)} | {case.weight} | {case.comment} |"
        )
    return "\n".join([header] + rows)


def annual_markdown(annual: pd.DataFrame) -> str:
    header = "| 年度 | 营收 | 营收同比 | 归母净利 | 净利同比 | ROE | ROA | 毛利率 | 资产负债率 | 流动比率 | 经营现金流 | 现净比 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = []
    for _, row in annual.head(5).iterrows():
        rows.append(
            "| {year} | {rev} | {rev_yoy} | {profit} | {profit_yoy} | {roe} | {roa} | {gross} | {debt} | {current} | {ocf} | {ocf_ratio} |".format(
                year=str(row["end_date"])[:4],
                rev=fmt_yi(row["total_revenue"]),
                rev_yoy=fmt_pct(row["revenue_yoy"]),
                profit=fmt_yi(row["n_income_attr_p"]),
                profit_yoy=fmt_pct(row["profit_yoy"]),
                roe=fmt_pct(row["roe"]),
                roa=fmt_pct(row["roa"]),
                gross=fmt_pct(row["grossprofit_margin"]),
                debt=fmt_pct(row["debt_to_assets"]),
                current=fmt_num(row["current_ratio"]),
                ocf=fmt_yi(row["n_cashflow_act"]),
                ocf_ratio=fmt_pct(row["ocf_profit_ratio"]),
            )
        )
    return "\n".join([header] + rows)


def dividend_summary(dividend_df: pd.DataFrame) -> str:
    if dividend_df.empty:
        return "分红数据缺失。"
    dedup = (
        dividend_df.sort_values(["end_date", "ann_date", "ex_date"], ascending=False)
        .drop_duplicates(subset=["end_date"], keep="first")
        .head(5)
    )
    lines = []
    for _, row in dedup.iterrows():
        ex_date = row["ex_date"] if pd.notna(row["ex_date"]) else "未披露"
        lines.append(f"- {row['end_date']}：每股现金分红 {fmt_num(row['cash_div_tax'])} 元，除权日 {ex_date}")
    return "\n".join(lines)


def audit_summary(audit_df: pd.DataFrame) -> str:
    if audit_df.empty:
        return "审计意见数据缺失。"
    lines = []
    for _, row in audit_df.head(5).iterrows():
        lines.append(f"- {row['end_date']}：{row['audit_result']}（{row['audit_agency']}）")
    return "\n".join(lines)


def build_peer_comparison(engine, base_ts_code: str, peer_codes: list[str]) -> pd.DataFrame:
    rows = []
    for code in [base_ts_code] + peer_codes:
        bundle = build_data_bundle(engine, code)
        annual = build_annual_table(bundle)
        market = build_market_view(bundle)
        latest = market["latest"]
        latest_ratio = annual[annual["roe"].notna()].iloc[0] if annual["roe"].notna().any() else annual.iloc[0]
        latest_annual = annual.iloc[0]
        ocf_profit = latest_annual["ocf_profit_ratio"]
        rows.append(
            {
                "ts_code": code,
                "name": bundle["stock"]["name"],
                "report_date": latest_annual["end_date"],
                "trade_date": latest["trade_date"],
                "revenue": latest_annual["total_revenue"],
                "net_profit": latest_annual["n_income_attr_p"],
                "ocf_profit_ratio": ocf_profit,
                "roe": latest_ratio["roe"],
                "gross_margin": latest_ratio["grossprofit_margin"],
                "debt_to_assets": latest_ratio["debt_to_assets"],
                "pe_ttm": latest["pe_ttm"],
                "pb": latest["pb"],
                "market_cap": latest["total_mv"],
            }
        )
    return pd.DataFrame(rows)


def peer_comparison_markdown(df: pd.DataFrame) -> str:
    header = "| 公司 | 最新财报期 | 最新收盘日 | 营收 | 归母净利 | 现净比 | ROE | 毛利率 | 资产负债率 | PE(TTM) | PB | 总市值 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = []
    for _, row in df.iterrows():
        rows.append(
            "| {name} | {report} | {trade} | {rev} | {profit} | {ocf} | {roe} | {gross} | {debt} | {pe} | {pb} | {mv} |".format(
                name=row["name"],
                report=row["report_date"],
                trade=row["trade_date"],
                rev=fmt_yi(row["revenue"]),
                profit=fmt_yi(row["net_profit"]),
                ocf=fmt_pct(row["ocf_profit_ratio"]),
                roe=fmt_pct(row["roe"]),
                gross=fmt_pct(row["gross_margin"]),
                debt=fmt_pct(row["debt_to_assets"]),
                pe=fmt_num(row["pe_ttm"]),
                pb=fmt_num(row["pb"]),
                mv=f"{float(row['market_cap'])/10000:.2f}亿" if pd.notna(row["market_cap"]) else "N/A",
            )
        )
    return "\n".join([header] + rows)


def peer_comparison_insight(df: pd.DataFrame, base_ts_code: str) -> list[str]:
    base = df[df["ts_code"] == base_ts_code].iloc[0]
    peers = df[df["ts_code"] != base_ts_code]
    insights = []
    if not peers.empty:
        if base["revenue"] == df["revenue"].max():
            insights.append(f"{base['name']}在可比公司里营收规模最大，规模优势最明显。")
        if pd.notna(base["net_profit"]) and base["net_profit"] == df["net_profit"].max():
            insights.append(f"{base['name']}归母净利润领先，盈利厚度明显强于多数同行。")
        if pd.notna(base["roe"]) and base["roe"] == df["roe"].max():
            insights.append(f"{base['name']}最新可比ROE最高，说明资本回报能力在同行里处于第一梯队。")
        if pd.notna(base["pe_ttm"]):
            cheaper = peers[peers["pe_ttm"] < base["pe_ttm"]]
            expensive = peers[peers["pe_ttm"] > base["pe_ttm"]]
            if not cheaper.empty and not expensive.empty:
                insights.append(f"{base['name']}当前PE(TTM)位于同行中间偏低区间，估值并没有因为龙头地位而被极端透支。")
        if pd.notna(base["ocf_profit_ratio"]) and base["ocf_profit_ratio"] > peers["ocf_profit_ratio"].median():
            insights.append(f"{base['name']}经营现金流/净利润优于同行中位数，利润兑现质量更稳。")
    return insights


def public_context_markdown(ts_code: str) -> str:
    items = PUBLIC_CONTEXT.get(ts_code, [])
    if not items:
        return "- 未补到外部公开资料，当前报告仅基于本地库。"
    lines = []
    for item in items:
        lines.append(f"- {item['date']}｜{item['source']}：{item['note']} [链接]({item['url']})")
    return "\n".join(lines)


def score_item(condition: bool, strong: bool = False) -> int:
    if strong:
        return 3 if condition else 1
    return 3 if condition else 2


def build_buffett_score(stock, annual: pd.DataFrame, market: dict, valuation_cases: list[ValuationCase], valuation_summary: dict) -> tuple[int, str]:
    latest = annual.iloc[0]
    metrics = [
        ("业务是否易于理解", 3, "乳制品主业清晰，收入结构和渠道逻辑可解释。"),
        ("经营历史是否一致", 2 if latest["total_revenue"] < annual.iloc[min(1, len(annual)-1)]["total_revenue"] else 3, "营收在近两年有波动，但十年主航道未变。"),
        ("长期前景是否良好", 2, "总量增长偏慢，但高端化、功能化、奶粉和海外仍有空间。"),
        ("管理层坦诚与理性", 2, "高分红与回购体现股东友好，但公开口径以正面表述为主。"),
        ("主人翁经营心态", 2, "资本回报意识较强，但仍需持续证明项目投资回报率。"),
        ("高ROE低负债", 2 if latest["roe"] >= 15 and latest["debt_to_assets"] <= 65 else 1, f"2024年ROE {fmt_pct(latest['roe'])}，资产负债率 {fmt_pct(latest['debt_to_assets'])}。"),
        ("强劲自由现金流", 3 if latest["owner_earnings"] > 0 and latest["ocf_profit_ratio"] >= 120 else 2, "经营现金流长期显著高于净利润。"),
        ("宽广经济护城河", 2, "品牌与渠道构成较强护城河，但不是不可撼动的超级垄断。"),
        ("保守会计处理", 2, "审计意见稳定，但2024年出现商誉减值，提示并购资产仍需谨慎看待。"),
        ("存在安全边际", 2 if valuation_summary.get("current_price") and valuation_cases else 1, "当前价格更接近合理偏上，而非显著低估。"),
        ("定价能力（抗通胀）", 2, "高端白奶与功能品类具一定提价权，大众液奶仍受竞争和促销制约。"),
        ("低资本再投入需求", 2, "主业不属于超重资本行业，但乳深加工与产能建设仍在持续投入。"),
    ]
    total = sum(item[1] for item in metrics)
    rating = "A" if total >= 30 else "B" if total >= 24 else "C" if total >= 18 else "D" if total >= 12 else "F"
    return total, rating


def render_report(ts_code: str, bundle: dict, quarter: pd.DataFrame, annual: pd.DataFrame, market: dict, valuations: list[ValuationCase], valuation_summary: dict, peer_df: pd.DataFrame | None = None) -> str:
    profile = COMPANY_PROFILES.get(ts_code, COMPANY_PROFILES["600887.SH"])
    stock = bundle["stock"]
    latest_q = quarter.iloc[0]
    latest_a = annual.iloc[0]
    latest_ratio_a = annual[annual["roe"].notna()].iloc[0] if annual["roe"].notna().any() else latest_a
    latest_ratio_q = quarter[quarter["roe"].notna()].iloc[0] if quarter["roe"].notna().any() else latest_q
    latest = market["latest"]
    moat = profile["moat"]
    moat_lines = "\n".join([f"- {name}：{grade}。{evidence}" for name, grade, evidence in moat])
    moat_total = profile["moat_total"]
    moat_trend = profile["moat_trend"]
    score_total, score_rating = build_buffett_score(stock, annual, market, valuations, valuation_summary)
    implied_growth = valuation_summary.get("implied_growth")
    current_price = valuation_summary.get("current_price")
    fair_values = [case.base for case in valuations if case.base is not None]
    base_fair = sum(fair_values[:4]) / min(len(fair_values[:4]), 4) if fair_values else None
    peer_section = ""
    if peer_df is not None and not peer_df.empty:
        peer_table = peer_comparison_markdown(peer_df)
        peer_lines = "\n".join([f"- {line}" for line in peer_comparison_insight(peer_df, ts_code)])
        peer_section = f"#### 同行横向对比\n{peer_table}\n{peer_lines}"

    buy_judgement = "跟踪为主，接近合理价" if base_fair and current_price and current_price <= base_fair * 1.05 else "回避追高" if base_fair and current_price and current_price > base_fair * 1.15 else "可以分批观察"
    good_company = "是，好公司" if latest_ratio_a["roe"] >= 15 and latest_a["ocf_profit_ratio"] >= 120 else "算得上，但不是无脑型好公司"
    good_price = "不是特别便宜" if base_fair and current_price and current_price >= base_fair * 0.95 else "接近合理" if base_fair else "价格判断需保留"

    rev_3y = cagr(annual.iloc[min(3, len(annual)-1)]["total_revenue"], annual.iloc[0]["total_revenue"], min(3, len(annual)-1))
    np_3y = cagr(annual.iloc[min(3, len(annual)-1)]["n_income_attr_p"], annual.iloc[0]["n_income_attr_p"], min(3, len(annual)-1))

    sections = [
        f"# {stock['name']}（{ts_code}）对话式基本面分析报告",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 公司：{stock['name']}｜行业：{stock['industry']}｜地区：{stock['area']}｜上市日期：{stock['list_date']}",
        f"- 主席/管理层：董事长 {stock['chairman'] or 'N/A'}；总经理 {stock['manager'] or 'N/A'}；员工数 {stock['employees'] if pd.notna(stock['employees']) else 'N/A'}",
        "- 数据口径：表结构以 `app/models/models.py` 为准，核心使用 `income`、`balancesheet`、`cashflow`、`daily_basic`、`fina_indicator`、`fina_audit`、`dividend`。",
        f"- 时点说明：当前市场价格采用 {latest['trade_date']} 收盘口径；最新正式财务披露采用 {latest_q['end_date']} 报告期。{profile['latest_notice']}",
        "",
        "【投资裁决】",
        f"- 公司判断：{good_company}。{profile['company_quality']}",
        f"- 价格判断：{good_price}。按 {latest['trade_date']} 收盘价 {fmt_num(latest['close'])} 元看，{profile['price_desc']}",
        f"- 当前结论：{buy_judgement}。{profile['judgement_desc']}",
        f"- 未来6-12个月关键变量：{profile['key_vars']}",
        f"- 最大风险：{profile['max_risk']}",
        "",
        "【投资结构化报告】",
        "### 模块1：公司概览与背景",
        f"- 一句话生意：{profile['one_line_business']}",
        f"- 公司背景：{stock['name']}{profile['background']}",
        "- 公开背景补充：",
        public_context_markdown(ts_code),
        "- 股权与治理：本报告未直接拉取前十大股东和董事会细项，治理判断主要依据审计、分红、回购和公开经营表态，需把股权穿透留作后续补充。",
        "",
        "### 模块2：管理层评估",
        f"- {profile['management_style']}",
        f"- {profile['shareholder_return']}",
        f"- {profile['management_risk']}",
        "",
        "### 模块3：商业模式深度解析",
        f"- 主营业务：{stock['main_business'] or profile['main_business_fallback']}。",
        f"- 收入引擎：{profile['revenue_engine']}",
        f"- 巴菲特一句话测试：{profile['buffett_test']}",
        f"- 单位经济：{profile['unit_economics']}",
        "",
        "### 模块4：经济护城河分析",
        moat_lines,
        f"- 护城河总评：{moat_total}。",
        f"- 护城河趋势：{moat_trend}",
        "",
        "### 模块5：财务深度分析",
        f"- 最新季度：{latest_q['end_date']} 营收 {fmt_yi(latest_q['total_revenue'])}，同比 {fmt_pct(latest_q['revenue_yoy'])}；归母净利 {fmt_yi(latest_q['n_income_attr_p'])}，同比 {fmt_pct(latest_q['profit_yoy'])}；经营现金流 {fmt_yi(latest_q['n_cashflow_act'])}，同比 {fmt_pct(latest_q['ocf_yoy'])}。",
        f"- 盈利能力：最近可比质量指标期为 {latest_ratio_a['end_date']}，ROE {fmt_pct(latest_ratio_a['roe'])}，ROA {fmt_pct(latest_ratio_a['roa'])}，毛利率 {fmt_pct(latest_ratio_a['grossprofit_margin'])}。",
        f"- 偿债能力：最近可比质量指标期资产负债率 {fmt_pct(latest_ratio_a['debt_to_assets'])}，流动比率 {fmt_num(latest_ratio_a['current_ratio'])}，速动比率 {fmt_num(latest_ratio_a['quick_ratio'])}。",
        f"- 现金流质量：{latest_a['end_date']} 经营现金流/归母净利润 {fmt_pct(latest_a['ocf_profit_ratio'])}；最近可比质量指标期 {latest_ratio_q['end_date']} 的经营现金流/利润口径为 {fmt_pct(latest_ratio_q['ocf_to_profit'])}。",
        f"- 营运效率：最近可比质量指标期应收周转天数 {fmt_num(latest_ratio_q['arturn_days'])} 天，存货周转天数 {fmt_num(latest_ratio_q['invturn_days'])} 天，总资产周转率 {fmt_num(latest_ratio_q['assets_turn'])}。",
        f"- 近五年年报趋势：\n{annual_markdown(annual)}",
        f"- 三年复合增速：营收 CAGR {fmt_pct((rev_3y or 0) * 100)}；归母净利 CAGR {fmt_pct((np_3y or 0) * 100)}。结论很直接：{'这是高质量成长，而不是单纯题材故事。' if (np_3y or 0) > 0.15 else '这是稳健复利，不是高增故事。'}",
        "",
        "### 模块6：管理层沟通与经营表态",
        "- A股没有像美股那样标准化的电话会文字稿，本报告用年报、半年报、季度经营解读替代。",
        f"- {profile['comms_1']}",
        f"- {profile['comms_2']}",
        "",
        "### 模块7：多模型估值",
        valuation_table(valuations),
        f"- 当前股价：{fmt_num(current_price)} 元。",
        f"- 反向DCF：若以所有者盈余口径、5年显性期、9%折现率、2.5%永续增长估算，当前市值大致隐含未来5年所有者盈余 CAGR 约 {fmt_pct((implied_growth or 0) * 100)}。{profile['reverse_dcf_note']}",
        f"- 估值汇总判断：综合各法，合理价值中枢约 {fmt_num(base_fair)} 元/股；理想买点更像 {fmt_num(base_fair * 0.8 if base_fair else None)} 元附近。",
        "",
        "### 模块8：竞争与行业分析",
        f"- {profile['industry_lines'][0]}",
        f"- {profile['industry_lines'][1]}",
        f"- {profile['industry_lines'][2]}",
        peer_section if peer_section else "",
        "",
        "### 模块9：技术面与交易补充",
        "- 巴菲特本人不依赖技术分析，本节仅作交易补充。",
        f"- 最新收盘 {fmt_num(latest['close'])} 元；MA20 {fmt_num(market['ma20'])}，MA60 {fmt_num(market['ma60'])}，MA120 {fmt_num(market['ma120'])}，MA250 {fmt_num(market['ma250'])}。",
        f"- 52周区间：{fmt_num(market['low_52w'])} - {fmt_num(market['high_52w'])} 元；近20日平均换手率 {fmt_pct(market['avg_turnover_20d'])}。",
        f"- RSI14 {fmt_num(market['rsi14'])}；MACD DIF {fmt_num(market['macd_dif'])} / DEA {fmt_num(market['macd_dea'])} / Hist {fmt_num(market['macd_hist'])}。",
        f"- 估值分位：近1年 PE(TTM) 分位约 {fmt_pct(market['pe_percentile_1y'])}，PB 分位约 {fmt_pct(market['pb_percentile_1y'])}。从分位看，当前位置偏低，但距离“极端错杀”仍差一层基本面催化。",
        "",
        "### 模块10：增长催化剂与前景展望",
        f"- 短期催化剂：{profile['catalysts_short']}",
        f"- 中期催化剂：{profile['catalysts_mid']}",
        f"- 长期展望：{profile['long_term']}",
        "",
        "### 模块11：风险矩阵",
        *[f"- {line}" for line in profile["risk_matrix"]],
        f"- 黑天鹅情景：{profile['black_swan']}",
        "",
        "### 模块12：巴菲特计分卡与投资决策",
        f"- 巴菲特计分卡：{score_total}/36，评级 {score_rating}。",
        f"- 投资评级：{'持有/跟踪' if base_fair and current_price and current_price >= base_fair * 0.95 else '买入观察' if base_fair else '跟踪'}。",
        f"- 12个月目标价：悲观 {fmt_num(base_fair * 0.85 if base_fair else None)} 元；基准 {fmt_num(base_fair)} 元；乐观 {fmt_num(base_fair * 1.15 if base_fair else None)} 元。",
        f"- 理想买入区间：{fmt_num(base_fair * 0.75 if base_fair else None)} - {fmt_num(base_fair * 0.85 if base_fair else None)} 元。",
        f"- 仓位建议：{profile['positioning']}",
        f"- 关键监控指标：{profile['monitoring']}",
        "",
        "【沃伦与查理】",
        *profile["dialogue"],
        "",
        "【本杰明插话：估值】",
        profile["benjamin_opening"],
        f"本杰明：当前收盘价 {fmt_num(current_price)} 元。按多模型估值，合理价值中枢约 {fmt_num(base_fair)} 元。保守情景下，我愿意给 {fmt_num(base_fair * 0.85 if base_fair else None)} 元附近；中性情景是 {fmt_num(base_fair)} 元左右；乐观情景也不过 {fmt_num(base_fair * 1.15 if base_fair else None)} 元。",
        f"本杰明：如果你按反向DCF回推，市场只要求未来5年所有者盈余年化大约 {fmt_pct((implied_growth or 0) * 100)}。这意味着市场预期并不夸张，但 2024 年现金流偏强，不能把一年的好数字直接当成永远。",
        profile["benjamin_wrap"],
        "",
        "【综合结论】",
        *profile["closing"],
        "",
        "### 分红与审计补充",
        "#### 分红",
        dividend_summary(bundle["dividend"]),
        "",
        "#### 审计意见",
        audit_summary(bundle["audit"]),
        "",
        "> ⚠️ **免责声明**：本分析仅供教育和研究用途，不构成投资建议。\"巴菲特\"视角是一个受沃伦·巴菲特公开表述的投资原则启发的分析框架，它并不代表沃伦·巴菲特本人对任何具体公司的观点。所有投资都有风险，请在做出投资决策前咨询合格的财务顾问。",
    ]
    return "\n".join(sections)


def main():
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/analysis_dialogue_report.py 600887.SH")
        sys.exit(1)

    ts_code = sys.argv[1].strip().upper()
    engine = load_engine()
    bundle = build_data_bundle(engine, ts_code)
    quarter = build_quarter_table(bundle)
    annual = build_annual_table(bundle)
    market = build_market_view(bundle)
    valuations, valuation_summary = build_valuations(bundle, annual, market)
    profile = COMPANY_PROFILES.get(ts_code, COMPANY_PROFILES["600887.SH"])
    peer_df = build_peer_comparison(engine, ts_code, profile.get("peers", [])) if profile.get("peers") else None
    report = render_report(ts_code, bundle, quarter, annual, market, valuations, valuation_summary, peer_df)

    OUTPUT_DIR.mkdir(exist_ok=True)
    code_slug = ts_code.replace(".", "-")
    name_slug = str(bundle["stock"]["name"]).replace("/", "-").replace(" ", "")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_path = OUTPUT_DIR / f"skill-analysis--{code_slug}--{name_slug}--{timestamp}--dialogue.md"
    output_path.write_text(report, encoding="utf-8")

    print(f"报告已生成: {output_path}")
    print(report)


if __name__ == "__main__":
    main()
