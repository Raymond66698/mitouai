"""港股+美股行情路由"""
from fastapi import APIRouter, Query
from services.hk_us_service import hk_us_service

router = APIRouter()


@router.get("/search")
async def search_multi_market(q: str = Query("", description="搜索关键词")):
    """多市场联合搜索"""
    return hk_us_service.search_multi_market(q)


@router.get("/hk/quote/{code}")
async def get_hk_quote(code: str):
    """港股实时行情"""
    return {"code": code, "quote": hk_us_service.get_hk_realtime_quote(code)}


@router.get("/us/quote/{symbol}")
async def get_us_quote(symbol: str):
    """美股实时行情"""
    return {"symbol": symbol, "quote": hk_us_service.get_us_realtime_quote(symbol)}


@router.get("/hk/kline/{code}")
async def get_hk_kline(code: str, days: int = Query(365, description="数据天数")):
    """港股K线"""
    return {"code": code, "kline": hk_us_service.get_hk_kline(code, days)}


@router.get("/us/kline/{symbol}")
async def get_us_kline(symbol: str, days: int = Query(365, description="数据天数")):
    """美股K线"""
    return {"symbol": symbol, "kline": hk_us_service.get_us_kline(symbol, days)}


@router.get("/hk/indices")
async def get_hk_indices():
    """港股指数"""
    return {"indices": hk_us_service.get_hk_indices()}


@router.get("/us/indices")
async def get_us_indices():
    """美股指数"""
    return {"indices": hk_us_service.get_us_indices()}
