"""
选股器路由 — 多因子筛选、自然语言选股、策略选股
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from services.screener_service import screener

logger = logging.getLogger("mitouai.screener")
router = APIRouter()


@router.get("/search")
async def natural_language_search(
    q: str = Query(..., description="自然语言选股条件"),
    top_n: int = Query(20, description="返回数量"),
):
    """自然语言选股（用AI解析选股意图）"""
    if not q or len(q.strip()) < 2:
        return {"results": [], "total": 0, "message": "请输入更多筛选条件"}

    result = screener.natural_language_search(q.strip(), top_n)
    return result


@router.post("/filter")
async def filter_stocks(
    conditions: dict,
    top_n: int = Query(30, description="返回数量"),
):
    """按条件筛选股票"""
    result = screener.search_by_conditions(conditions, top_n)
    return result


@router.get("/strategy/{strategy_id}")
async def strategy_screen(
    strategy_id: str,
    top_n: int = Query(30, description="返回数量"),
):
    """使用策略模板选股"""
    result = screener.apply_strategy_template(strategy_id, top_n)
    return result


@router.get("/conditions")
async def get_available_conditions():
    """获取可用的筛选条件说明"""
    return {
        "conditions": {
            "估值": ["min_pe", "max_pe", "min_pb", "max_pb"],
            "质量": ["min_roe", "min_roe", "max_debt_ratio"],
            "规模": ["min_mv", "max_mv"],
            "成长": ["min_revenue_growth", "min_profit_growth"],
            "市场": ["change_min", "change_max", "min_turnover", "max_turnover"],
            "分红": ["min_dividend_yield"],
            "其他": ["sector", "exclude_st", "sort_by"],
        },
        "examples": [
            "低估值高分红蓝筹股",
            "PE小于20且ROE大于15%的消费股",
            "科技板块高成长小盘股",
            "近期超跌的优质股",
            "市盈率低于15的银行股",
        ],
    }
