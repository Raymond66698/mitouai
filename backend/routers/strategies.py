"""
策略超市路由 — 投资大师方法论 + 量化因子 + 技术流派
"""
from fastapi import APIRouter, HTTPException, Query
from models.schemas import StrategyListResponse, StrategyTemplate, StrategyCategory

router = APIRouter()

# ── 策略模板库（阶段 0 硬编码，后续迁入数据库）──
STRATEGY_TEMPLATES: list[dict] = [
    # === 投资大师 ===
    {
        "id": "buffett-value",
        "name": "巴菲特价值投资",
        "category": StrategyCategory.MASTER,
        "description": "寻找具有持久竞争优势、低负债、高ROE的优质企业，以合理价格买入并长期持有",
        "author": "沃伦·巴菲特",
        "tags": ["价值投资", "护城河", "长期持有", "ROE", "自由现金流"],
        "icon": "🏛️",
        "config_schema": {
            "min_roe": {"type": "number", "default": 15, "description": "最低 ROE (%)"},
            "min_fcf_yield": {"type": "number", "default": 5, "description": "最低自由现金流收益率 (%)"},
            "max_debt_equity": {"type": "number", "default": 0.5, "description": "最高负债权益比"},
            "min_years_profit": {"type": "number", "default": 5, "description": "最低连续盈利年数"},
        },
        "default_config": {"min_roe": 15, "min_fcf_yield": 5, "max_debt_equity": 0.5, "min_years_profit": 5},
    },
    {
        "id": "graham-value",
        "name": "格雷厄姆烟蒂投资",
        "category": StrategyCategory.MASTER,
        "description": "寻找股价低于净流动资产价值的股票，注重安全边际，是巴菲特早期的核心策略",
        "author": "本杰明·格雷厄姆",
        "tags": ["烟蒂股", "安全边际", "低市净率", "净流动资产"],
        "icon": "🕯️",
        "config_schema": {
            "max_pb": {"type": "number", "default": 0.8, "description": "最高市净率"},
            "max_pe": {"type": "number", "default": 10, "description": "最高市盈率"},
            "min_current_ratio": {"type": "number", "default": 2.0, "description": "最低流动比率"},
        },
        "default_config": {"max_pb": 0.8, "max_pe": 10, "min_current_ratio": 2.0},
    },
    {
        "id": "lynch-growth",
        "name": "彼得·林奇成长投资",
        "category": StrategyCategory.MASTER,
        "description": "寻找 PEG < 1 的成长股，关注盈利增长、低负债、机构持仓低的企业",
        "author": "彼得·林奇",
        "tags": ["成长投资", "PEG", "低负债", "盈利增长"],
        "icon": "🌱",
        "config_schema": {
            "max_peg": {"type": "number", "default": 1.0, "description": "最高 PEG"},
            "min_eps_growth": {"type": "number", "default": 15, "description": "最低 EPS 增长率 (%)"},
            "max_debt_equity": {"type": "number", "default": 0.3, "description": "最高负债权益比"},
        },
        "default_config": {"max_peg": 1.0, "min_eps_growth": 15, "max_debt_equity": 0.3},
    },
    {
        "id": "dalio-allweather",
        "name": "达里奥全天候策略",
        "category": StrategyCategory.MASTER,
        "description": "跨资产大类配置：股票+债券+黄金+大宗商品，通过风险平价实现任何经济环境下的稳健收益",
        "author": "雷·达里奥",
        "tags": ["资产配置", "风险平价", "全天候", "多元化"],
        "icon": "🌦️",
        "config_schema": {
            "stock_weight": {"type": "number", "default": 30, "description": "股票权重 (%)"},
            "bond_weight": {"type": "number", "default": 55, "description": "债券权重 (%)"},
            "gold_weight": {"type": "number", "default": 7.5, "description": "黄金权重 (%)"},
            "commodity_weight": {"type": "number", "default": 7.5, "description": "大宗商品权重 (%)"},
        },
        "default_config": {"stock_weight": 30, "bond_weight": 55, "gold_weight": 7.5, "commodity_weight": 7.5},
    },
    {
        "id": "duan-yongping",
        "name": "段永平投资哲学",
        "category": StrategyCategory.MASTER,
        "description": "只投看得懂的生意，注重商业模式和企业文化，好价格不如好公司",
        "author": "段永平",
        "tags": ["商业模式", "企业文化", "能力圈", "集中投资"],
        "icon": "🎯",
        "config_schema": {},
        "default_config": {},
    },
    {
        "id": "munger-mental",
        "name": "芒格多元思维模型",
        "category": StrategyCategory.MASTER,
        "description": "运用心理学、经济学、生物学等多学科思维模型综合评估企业价值",
        "author": "查理·芒格",
        "tags": ["多元思维", "逆向思维", "心理误判", "能力圈"],
        "icon": "🧠",
        "config_schema": {},
        "default_config": {},
    },
    # === 量化因子 ===
    {
        "id": "momentum-factor",
        "name": "动量因子策略",
        "category": StrategyCategory.QUANT,
        "description": "买入过去表现强势的股票，利用价格趋势延续性获利。核心指标：N日收益率排名",
        "author": "学术研究 (Jegadeesh & Titman)",
        "tags": ["动量", "趋势", "相对强度", "中期"],
        "icon": "🚀",
        "config_schema": {
            "lookback_days": {"type": "number", "default": 60, "description": "回溯天数"},
            "top_pct": {"type": "number", "default": 20, "description": "选前 N%"},
            "hold_days": {"type": "number", "default": 20, "description": "持有天数"},
        },
        "default_config": {"lookback_days": 60, "top_pct": 20, "hold_days": 20},
    },
    {
        "id": "value-factor",
        "name": "价值因子策略",
        "category": StrategyCategory.QUANT,
        "description": "买入低估值股票，基于 PE/PB/PS/股息率等指标综合评分",
        "author": "学术研究 (Fama & French)",
        "tags": ["价值", "低估值", "PE", "PB", "股息率"],
        "icon": "💎",
        "config_schema": {
            "metrics": {"type": "list", "default": ["pe", "pb", "ps", "dividend_yield"]},
            "top_pct": {"type": "number", "default": 20},
        },
        "default_config": {"metrics": ["pe", "pb", "ps", "dividend_yield"], "top_pct": 20},
    },
    {
        "id": "quality-factor",
        "name": "质量因子策略",
        "category": StrategyCategory.QUANT,
        "description": "买入高ROE、低负债、盈利稳定的优质公司",
        "author": "学术研究",
        "tags": ["质量", "ROE", "低负债", "盈利稳定"],
        "icon": "⭐",
        "config_schema": {
            "min_roe": {"type": "number", "default": 15},
            "max_debt_equity": {"type": "number", "default": 1.0},
            "min_profit_growth": {"type": "number", "default": 10},
        },
        "default_config": {"min_roe": 15, "max_debt_equity": 1.0, "min_profit_growth": 10},
    },
    {
        "id": "lowvol-factor",
        "name": "低波动因子策略",
        "category": StrategyCategory.QUANT,
        "description": "买入低波动率股票，追求稳健收益和低回撤",
        "author": "学术研究",
        "tags": ["低波动", "低回撤", "夏普比率", "防御型"],
        "icon": "🛡️",
        "config_schema": {
            "vol_window": {"type": "number", "default": 60, "description": "波动率计算窗口"},
            "top_pct": {"type": "number", "default": 20},
        },
        "default_config": {"vol_window": 60, "top_pct": 20},
    },
    # === 技术流派 ===
    {
        "id": "t0-scalping",
        "name": "T+0 日内波段",
        "category": StrategyCategory.TECHNICAL,
        "description": "利用A股T+0机制（底仓+当日买卖），结合分时图、量价关系做日内波段",
        "author": "市场牛散",
        "tags": ["T+0", "日内交易", "分时图", "量价关系"],
        "icon": "⚡",
        "config_schema": {
            "position_pct": {"type": "number", "default": 30, "description": "单笔仓位 (%)"},
            "stop_loss_pct": {"type": "number", "default": 2, "description": "止损 (%)"},
            "target_profit_pct": {"type": "number", "default": 3, "description": "止盈 (%)"},
        },
        "default_config": {"position_pct": 30, "stop_loss_pct": 2, "target_profit_pct": 3},
    },
    {
        "id": "ma-crossover",
        "name": "均线金叉战法",
        "category": StrategyCategory.TECHNICAL,
        "description": "经典均线交叉系统：短期均线上穿长期均线买入，下穿卖出",
        "author": "技术分析经典",
        "tags": ["均线", "金叉", "死叉", "趋势跟踪"],
        "icon": "📈",
        "config_schema": {
            "short_period": {"type": "number", "default": 5},
            "long_period": {"type": "number", "default": 20},
        },
        "default_config": {"short_period": 5, "long_period": 20},
    },
    {
        "id": "volume-price",
        "name": "量价突破战法",
        "category": StrategyCategory.TECHNICAL,
        "description": "放量突破关键阻力位时买入，缩量跌破支撑位时卖出",
        "author": "市场牛散",
        "tags": ["量价", "突破", "阻力位", "支撑位"],
        "icon": "📊",
        "config_schema": {
            "volume_ratio": {"type": "number", "default": 1.5, "description": "量比阈值"},
            "breakout_pct": {"type": "number", "default": 3, "description": "突破幅度 (%)"},
        },
        "default_config": {"volume_ratio": 1.5, "breakout_pct": 3},
    },
]


