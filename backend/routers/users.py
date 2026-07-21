"""
用户路由 — 个人信息、配额、自带Key管理
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import (
    UserProfile, QuotaResponse, UpdateProfileRequest,
    SetKeyRequest, APIResponse,
)
from core.dependencies import get_current_user
from services.user_service import UserService

logger = logging.getLogger("mitouai.users")
router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户完整信息"""
    svc = UserService()
    fresh_user = svc.get_user(user["id"])
    if not fresh_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserProfile(**svc._sanitize(fresh_user))


@router.put("/me", response_model=APIResponse)
async def update_me(
    req: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
):
    """更新个人信息"""
    try:
        updated = UserService().update_profile(user["id"], req.display_name)
        return APIResponse(
            success=True,
            message="更新成功",
            data={"user": updated},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quota", response_model=QuotaResponse)
async def get_quota(user: dict = Depends(get_current_user)):
    """查询当前配额"""
    return QuotaResponse(**UserService().get_remaining_quota(user["id"]))


# ── 自带 Key ──

@router.put("/me/key", response_model=APIResponse)
async def set_my_key(
    req: SetKeyRequest,
    user: dict = Depends(get_current_user),
):
    """设置我的 API Key（大师版可用）"""
    svc = UserService()
    fuser = svc.get_user(user["id"])
    plan_config = __import__("config").settings.SUBSCRIPTION_PLANS.get(fuser["plan"], {})

    if not plan_config.get("bring_your_own_key", False):
        raise HTTPException(
            status_code=403,
            detail="此功能仅限大师版用户使用。请升级套餐。"
        )

    svc.set_user_key(user["id"], req.provider, req.api_key)
    return APIResponse(success=True, message=f"{req.provider} Key 已设置")


@router.delete("/me/key/{provider}", response_model=APIResponse)
async def remove_my_key(
    provider: str,
    user: dict = Depends(get_current_user),
):
    """删除我的 API Key"""
    UserService().remove_user_key(user["id"], provider)
    return APIResponse(success=True, message=f"{provider} Key 已删除")


@router.get("/me/keys", response_model=APIResponse)
async def get_my_keys(user: dict = Depends(get_current_user)):
    """查看已设置的 Key"""
    status = UserService().get_user_keys_status(user["id"])
    return APIResponse(success=True, data={"keys": status})
