"""
自选股与模拟组合路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from services.watchlist_service import watchlist_service
from core.dependencies import get_current_user

router = APIRouter()


# ── 请求模型 ──

class AddStockRequest(BaseModel):
    list_id: str = ""
    ticker: str
    name: str = ""


class CreateListRequest(BaseModel):
    name: str = "默认"


class CreatePortfolioRequest(BaseModel):
    name: str = "我的组合"
    initial_cash: float = 100000.0


class TradeRequest(BaseModel):
    portfolio_id: str
    ticker: str
    name: str = ""
    action: str = Field(..., pattern="^(buy|sell)$")
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


# ── 自选股 ──

@router.get("/watchlists")
async def get_watchlists(user: dict = Depends(get_current_user)):
    """获取我的自选列表"""
    return {"watchlists": watchlist_service.get_watchlists(user["id"])}


@router.post("/watchlists")
async def create_watchlist(req: CreateListRequest, user: dict = Depends(get_current_user)):
    """创建自选列表"""
    return watchlist_service.create_watchlist(user["id"], req.name)


@router.delete("/watchlists/{list_id}")
async def delete_watchlist(list_id: str, user: dict = Depends(get_current_user)):
    """删除自选列表"""
    return watchlist_service.delete_watchlist(user["id"], list_id)


@router.get("/watchlists/quotes")
async def get_watchlist_quotes(
    list_id: str = Query(""),
    user: dict = Depends(get_current_user),
):
    """获取自选股实时行情"""
    quotes = watchlist_service.get_watchlist_with_quotes(user["id"], list_id)
    return {"quotes": quotes, "total": len(quotes)}


@router.post("/watchlists/add")
async def add_to_watchlist(req: AddStockRequest, user: dict = Depends(get_current_user)):
    """添加股票到自选"""
    list_id = req.list_id
    if not list_id:
        # 如果没指定列表，取第一个或自动创建
        lists = watchlist_service.get_watchlists(user["id"])
        if lists:
            list_id = lists[0]["id"]
        else:
            wl = watchlist_service.create_watchlist(user["id"], "默认")
            list_id = wl["id"]
    return watchlist_service.add_stock(user["id"], list_id, req.ticker, req.name)


@router.post("/watchlists/remove")
async def remove_from_watchlist(req: AddStockRequest, user: dict = Depends(get_current_user)):
    """从自选移除"""
    return watchlist_service.remove_stock(user["id"], req.list_id, req.ticker)


# ── 模拟组合 ──

@router.get("/portfolios")
async def get_portfolios(user: dict = Depends(get_current_user)):
    """获取我的组合列表"""
    return {"portfolios": watchlist_service.get_portfolios(user["id"])}


@router.post("/portfolios")
async def create_portfolio(req: CreatePortfolioRequest, user: dict = Depends(get_current_user)):
    """创建组合"""
    return watchlist_service.create_portfolio(user["id"], req.name, req.initial_cash)


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str, user: dict = Depends(get_current_user)):
    """删除组合"""
    return watchlist_service.delete_portfolio(user["id"], portfolio_id)


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio_summary(portfolio_id: str, user: dict = Depends(get_current_user)):
    """获取组合详情（含实时市值）"""
    data = watchlist_service.get_portfolio_summary(user["id"], portfolio_id)
    if not data:
        raise HTTPException(status_code=404, detail="组合不存在")
    return data


@router.post("/portfolios/trade")
async def execute_trade(req: TradeRequest, user: dict = Depends(get_current_user)):
    """执行交易"""
    result = watchlist_service.trade(
        user["id"], req.portfolio_id, req.ticker, req.name,
        req.action, req.quantity, req.price,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "交易失败"))
    return result


@router.get("/portfolios/{portfolio_id}/trades")
async def get_trade_history(
    portfolio_id: str,
    limit: int = Query(50),
    user: dict = Depends(get_current_user),
):
    """获取交易记录"""
    trades = watchlist_service.get_trade_history(user["id"], portfolio_id, limit)
    return {"trades": trades, "total": len(trades)}
