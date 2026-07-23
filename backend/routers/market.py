"""
行情数据路由 — 股票搜索、实时行情、K线数据
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from services.data_service import DataService

logger = logging.getLogger("mitouai.market")
router = APIRouter()
data_service = DataService()


@router.get("/search")
async def search_stocks(q: str = Query("", description="股票代码或名称")):
    """搜索股票"""
    results = data_service.search_stocks(q)
    return {"results": results, "total": len(results)}


@router.get("/quote/{ticker}")
async def get_quote(ticker: str):
    """获取实时行情"""
    try:
        quote = data_service.get_realtime_quote(ticker)
        return {"ticker": ticker, "quote": quote}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{ticker}")
async def get_kline(
    ticker: str,
    start_date: str = Query("", description="起始日期 YYYY-MM-DD"),
    end_date: str = Query("", description="结束日期 YYYY-MM-DD"),
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
):
    """获取K线数据"""
    try:
        kline = data_service.get_kline(ticker, start_date, end_date, period)
        return {"ticker": ticker, "period": period, "data": kline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices")
async def get_market_indices():
    """获取主要市场指数"""
    return {"indices": data_service.get_market_indices()}


@router.get("/sectors")
async def get_sectors():
    """获取行业板块表现"""
    sectors = data_service.get_sector_performance()
    return {"sectors": sectors}


@router.get("/news")
async def get_news(limit: int = Query(15, description="新闻数量")):
    """获取市场要闻"""
    news = data_service.get_market_news(limit)
    return {"news": news}


@router.get("/fundamentals/{ticker}")
async def get_fundamentals(ticker: str):
    """获取个股基本面"""
    data = data_service.get_stock_fundamentals(ticker)
    return {"ticker": ticker, "fundamentals": data}


@router.get("/snowflake/{ticker}")
async def get_snowflake(ticker: str):
    """获取五维分析数据（估值/成长/质量/动量/风险）"""
    import math
    try:
        # 获取基本面
        fund = data_service.get_stock_fundamentals(ticker)

        # 获取K线用于动量和风险计算
        kline = data_service.get_kline(ticker, start_date="", end_date="", period="daily")

        # 实时行情
        quote = data_service.get_realtime_quote(ticker)

        # ── 估值维度（0-100，越高越低估）──
        pe = fund.get("pe") or quote.get("pe")
        pb = fund.get("pb") or quote.get("pb")
        value_score = 50
        if pe and pe > 0:
            if pe < 10: value_score = 90
            elif pe < 15: value_score = 75
            elif pe < 20: value_score = 60
            elif pe < 30: value_score = 45
            elif pe < 50: value_score = 30
            else: value_score = 15
        if pb and pb > 0 and pb < 1: value_score = min(100, value_score + 10)

        # ── 成长维度 ──
        growth_score = 50
        rev_g = fund.get("revenue_growth")
        profit_g = fund.get("profit_growth")
        if rev_g is not None:
            growth_score = min(100, max(0, 50 + rev_g * 1.5))
        if profit_g is not None:
            growth_score = min(100, (growth_score + min(100, max(0, 50 + profit_g * 1.5))) / 2)

        # ── 质量维度 ──
        quality_score = 50
        roe = fund.get("roe")
        if roe is not None:
            if roe > 25: quality_score = 90
            elif roe > 15: quality_score = 75
            elif roe > 10: quality_score = 60
            elif roe > 5: quality_score = 45
            else: quality_score = 25
        dr = fund.get("debt_ratio")
        if dr is not None and dr > 70: quality_score = max(10, quality_score - 20)

        # ── 动量维度 ──
        momentum_score = 50
        if kline and len(kline) >= 20:
            close_prices = [float(k["close"]) for k in kline]
            # 20日涨跌幅
            if len(close_prices) >= 20:
                ret_20 = (close_prices[-1] - close_prices[-20]) / close_prices[-20] * 100
                momentum_score = min(100, max(0, 50 + ret_20 * 2))
            # 换手率加分
            turnover = quote.get("turnover", 0)
            if turnover > 5: momentum_score = min(100, momentum_score + 15)

        # ── 风险维度（越高风险越低）──
        risk_score = 50
        if kline and len(kline) >= 20:
            daily_returns = []
            for i in range(1, len(close_prices)):
                if close_prices[i-1] > 0:
                    daily_returns.append((close_prices[i] - close_prices[i-1]) / close_prices[i-1])
            if daily_returns:
                std = (sum(r*r for r in daily_returns) / len(daily_returns)) ** 0.5
                vol = std * (252 ** 0.5) * 100  # 年化波动率
                if vol < 20: risk_score = 85
                elif vol < 30: risk_score = 65
                elif vol < 40: risk_score = 50
                elif vol < 50: risk_score = 35
                else: risk_score = 20
            # 最大回撤
            peak = close_prices[0]
            max_dd = 0
            for p in close_prices:
                peak = max(peak, p)
                dd = (peak - p) / peak * 100
                max_dd = max(max_dd, dd)
            if max_dd > 30: risk_score = max(15, risk_score - 20)

        # 综合评分
        composite = round((value_score * 0.25 + growth_score * 0.2 + quality_score * 0.25 + momentum_score * 0.15 + risk_score * 0.15), 1)

        return {
            "ticker": ticker,
            "name": fund.get("name", quote.get("name", ticker)),
            "dimensions": {
                "value": {"label": "估值优势", "score": round(value_score, 1), "max": 100},
                "growth": {"label": "成长性", "score": round(growth_score, 1), "max": 100},
                "quality": {"label": "质量", "score": round(quality_score, 1), "max": 100},
                "momentum": {"label": "动量", "score": round(momentum_score, 1), "max": 100},
                "risk": {"label": "低风险", "score": round(risk_score, 1), "max": 100},
            },
            "composite_score": composite,
            "fundamentals": fund,
            "quote": quote,
        }
    except Exception as e:
        logger.warning(f"Snowflake计算失败 [{ticker}]: {e}")
        return {"ticker": ticker, "error": str(e)}
