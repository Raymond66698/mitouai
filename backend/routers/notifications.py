"""
通知路由 — 推送设置、通知历史
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import (
    NotificationSettingsUpdate, APIResponse, NotificationItem,
)
from core.dependencies import get_current_user
from services.user_service import UserService
from services.push_service import push_service

logger = logging.getLogger("mitouai.notify")
router = APIRouter()


@router.get("/settings", response_model=APIResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    """获取推送通知设置"""
    settings_dict = UserService().get_notification_settings(user["id"])
    return APIResponse(success=True, data={"settings": settings_dict})


@router.put("/settings", response_model=APIResponse)
async def update_settings(
    req: NotificationSettingsUpdate,
    user: dict = Depends(get_current_user),
):
    """更新推送通知设置"""
    update_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    if update_dict:
        UserService().update_notification_settings(user["id"], update_dict)
    return APIResponse(success=True, message="推送设置已更新")


@router.get("/history", response_model=APIResponse)
async def get_history(
    limit: int = 20,
    unread_only: bool = False,
    user: dict = Depends(get_current_user),
):
    """获取通知历史"""
    notifications = push_service.get_notifications(
        user["id"], limit=limit, unread_only=unread_only
    )
    return APIResponse(
        success=True,
        data={
            "notifications": notifications,
            "total": len(notifications),
        },
    )


@router.post("/read/{index}", response_model=APIResponse)
async def mark_read(
    index: int,
    user: dict = Depends(get_current_user),
):
    """标记通知已读"""
    push_service.mark_read(user["id"], index)
    return APIResponse(success=True, message="已标记为已读")


@router.post("/read-all", response_model=APIResponse)
async def mark_all_read(user: dict = Depends(get_current_user)):
    """全部标记已读"""
    push_service.mark_all_read(user["id"])
    return APIResponse(success=True, message="全部已标记为已读")


@router.get("/help", response_model=APIResponse)
async def push_help():
    """PushPlus 配置帮助"""
    return APIResponse(
        success=True,
        data={
            "service": "PushPlus (pushplus.plus)",
            "description": "免费微信推送服务，分析完成后即时通知",
            "steps": [
                "1. 打开 pushplus.plus 官网",
                "2. 微信扫码登录",
                "3. 在「发送消息」页面复制您的 Token",
                "4. 在觅投AI通知设置中填入 Token",
                "5. 分析完成后您将收到微信推送通知",
            ],
        },
    )
