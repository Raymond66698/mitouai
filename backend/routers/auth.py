"""
认证路由 — 注册、登录
"""
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import RegisterRequest, LoginRequest, AuthResponse
from services.user_service import UserService

logger = logging.getLogger("mitouai.auth")
router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """邮箱注册"""
    try:
        user = UserService().register(
            email=req.email,
            password=req.password,
            display_name=req.display_name,
        )
        return AuthResponse(
            success=True,
            message="注册成功",
            user=user,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """邮箱密码登录"""
    try:
        result = UserService().login(email=req.email, password=req.password)
        if result is None:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")

        return AuthResponse(
            success=True,
            message="登录成功",
            user={k: v for k, v in result.items() if k != "access_token"},
            access_token=result.get("access_token"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试")
