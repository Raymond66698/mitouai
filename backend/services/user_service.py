"""
用户服务 — 注册、登录、配额管理、自带Key
使用 SQLAlchemy ORM + PostgreSQL/SQLite 双后端
"""
import logging
import uuid
from datetime import datetime, date
from typing import Optional

from config import settings
from database import get_db_context
from models.user import User, UserApiKey
from models.token import TokenBalance

logger = logging.getLogger("mitouai.user")


class UserService:
    """用户管理服务（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── 注册 / 登录 ──

    def register(self, email: str, password: str, display_name: str = "") -> dict:
        """注册新用户"""
        email = email.lower().strip()

        from core.auth import hash_password

        with get_db_context() as db:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise ValueError("该邮箱已注册")

            user_id = str(uuid.uuid4())[:12]
            now = datetime.now().isoformat()
            today = date.today().isoformat()

            user = User(
                id=user_id,
                email=email,
                password_hash=hash_password(password),
                display_name=display_name or email.split("@")[0],
                plan="free",
                daily_analyses_limit=settings.SUBSCRIPTION_PLANS["free"]["daily_analyses"],
                daily_analyses_date=today,
                created_at=now,
                updated_at=now,
            )
            db.add(user)

            # 初始化 Token 余额
            balance = TokenBalance(user_id=user_id, balance=0)
            db.add(balance)

            db.commit()

            logger.info(f"新用户注册: {email} -> {user_id}")
            return self._sanitize(user)

    def login(self, email: str, password: str) -> Optional[dict]:
        """邮箱密码登录，返回用户对象（含 token）"""
        email = email.lower().strip()
        from core.auth import verify_password, create_access_token

        with get_db_context() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            if not verify_password(password, user.password_hash):
                return None

            self._reset_daily_if_needed(user, db)
            db.commit()

            return {
                **self._sanitize(user),
                "access_token": create_access_token(user.id),
            }

    # ── 用户查询 ──

    def get_user(self, user_id: str) -> Optional[dict]:
        """根据 ID 获取用户（返回 dict，兼容旧接口）"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                self._reset_daily_if_needed(user, db)
                db.commit()
                return self._to_dict(user)
            return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """根据邮箱获取用户（返回 dict）"""
        with get_db_context() as db:
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            return self._to_dict(user) if user else None

    # ── 配额管理 ──

    def _reset_daily_if_needed(self, user: User, db):
        """跨天重置每日配额"""
        today = date.today().isoformat()
        if user.daily_analyses_date != today:
            user.daily_analyses_used = 0
            user.daily_analyses_date = today

    def check_quota(self, user_id: str) -> bool:
        """检查用户是否还有配额"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            self._reset_daily_if_needed(user, db)
            db.commit()
            limit = user.daily_analyses_limit
            if limit == -1:
                return True
            return user.daily_analyses_used < limit

    def consume_quota(self, user_id: str):
        """消耗一次分析配额"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                self._reset_daily_if_needed(user, db)
                user.daily_analyses_used += 1
                user.total_analyses += 1
                db.commit()

    def get_remaining_quota(self, user_id: str) -> dict:
        """获取剩余配额"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"remaining": 0, "limit": 3, "plan": "free"}

            self._reset_daily_if_needed(user, db)
            db.commit()
            limit = user.daily_analyses_limit
            plan = user.plan
            return {
                "plan": plan,
                "plan_name": settings.SUBSCRIPTION_PLANS.get(plan, {}).get("name", ""),
                "daily_used": user.daily_analyses_used,
                "daily_limit": limit if limit != -1 else "无限",
                "remaining": "无限" if limit == -1 else max(0, limit - user.daily_analyses_used),
                "total_analyses": user.total_analyses,
            }

    # ── 订阅管理 ──

    def upgrade_plan(self, user_id: str, plan: str) -> dict:
        """升级订阅套餐"""
        plan_config = settings.SUBSCRIPTION_PLANS.get(plan)
        if not plan_config:
            raise ValueError(f"无效的套餐: {plan}")

        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")

            user.plan = plan
            user.daily_analyses_limit = plan_config["daily_analyses"]
            user.daily_analyses_used = 0
            user.updated_at = datetime.now().isoformat()
            db.commit()

            logger.info(f"用户 {user.email} 升级到 {plan}")
            return self._sanitize(user)

    # ── 自带 Key (BYOK) ──

    def set_user_key(self, user_id: str, provider: str, api_key: str):
        """设置用户自己的 API Key"""
        with get_db_context() as db:
            existing = db.query(UserApiKey).filter(
                UserApiKey.user_id == user_id,
                UserApiKey.provider == provider,
            ).first()
            if existing:
                existing.api_key = api_key
                existing.updated_at = datetime.now().isoformat()
            else:
                key = UserApiKey(user_id=user_id, provider=provider, api_key=api_key)
                db.add(key)
            db.commit()
        logger.info(f"用户 {user_id} 设置了 {provider} key")

    def remove_user_key(self, user_id: str, provider: str):
        """删除用户的 API Key"""
        with get_db_context() as db:
            db.query(UserApiKey).filter(
                UserApiKey.user_id == user_id,
                UserApiKey.provider == provider,
            ).delete()
            db.commit()

    def get_user_key(self, user_id: str, provider: str = "deepseek") -> Optional[str]:
        """获取用户的 API Key"""
        with get_db_context() as db:
            key = db.query(UserApiKey).filter(
                UserApiKey.user_id == user_id,
                UserApiKey.provider == provider,
            ).first()
            return key.api_key if key else None

    def get_user_keys_status(self, user_id: str) -> dict:
        """获取用户已设置的 Key 列表（不暴露完整 key）"""
        with get_db_context() as db:
            keys = db.query(UserApiKey).filter(UserApiKey.user_id == user_id).all()
            return {k.provider: ("已设置" if k.api_key else "未设置") for k in keys}

    # ── 推送设置 ──

    def update_notification_settings(self, user_id: str, settings_dict: dict):
        """更新推送通知设置"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")

            if "pushplus_token" in settings_dict:
                user.notification_pushplus_token = settings_dict["pushplus_token"]
            if "email_notify" in settings_dict:
                user.notification_email_notify = settings_dict["email_notify"]
            if "analysis_complete" in settings_dict:
                user.notification_analysis_complete = settings_dict["analysis_complete"]
            if "breaking_news" in settings_dict:
                user.notification_breaking_news = settings_dict["breaking_news"]

            user.updated_at = datetime.now().isoformat()
            db.commit()

    def get_notification_settings(self, user_id: str) -> dict:
        """获取推送通知设置"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            return {
                "pushplus_token": user.notification_pushplus_token,
                "email_notify": user.notification_email_notify,
                "analysis_complete": user.notification_analysis_complete,
                "breaking_news": user.notification_breaking_news,
            }

    # ── 更新资料 ──

    def update_profile(self, user_id: str, display_name: str) -> dict:
        """更新用户资料"""
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            user.display_name = display_name
            user.updated_at = datetime.now().isoformat()
            db.commit()
            return self._sanitize(user)

    # ── 工具方法 ──

    def _sanitize(self, user: User) -> dict:
        """脱敏用户信息（去除 password_hash）"""
        d = {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "plan": user.plan,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "daily_analyses_used": user.daily_analyses_used,
            "daily_analyses_date": user.daily_analyses_date,
            "daily_analyses_limit": user.daily_analyses_limit,
            "total_analyses": user.total_analyses,
            "notification_settings": {
                "pushplus_token": user.notification_pushplus_token,
                "email_notify": user.notification_email_notify,
                "analysis_complete": user.notification_analysis_complete,
                "breaking_news": user.notification_breaking_news,
            },
            "plan_name": settings.SUBSCRIPTION_PLANS.get(user.plan, {}).get("name", ""),
            "plan_features": settings.SUBSCRIPTION_PLANS.get(user.plan, {}).get("features", []),
            "plan_price": settings.SUBSCRIPTION_PLANS.get(user.plan, {}).get("price", 0),
        }
        return d

    def _to_dict(self, user: User) -> dict:
        """转为对外兼容的 dict 格式（与旧 JSON 存储一致）"""
        d = {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "display_name": user.display_name,
            "plan": user.plan,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "daily_analyses_used": user.daily_analyses_used,
            "daily_analyses_date": user.daily_analyses_date,
            "daily_analyses_limit": user.daily_analyses_limit,
            "total_analyses": user.total_analyses,
            "notification_settings": {
                "pushplus_token": user.notification_pushplus_token,
                "email_notify": user.notification_email_notify,
                "analysis_complete": user.notification_analysis_complete,
                "breaking_news": user.notification_breaking_news,
            },
        }
        return d


# 全局单例
user_service = UserService()
