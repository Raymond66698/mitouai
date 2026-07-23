"""Token 模型 — token_balances + token_transactions"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Index

from models.base import Base


def _gen_id() -> str:
    return uuid.uuid4().hex[:12]


def _now_iso() -> str:
    return datetime.now().isoformat()


class TokenBalance(Base):
    """用户 Token 余额"""
    __tablename__ = "token_balances"

    user_id = Column(String(12), primary_key=True)
    balance = Column(Integer, default=0, nullable=False)
    total_purchased = Column(Integer, default=0, nullable=False)
    total_consumed = Column(Integer, default=0, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TokenTransaction(Base):
    """Token 交易流水"""
    __tablename__ = "token_transactions"

    id = Column(String(12), primary_key=True, default=_gen_id)
    user_id = Column(String(12), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # purchase | consume
    package_id = Column(String(50), nullable=True)   # 仅 purchase
    package_name = Column(String(100), nullable=True)  # 仅 purchase
    action = Column(String(50), nullable=True)      # 仅 consume
    tokens = Column(Integer, nullable=False)          # 正=购买, 负=消费
    amount = Column(Float, default=0.0)               # 金额
    balance_after = Column(Integer, nullable=False)
    created_at = Column(String(26), default=_now_iso, index=True)

    __table_args__ = (
        Index("idx_tx_user_created", "user_id", "created_at"),
    )

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
