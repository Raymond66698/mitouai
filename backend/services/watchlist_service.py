"""
自选股与模拟组合管理服务
SQLite 持久化：自选股列表、分组、模拟持仓
"""
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mitouai.watchlist")

DB_PATH = Path("data/watchlist.db")


class WatchlistService:
    """自选股/组合管理"""

    def __init__(self):
        self._ensure_db()

    def _ensure_db(self):
        """初始化数据库表"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlists (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT DEFAULT '默认',
                    stocks TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT DEFAULT '我的组合',
                    holdings TEXT DEFAULT '[]',
                    cash REAL DEFAULT 100000.0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    name TEXT DEFAULT '',
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    fee REAL DEFAULT 0,
                    trade_date TEXT DEFAULT (date('now')),
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def _get_ds(self):
        from services.data_service import DataService
        return DataService()

    # ═══════════════════════════════════════════════
    #  自选股
    # ═══════════════════════════════════════════════

    def get_watchlists(self, user_id: str) -> list[dict]:
        """获取用户所有自选列表"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM watchlists WHERE user_id=? ORDER BY created_at",
                (user_id,)
            ).fetchall()
            result = []
            for r in rows:
                wl = dict(r)
                wl["stocks"] = json.loads(wl.get("stocks", "[]"))
                result.append(wl)
            return result

    def create_watchlist(self, user_id: str, name: str = "") -> dict:
        """创建自选列表"""
        import uuid
        wl_id = str(uuid.uuid4())[:8]
        wl_name = name or "默认"
        now = datetime.now().isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO watchlists (id, user_id, name, stocks, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (wl_id, user_id, wl_name, "[]", now, now),
            )
            conn.commit()
        return {"id": wl_id, "user_id": user_id, "name": wl_name, "stocks": [], "created_at": now}

    def add_stock(self, user_id: str, list_id: str, ticker: str, name: str = "") -> dict:
        """添加股票到自选列表"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            row = conn.execute(
                "SELECT stocks FROM watchlists WHERE id=? AND user_id=?",
                (list_id, user_id)
            ).fetchone()
            if not row:
                # 列表不存在则自动创建
                wl = self.create_watchlist(user_id, "默认")
                list_id = wl["id"]
                stocks = []
            else:
                stocks = json.loads(row[0])

            # 避免重复
            if not any(s["ticker"] == ticker for s in stocks):
                stocks.append({
                    "ticker": ticker,
                    "name": name,
                    "added_at": datetime.now().isoformat(),
                })

            conn.execute(
                "UPDATE watchlists SET stocks=?, updated_at=? WHERE id=?",
                (json.dumps(stocks, ensure_ascii=False), datetime.now().isoformat(), list_id),
            )
            conn.commit()
        return {"success": True, "ticker": ticker, "name": name}

    def remove_stock(self, user_id: str, list_id: str, ticker: str) -> dict:
        """从自选列表移除"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            row = conn.execute(
                "SELECT stocks FROM watchlists WHERE id=? AND user_id=?",
                (list_id, user_id)
            ).fetchone()
            if not row:
                return {"success": False, "error": "列表不存在"}
            stocks = json.loads(row[0])
            new_stocks = [s for s in stocks if s["ticker"] != ticker]
            if len(new_stocks) != len(stocks):
                conn.execute(
                    "UPDATE watchlists SET stocks=?, updated_at=? WHERE id=?",
                    (json.dumps(new_stocks, ensure_ascii=False), datetime.now().isoformat(), list_id),
                )
                conn.commit()
        return {"success": True}

    def get_watchlist_with_quotes(self, user_id: str, list_id: str = "") -> list[dict]:
        """获取自选股含实时行情"""
        ds = self._get_ds()
        watchlists = self.get_watchlists(user_id)

        target_list = None
        if list_id:
            target_list = next((w for w in watchlists if w["id"] == list_id), None)
        if not target_list and watchlists:
            target_list = watchlists[0]
        if not target_list:
            return []

        result = []
        for stock in target_list.get("stocks", []):
            ticker = stock["ticker"]
            quote = ds.get_realtime_quote(ticker)
            result.append({
                "ticker": ticker,
                "name": quote.get("name", stock.get("name", "")),
                "price": quote.get("price", 0),
                "change_pct": quote.get("change_pct", 0),
                "change_amt": quote.get("change_amt", 0),
                "volume": quote.get("volume", 0),
                "amount": quote.get("amount", 0),
                "pe": quote.get("pe"),
                "pb": quote.get("pb"),
                "total_mv": quote.get("total_mv"),
                "added_at": stock.get("added_at", ""),
            })
        return result

    def delete_watchlist(self, user_id: str, list_id: str) -> dict:
        """删除自选列表"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("DELETE FROM watchlists WHERE id=? AND user_id=?", (list_id, user_id))
            conn.commit()
        return {"success": True}

    # ═══════════════════════════════════════════════
    #  模拟组合
    # ═══════════════════════════════════════════════

    def get_portfolios(self, user_id: str) -> list[dict]:
        """获取所有组合"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM portfolios WHERE user_id=? ORDER BY created_at",
                (user_id,)
            ).fetchall()
            result = []
            for r in rows:
                pf = dict(r)
                pf["holdings"] = json.loads(pf.get("holdings", "[]"))
                result.append(pf)
            return result

    def create_portfolio(self, user_id: str, name: str = "", initial_cash: float = 100000) -> dict:
        """创建组合"""
        import uuid
        pf_id = str(uuid.uuid4())[:8]
        pf_name = name or "我的组合"
        now = datetime.now().isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO portfolios (id, user_id, name, holdings, cash, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (pf_id, user_id, pf_name, "[]", initial_cash, now, now),
            )
            conn.commit()
        return {"id": pf_id, "user_id": user_id, "name": pf_name, "holdings": [], "cash": initial_cash}

    def trade(self, user_id: str, portfolio_id: str, ticker: str, name: str,
              action: str, quantity: int, price: float) -> dict:
        """执行交易（买入/卖出）"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            row = conn.execute(
                "SELECT holdings, cash FROM portfolios WHERE id=? AND user_id=?",
                (portfolio_id, user_id)
            ).fetchone()
            if not row:
                return {"success": False, "error": "组合不存在"}

            holdings = json.loads(row[0])
            cash = row[1]
            fee = max(5.0, price * quantity * 0.0003)  # 最低5元

            if action == "buy":
                cost = price * quantity + fee
                if cost > cash:
                    return {"success": False, "error": f"现金不足（需要{cost:.0f}，可用{cash:.0f}）"}
                cash -= cost

                # 合并持仓
                existing = next((h for h in holdings if h["ticker"] == ticker), None)
                if existing:
                    total_qty = existing["quantity"] + quantity
                    total_cost = existing["cost"] + cost
                    existing["quantity"] = total_qty
                    existing["cost"] = total_cost
                    existing["avg_price"] = round(total_cost / total_qty, 2)
                else:
                    holdings.append({
                        "ticker": ticker,
                        "name": name,
                        "quantity": quantity,
                        "cost": cost,
                        "avg_price": round(price, 2),
                    })

            elif action == "sell":
                existing = next((h for h in holdings if h["ticker"] == ticker), None)
                if not existing:
                    return {"success": False, "error": "持仓不存在"}
                if quantity > existing["quantity"]:
                    return {"success": False, "error": f"持仓不足（持有{existing['quantity']}股）"}

                revenue = price * quantity - fee
                cash += revenue
                existing["quantity"] -= quantity
                if existing["quantity"] == 0:
                    holdings.remove(existing)
                else:
                    existing["cost"] = existing["cost"] * (existing["quantity"] / (existing["quantity"] + quantity))

            # 保存
            conn.execute(
                "UPDATE portfolios SET holdings=?, cash=?, updated_at=? WHERE id=?",
                (json.dumps(holdings, ensure_ascii=False), cash, datetime.now().isoformat(), portfolio_id),
            )

            # 交易记录
            conn.execute(
                "INSERT INTO trades (portfolio_id, ticker, name, action, quantity, price, fee, trade_date) VALUES (?,?,?,?,?,?,?,?)",
                (portfolio_id, ticker, name, action, quantity, price, fee, datetime.now().strftime("%Y-%m-%d")),
            )
            conn.commit()

        return {"success": True, "cash": round(cash, 2), "holdings": holdings}

    def get_portfolio_summary(self, user_id: str, portfolio_id: str) -> dict:
        """获取组合总览（市值、盈亏）"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM portfolios WHERE id=? AND user_id=?",
                (portfolio_id, user_id)
            ).fetchone()
            if not row:
                return {}

            pf = dict(row)
            holdings = json.loads(pf.get("holdings", "[]"))
            cash = pf.get("cash", 0)

            ds = self._get_ds()
            total_market_value = 0
            total_cost = 0
            enriched_holdings = []

            for h in holdings:
                quote = ds.get_realtime_quote(h["ticker"])
                current_price = quote.get("price", h["avg_price"])
                current_value = current_price * h["quantity"]
                cost_value = h["avg_price"] * h["quantity"]
                pnl = current_value - cost_value
                pnl_pct = (pnl / cost_value * 100) if cost_value > 0 else 0

                total_market_value += current_value
                total_cost += cost_value

                enriched_holdings.append({
                    "ticker": h["ticker"],
                    "name": quote.get("name", h.get("name", "")),
                    "quantity": h["quantity"],
                    "avg_price": h["avg_price"],
                    "current_price": current_price,
                    "cost": cost_value,
                    "current_value": current_value,
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "change_pct": quote.get("change_pct", 0),
                })

            total_pnl = total_market_value - total_cost
            total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            total_assets = total_market_value + cash

            return {
                "id": pf["id"],
                "name": pf["name"],
                "cash": round(cash, 2),
                "total_cost": round(total_cost, 2),
                "total_market_value": round(total_market_value, 2),
                "total_assets": round(total_assets, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "holdings": enriched_holdings,
                "created_at": pf["created_at"],
                "updated_at": pf["updated_at"],
            }

    def get_trade_history(self, user_id: str, portfolio_id: str, limit: int = 50) -> list[dict]:
        """获取交易记录"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            # 先验证所有权
            pf = conn.execute("SELECT id FROM portfolios WHERE id=? AND user_id=?", (portfolio_id, user_id)).fetchone()
            if not pf:
                return []
            rows = conn.execute(
                "SELECT * FROM trades WHERE portfolio_id=? ORDER BY id DESC LIMIT ?",
                (portfolio_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_portfolio(self, user_id: str, portfolio_id: str) -> dict:
        """删除组合"""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("DELETE FROM trades WHERE portfolio_id=?", (portfolio_id,))
            conn.execute("DELETE FROM portfolios WHERE id=? AND user_id=?", (portfolio_id, user_id))
            conn.commit()
        return {"success": True}


# 单例
watchlist_service = WatchlistService()