@router.get("", response_model=StrategyListResponse)
async def list_strategies(
    category: str = Query("", description="筛选分类: master/quant/technical/custom"),
    keyword: str = Query("", description="搜索关键词"),
):
    """列出所有策略模板"""
    results = STRATEGY_TEMPLATES
    if category:
        results = [s for s in results if s["category"].value == category]
    if keyword:
        kw = keyword.lower()
        results = [
            s for s in results
            if kw in s["name"].lower() or kw in s["description"].lower()
            or any(kw in t.lower() for t in s["tags"])
        ]
    return StrategyListResponse(
        strategies=[StrategyTemplate(**s) for s in results],
        total=len(results),
    )


@router.get("/{strategy_id}", response_model=StrategyTemplate)
async def get_strategy(strategy_id: str):
    """获取单个策略详情"""
    for s in STRATEGY_TEMPLATES:
        if s["id"] == strategy_id:
            return StrategyTemplate(**s)
    raise HTTPException(status_code=404, detail="策略不存在")


@router.get("/{strategy_id}/analyze")
async def analyze_with_strategy(
    strategy_id: str,
    ticker: str = Query(..., description="股票代码"),
):
    """使用指定策略分析股票（后续实现）"""
    strategy = None
    for s in STRATEGY_TEMPLATES:
        if s["id"] == strategy_id:
            strategy = s
            break
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {
        "message": f"将使用 {strategy['name']} 分析 {ticker}（功能开发中）",
        "strategy": strategy["name"],
        "ticker": ticker,
    }
