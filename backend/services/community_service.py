"""
策略社区服务 — 策略分享、排行、评论
使用 SQLAlchemy ORM
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from database import get_db_context
from models.community import SharedStrategy, StrategyLike, StrategyComment

logger = logging.getLogger("mitouai.community")


class CommunityService:

    def share_strategy(self, user_id: str, name: str, description: str = "",
                       conditions: dict = None, backtest: dict = None,
                       strategy_id: str = None) -> dict:
        """分享一个策略"""
        sid = strategy_id or str(uuid.uuid4())[:12]
        now = datetime.now().isoformat()

        with get_db_context() as db:
            # upsert: delete old if exists, then insert
            existing = db.query(SharedStrategy).filter(SharedStrategy.id == sid).first()
            if existing:
                existing.name = name
                existing.description = description
                existing.conditions = conditions or {}
                existing.backtest_result = backtest or {}
                existing.updated_at = now
            else:
                strategy = SharedStrategy(
                    id=sid,
                    user_id=user_id,
                    name=name,
                    description=description,
                    conditions=conditions or {},
                    backtest_result=backtest or {},
                    created_at=now,
                    updated_at=now,
                )
                db.add(strategy)
            db.commit()

        return {"id": sid, "name": name, "message": "分享成功"}

    def get_community_strategies(self, sort: str = "likes",
                                  limit: int = 20, offset: int = 0) -> dict:
        """获取社区策略列表"""
        with get_db_context() as db:
            total = db.query(SharedStrategy).count()

            order_map = {
                "likes": SharedStrategy.likes.desc(),
                "newest": SharedStrategy.created_at.desc(),
                "usage": SharedStrategy.usage_count.desc(),
            }
            order = order_map.get(sort, SharedStrategy.likes.desc())

            rows = db.query(SharedStrategy).order_by(order).offset(offset).limit(limit).all()

            items = []
            for r in rows:
                items.append({
                    "id": r.id,
                    "user_id": r.user_id,
                    "name": r.name,
                    "description": r.description,
                    "category": r.category,
                    "conditions": r.conditions if isinstance(r.conditions, dict) else {},
                    "backtest_result": r.backtest_result if isinstance(r.backtest_result, dict) else {},
                    "likes": r.likes,
                    "usage_count": r.usage_count,
                    "is_featured": bool(r.is_featured),
                    "created_at": r.created_at,
                })

            return {"total": total, "items": items, "limit": limit, "offset": offset}

    def like_strategy(self, strategy_id: str, user_id: str) -> dict:
        """点赞/取消点赞"""
        with get_db_context() as db:
            existing = db.query(StrategyLike).filter(
                StrategyLike.strategy_id == strategy_id,
                StrategyLike.user_id == user_id,
            ).first()

            if existing:
                db.delete(existing)
                strategy = db.query(SharedStrategy).filter(SharedStrategy.id == strategy_id).first()
                if strategy and strategy.likes > 0:
                    strategy.likes -= 1
                db.commit()
                return {"liked": False, "message": "已取消点赞"}
            else:
                like = StrategyLike(strategy_id=strategy_id, user_id=user_id)
                db.add(like)
                strategy = db.query(SharedStrategy).filter(SharedStrategy.id == strategy_id).first()
                if strategy:
                    strategy.likes += 1
                db.commit()
                return {"liked": True, "message": "点赞成功"}

    def get_strategy_detail(self, strategy_id: str) -> Optional[dict]:
        """获取策略详情+评论"""
        with get_db_context() as db:
            row = db.query(SharedStrategy).filter(SharedStrategy.id == strategy_id).first()
            if not row:
                return None

            comments = db.query(StrategyComment).filter(
                StrategyComment.strategy_id == strategy_id
            ).order_by(StrategyComment.created_at.desc()).limit(50).all()

            # 增加使用次数
            row.usage_count += 1
            db.commit()

            result = {
                "id": row.id,
                "user_id": row.user_id,
                "name": row.name,
                "description": row.description,
                "category": row.category,
                "conditions": row.conditions if isinstance(row.conditions, dict) else {},
                "backtest_result": row.backtest_result if isinstance(row.backtest_result, dict) else {},
                "likes": row.likes,
                "usage_count": row.usage_count,
                "is_featured": bool(row.is_featured),
                "created_at": row.created_at,
                "comments": [c.to_dict() for c in comments],
            }
            return result

    def add_comment(self, strategy_id: str, user_id: str,
                    user_name: str, content: str) -> dict:
        """添加评论"""
        cid = str(uuid.uuid4())[:12]
        with get_db_context() as db:
            comment = StrategyComment(
                id=cid,
                strategy_id=strategy_id,
                user_id=user_id,
                user_name=user_name,
                content=content,
            )
            db.add(comment)
            db.commit()
        return {"id": cid, "message": "评论成功"}


community_service = CommunityService()
