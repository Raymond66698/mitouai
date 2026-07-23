"""
港股 + 美股数据服务
支持：搜索、实时行情、K线、全市场快照
"""
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger("mitouai.hkus")

# 简易缓存
_cache: dict = {}
CACHE_TTL = 300


def _cached_get(key, ttl=300):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < ttl:
        return _cache[key]["data"]
    return None


def _cached_set(key, data):
    _cache[key] = {"ts": time.time(), "data": data}


class HKUSService:
    """港股+美股数据服务"""

    # ═══════════════════════════════════════
    #  搜索
    # ═══════════════════════════════════════

    def search_hk_stocks(self, query: str) -> list[dict]:
        """搜索港股"""
        try:
            import akshare as ak
            df = ak.stock_hk_spot_em()
            results = []
            q = query.strip().upper()
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                if q in name or q in code:
                    results.append({
                        "code": code,
                        "name": name,
                        "exchange": "港交所",
                        "market": "HK",
                        "ticker": f"{code}.HK",
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                    })
                if len(results) >= 20:
                    break
            return results
        except Exception as e:
            logger.warning(f"搜索港股失败: {e}")
            return []

    def search_us_stocks(self, query: str) -> list[dict]:
        """搜索美股（用知名股票列表）"""
        # akshare 美股搜索较慢，用本地知名股票列表兜底
        popular_us = [
            ("AAPL", "苹果", "NASDAQ"),
            ("MSFT", "微软", "NASDAQ"),
            ("GOOGL", "谷歌", "NASDAQ"),
            ("AMZN", "亚马逊", "NASDAQ"),
            ("META", "Meta", "NASDAQ"),
            ("TSLA", "特斯拉", "NASDAQ"),
            ("NVDA", "英伟达", "NASDAQ"),
            ("AMD", "AMD", "NASDAQ"),
            ("INTC", "英特尔", "NASDAQ"),
            ("NFLX", "奈飞", "NASDAQ"),
            ("BABA", "阿里巴巴", "NYSE"),
            ("JD", "京东", "NASDAQ"),
            ("PDD", "拼多多", "NASDAQ"),
            ("BIDU", "百度", "NASDAQ"),
            ("NIO", "蔚来", "NYSE"),
            ("XPEV", "小鹏汽车", "NYSE"),
            ("LI", "理想汽车", "NASDAQ"),
            ("TME", "腾讯音乐", "NYSE"),
            ("BEKE", "贝壳", "NYSE"),
            ("JPM", "摩根大通", "NYSE"),
            ("GS", "高盛", "NYSE"),
            ("BAC", "美国银行", "NYSE"),
            ("WMT", "沃尔玛", "NYSE"),
            ("KO", "可口可乐", "NYSE"),
            ("PEP", "百事", "NASDAQ"),
            ("DIS", "迪士尼", "NYSE"),
            ("PYPL", "PayPal", "NASDAQ"),
            ("UBER", "Uber", "NYSE"),
            ("COIN", "Coinbase", "NASDAQ"),
            ("SNOW", "Snowflake", "NYSE"),
            ("CRM", "Salesforce", "NYSE"),
            ("SHOP", "Shopify", "NYSE"),
            ("SQ", "Block", "NYSE"),
            ("PLTR", "Palantir", "NYSE"),
        ]
        q = query.strip().upper()
        results = []
        for sym, name, exchange in popular_us:
            if q in sym or q in name.upper():
                results.append({
                    "code": sym,
                    "name": name,
                    "exchange": exchange,
                    "market": "US",
                    "ticker": f"{sym}.US",
                })
        return results[:20]

    def search_multi_market(self, query: str) -> dict:
        """多市场搜索"""
        return {
            "cn": self._search_cn_wrapper(query),
            "hk": self.search_hk_stocks(query),
            "us": self.search_us_stocks(query),
        }

    def _search_cn_wrapper(self, q):
        """A股搜索包装"""
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            results = []
            qt = q.strip().upper()
            for _, row in df.iterrows():
                code = str(row.get("code", ""))
                name = str(row.get("name", ""))
                if qt in name or qt in code:
                    if code.startswith(("6", "9")):
                        suffix = ".SH"
                    elif code.startswith(("0", "3", "4", "8")):
                        suffix = ".SZ"
                    else:
                        suffix = ".SH"
                    results.append({
                        "code": f"{code}{suffix}",
                        "name": name,
                        "exchange": "上交所" if code.startswith(("6", "9")) else "深交所",
                        "market": "CN",
                        "ticker": f"{code}{suffix}",
                    })
                if len(results) >= 20:
                    break
            return results
        except:
            return []

    # ═══════════════════════════════════════
    #  实时行情
    # ═══════════════════════════════════════

    def get_hk_realtime_quote(self, code: str) -> dict:
        """获取港股实时行情"""
        try:
            import akshare as ak
            df = ak.stock_hk_spot_em()
            row = df[df["代码"] == code]
            if not row.empty:
                r = row.iloc[0]
                return {
                    "code": code,
                    "name": str(r.get("名称", "")),
                    "price": float(r.get("最新价", 0)),
                    "change_pct": float(r.get("涨跌幅", 0)),
                    "change_amt": float(r.get("涨跌额", 0)),
                    "volume": float(r.get("成交量", 0)),
                    "amount": float(r.get("成交额", 0)),
                    "high": float(r.get("最高", 0)),
                    "low": float(r.get("最低", 0)),
                    "open": float(r.get("今开", 0)),
                    "pre_close": float(r.get("昨收", 0)),
                    "market": "HK",
                }
        except Exception as e:
            logger.warning(f"获取港股行情失败 [{code}]: {e}")
        return {}

    def get_us_realtime_quote(self, symbol: str) -> dict:
        """获取美股实时行情（yfinance）"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            fast_info = {}
            try:
                fast_info = ticker.fast_info or {}
            except:
                pass

            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
            current = info.get("currentPrice") or info.get("regularMarketPrice") or fast_info.get("lastPrice", 0)

            change = 0
            change_pct = 0
            if prev_close and current:
                change = current - prev_close
                if prev_close > 0:
                    change_pct = (change / prev_close) * 100

            return {
                "code": symbol,
                "name": str(info.get("longName", info.get("shortName", symbol))),
                "price": current,
                "change_pct": round(change_pct, 2),
                "change_amt": round(change, 2),
                "high": float(info.get("dayHigh", 0)),
                "low": float(info.get("dayLow", 0)),
                "open": float(info.get("open", 0)),
                "pre_close": float(prev_close),
                "volume": int(info.get("volume", 0) or 0),
                "market": "US",
                "pe": info.get("trailingPE"),
                "pb": info.get("priceToBook"),
                "total_mv": info.get("marketCap"),
                "currency": info.get("currency", "USD"),
            }
        except Exception as e:
            logger.warning(f"获取美股行情失败 [{symbol}]: {e}")
            return {}

    # ═══════════════════════════════════════
    #  K线数据
    # ═══════════════════════════════════════

    def get_hk_kline(self, code: str, days: int = 365) -> list[dict]:
        """获取港股K线"""
        try:
            import akshare as ak
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            df = ak.stock_hk_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
            if df is not None and not df.empty:
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "date": str(row.get("日期", "")),
                        "open": float(row.get("开盘", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "close": float(row.get("收盘", 0)),
                        "volume": float(row.get("成交量", 0)),
                    })
                return records
        except Exception as e:
            logger.warning(f"获取港股K线失败 [{code}]: {e}")
        return []

    def get_us_kline(self, symbol: str, days: int = 365) -> list[dict]:
        """获取美股K线（yfinance）"""
        try:
            import yfinance as yf
            end = datetime.now()
            start = end - timedelta(days=days)
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)
            if df is not None and not df.empty:
                records = []
                for idx, row in df.iterrows():
                    records.append({
                        "date": idx.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": float(row["Volume"]),
                    })
                return records
        except Exception as e:
            logger.warning(f"获取美股K线失败 [{symbol}]: {e}")
        return []

    # ═══════════════════════════════════════
    #  市场指数
    # ═══════════════════════════════════════

    def get_hk_indices(self) -> list[dict]:
        """获取港股主要指数"""
        try:
            import akshare as ak
            df = ak.stock_hk_index_spot_em()
            target = {
                "HSI": "恒生指数",
                "HSCEI": "国企指数",
                "HSTECH": "恒生科技",
            }
            results = []
            for code, name in target.items():
                found = False
                for _, r in df.iterrows():
                    if str(r.get("代码", "")).upper() == code:
                        results.append({
                            "name": name,
                            "code": code,
                            "value": float(r.get("最新价", 0)),
                            "change": float(r.get("涨跌幅", 0)),
                            "change_amt": float(r.get("涨跌额", 0)),
                        })
                        found = True
                        break
                if not found:
                    results.append({"name": name, "code": code, "value": 0, "change": 0, "change_amt": 0})
            return results
        except Exception:
            return [
                {"name": "恒生指数", "code": "HSI", "value": 0, "change": 0, "change_amt": 0},
                {"name": "国企指数", "code": "HSCEI", "value": 0, "change": 0, "change_amt": 0},
                {"name": "恒生科技", "code": "HSTECH", "value": 0, "change": 0, "change_amt": 0},
            ]

    def get_us_indices(self) -> list[dict]:
        """获取美股主要指数（yfinance）"""
        indices = [
            ("^GSPC", "标普500"),
            ("^IXIC", "纳斯达克"),
            ("^DJI", "道琼斯"),
        ]
        results = []
        try:
            import yfinance as yf
            for sym, name in indices:
                try:
                    t = yf.Ticker(sym)
                    info = t.info or {}
                    price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
                    prev = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
                    chg = price - prev if price and prev else 0
                    chg_pct = (chg / prev * 100) if prev > 0 else 0
                    results.append({
                        "name": name,
                        "code": sym.replace("^", ""),
                        "value": price,
                        "change": round(chg_pct, 2),
                        "change_amt": round(chg, 2),
                    })
                except:
                    results.append({"name": name, "code": sym, "value": 0, "change": 0, "change_amt": 0})
        except:
            pass
        return results or [
            {"name": "标普500", "code": "GSPC", "value": 0, "change": 0, "change_amt": 0},
            {"name": "纳斯达克", "code": "IXIC", "value": 0, "change": 0, "change_amt": 0},
            {"name": "道琼斯", "code": "DJI", "value": 0, "change": 0, "change_amt": 0},
        ]

    # ═══════════════════════════════════════
    #  港股全市场快照（供选股器使用）
    # ═══════════════════════════════════════

    def get_hk_all_stocks_snapshot(self, force_refresh=False) -> list[dict]:
        """获取全港股快照"""
        cache_key = "hk_all_snapshot"
        now = time.time()
        if not force_refresh and cache_key in _cache and now - _cache[cache_key]["ts"] < 600:
            return _cache[cache_key]["data"]

        try:
            import akshare as ak
            df = ak.stock_hk_spot_em()
            results = []
            for _, row in df.iterrows():
                try:
                    results.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "turnover": float(row.get("换手率", 0)) if row.get("换手率") else 0,
                        "total_mv": float(row.get("总市值", 0)) if row.get("总市值") else 0,
                        "pe": float(row.get("市盈率", 0)) if row.get("市盈率") and float(row.get("市盈率", 0)) > 0 else None,
                        "market": "HK",
                    })
                except:
                    pass
            _cached_set(cache_key, results)
            logger.info(f"港股快照更新: {len(results)} 只")
            return results
        except Exception as e:
            logger.warning(f"获取港股快照失败: {e}")
            return _cache.get(cache_key, {}).get("data", [])


hk_us_service = HKUSService()
