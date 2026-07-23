"""自选股 + 模拟组合模型"""
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from models.base import Base


def _now_iso() -> str:
    return datetime.now().isoformat()


class Watchlist(Base):
    """自选股列表"""
    __tablename__ = "watchlists"

    id = Column(String(8), primary_key=True)
    user_id = Column(String(12), nullable=False, index=True)
    name = Column(String(100), default="默认")
    stocks = Column(JSON, default=list)  # [{ticker, name, added_at}, ...]
    created_at = Column(String(26), default=_now_iso)
    updated_at = Column(String(26), default=_now_iso)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Portfolio(Base):
    """模拟组合"""
    __tablename__ = "portfolios"

    id = Column(String(8), primary_key=True)
    user_id = Column(String(12), nullable=False, index=True)
    name = Column(String(100), default="我的组合")
    holdings = Column(JSON, default=list)  # [{ticker, name, quantity, cost, avg_price}, ...]
    cash = Column(Float, default=100000.0)
    created_at = Column(String(26), default=_now_iso)
    updated_at = Column(String(26), default=_now_iso)

    # 关联
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Trade(Base):
    """交易记录"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(8), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    name = Column(String(100), default="")
    action = Column(String(10), nullable=False)  # buy | sell
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    trade_date = Column(String(10), default=lambda: datetime.now().strftime("%Y-%m-%d"))
    created_at = Column(String(26), default=_now_iso)

    # 关联
    portfolio = relationship("Portfolio", back_populates="trades")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
