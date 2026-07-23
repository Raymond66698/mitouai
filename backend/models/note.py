"""知识笔记模型"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Index, JSON,
)

from models.base import Base


class Note(Base):
    """用户知识笔记"""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(12), nullable=False, default="default", index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, default="")
    category = Column(String(50), default="general", index=True)
    tags = Column(JSON, default=list)
    is_pinned = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(String(19), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = Column(String(19), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    __table_args__ = (
        Index("idx_notes_user", "user_id"),
        Index("idx_notes_category", "category"),
    )

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
