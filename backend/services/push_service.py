"""
推送通知服务 — PushPlus 微信推送 + 应用内通知记录
通知持久化到 SQLAlchemy ORM
"""
import json
import logging
from datetime import datetime
from typing import Optional
import httpx

from database import get_db_context
from models.notification import Notification
from config import settings

logger = logging.getLogger("mitouai.push")


class PushService:
    """推送通知服务"""

    async def send_analysis_complete(
        self,
        user_id: str,
        user_email: str,
        pushplus_token: str,
        ticker: str,
        ticker_name: str,
        decision: str,
        task_id: str,
    ):
        """分析完成后推送通知"""
        decision_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(decision, "⚪")
        title = f"{decision_emoji} {ticker_name} 分析完成"
        content = f"""
📊 <b>{ticker_name}</b> ({ticker}) 多智能体分析完成

<b>决策</b>：{decision_emoji} {decision}
<b>时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M')}

👉 <a href="https://{settings.DOMAIN}/analysis/{task_id}">查看完整报告</a>
        """.strip()

        # 记录到应用内通知（持久化到数据库）
        self._record_notification(user_id, {
            "type": "analysis_complete",
            "title": title,
            "content": content.replace("<b>", "").replace("</b>", "").replace("<br>", "\n"),
            "task_id": task_id,
            "ticker": ticker,
            "decision": decision,
        })

        # PushPlus 微信推送
        if pushplus_token:
            await self._pushplus_send(pushplus_token, title, content)

    async def send_daily_report(
        self,
        user_id: str,
        pushplus_token: str,
        report_text: str,
    ):
        """每日分析汇总推送"""
        await self._pushplus_send(
            pushplus_token,
            "📋 觅投AI 每日投资报告",
            report_text,
        )

    async def send_breaking_news(
        self,
        user_id: str,
        pushplus_token: str,
        news_title: str,
        news_summary: str,
    ):
        """突发新闻推送"""
        title = f"📰 {news_title}"
        # 记录到数据库
        self._record_notification(user_id, {
            "type": "breaking_news",
            "title": title,
            "content": news_summary,
        })
        await self._pushplus_send(pushplus_token, title, news_summary)

    async def _pushplus_send(self, token: str, title: str, content: str) -> bool:
        """通过 PushPlus 发送微信推送"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    settings.PUSHPLUS_URL,
                    json={
                        "token": token,
                        "title": title,
                        "content": content,
                        "template": "html",
                    },
                )
                result = resp.json()
                if result.get("code") == 200:
                    logger.info(f"PushPlus 推送成功: {title}")
                    return True
                else:
                    logger.warning(f"PushPlus 推送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"PushPlus 推送异常: {e}")
            return False

    def _record_notification(self, user_id: str, data: dict) -> Optional[int]:
        """记录应用内通知到数据库，返回通知 ID"""
        if not user_id:
            return None
        try:
            with get_db_context() as db:
                notification = Notification(
                    user_id=user_id,
                    type=data.get("type", "system"),
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    task_id=data.get("task_id"),
                    ticker=data.get("ticker"),
                    decision=data.get("decision"),
                    is_read=False,
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                # 保留最近 50 条，删除多余的通知
                self._trim_notifications(db, user_id)
                return notification.id
        except Exception as e:
            logger.error(f"记录通知失败: {e}")
            return None

    def _trim_notifications(self, db, user_id: str, max_count: int = 50):
        """只保留最近 max_count 条通知"""
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        if total > max_count:
            # 找到需要删除的旧通知（保留最新 max_count 条）
            old_ids = (
                db.query(Notification.id)
                .filter(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .offset(max_count)
                .all()
            )
            if old_ids:
                old_id_list = [oid[0] for oid in old_ids]
                db.query(Notification).filter(Notification.id.in_(old_id_list)).delete(synchronize_session=False)
                db.commit()

    def get_notifications(self, user_id: str, limit: int = 20, unread_only: bool = False) -> list[dict]:
        """获取用户通知列表（从数据库）"""
        if not user_id:
            return []
        try:
            with get_db_context() as db:
                query = db.query(Notification).filter(Notification.user_id == user_id)
                if unread_only:
                    query = query.filter(Notification.is_read == False)
                notifications = (
                    query.order_by(Notification.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [self._notification_to_dict(n) for n in notifications]
        except Exception as e:
            logger.error(f"获取通知失败: {e}")
            return []

    def mark_read(self, user_id: str, notification_id: int) -> bool:
        """标记通知已读（通过通知 ID）"""
        try:
            with get_db_context() as db:
                n = (
                    db.query(Notification)
                    .filter(Notification.id == notification_id, Notification.user_id == user_id)
                    .first()
                )
                if n:
                    n.is_read = True
                    db.commit()
                    return True
            return False
        except Exception as e:
            logger.error(f"标记已读失败: {e}")
            return False

    def mark_all_read(self, user_id: str):
        """全部标记已读"""
        try:
            with get_db_context() as db:
                db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                ).update({"is_read": True})
                db.commit()
        except Exception as e:
            logger.error(f"全部已读失败: {e}")

    def get_unread_count(self, user_id: str) -> int:
        """获取未读通知数量"""
        if not user_id:
            return 0
        try:
            with get_db_context() as db:
                return (
                    db.query(Notification)
                    .filter(Notification.user_id == user_id, Notification.is_read == False)
                    .count()
                )
        except Exception:
            return 0

    @staticmethod
    def _notification_to_dict(n: Notification) -> dict:
        """ORM → dict，兼容 NotificationItem schema"""
        return {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "content": n.content,
            "task_id": n.task_id,
            "ticker": n.ticker,
            "decision": n.decision,
            "read": n.is_read,
            "created_at": n.created_at,
        }


# 全局单例
push_service = PushService()
