"""
FastAPI 依赖注入 — 认证中间件
"""
import logging
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.auth import decode_access_token
from services.user_service import UserService

logger = logging.getLogger("mitouai.deps")
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """从 JWT token 中提取当前用户，必须登录"""
    if not credentials:
        raise HTTPException(status_code=401, detail="请先登录")

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    user = UserService().get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict | None:
    """尝试提取用户，不强制登录"""
    if not credentials:
        return None

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        return None

    return UserService().get_user(user_id)


async def require_quota(user: dict = Depends(get_current_user)) -> dict:
    """检查用户配额，超量则拒绝"""
    from services.user_service import UserService
    svc = UserService()
    if not svc.check_quota(user["id"]):
        plan_name = user.get("plan", "free")
        limit = user.get("daily_analyses_limit", 3)
        raise HTTPException(
            status_code=429,
            detail=f"今日分析次数已用完（{plan_name}套餐：每日{limit}次）。请升级套餐或明天再试。",
        )
    return user
