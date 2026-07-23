"""
回测路由 — 策略回测、多策略对比
"""
import logging
from fastapi import APIRouter, Query
from services.backtest_service import backtest_engine

logger = logging.getLogger("mitouai.backtest")
router = APIRouter()


@router.post("/run")
async def run_backtest(req: dict):
    """运行单个策略回测

    请求体: {
        "ticker": "601991.SS",
        "strategy": "ma_crossover",
        "params": {"short_period": 5, "long_period": 20},
        "start_date": "2025-01-01",
        "end_date": "2026-07-22",
        "initial_capital": 100000
    }
    """
    try:
        result = backtest_engine.run(
            ticker=req.get("ticker", ""),
            strategy=req.get("strategy", "ma_crossover"),
            params=req.get("params", {}),
            start_date=req.get("start_date"),
            end_date=req.get("end_date"),
            initial_capital=req.get("initial_capital", 100000),
        )
        return result
    except Exception as e:
        logger.error(f"回测失败: {e}")
        return {"error": str(e)}


@router.get("/quick")
async def quick_backtest(
    ticker: str = Query(..., description="股票代码"),
    strategy: str = Query("ma_crossover", description="策略ID"),
    short_period: int = Query(5, description="短期均线"),
    long_period: int = Query(20, description="长期均线"),
    lookback_days: int = Query(365, description="回测天数"),
):
    """快速回测"""
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    params = {}
    if strategy == "ma_crossover":
        params = {"short_period": short_period, "long_period": long_period}
    elif strategy == "momentum":
        params = {"lookback_days": 20, "threshold": 5}
    elif strategy == "rsi_reversal":
        params = {"rsi_period": 14, "oversold": 30, "overbought": 70}

    result = backtest_engine.run(
        ticker=ticker, strategy=strategy, params=params,
        start_date=start_date, end_date=end_date,
    )
    return result


@router.post("/compare")
async def compare_strategies(req: dict):
    """多策略对比回测

    请求体: {
        "ticker": "601991.SS",
        "strategies": ["buy_hold", "ma_crossover", "momentum"],
        "start_date": "2025-01-01",
        "end_date": "2026-07-22"
    }
    """
    try:
        result = backtest_engine.run_benchmark_comparison(
            ticker=req.get("ticker", ""),
            strategies=req.get("strategies"),
            start_date=req.get("start_date"),
            end_date=req.get("end_date"),
        )
        return result
    except Exception as e:
        logger.error(f"回测对比失败: {e}")
        return {"error": str(e)}


@router.get("/strategies")
async def list_backtest_strategies():
    """列出可回测的策略"""
    return {
        "strategies": [
            {
                "id": "buy_hold", "name": "买入持有",
                "category": "基准", "description": "买入并持有的被动策略，作为回测基准",
                "params": {},
            },
            {
                "id": "ma_crossover", "name": "均线交叉",
                "category": "技术", "description": "短期均线上穿长期均线买入，下穿卖出",
                "params": {"short_period": 5, "long_period": 20},
            },
            {
                "id": "momentum", "name": "动量突破",
                "category": "量化", "description": "N日涨幅超阈值买入，跌破阈值卖出",
                "params": {"lookback_days": 20, "threshold": 5},
            },
            {
                "id": "rsi_reversal", "name": "RSI反转",
                "category": "技术", "description": "RSI超卖买入，超买卖出",
                "params": {"rsi_period": 14, "oversold": 30, "overbought": 70},
            },
        ],
    }
