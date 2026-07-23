"""应用内通知模型"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean,
)

from models.base import Base


def _now_iso() -> str:
    return datetime.now().isoformat()


class Notification(Base):
    """用户应用内通知"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # analysis_complete, breaking_news, system
    title = Column(String(200), nullable=False)
    content = Column(String(2000), default="")
    task_id = Column(String(36), nullable=True)
    ticker = Column(String(20), nullable=True)
    decision = Column(String(20), nullable=True)  # buy|sell|hold
    is_read = Column(Boolean, default=False)
    created_at = Column(String(26), default=_now_iso)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
