"""
知识笔记服务 — 觅投AI 金融知识教育平台

提供用户个人知识笔记的 CRUD 功能，
支持分类标签、全文搜索、收藏标记。

存储：SQLite (data/notes.db)
"""
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mitouai.notes")

DB_PATH = Path("data/notes.db")


def _get_db() -> sqlite3.Connection:
    """获取 SQLite 连接（自动建表）"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL DEFAULT 'default',
            title       TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            category    TEXT NOT NULL DEFAULT 'general',
            tags        TEXT NOT NULL DEFAULT '[]',
            is_pinned   INTEGER NOT NULL DEFAULT 0,
            is_public   INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category)
    """)
    conn.commit()
    return conn


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


def _row_to_dict(row: sqlite3.Row) -> dict:
    """行转字典"""
    d = dict(row)
    d["tags"] = json.loads(d.get("tags", "[]"))
    d["is_pinned"] = bool(d["is_pinned"])
    d["is_public"] = bool(d["is_public"])
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
        conn = _get_db()
        try:
            sql = "SELECT * FROM notes WHERE user_id = ?"
            params: list = [user_id]

            if category and category != "all":
                sql += " AND category = ?"
                params.append(category)

            if pinned_only:
                sql += " AND is_pinned = 1"

            if keyword:
                sql += " AND (title LIKE ? OR content LIKE ?)"
                kw = f"%{keyword}%"
                params.extend([kw, kw])

            sql += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(sql, params).fetchall()
            notes = [_row_to_dict(r) for r in rows]

            # tag 过滤（在 Python 层做，因为 tags 是 JSON）
            if tag:
                notes = [n for n in notes if tag in n["tags"]]

            # 总数
            count_sql = "SELECT COUNT(*) as cnt FROM notes WHERE user_id = ?"
            count_params: list = [user_id]
            if category and category != "all":
                count_sql += " AND category = ?"
                count_params.append(category)
            if pinned_only:
                count_sql += " AND is_pinned = 1"
            if keyword:
                count_sql += " AND (title LIKE ? OR content LIKE ?)"
                count_params.extend([f"%{keyword}%", f"%{keyword}%"])
            total = conn.execute(count_sql, count_params).fetchone()["cnt"]

            return {
                "total": total,
                "notes": notes,
                "categories": CATEGORY_LIST,
            }
        finally:
            conn.close()

    def get_note(self, note_id: int, user_id: str = "default") -> Optional[dict]:
        """获取单条笔记"""
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id),
            ).fetchone()
            return _row_to_dict(row) if row else None
        finally:
            conn.close()

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
        tags_json = json.dumps(tags or [], ensure_ascii=False)

        conn = _get_db()
        try:
            cur = conn.execute(
                """INSERT INTO notes
                   (user_id, title, content, category, tags, is_pinned, is_public, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, title, content, category, tags_json,
                 1 if is_pinned else 0, 1 if is_public else 0, now, now),
            )
            conn.commit()
            note_id = cur.lastrowid
            logger.info(f"笔记创建: id={note_id}, title={title}")
            return self.get_note(note_id, user_id)
        finally:
            conn.close()

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
        existing = self.get_note(note_id, user_id)
        if not existing:
            return None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags, ensure_ascii=False))
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            params.append(1 if is_pinned else 0)
        if is_public is not None:
            updates.append("is_public = ?")
            params.append(1 if is_public else 0)

        if not updates:
            return existing

        updates.append("updated_at = ?")
        params.append(now)
        params.extend([note_id, user_id])

        conn = _get_db()
        try:
            conn.execute(
                f"UPDATE notes SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
                params,
            )
            conn.commit()
            return self.get_note(note_id, user_id)
        finally:
            conn.close()

    def delete_note(self, note_id: int, user_id: str = "default") -> bool:
        """删除笔记"""
        conn = _get_db()
        try:
            cur = conn.execute(
                "DELETE FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def get_stats(self, user_id: str = "default") -> dict:
        """获取笔记统计"""
        conn = _get_db()
        try:
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM notes WHERE user_id = ?", (user_id,)
            ).fetchone()["cnt"]

            pinned = conn.execute(
                "SELECT COUNT(*) as cnt FROM notes WHERE user_id = ? AND is_pinned = 1",
                (user_id,),
            ).fetchone()["cnt"]

            # 按分类统计
            cat_rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM notes WHERE user_id = ? GROUP BY category",
                (user_id,),
            ).fetchall()
            by_category = {r["category"]: r["cnt"] for r in cat_rows}

            # 所有标签
            all_rows = conn.execute(
                "SELECT tags FROM notes WHERE user_id = ?", (user_id,)
            ).fetchall()
            tag_count: dict = {}
            for r in all_rows:
                for t in json.loads(r["tags"] or "[]"):
                    tag_count[t] = tag_count.get(t, 0) + 1
            top_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:10]

            return {
                "total": total,
                "pinned": pinned,
                "by_category": {k: v for k, v in by_category.items()},
                "top_tags": [{"name": t, "count": c} for t, c in top_tags],
                "categories": CATEGORY_LIST,
            }
        finally:
            conn.close()


# 单例
notes_service = NotesService()
