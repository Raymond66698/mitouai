"""
每日AI市场播报路由
"""
from fastapi import APIRouter, Depends
from services.daily_brief_service import daily_brief_service
from core.dependencies import get_current_user

router = APIRouter()


@router.get("/overview")
async def get_market_overview(user: dict = Depends(get_current_user)):
    """获取市场全貌数据"""
    data = daily_brief_service.get_market_overview()
    return data


@router.get("/ai-summary")
async def get_ai_summary(user: dict = Depends(get_current_user)):
    """获取AI市场解读"""
    data = daily_brief_service.get_ai_interpretation()
    return data


@router.get("/events")
async def get_today_events(user: dict = Depends(get_current_user)):
    """获取今日重要事件"""
    events = daily_brief_service.get_today_events()
    return {"events": events, "total": len(events)}


@router.get("/concepts")
async def get_concept_movers(user: dict = Depends(get_current_user)):
    """获取概念板块异动"""
    concepts = daily_brief_service.get_concept_movers()
    return {"concepts": concepts}
