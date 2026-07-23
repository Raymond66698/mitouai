"""用户模型 — users + user_api_keys"""
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, ForeignKey, Text,
)
from sqlalchemy.orm import relationship

from models.base import Base


def _gen_id() -> str:
    return uuid.uuid4().hex[:12]


def _now_iso() -> str:
    return datetime.now().isoformat()


class User(Base):
    """用户主表"""
    __tablename__ = "users"

    id = Column(String(12), primary_key=True, default=_gen_id)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), default="")
    plan = Column(String(20), default="free", nullable=False)

    # 配额
    daily_analyses_used = Column(Integer, default=0)
    daily_analyses_date = Column(String(10), default=lambda: date.today().isoformat())
    daily_analyses_limit = Column(Integer, default=3)
    total_analyses = Column(Integer, default=0)

    # 通知设置
    notification_pushplus_token = Column(String(255), default="")
    notification_email_notify = Column(Boolean, default=False)
    notification_analysis_complete = Column(Boolean, default=True)
    notification_breaking_news = Column(Boolean, default=False)

    created_at = Column(String(26), default=_now_iso)
    updated_at = Column(String(26), default=_now_iso, onupdate=_now_iso)

    # 关联
    api_keys = relationship("UserApiKey", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """转为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def sanitize(self) -> dict:
        """脱敏，去除 password_hash"""
        d = self.to_dict()
        d.pop("password_hash", None)
        return d


class UserApiKey(Base):
    """用户自带 API Key (BYOK)"""
    __tablename__ = "user_api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(12), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # deepseek, openai, etc.
    api_key = Column(String(512), nullable=False)
    created_at = Column(String(26), default=_now_iso)
    updated_at = Column(String(26), default=_now_iso, onupdate=_now_iso)

    # 关联
    user = relationship("User", back_populates="api_keys")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
