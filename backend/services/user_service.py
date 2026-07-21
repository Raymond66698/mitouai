"""
用户服务 — 注册、登录、配额管理、自带Key
MVP 阶段使用 JSON 文件存储，生产环境切换到 Supabase PostgreSQL
"""
import json
import logging
import os
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from config import settings

logger = logging.getLogger("mitouai.user")

# 数据存储路径
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
KEYS_FILE = DATA_DIR / "user_keys.json"


class UserService:
    """用户管理服务（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """从 JSON 文件加载用户数据"""
        if USERS_FILE.exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                self._users = json.load(f)
        else:
            self._users = {}

        if KEYS_FILE.exists():
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                self._user_keys = json.load(f)
        else:
            self._user_keys = {}

    def _save(self):
        """持久化到 JSON 文件"""
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._users, f, ensure_ascii=False, indent=2)
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._user_keys, f, ensure_ascii=False, indent=2)

    # ── 注册 / 登录 ──

    def register(self, email: str, password: str, display_name: str = "") -> dict:
        """注册新用户"""
        email = email.lower().strip()
        # 检查是否已存在
        for uid, user in self._users.items():
            if user["email"] == email:
                raise ValueError("该邮箱已注册")

        from core.auth import hash_password

        user_id = str(uuid.uuid4())[:12]
        now = datetime.now().isoformat()
        today = date.today().isoformat()

        user = {
            "id": user_id,
            "email": email,
            "password_hash": hash_password(password),
            "display_name": display_name or email.split("@")[0],
            "plan": "free",
            "created_at": now,
            "updated_at": now,
            "daily_analyses_used": 0,
            "daily_analyses_date": today,
            "daily_analyses_limit": settings.SUBSCRIPTION_PLANS["free"]["daily_analyses"],
            "total_analyses": 0,
            "notification_settings": {
                "pushplus_token": "",
                "email_notify": False,
                "analysis_complete": True,
                "breaking_news": False,
            },
        }
        self._users[user_id] = user
        self._save()

        logger.info(f"新用户注册: {email} -> {user_id}")
        return self._sanitize(user)

    def login(self, email: str, password: str) -> Optional[dict]:
        """邮箱密码登录，返回用户对象（含 token）"""
        email = email.lower().strip()
        from core.auth import verify_password, create_access_token

        for uid, user in self._users.items():
            if user["email"] == email:
                if verify_password(password, user["password_hash"]):
                    # 重置每日配额（跨天）
                    self._reset_daily_if_needed(user)
                    return {
                        **self._sanitize(user),
                        "access_token": create_access_token(uid),
                    }
                return None  # 密码错误
        return None  # 用户不存在

    # ── 用户查询 ──

    def get_user(self, user_id: str) -> Optional[dict]:
        """根据 ID 获取用户"""
        user = self._users.get(user_id)
        if user:
            self._reset_daily_if_needed(user)
        return user

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """根据邮箱获取用户"""
        for user in self._users.values():
            if user["email"] == email.lower().strip():
                return user
        return None

    # ── 配额管理 ──

    def _reset_daily_if_needed(self, user: dict):
        """跨天重置每日配额"""
        today = date.today().isoformat()
        if user.get("daily_analyses_date") != today:
            user["daily_analyses_used"] = 0
            user["daily_analyses_date"] = today
            self._save()

    def check_quota(self, user_id: str) -> bool:
        """检查用户是否还有配额"""
        user = self._users.get(user_id)
        if not user:
            return False
        self._reset_daily_if_needed(user)
        limit = user.get("daily_analyses_limit", 3)
        if limit == -1:  # 无限
            return True
        return user.get("daily_analyses_used", 0) < limit

    def consume_quota(self, user_id: str):
        """消耗一次分析配额"""
        user = self._users.get(user_id)
        if user:
            self._reset_daily_if_needed(user)
            user["daily_analyses_used"] = user.get("daily_analyses_used", 0) + 1
            user["total_analyses"] = user.get("total_analyses", 0) + 1
            self._save()

    def get_remaining_quota(self, user_id: str) -> dict:
        """获取剩余配额"""
        user = self._users.get(user_id)
        if not user:
            return {"remaining": 0, "limit": 3, "plan": "free"}
        self._reset_daily_if_needed(user)
        limit = user.get("daily_analyses_limit", 3)
        used = user.get("daily_analyses_used", 0)
        return {
            "plan": user.get("plan", "free"),
            "plan_name": settings.SUBSCRIPTION_PLANS.get(user.get("plan", "free"), {}).get("name", ""),
            "daily_used": used,
            "daily_limit": limit if limit != -1 else "无限",
            "remaining": "无限" if limit == -1 else max(0, limit - used),
            "total_analyses": user.get("total_analyses", 0),
        }

    # ── 订阅管理 ──

    def upgrade_plan(self, user_id: str, plan: str) -> dict:
        """升级订阅套餐"""
        user = self._users.get(user_id)
        if not user:
            raise ValueError("用户不存在")

        plan_config = settings.SUBSCRIPTION_PLANS.get(plan)
        if not plan_config:
            raise ValueError(f"无效的套餐: {plan}")

        user["plan"] = plan
        user["daily_analyses_limit"] = plan_config["daily_analyses"]
        user["daily_analyses_used"] = 0
        user["updated_at"] = datetime.now().isoformat()
        self._save()

        logger.info(f"用户 {user['email']} 升级到 {plan}")
        return self._sanitize(user)

    # ── 自带 Key (BYOK) ──

    def set_user_key(self, user_id: str, provider: str, api_key: str):
        """设置用户自己的 API Key"""
        if user_id not in self._user_keys:
            self._user_keys[user_id] = {}
        self._user_keys[user_id][provider] = api_key
        self._save()
        logger.info(f"用户 {user_id} 设置了 {provider} key")

    def remove_user_key(self, user_id: str, provider: str):
        """删除用户的 API Key"""
        if user_id in self._user_keys and provider in self._user_keys[user_id]:
            del self._user_keys[user_id][provider]
            self._save()

    def get_user_key(self, user_id: str, provider: str = "deepseek") -> Optional[str]:
        """获取用户的 API Key"""
        return self._user_keys.get(user_id, {}).get(provider)

    def get_user_keys_status(self, user_id: str) -> dict:
        """获取用户已设置的 Key 列表（不暴露完整 key）"""
        keys = self._user_keys.get(user_id, {})
        return {
            k: ("已设置" if v else "未设置") for k, v in keys.items()
        }

    # ── 推送设置 ──

    def update_notification_settings(self, user_id: str, settings_dict: dict):
        """更新推送通知设置"""
        user = self._users.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        user["notification_settings"] = {
            **user.get("notification_settings", {}),
            **settings_dict,
        }
        user["updated_at"] = datetime.now().isoformat()
        self._save()

    def get_notification_settings(self, user_id: str) -> dict:
        """获取推送通知设置"""
        user = self._users.get(user_id)
        if not user:
            return {}
        return user.get("notification_settings", {})

    # ── 更新资料 ──

    def update_profile(self, user_id: str, display_name: str) -> dict:
        """更新用户资料"""
        user = self._users.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        user["display_name"] = display_name
        user["updated_at"] = datetime.now().isoformat()
        self._save()
        return self._sanitize(user)

    # ── 工具方法 ──

    def _sanitize(self, user: dict) -> dict:
        """脱敏用户信息（去除 password_hash）"""
        result = {k: v for k, v in user.items() if k != "password_hash"}
        # 添加套餐详情
        plan = user.get("plan", "free")
        plan_config = settings.SUBSCRIPTION_PLANS.get(plan, {})
        result["plan_name"] = plan_config.get("name", "")
        result["plan_features"] = plan_config.get("features", [])
        result["plan_price"] = plan_config.get("price", 0)
        return result
