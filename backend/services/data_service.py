"""
行情数据服务 — 基于 akshare 的 A 股数据查询
"""
import logging
import sys
from datetime import datetime, timedelta

logger = logging.getLogger("mitouai.data")


class DataService:
    """行情数据服务"""

    def search_stocks(self, query: str) -> list[dict]:
        """搜索股票（优先用 TradingAgents 模块，回退到直接 akshare）"""
        # 优先：TradingAgents 已封装的搜索（含缓存）
        try:
            sys.path.insert(0, "D:/TradingAgents")
            from tradingagents.dataflows.akshare_data import search_stocks as ak_search
            return ak_search(query)
        except ImportError:
            pass

        # 回退：直接用 akshare
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            results = []
            q = query.strip().upper()
            for _, row in df.iterrows():
                code = str(row.get("code", ""))
                name = str(row.get("name", ""))
                if q in name or q in code:
                    results.append({
                        "code": f"{code}.{'SS' if code.startswith(('6','9')) else 'SZ'}",
                        "name": name,
                        "exchange": "上交所" if code.startswith(("6", "9")) else "深交所",
                        "market": "A",
                    })
                if len(results) >= 20:
                    break
            return results
        except Exception:
            return []

    def get_realtime_quote(self, ticker: str) -> dict:
        """获取实时行情"""
        try:
            import akshare as ak
            code = ticker.split(".")[0]
            sina_sym = ("sh" if ticker.endswith(".SS") else "sz") + code
            df = ak.stock_zh_a_daily(
                symbol=sina_sym,
                start_date=(datetime.now() - timedelta(days=5)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq",
            )
            if df is not None and not df.empty:
                last = df.iloc[-1]
                return {
                    "open": str(last.get("open", "")),
                    "high": str(last.get("high", "")),
                    "low": str(last.get("low", "")),
                    "close": str(last.get("close", "")),
                    "volume": str(last.get("volume", "")),
                    "date": str(last.get("date", "")),
                }
        except Exception as e:
            logger.warning(f"获取实时行情失败 [{ticker}]: {e}")
        return {}

    def get_kline(self, ticker: str, start_date: str = "", end_date: str = "", period: str = "daily") -> list[dict]:
        """获取K线数据"""
        try:
            import akshare as ak
            code = ticker.split(".")[0]
            sina_sym = ("sh" if ticker.endswith(".SS") else "sz") + code

            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
            else:
                start_date = start_date.replace("-", "")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            else:
                end_date = end_date.replace("-", "")

            df = ak.stock_zh_a_daily(
                symbol=sina_sym,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            if df is not None and not df.empty:
                return df.reset_index().to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取K线失败 [{ticker}]: {e}")
        return []

    def get_market_indices(self) -> list[dict]:
        """获取主要市场指数"""
        return [
            {"name": "上证指数", "code": "000001.SS", "value": "--", "change": "--"},
            {"name": "深证成指", "code": "399001.SZ", "value": "--", "change": "--"},
            {"name": "沪深300", "code": "000300.SS", "value": "--", "change": "--"},
            {"name": "创业板指", "code": "399006.SZ", "value": "--", "change": "--"},
        ]
