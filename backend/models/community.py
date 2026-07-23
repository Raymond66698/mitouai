"""策略社区模型"""
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey, Index, JSON,
)
from sqlalchemy.orm import relationship

from models.base import Base


def _now_iso() -> str:
    return datetime.now().isoformat()


class SharedStrategy(Base):
    """共享策略"""
    __tablename__ = "shared_strategies"

    id = Column(String(12), primary_key=True)
    user_id = Column(String(12), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), default="custom")
    conditions = Column(JSON, default=dict)
    backtest_result = Column(JSON, default=dict)
    likes = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    created_at = Column(String(26), default=_now_iso)
    updated_at = Column(String(26), default=_now_iso)

    # 关联
    comments = relationship("StrategyComment", back_populates="strategy", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ss_user", "user_id"),
        Index("idx_ss_likes", "likes"),
    )

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class StrategyLike(Base):
    """策略点赞"""
    __tablename__ = "strategy_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(12), nullable=False, index=True)
    user_id = Column(String(12), nullable=False)
    created_at = Column(String(26), default=_now_iso)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class StrategyComment(Base):
    """策略评论"""
    __tablename__ = "strategy_comments"

    id = Column(String(12), primary_key=True)
    strategy_id = Column(String(12), ForeignKey("shared_strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(12), nullable=False)
    user_name = Column(String(100), default="用户")
    content = Column(Text, nullable=False)
    created_at = Column(String(26), default=_now_iso)

    # 关联
    strategy = relationship("SharedStrategy", back_populates="comments")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
