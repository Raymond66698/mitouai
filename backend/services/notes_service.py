"""
知识笔记服务 — 觅投AI 金融知识教育平台
使用 SQLAlchemy ORM (SQLite/PostgreSQL 双后端)
"""
import json
import logging
from datetime import datetime
from typing import Optional

from database import get_db_context
from models.note import Note

logger = logging.getLogger("mitouai.notes")


# ── 预置分类 ──
CATEGORIES = {
    "general": "通用笔记",
    "stocks": "个股研究",
    "macro": "宏观经济",
    "strategy": "策略方法",
    "factors": "量化因子",
    "risk": "风险管控",
    "lesson": "学习心得",
}

CATEGORY_LIST = [{"key": k, "label": v} for k, v in CATEGORIES.items()]


def _note_to_dict(note: Note) -> dict:
    """Note ORM 对象转为字典"""
    d = {
        "id": note.id,
        "user_id": note.user_id,
        "title": note.title,
        "content": note.content,
        "category": note.category,
        "tags": note.tags if isinstance(note.tags, list) else [],
        "is_pinned": bool(note.is_pinned),
        "is_public": bool(note.is_public),
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }
    return d


class NotesService:
    """知识笔记 CRUD 服务"""

    def list_notes(
        self,
        user_id: str = "default",
        category: Optional[str] = None,
        tag: Optional[str] = None,
        keyword: Optional[str] = None,
        pinned_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """查询笔记列表（支持筛选+搜索）"""
        with get_db_context() as db:
            query = db.query(Note).filter(Note.user_id == user_id)

            if category and category != "all":
                query = query.filter(Note.category == category)

            if pinned_only:
                query = query.filter(Note.is_pinned == True)

            if keyword:
                query = query.filter(
                    (Note.title.ilike(f"%{keyword}%")) |
                    (Note.content.ilike(f"%{keyword}%"))
                )

            # 总数
            total = query.count()

            # 排序 + 分页
            query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
            notes = query.offset(offset).limit(limit).all()

            result = [_note_to_dict(n) for n in notes]

            # tag 过滤（Python 层，兼容 SQLite 和 PostgreSQL）
            if tag:
                result = [n for n in result if tag in n.get("tags", [])]

            return {
                "total": total,
                "notes": result,
                "categories": CATEGORY_LIST,
            }

    def get_note(self, note_id: int, user_id: str = "default") -> Optional[dict]:
        """获取单条笔记"""
        with get_db_context() as db:
            note = db.query(Note).filter(
                Note.id == note_id,
                Note.user_id == user_id,
            ).first()
            return _note_to_dict(note) if note else None

    def create_note(
        self,
        title: str,
        content: str = "",
        category: str = "general",
        tags: list = None,
        is_pinned: bool = False,
        is_public: bool = False,
        user_id: str = "default",
    ) -> dict:
        """创建笔记"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_context() as db:
            note = Note(
                user_id=user_id,
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                is_pinned=is_pinned,
                is_public=is_public,
                created_at=now,
                updated_at=now,
            )
            db.add(note)
            db.commit()
            db.refresh(note)

            logger.info(f"笔记创建: id={note.id}, title={title}")
            return _note_to_dict(note)

    def update_note(
        self,
        note_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list] = None,
        is_pinned: Optional[bool] = None,
        is_public: Optional[bool] = None,
        user_id: str = "default",
    ) -> Optional[dict]:
        """更新笔记（只更新传入的字段）"""
        with get_db_context() as db:
            note = db.query(Note).filter(
                Note.id == note_id,
                Note.user_id == user_id,
            ).first()

            if not note:
                return None

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changed = False

            if title is not None:
                note.title = title
                changed = True
            if content is not None:
                note.content = content
                changed = True
            if category is not None:
                note.category = category
                changed = True
            if tags is not None:
                note.tags = tags
                changed = True
            if is_pinned is not None:
                note.is_pinned = is_pinned
                changed = True
            if is_public is not None:
                note.is_public = is_public
                changed = True

            if not changed:
                return _note_to_dict(note)

            note.updated_at = now
            db.commit()
            db.refresh(note)
            return _note_to_dict(note)

    def delete_note(self, note_id: int, user_id: str = "default") -> bool:
        """删除笔记"""
        with get_db_context() as db:
            result = db.query(Note).filter(
                Note.id == note_id,
                Note.user_id == user_id,
            ).delete()
            db.commit()
            return result > 0

    def get_stats(self, user_id: str = "default") -> dict:
        """获取笔记统计"""
        with get_db_context() as db:
            total = db.query(Note).filter(Note.user_id == user_id).count()
            pinned = db.query(Note).filter(
                Note.user_id == user_id,
                Note.is_pinned == True,
            ).count()

            # 按分类统计
            from sqlalchemy import func
            cat_rows = db.query(
                Note.category, func.count(Note.id)
            ).filter(
                Note.user_id == user_id
            ).group_by(Note.category).all()
            by_category = {r[0]: r[1] for r in cat_rows}

            # 所有标签统计
            all_notes = db.query(Note.tags).filter(Note.user_id == user_id).all()
            tag_count: dict = {}
            for (tags_val,) in all_notes:
                tag_list = tags_val if isinstance(tags_val, list) else (json.loads(tags_val) if isinstance(tags_val, str) else [])
                for t in tag_list:
                    tag_count[t] = tag_count.get(t, 0) + 1
            top_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:10]

            return {
                "total": total,
                "pinned": pinned,
                "by_category": by_category,
                "top_tags": [{"name": t, "count": c} for t, c in top_tags],
                "categories": CATEGORY_LIST,
            }


# 单例
notes_service = NotesService()
