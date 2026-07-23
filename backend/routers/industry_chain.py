"""产业链知识图谱路由"""
from fastapi import APIRouter
from services.industry_chain_service import industry_chain_service

router = APIRouter()


@router.get("/chains")
async def list_chains():
    """列出所有产业链"""
    return {"chains": industry_chain_service.list_chains()}


@router.get("/chains/{chain_id}")
async def get_chain(chain_id: str):
    """获取产业链详情（含图谱数据）"""
    chain = industry_chain_service.get_chain(chain_id)
    if not chain:
        return {"error": "产业链不存在"}
    return chain


@router.get("/stock/{ticker}")
async def get_stock_chain(ticker: str):
    """查询个股所在产业链"""
    result = industry_chain_service.get_stock_chain(ticker)
    if not result:
        return {"ticker": ticker, "chain": None, "message": "该股票暂未收录产业链数据"}
    return result
