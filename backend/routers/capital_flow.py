"""资金流向+龙虎榜路由"""
from fastapi import APIRouter, Query
from services.capital_flow_service import capital_flow_service

router = APIRouter()


@router.get("/north-flow")
async def get_north_flow():
    """北向资金今日流向"""
    return capital_flow_service.get_north_flow_today()


@router.get("/north-flow/detail")
async def get_north_flow_detail():
    """北向资金个股明细"""
    return {"stocks": capital_flow_service.get_north_flow_detail()}


@router.get("/north-flow/sector")
async def get_north_flow_sector():
    """北向资金行业流向"""
    return {"sectors": capital_flow_service.get_north_flow_sector()}


@router.get("/major-flow")
async def get_major_capital_flow():
    """主力资金流向"""
    return capital_flow_service.get_major_capital_flow()


@router.get("/dragon-tiger")
async def get_dragon_tiger(date: str = Query("", description="日期 YYYYMMDD")):
    """龙虎榜"""
    return {"list": capital_flow_service.get_dragon_tiger_list(date)}


@router.get("/margin")
async def get_margin_trading():
    """融资融券"""
    return capital_flow_service.get_margin_trading()
