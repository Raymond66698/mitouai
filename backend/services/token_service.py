"""Token 消费管理服务 — 使用 SQLAlchemy ORM"""
import uuid
from datetime import datetime
from typing import Optional

from database import get_db_context
from models.token import TokenBalance, TokenTransaction
from models.user import User


class TokenService:
    """Token 消费管理（单例模式）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── 套餐定义 ──
    TOKEN_PACKAGES = [
        {
            "id": "starter",
            "name": "新手体验包",
            "tokens": 5000,
            "price": 0,
            "original_price": 9.9,
            "description": "免费获得 5,000 tokens，体验全部功能",
            "tag": "限时免费",
            "color": "gold",
        },
        {
            "id": "basic",
            "name": "轻量包",
            "tokens": 10000,
            "price": 9.9,
            "description": "10,000 tokens，适合轻度使用",
            "tag": "热门",
            "color": "gold",
        },
        {
            "id": "standard",
            "name": "标准包",
            "tokens": 50000,
            "price": 39,
            "original_price": 49,
            "description": "50,000 tokens，深度分析不焦虑",
            "tag": "超值",
            "color": "red",
        },
        {
            "id": "pro",
            "name": "专业包",
            "tokens": 200000,
            "price": 99,
            "original_price": 149,
            "description": "200,000 tokens，量化研究利器",
            "tag": "推荐",
            "color": "red",
        },
        {
            "id": "max",
            "name": "旗舰包",
            "tokens": 500000,
            "price": 199,
            "original_price": 299,
            "description": "500,000 tokens，机构级数据支撑",
            "tag": "",
            "color": "gold",
        },
    ]

    # ── Token 消耗单价 ──
    TOKEN_COSTS = {
        "analysis_basic": 300,
        "analysis_deep": 800,
        "analysis_report": 2000,
        "screener_scan": 500,
        "backtest": 300,
        "daily_brief": 100,
        "research_summary": 600,
    }

    def _ensure_user_balance(self, db, user_id: str) -> TokenBalance:
        """确保用户有余额记录，没有则创建"""
        b = db.query(TokenBalance).filter(TokenBalance.user_id == user_id).first()
        if not b:
            b = TokenBalance(user_id=user_id, balance=0)
            db.add(b)
            db.flush()
        return b

    def get_packages(self) -> list:
        """获取所有 token 套餐"""
        return self.TOKEN_PACKAGES

    def get_balance(self, user_id: str) -> dict:
        """获取用户 token 余额"""
        with get_db_context() as db:
            b = self._ensure_user_balance(db, user_id)
            return {
                "user_id": user_id,
                "balance": b.balance,
                "total_purchased": b.total_purchased,
                "total_consumed": b.total_consumed,
            }

    def purchase(self, user_id: str, package_id: str) -> dict:
        """购买 token 套餐"""
        pkg = next((p for p in self.TOKEN_PACKAGES if p["id"] == package_id), None)
        if not pkg:
            raise ValueError(f"套餐不存在: {package_id}")

        with get_db_context() as db:
            b = self._ensure_user_balance(db, user_id)

            # 检查新手包是否已领取过
            if package_id == "starter":
                existing = db.query(TokenTransaction).filter(
                    TokenTransaction.user_id == user_id,
                    TokenTransaction.package_id == "starter",
                ).first()
                if existing:
                    raise ValueError("新手体验包已领取过，每人限领一次")

            # 更新余额
            b.balance += pkg["tokens"]
            b.total_purchased += pkg["tokens"]

            # 记录交易
            tx = TokenTransaction(
                id=uuid.uuid4().hex[:12],
                user_id=user_id,
                type="purchase",
                package_id=package_id,
                package_name=pkg["name"],
                tokens=pkg["tokens"],
                amount=pkg["price"],
                balance_after=b.balance,
                created_at=datetime.now().isoformat(),
            )
            db.add(tx)
            db.commit()

            return self.get_balance(user_id)

    def consume_tokens(self, user_id: str, action: str, tokens_override: int = 0) -> dict:
        """消耗 tokens"""
        cost = tokens_override if tokens_override > 0 else self.TOKEN_COSTS.get(action, 300)

        with get_db_context() as db:
            b = self._ensure_user_balance(db, user_id)

            if b.balance < cost:
                raise ValueError(
                    f"Token 余额不足，需要 {cost} tokens，当前余额 {b.balance}"
                )

            b.balance -= cost
            b.total_consumed += cost

            tx = TokenTransaction(
                id=uuid.uuid4().hex[:12],
                user_id=user_id,
                type="consume",
                action=action,
                tokens=-cost,
                amount=0,
                balance_after=b.balance,
                created_at=datetime.now().isoformat(),
            )
            db.add(tx)
            db.commit()

            return {"consumed": cost, "balance": b.balance}

    def get_usage_history(self, user_id: str, limit: int = 50) -> list:
        """获取 token 使用记录"""
        with get_db_context() as db:
            txs = db.query(TokenTransaction).filter(
                TokenTransaction.user_id == user_id
            ).order_by(TokenTransaction.created_at.desc()).limit(limit).all()

            return [tx.to_dict() for tx in txs]

    def get_usage_stats(self, user_id: str) -> dict:
        """获取使用统计（按操作类型分组）"""
        with get_db_context() as db:
            consumed = db.query(TokenTransaction).filter(
                TokenTransaction.user_id == user_id,
                TokenTransaction.type == "consume",
            ).all()

            by_action: dict = {}
            daily: dict = {}

            for tx in consumed:
                action = tx.action or "other"
                tokens = abs(tx.tokens)
                by_action[action] = by_action.get(action, 0) + tokens

                day = tx.created_at[:10] if tx.created_at else ""
                daily[day] = daily.get(day, 0) + tokens

            daily_list = sorted(
                [{"date": d, "tokens": t} for d, t in daily.items()],
                key=lambda x: x["date"],
            )[-30:]

            total = sum(abs(tx.tokens) for tx in consumed)

            return {
                "by_action": by_action,
                "daily": daily_list,
                "total_consumed": total,
            }


# ── 全局单例 ──
token_service = TokenService()
