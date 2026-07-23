"""
策略社区服务 — 策略分享、排行、评论
使用 SQLite 存储社区数据
"""
import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mitouai.community")

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "community.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_community_db():
    """初始化社区数据库"""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS shared_strategies (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'custom',
            conditions TEXT DEFAULT '{}',
            backtest_result TEXT DEFAULT '{}',
            likes INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            is_featured INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS strategy_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(strategy_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS strategy_comments (
            id TEXT PRIMARY KEY,
            strategy_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT DEFAULT '用户',
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_ss_user ON shared_strategies(user_id);
        CREATE INDEX IF NOT EXISTS idx_ss_likes ON shared_strategies(likes DESC);
        CREATE INDEX IF NOT EXISTS idx_sc_strategy ON strategy_comments(strategy_id);
    """)
    conn.commit()
    conn.close()


# 初始化
init_community_db()


class CommunityService:

    def share_strategy(self, user_id: str, name: str, description: str = "",
                       conditions: dict = None, backtest: dict = None,
                       strategy_id: str = None) -> dict:
        """分享一个策略"""
        conn = _get_db()
        sid = strategy_id or str(uuid.uuid4())[:12]
        conditions_json = json.dumps(conditions or {}, ensure_ascii=False)
        bt_json = json.dumps(backtest or {}, ensure_ascii=False)
        now = datetime.now().isoformat()

        conn.execute("""
            INSERT OR REPLACE INTO shared_strategies (id, user_id, name, description, conditions, backtest_result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sid, user_id, name, description, conditions_json, bt_json, now, now))
        conn.commit()
        conn.close()
        return {"id": sid, "name": name, "message": "分享成功"}

    def get_community_strategies(self, sort: str = "likes",
                                  limit: int = 20, offset: int = 0) -> dict:
        """获取社区策略列表"""
        conn = _get_db()
        order_map = {
            "likes": "likes DESC",
            "newest": "created_at DESC",
            "usage": "usage_count DESC",
        }
        order = order_map.get(sort, "likes DESC")

        total = conn.execute("SELECT COUNT(*) FROM shared_strategies").fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM shared_strategies ORDER BY {order} LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "user_id": r["user_id"],
                "name": r["name"],
                "description": r["description"],
                "category": r["category"],
                "conditions": json.loads(r["conditions"]),
                "backtest_result": json.loads(r["backtest_result"]),
                "likes": r["likes"],
                "usage_count": r["usage_count"],
                "is_featured": bool(r["is_featured"]),
                "created_at": r["created_at"],
            })
        conn.close()
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def like_strategy(self, strategy_id: str, user_id: str) -> dict:
        """点赞/取消点赞"""
        conn = _get_db()
        existing = conn.execute(
            "SELECT id FROM strategy_likes WHERE strategy_id=? AND user_id=?",
            (strategy_id, user_id)
        ).fetchone()

        if existing:
            conn.execute("DELETE FROM strategy_likes WHERE id=?", (existing["id"],))
            conn.execute("UPDATE shared_strategies SET likes=MAX(0, likes-1) WHERE id=?", (strategy_id,))
            conn.commit()
            conn.close()
            return {"liked": False, "message": "已取消点赞"}
        else:
            conn.execute(
                "INSERT INTO strategy_likes (strategy_id, user_id) VALUES (?, ?)",
                (strategy_id, user_id)
            )
            conn.execute("UPDATE shared_strategies SET likes=likes+1 WHERE id=?", (strategy_id,))
            conn.commit()
            conn.close()
            return {"liked": True, "message": "点赞成功"}

    def get_strategy_detail(self, strategy_id: str) -> Optional[dict]:
        """获取策略详情+评论"""
        conn = _get_db()
        row = conn.execute(
            "SELECT * FROM shared_strategies WHERE id=?", (strategy_id,)
        ).fetchone()
        if not row:
            conn.close()
            return None

        comments = conn.execute(
            "SELECT * FROM strategy_comments WHERE strategy_id=? ORDER BY created_at DESC LIMIT 50",
            (strategy_id,)
        ).fetchall()

        # 增加使用次数
        conn.execute("UPDATE shared_strategies SET usage_count=usage_count+1 WHERE id=?", (strategy_id,))
        conn.commit()

        result = {
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "description": row["description"],
            "category": row["category"],
            "conditions": json.loads(row["conditions"]),
            "backtest_result": json.loads(row["backtest_result"]),
            "likes": row["likes"],
            "usage_count": row["usage_count"] + 1,
            "is_featured": bool(row["is_featured"]),
            "created_at": row["created_at"],
            "comments": [dict(c) for c in comments],
        }
        conn.close()
        return result

    def add_comment(self, strategy_id: str, user_id: str,
                    user_name: str, content: str) -> dict:
        """添加评论"""
        conn = _get_db()
        cid = str(uuid.uuid4())[:12]
        conn.execute(
            "INSERT INTO strategy_comments (id, strategy_id, user_id, user_name, content) VALUES (?,?,?,?,?)",
            (cid, strategy_id, user_id, user_name, content)
        )
        conn.commit()
        conn.close()
        return {"id": cid, "message": "评论成功"}


community_service = CommunityService()
