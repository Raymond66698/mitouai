"""Token 消费管理服务 — token 余额、消耗记录、套餐购买"""
import json
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEDGER_FILE = DATA_DIR / "token_ledger.json"
TOKEN_BALANCE_FILE = DATA_DIR / "token_balances.json"


class TokenService:
    """Token 消费管理（单例模式）"""
    _instance = None
    _ledger: dict = {}       # user_id -> [transactions]
    _balances: dict = {}     # user_id -> {"balance": int, "total_purchased": int, "total_consumed": int}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if LEDGER_FILE.exists():
            self._ledger = json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
        else:
            self._ledger = {}

        if TOKEN_BALANCE_FILE.exists():
            self._balances = json.loads(TOKEN_BALANCE_FILE.read_text(encoding="utf-8"))
        else:
            self._balances = {}

    def _save(self):
        LEDGER_FILE.write_text(json.dumps(self._ledger, ensure_ascii=False, indent=2), encoding="utf-8")
        TOKEN_BALANCE_FILE.write_text(json.dumps(self._balances, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_user_balance(self, user_id: str):
        if user_id not in self._balances:
            self._balances[user_id] = {
                "balance": 0,
                "total_purchased": 0,
                "total_consumed": 0,
            }

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

    # ── Token 消耗单价（每次分析） ──
    TOKEN_COSTS = {
        "analysis_basic": 300,       # 基础分析
        "analysis_deep": 800,        # 深度分析（GPT-4o）
        "analysis_report": 2000,     # 深度研报
        "screener_scan": 500,        # 选股扫描
        "backtest": 300,             # 策略回测
        "daily_brief": 100,          # 每日播报
        "research_summary": 600,     # 研报聚合
    }

    def get_packages(self) -> list:
        """获取所有 token 套餐"""
        return self.TOKEN_PACKAGES

    def get_balance(self, user_id: str) -> dict:
        """获取用户 token 余额"""
        self._ensure_user_balance(user_id)
        b = self._balances[user_id]
        return {
            "user_id": user_id,
            "balance": b["balance"],
            "total_purchased": b["total_purchased"],
            "total_consumed": b["total_consumed"],
        }

    def purchase(self, user_id: str, package_id: str) -> dict:
        """购买 token 套餐"""
        pkg = next((p for p in self.TOKEN_PACKAGES if p["id"] == package_id), None)
        if not pkg:
            raise ValueError(f"套餐不存在: {package_id}")

        # 检查新手包是否已领取过
        if package_id == "starter":
            if user_id in self._ledger:
                for tx in self._ledger.get(user_id, []):
                    if tx.get("package_id") == "starter":
                        raise ValueError("新手体验包已领取过，每人限领一次")

        self._ensure_user_balance(user_id)
        self._balances[user_id]["balance"] += pkg["tokens"]
        self._balances[user_id]["total_purchased"] += pkg["tokens"]

        # 记录交易
        tx = {
            "id": uuid.uuid4().hex[:12],
            "user_id": user_id,
            "type": "purchase",
            "package_id": package_id,
            "package_name": pkg["name"],
            "tokens": pkg["tokens"],
            "amount": pkg["price"],
            "balance_after": self._balances[user_id]["balance"],
            "created_at": datetime.now().isoformat(),
        }

        if user_id not in self._ledger:
            self._ledger[user_id] = []
        self._ledger[user_id].append(tx)
        self._save()

        return self.get_balance(user_id)

    def consume_tokens(self, user_id: str, action: str, tokens_override: int = 0) -> dict:
        """消耗 tokens（内部调用）"""
        cost = tokens_override if tokens_override > 0 else self.TOKEN_COSTS.get(action, 300)
        self._ensure_user_balance(user_id)

        if self._balances[user_id]["balance"] < cost:
            raise ValueError(f"Token 余额不足，需要 {cost} tokens，当前余额 {self._balances[user_id]['balance']}")

        self._balances[user_id]["balance"] -= cost
        self._balances[user_id]["total_consumed"] += cost

        tx = {
            "id": uuid.uuid4().hex[:12],
            "user_id": user_id,
            "type": "consume",
            "action": action,
            "tokens": -cost,
            "amount": 0,
            "balance_after": self._balances[user_id]["balance"],
            "created_at": datetime.now().isoformat(),
        }

        if user_id not in self._ledger:
            self._ledger[user_id] = []
        self._ledger[user_id].append(tx)
        self._save()

        return {"consumed": cost, "balance": self._balances[user_id]["balance"]}

    def get_usage_history(self, user_id: str, limit: int = 50) -> list:
        """获取 token 使用记录"""
        if user_id not in self._ledger:
            return []
        history = self._ledger[user_id]
        # 按时间倒序
        sorted_history = sorted(history, key=lambda x: x["created_at"], reverse=True)
        return sorted_history[:limit]

    def get_usage_stats(self, user_id: str) -> dict:
        """获取使用统计（按操作类型分组）"""
        if user_id not in self._ledger:
            return {"by_action": {}, "daily": [], "total_consumed": 0}

        by_action = {}
        daily = {}
        consumed_history = [tx for tx in self._ledger[user_id] if tx["type"] == "consume"]

        for tx in consumed_history:
            action = tx.get("action", "other")
            tokens = abs(tx["tokens"])
            by_action[action] = by_action.get(action, 0) + tokens

            day = tx["created_at"][:10]
            daily[day] = daily.get(day, 0) + tokens

        # 最近 30 天
        daily_list = sorted(
            [{"date": d, "tokens": t} for d, t in daily.items()],
            key=lambda x: x["date"]
        )[-30:]

        total = sum(abs(tx["tokens"]) for tx in consumed_history)

        return {
            "by_action": by_action,
            "daily": daily_list,
            "total_consumed": total,
        }


# ── 全局单例 ──
token_service = TokenService()
