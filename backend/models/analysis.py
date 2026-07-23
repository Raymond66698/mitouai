"""分析任务模型 — 持久化分析任务和报告"""
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from models.base import Base


def _now_iso() -> str:
    return datetime.now().isoformat()


class AnalysisTask(Base):
    """分析任务"""
    __tablename__ = "analysis_tasks"

    task_id = Column(String(36), primary_key=True)
    user_id = Column(String(255), nullable=True, index=True)
    ticker = Column(String(20), nullable=False)
    trade_date = Column(String(10), nullable=True)
    status = Column(String(20), default="pending")  # pending|running|completed|failed
    model = Column(String(50), default="default")
    strategy_id = Column(String(50), nullable=True)
    debate_rounds = Column(Integer, default=1)
    risk_rounds = Column(Integer, default=1)

    # 结果
    result_summary = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    created_at = Column(String(26), default=_now_iso)
    completed_at = Column(String(26), nullable=True)

    # 关联
    report = relationship("AnalysisReport", back_populates="task", uselist=False, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class AnalysisReport(Base):
    """分析报告"""
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("analysis_tasks.task_id", ondelete="CASCADE"), unique=True, nullable=False)
    ticker = Column(String(20), nullable=False)
    trade_date = Column(String(10), nullable=True)
    latest_price = Column(Float, nullable=True)

    # 数据可用性
    data_points = Column(Integer, default=0)
    indicators_available = Column(Integer, default=0)
    fundamentals_available = Column(Integer, default=0)
    news_available = Column(Integer, default=0)
    global_news_available = Column(Integer, default=0)

    # 分析结论
    decision = Column(String(20), nullable=True)  # BUY|SELL|HOLD
    confidence = Column(String(50), nullable=True)  # 高/中等/低
    summary = Column(Text, nullable=True)

    # 原始分析章节
    raw_sections = Column(JSON, default=dict)  # {indicators, fundamentals, news, global_news}

    created_at = Column(String(26), default=_now_iso)

    # 关联
    task = relationship("AnalysisTask", back_populates="report")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
