"""
自选股与模拟组合管理服务
使用 SQLAlchemy ORM
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm.attributes import flag_modified

from database import get_db_context
from models.watchlist import Watchlist, Portfolio, Trade

logger = logging.getLogger("mitouai.watchlist")


class WatchlistService:
    """自选股/组合管理"""

    def _get_ds(self):
        from services.data_service import DataService
        return DataService()

    # ═══════════════════════════════════════════════
    #  自选股
    # ═══════════════════════════════════════════════

    def get_watchlists(self, user_id: str) -> list[dict]:
        """获取用户所有自选列表"""
        with get_db_context() as db:
            rows = db.query(Watchlist).filter(
                Watchlist.user_id == user_id
            ).order_by(Watchlist.created_at).all()
            result = []
            for r in rows:
                d = r.to_dict()
                d["stocks"] = d["stocks"] if isinstance(d["stocks"], list) else json.loads(str(d["stocks"]))
                result.append(d)
            return result

    def create_watchlist(self, user_id: str, name: str = "") -> dict:
        """创建自选列表"""
        wl_id = str(uuid.uuid4())[:8]
        wl_name = name or "默认"
        now = datetime.now().isoformat()
        with get_db_context() as db:
            wl = Watchlist(
                id=wl_id, user_id=user_id, name=wl_name,
                stocks=[], created_at=now, updated_at=now,
            )
            db.add(wl)
            db.commit()
        return {"id": wl_id, "user_id": user_id, "name": wl_name, "stocks": [], "created_at": now}

    def add_stock(self, user_id: str, list_id: str, ticker: str, name: str = "") -> dict:
        """添加股票到自选列表"""
        with get_db_context() as db:
            wl = db.query(Watchlist).filter(
                Watchlist.id == list_id, Watchlist.user_id == user_id
            ).first()
            if not wl:
                # 列表不存在则自动创建
                wl = Watchlist(
                    id=str(uuid.uuid4())[:8], user_id=user_id, name="默认",
                    stocks=[], created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                )
                db.add(wl)
                db.flush()
                list_id = wl.id
                stocks = []
            else:
                stocks = wl.stocks if isinstance(wl.stocks, list) else []

            # 避免重复
            if not any(s.get("ticker") == ticker for s in stocks):
                stocks.append({
                    "ticker": ticker,
                    "name": name,
                    "added_at": datetime.now().isoformat(),
                })

            wl.stocks = stocks
            flag_modified(wl, "stocks")
            wl.updated_at = datetime.now().isoformat()
            db.commit()

        return {"success": True, "ticker": ticker, "name": name}

    def remove_stock(self, user_id: str, list_id: str, ticker: str) -> dict:
        """从自选列表移除"""
        with get_db_context() as db:
            wl = db.query(Watchlist).filter(
                Watchlist.id == list_id, Watchlist.user_id == user_id
            ).first()
            if not wl:
                return {"success": False, "error": "列表不存在"}
            stocks = wl.stocks if isinstance(wl.stocks, list) else []
            new_stocks = [s for s in stocks if s.get("ticker") != ticker]
            if len(new_stocks) != len(stocks):
                wl.stocks = new_stocks
                flag_modified(wl, "stocks")
                wl.updated_at = datetime.now().isoformat()
                db.commit()
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
        with get_db_context() as db:
            db.query(Watchlist).filter(
                Watchlist.id == list_id, Watchlist.user_id == user_id
            ).delete()
            db.commit()
        return {"success": True}

    # ═══════════════════════════════════════════════
    #  模拟组合
    # ═══════════════════════════════════════════════

    def get_portfolios(self, user_id: str) -> list[dict]:
        """获取所有组合"""
        with get_db_context() as db:
            rows = db.query(Portfolio).filter(
                Portfolio.user_id == user_id
            ).order_by(Portfolio.created_at).all()
            result = []
            for r in rows:
                d = r.to_dict()
                d["holdings"] = d["holdings"] if isinstance(d["holdings"], list) else json.loads(str(d["holdings"]))
                result.append(d)
            return result

    def create_portfolio(self, user_id: str, name: str = "", initial_cash: float = 100000) -> dict:
        """创建组合"""
        pf_id = str(uuid.uuid4())[:8]
        pf_name = name or "我的组合"
        now = datetime.now().isoformat()
        with get_db_context() as db:
            pf = Portfolio(
                id=pf_id, user_id=user_id, name=pf_name,
                holdings=[], cash=initial_cash,
                created_at=now, updated_at=now,
            )
            db.add(pf)
            db.commit()
        return {"id": pf_id, "user_id": user_id, "name": pf_name, "holdings": [], "cash": initial_cash}

    def trade(self, user_id: str, portfolio_id: str, ticker: str, name: str,
              action: str, quantity: int, price: float) -> dict:
        """执行交易（买入/卖出）"""
        with get_db_context() as db:
            pf = db.query(Portfolio).filter(
                Portfolio.id == portfolio_id, Portfolio.user_id == user_id
            ).first()
            if not pf:
                return {"success": False, "error": "组合不存在"}

            holdings = pf.holdings if isinstance(pf.holdings, list) else []
            cash = pf.cash
            fee = max(5.0, price * quantity * 0.0003)

            if action == "buy":
                cost = price * quantity + fee
                if cost > cash:
                    return {"success": False, "error": f"现金不足（需要{cost:.0f}，可用{cash:.0f}）"}
                cash -= cost

                existing = next((h for h in holdings if h.get("ticker") == ticker), None)
                if existing:
                    total_qty = existing["quantity"] + quantity
                    total_cost = existing["cost"] + cost
                    existing["quantity"] = total_qty
                    existing["cost"] = total_cost
                    existing["avg_price"] = round(total_cost / total_qty, 2)
                else:
                    holdings.append({
                        "ticker": ticker, "name": name,
                        "quantity": quantity, "cost": cost,
                        "avg_price": round(price, 2),
                    })

            elif action == "sell":
                existing = next((h for h in holdings if h.get("ticker") == ticker), None)
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

            # 保存组合
            pf.holdings = holdings
            flag_modified(pf, "holdings")
            pf.cash = cash
            pf.updated_at = datetime.now().isoformat()

            # 交易记录
            trade = Trade(
                portfolio_id=portfolio_id, ticker=ticker, name=name,
                action=action, quantity=quantity, price=price, fee=fee,
                trade_date=datetime.now().strftime("%Y-%m-%d"),
            )
            db.add(trade)
            db.commit()

        return {"success": True, "cash": round(cash, 2), "holdings": holdings}

    def get_portfolio_summary(self, user_id: str, portfolio_id: str) -> dict:
        """获取组合总览（市值、盈亏）"""
        with get_db_context() as db:
            pf = db.query(Portfolio).filter(
                Portfolio.id == portfolio_id, Portfolio.user_id == user_id
            ).first()
            if not pf:
                return {}

            holdings = pf.holdings if isinstance(pf.holdings, list) else []
            cash = pf.cash

            ds = self._get_ds()
            total_market_value = 0
            total_cost = 0
            enriched_holdings = []

            for h in holdings:
                quote = ds.get_realtime_quote(h["ticker"])
                current_price = quote.get("price", h.get("avg_price", 0))
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
                "id": pf.id, "name": pf.name,
                "cash": round(cash, 2),
                "total_cost": round(total_cost, 2),
                "total_market_value": round(total_market_value, 2),
                "total_assets": round(total_assets, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "holdings": enriched_holdings,
                "created_at": pf.created_at, "updated_at": pf.updated_at,
            }

    def get_trade_history(self, user_id: str, portfolio_id: str, limit: int = 50) -> list[dict]:
        """获取交易记录"""
        with get_db_context() as db:
            pf = db.query(Portfolio).filter(
                Portfolio.id == portfolio_id, Portfolio.user_id == user_id
            ).first()
            if not pf:
                return []
            trades = db.query(Trade).filter(
                Trade.portfolio_id == portfolio_id
            ).order_by(Trade.id.desc()).limit(limit).all()
            return [t.to_dict() for t in trades]

    def delete_portfolio(self, user_id: str, portfolio_id: str) -> dict:
        """删除组合"""
        with get_db_context() as db:
            db.query(Trade).filter(Trade.portfolio_id == portfolio_id).delete()
            db.query(Portfolio).filter(
                Portfolio.id == portfolio_id, Portfolio.user_id == user_id
            ).delete()
            db.commit()
        return {"success": True}


# 单例
watchlist_service = WatchlistService()
