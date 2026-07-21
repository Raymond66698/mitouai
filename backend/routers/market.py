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
