"""
产业链知识图谱服务
构建行业上下游关系，支持个股产业链穿透
"""
import logging
from typing import Optional

logger = logging.getLogger("mitouai.chain")

# ═══════════════════════════════════════════
#  行业-产业链定义数据库
# ═══════════════════════════════════════════

INDUSTRY_CHAINS = {
    "新能源汽车": {
        "name": "新能源汽车产业链",
        "description": "从上游锂矿资源到整车制造再到充电运营的完整产业链",
        "nodes": [
            # 上游 - 资源/材料
            {"id": "upstream_1", "name": "锂矿资源", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "002460.SZ", "name": "赣锋锂业", "role": "锂盐龙头"},
                 {"code": "002466.SZ", "name": "天齐锂业", "role": "锂矿+锂盐"},
                 {"code": "300390.SZ", "name": "天华超净", "role": "氢氧化锂"},
             ]},
            {"id": "upstream_2", "name": "钴矿/镍矿", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "603799.SH", "name": "华友钴业", "role": "钴+前驱体"},
                 {"code": "300618.SZ", "name": "寒锐钴业", "role": "钴粉"},
             ]},
            {"id": "upstream_3", "name": "正极材料", "layer": "上游", "layer_idx": 1,
             "stocks": [
                 {"code": "300073.SZ", "name": "当升科技", "role": "三元正极"},
                 {"code": "688005.SH", "name": "容百科技", "role": "高镍正极"},
                 {"code": "300769.SZ", "name": "德方纳米", "role": "磷酸铁锂"},
             ]},
            {"id": "upstream_4", "name": "负极/隔膜/电解液", "layer": "上游", "layer_idx": 1,
             "stocks": [
                 {"code": "603659.SH", "name": "璞泰来", "role": "负极"},
                 {"code": "300750.SZ", "name": "宁德时代", "role": "电池龙头"},
                 {"code": "002709.SZ", "name": "天赐材料", "role": "电解液"},
                 {"code": "300568.SZ", "name": "星源材质", "role": "隔膜"},
             ]},
            # 中游 - 零部件/电池
            {"id": "mid_1", "name": "动力电池", "layer": "中游", "layer_idx": 2,
             "stocks": [
                 {"code": "300750.SZ", "name": "宁德时代", "role": "全球龙头"},
                 {"code": "002594.SZ", "name": "比亚迪", "role": "刀片电池"},
                 {"code": "300014.SZ", "name": "亿纬锂能", "role": "锂电第二梯队"},
                 {"code": "688567.SH", "name": "孚能科技", "role": "软包电池"},
             ]},
            {"id": "mid_2", "name": "电机电控", "layer": "中游", "layer_idx": 2,
             "stocks": [
                 {"code": "300124.SZ", "name": "汇川技术", "role": "电控龙头"},
                 {"code": "002196.SZ", "name": "方正电机", "role": "驱动电机"},
             ]},
            {"id": "mid_3", "name": "热管理/轻量化", "layer": "中游", "layer_idx": 2,
             "stocks": [
                 {"code": "002050.SZ", "name": "三花智控", "role": "热管理"},
                 {"code": "601689.SH", "name": "拓普集团", "role": "轻量化底盘"},
             ]},
            # 下游 - 整车/充电
            {"id": "down_1", "name": "新能源整车", "layer": "下游", "layer_idx": 3,
             "stocks": [
                 {"code": "002594.SZ", "name": "比亚迪", "role": "销量第一"},
                 {"code": "000625.SZ", "name": "长安汽车", "role": "自主品牌"},
                 {"code": "601633.SH", "name": "长城汽车", "role": "SUV新能源"},
                 {"code": "600104.SH", "name": "上汽集团", "role": "合资转型"},
                 {"code": "601238.SH", "name": "广汽集团", "role": "埃安品牌"},
             ]},
            {"id": "down_2", "name": "充电桩/换电", "layer": "下游", "layer_idx": 3,
             "stocks": [
                 {"code": "300001.SZ", "name": "特锐德", "role": "充电运营龙头"},
                 {"code": "002276.SZ", "name": "万马股份", "role": "充电桩"},
             ]},
        ],
        "edges": [
            {"from": "upstream_1", "to": "upstream_3"},  # 锂矿→正极
            {"from": "upstream_2", "to": "upstream_3"},  # 钴→正极
            {"from": "upstream_3", "to": "upstream_4"},  # 正极→电池
            {"from": "upstream_4", "to": "mid_1"},       # 材料→电池
            {"from": "mid_1", "to": "mid_2"},             # 电池→电机
            {"from": "mid_1", "to": "mid_3"},             # 电池→热管理
            {"from": "mid_1", "to": "down_1"},            # 电池→整车
            {"from": "mid_2", "to": "down_1"},            # 电机→整车
            {"from": "mid_3", "to": "down_1"},            # 热管理→整车
            {"from": "down_1", "to": "down_2"},           # 整车→充电
        ],
    },
    "半导体芯片": {
        "name": "半导体芯片产业链",
        "description": "从设计到制造封测的完整半导体产业",
        "nodes": [
            {"id": "semi_1", "name": "EDA/IP", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "688521.SH", "name": "芯原股份", "role": "IP授权"},
                 {"code": "301269.SZ", "name": "华大九天", "role": "EDA龙头"},
             ]},
            {"id": "semi_2", "name": "半导体设备", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "002371.SZ", "name": "北方华创", "role": "设备龙头"},
                 {"code": "688012.SH", "name": "中微公司", "role": "刻蚀设备"},
                 {"code": "688037.SH", "name": "芯源微", "role": "涂胶显影"},
             ]},
            {"id": "semi_3", "name": "硅片/材料", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "688126.SH", "name": "沪硅产业", "role": "大硅片"},
                 {"code": "300054.SZ", "name": "鼎龙股份", "role": "CMP抛光垫"},
                 {"code": "688019.SH", "name": "安集科技", "role": "抛光液"},
             ]},
            {"id": "semi_4", "name": "芯片设计", "layer": "中游", "layer_idx": 1,
             "stocks": [
                 {"code": "603986.SH", "name": "兆易创新", "role": "存储/MCU"},
                 {"code": "603501.SH", "name": "韦尔股份", "role": "CIS龙头"},
                 {"code": "688981.SH", "name": "中芯国际", "role": "晶圆代工"},
                 {"code": "002049.SZ", "name": "紫光国微", "role": "特种IC"},
             ]},
            {"id": "semi_5", "name": "封装测试", "layer": "下游", "layer_idx": 2,
             "stocks": [
                 {"code": "600584.SH", "name": "长电科技", "role": "封测龙头"},
                 {"code": "002156.SZ", "name": "通富微电", "role": "封测第二"},
                 {"code": "603005.SH", "name": "晶方科技", "role": "CMOS封测"},
             ]},
        ],
        "edges": [
            {"from": "semi_1", "to": "semi_4"},
            {"from": "semi_2", "to": "semi_4"},
            {"from": "semi_3", "to": "semi_4"},
            {"from": "semi_4", "to": "semi_5"},
        ],
    },
    "光伏": {
        "name": "光伏产业链",
        "description": "硅料→硅片→电池片→组件→电站",
        "nodes": [
            {"id": "pv_1", "name": "硅料", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "600438.SH", "name": "通威股份", "role": "硅料+电池双龙头"},
                 {"code": "688303.SH", "name": "大全能源", "role": "多晶硅"},
             ]},
            {"id": "pv_2", "name": "硅片", "layer": "上游", "layer_idx": 1,
             "stocks": [
                 {"code": "601012.SH", "name": "隆基绿能", "role": "硅片+组件龙头"},
                 {"code": "002129.SZ", "name": "TCL中环", "role": "硅片第二"},
             ]},
            {"id": "pv_3", "name": "电池/组件", "layer": "中游", "layer_idx": 2,
             "stocks": [
                 {"code": "688599.SH", "name": "天合光能", "role": "组件第三"},
                 {"code": "002459.SZ", "name": "晶澳科技", "role": "组件"},
                 {"code": "688472.SH", "name": "阿特斯", "role": "组件"},
             ]},
            {"id": "pv_4", "name": "逆变器/储能", "layer": "中游", "layer_idx": 2,
             "stocks": [
                 {"code": "300274.SZ", "name": "阳光电源", "role": "逆变器龙头"},
                 {"code": "300763.SZ", "name": "锦浪科技", "role": "组串式逆变器"},
             ]},
            {"id": "pv_5", "name": "电站运营", "layer": "下游", "layer_idx": 3,
             "stocks": [
                 {"code": "601778.SH", "name": "晶科科技", "role": "电站运营"},
                 {"code": "000591.SZ", "name": "太阳能", "role": "央企电站"},
             ]},
        ],
        "edges": [
            {"from": "pv_1", "to": "pv_2"}, {"from": "pv_2", "to": "pv_3"},
            {"from": "pv_3", "to": "pv_4"}, {"from": "pv_3", "to": "pv_5"},
            {"from": "pv_4", "to": "pv_5"},
        ],
    },
    "人工智能": {
        "name": "人工智能产业链",
        "description": "算力→大模型→应用→数据",
        "nodes": [
            {"id": "ai_1", "name": "AI芯片/算力", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "688256.SH", "name": "寒武纪", "role": "AI芯片"},
                 {"code": "688041.SH", "name": "海光信息", "role": "DCU"},
                 {"code": "688047.SH", "name": "龙芯中科", "role": "CPU"},
             ]},
            {"id": "ai_2", "name": "光模块/服务器", "layer": "上游", "layer_idx": 0,
             "stocks": [
                 {"code": "300308.SZ", "name": "中际旭创", "role": "800G光模块"},
                 {"code": "300502.SZ", "name": "新易盛", "role": "光模块"},
                 {"code": "000977.SZ", "name": "浪潮信息", "role": "AI服务器"},
             ]},
            {"id": "ai_3", "name": "大模型/AI平台", "layer": "中游", "layer_idx": 1,
             "stocks": [
                 {"code": "688111.SH", "name": "金山办公", "role": "AI办公"},
                 {"code": "002230.SZ", "name": "科大讯飞", "role": "星火大模型"},
                 {"code": "300624.SZ", "name": "万兴科技", "role": "AI创意工具"},
             ]},
            {"id": "ai_4", "name": "AI应用", "layer": "下游", "layer_idx": 2,
             "stocks": [
                 {"code": "300033.SZ", "name": "同花顺", "role": "AI金融"},
                 {"code": "688568.SH", "name": "中科星图", "role": "AI遥感"},
                 {"code": "300454.SZ", "name": "深信服", "role": "AI安全"},
             ]},
        ],
        "edges": [
            {"from": "ai_1", "to": "ai_3"}, {"from": "ai_2", "to": "ai_3"},
            {"from": "ai_3", "to": "ai_4"},
        ],
    },
    "消费白酒": {
        "name": "白酒产业链",
        "description": "原料→酿造→品牌→渠道→终端",
        "nodes": [
            {"id": "baijiu_1", "name": "高端白酒", "layer": "品牌", "layer_idx": 1,
             "stocks": [
                 {"code": "600519.SH", "name": "贵州茅台", "role": "白酒之王"},
                 {"code": "000858.SZ", "name": "五粮液", "role": "浓香龙头"},
                 {"code": "000568.SZ", "name": "泸州老窖", "role": "国窖1573"},
             ]},
            {"id": "baijiu_2", "name": "次高端/区域", "layer": "品牌", "layer_idx": 1,
             "stocks": [
                 {"code": "002304.SZ", "name": "洋河股份", "role": "绵柔型"},
                 {"code": "000596.SZ", "name": "古井贡酒", "role": "年份原浆"},
                 {"code": "600809.SH", "name": "山西汾酒", "role": "清香龙头"},
                 {"code": "000799.SZ", "name": "酒鬼酒", "role": "馥郁香型"},
             ]},
            {"id": "baijiu_3", "name": "渠道/经销商", "layer": "下游", "layer_idx": 2,
             "stocks": [
                 {"code": "600655.SH", "name": "豫园股份", "role": "酒类零售"},
                 {"code": "603369.SH", "name": "今世缘", "role": "婚宴渠道"},
             ]},
        ],
        "edges": [
            {"from": "baijiu_1", "to": "baijiu_3"},
            {"from": "baijiu_2", "to": "baijiu_3"},
        ],
    },
}

