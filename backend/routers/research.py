"""
AI研报聚合路由
"""
from fastapi import APIRouter, Depends, Query
from services.research_service import research_service
from core.dependencies import get_current_user

router = APIRouter()


@router.get("/stock/{ticker}")
async def get_stock_research(ticker: str, user: dict = Depends(get_current_user)):
    """获取个股研报聚合"""
    data = research_service.get_stock_research(ticker)
    return data


@router.get("/hot")
async def get_hot_research(
    limit: int = Query(20, le=50),
    user: dict = Depends(get_current_user),
):
    """获取热门研报"""
    reports = research_service.get_hot_research(limit)
    return {"reports": reports, "total": len(reports)}


@router.get("/chain/{ticker}")
async def get_industry_chain(ticker: str, user: dict = Depends(get_current_user)):
    """获取产业链分析"""
    data = research_service.get_industry_chain(ticker)
    return data
