"""Token 管理路由 — 余额、套餐、使用记录"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.dependencies import get_current_user
from services.token_service import token_service

router = APIRouter()


class PurchaseRequest(BaseModel):
    package_id: str


class ConsumeRequest(BaseModel):
    action: str
    tokens: int = 0


@router.get("/balance")
async def get_balance(user: dict = Depends(get_current_user)):
    """获取 token 余额"""
    return token_service.get_balance(user["id"])


@router.get("/packages")
async def get_packages(user: dict = Depends(get_current_user)):
    """获取所有可用套餐"""
    pkgs = token_service.get_packages()
    # 检查新手包是否已领取
    history = token_service.get_usage_history(user["id"])
    has_starter = any(tx.get("package_id") == "starter" for tx in history)
    result = []
    for p in pkgs:
        p_copy = dict(p)
        if p["id"] == "starter" and has_starter:
            p_copy["disabled"] = True
            p_copy["tag"] = "已领取"
        result.append(p_copy)
    return {"packages": result, "balance": token_service.get_balance(user["id"])}


@router.post("/purchase")
async def purchase_package(req: PurchaseRequest, user: dict = Depends(get_current_user)):
    """购买/领取 token 套餐"""
    try:
        result = token_service.purchase(user["id"], req.package_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
):
    """获取 token 使用记录"""
    history = token_service.get_usage_history(user["id"], limit)
    return {"history": history, "balance": token_service.get_balance(user["id"])}


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """获取 token 使用统计"""
    stats = token_service.get_usage_stats(user["id"])
    stats["balance"] = token_service.get_balance(user["id"])
    return stats