# 个股→产业链映射表
STOCK_CHAIN_MAP: dict = {}
for chain_id, chain_data in INDUSTRY_CHAINS.items():
    for node in chain_data["nodes"]:
        for stock in node["stocks"]:
            STOCK_CHAIN_MAP[stock["code"]] = {
                "chain_id": chain_id,
                "chain_name": chain_data["name"],
                "node_id": node["id"],
                "node_name": node["name"],
                "layer": node["layer"],
                "role": stock["role"],
            }


class IndustryChainService:

    def list_chains(self) -> list[dict]:
        """列出所有产业链"""
        return [
            {
                "id": cid,
                "name": data["name"],
                "description": data["description"],
                "node_count": len(data["nodes"]),
                "edge_count": len(data["edges"]),
                "layer_count": len(set(n["layer"] for n in data["nodes"])),
            }
            for cid, data in INDUSTRY_CHAINS.items()
        ]

    def get_chain(self, chain_id: str) -> Optional[dict]:
        """获取产业链详情"""
        return INDUSTRY_CHAINS.get(chain_id)

    def get_stock_chain(self, ticker: str) -> Optional[dict]:
        """获取个股所在的产业链信息"""
        info = STOCK_CHAIN_MAP.get(ticker)
        if not info:
            # 也尝试只匹配6位代码
            code = ticker.split(".")[0]
            for k, v in STOCK_CHAIN_MAP.items():
                if k.startswith(code):
                    info = v
                    break
        if not info:
            return None

        chain = INDUSTRY_CHAINS.get(info["chain_id"])
        if not chain:
            return None

        return {
            "stock": {"ticker": ticker, "node_name": info["node_name"],
                       "layer": info["layer"], "role": info["role"]},
            "chain": chain,
            "chain_id": info["chain_id"],
            "chain_name": info["chain_name"],
        }

    def get_chain_comparison(self, chain_id: str) -> list[dict]:
        """产业链内所有股票估值横向对比"""
        chain = INDUSTRY_CHAINS.get(chain_id)
        if not chain:
            return []

        all_stocks = []
        for node in chain["nodes"]:
            for stock in node["stocks"]:
                all_stocks.append({
                    **stock,
                    "node_name": node["name"],
                    "layer": node["layer"],
                })
        return all_stocks


industry_chain_service = IndustryChainService()
