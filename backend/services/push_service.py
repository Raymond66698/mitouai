"""
推送通知服务 — PushPlus 微信推送 + 应用内通知记录
"""
import json
import logging
from datetime import datetime
from typing import Optional
import httpx
from config import settings

logger = logging.getLogger("mitouai.push")


class PushService:
    """推送通知服务"""

    def __init__(self):
        self._notifications: dict[str, list[dict]] = {}  # user_id -> [notifications]

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

        # 记录到应用内通知
        self._record_notification(user_id, {
            "type": "analysis_complete",
            "title": title,
            "content": content.replace("<b>", "").replace("</b>", "").replace("<br>", "\n"),
            "task_id": task_id,
            "ticker": ticker,
            "decision": decision,
            "read": False,
            "created_at": datetime.now().isoformat(),
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

    def _record_notification(self, user_id: str, notification: dict):
        """记录应用内通知"""
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].insert(0, notification)
        # 只保留最近 50 条
        if len(self._notifications[user_id]) > 50:
            self._notifications[user_id] = self._notifications[user_id][:50]

    def get_notifications(self, user_id: str, limit: int = 20, unread_only: bool = False) -> list[dict]:
        """获取用户通知列表"""
        notifications = self._notifications.get(user_id, [])
        if unread_only:
            notifications = [n for n in notifications if not n.get("read")]
        return notifications[:limit]

    def mark_read(self, user_id: str, notification_index: int):
        """标记通知已读"""
        if user_id in self._notifications and notification_index < len(self._notifications[user_id]):
            self._notifications[user_id][notification_index]["read"] = True

    def mark_all_read(self, user_id: str):
        """全部标记已读"""
        for n in self._notifications.get(user_id, []):
            n["read"] = True


# 全局单例
push_service = PushService()
