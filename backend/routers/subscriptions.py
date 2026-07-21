"""
订阅路由 — 套餐查询、升级
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import (
    PlansResponse, PlanInfo, UpgradeRequest, UpgradeResponse, APIResponse,
)
from core.dependencies import get_current_user
from services.user_service import UserService
from config import settings

logger = logging.getLogger("mitouai.subs")
router = APIRouter()


@router.get("/plans", response_model=PlansResponse)
async def list_plans(user: dict = Depends(get_current_user)):
    """获取所有订阅套餐"""
    plans = []
    for plan_id, config in settings.SUBSCRIPTION_PLANS.items():
        plans.append(PlanInfo(
            id=plan_id,
            name=config["name"],
            price=config["price"],
            price_unit=config["price_unit"],
            daily_analyses="无限" if config["daily_analyses"] == -1 else config["daily_analyses"],
            models=config["models"],
            features=config["features"],
            bring_your_own_key=config["bring_your_own_key"],
        ))
    return PlansResponse(
        plans=plans,
        current_plan=user.get("plan", "free"),
    )


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_plan(
    req: UpgradeRequest,
    user: dict = Depends(get_current_user),
):
    """升级订阅套餐（MVP阶段直接生效，后续接支付）"""
    svc = UserService()
    try:
        updated = svc.upgrade_plan(user["id"], req.plan)
        plan_config = settings.SUBSCRIPTION_PLANS.get(req.plan, {})

        return UpgradeResponse(
            success=True,
            message=f"已升级到{plan_config.get('name', req.plan)}！",
            new_plan=req.plan,
            new_plan_name=plan_config.get("name", req.plan),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
