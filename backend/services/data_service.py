"""
行情数据服务 — 多数据源整合（akshare + 新浪 + 东方财富）
支持：实时行情、指数、板块、全市场快照、基本面、K线、缓存
"""
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mitouai.data")

# 简易内存缓存
_cache: dict = {}
CACHE_TTL = 300  # 5 分钟


def _cached(key: str, ttl: int = None):
    """缓存装饰器"""
    if ttl is None:
        ttl = CACHE_TTL

    def decorator(fn):
        def wrapper(*args, **kwargs):
            now = time.time()
            if key in _cache and now - _cache[key]["ts"] < ttl:
                return _cache[key]["data"]
            result = fn(*args, **kwargs)
            _cache[key] = {"ts": now, "data": result}
            return result
        return wrapper
    return decorator


class DataService:
    """行情数据服务"""

    # ═══════════════════════════════════════════════
    #  股票搜索
    # ═══════════════════════════════════════════════

    def search_stocks(self, query: str) -> list[dict]:
        """搜索股票（直接 akshare）"""
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            results = []
            q = query.strip().upper()
            for _, row in df.iterrows():
                code = str(row.get("code", ""))
                name = str(row.get("name", ""))
                if q in name or q in code:
                    if code.startswith(("6", "9")):
                        suffix = ".SS"
                    elif code.startswith(("0", "3")):
                        suffix = ".SZ"
                    else:
                        suffix = ".SS"
                    results.append({
                        "code": f"{code}{suffix}",
                        "name": name,
                        "exchange": "上交所" if code.startswith(("6", "9")) else "深交所",
                        "market": "A",
                    })
                if len(results) >= 20:
                    break
            return results
        except Exception as e:
            logger.warning(f"搜索股票失败: {e}")
            return []

    # ═══════════════════════════════════════════════
    #  实时行情
    # ═══════════════════════════════════════════════

    def get_realtime_quote(self, ticker: str) -> dict:
        """获取实时行情（东方财富实时接口）"""
        try:
            import akshare as ak
            code = ticker.split(".")[0]
            market_map = {".SS": "1", ".SZ": "0"}
            suffix = ticker[-3:].upper()
            market = market_map.get(suffix, "1")

            df = ak.stock_zh_a_spot_em()
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
                    "turnover": float(r.get("换手率", 0)),
                    "pe": float(r.get("市盈率-动态", 0)) if r.get("市盈率-动态") else None,
                    "pb": float(r.get("市净率", 0)) if r.get("市净率") else None,
                    "total_mv": float(r.get("总市值", 0)) if r.get("总市值") else None,
                    "circ_mv": float(r.get("流通市值", 0)) if r.get("流通市值") else None,
                    "market": market,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
        except Exception as e:
            logger.warning(f"获取实时行情失败 [{ticker}]: {e}")
        return {}

    # ═══════════════════════════════════════════════
    #  K线数据
    # ═══════════════════════════════════════════════

    def get_kline(self, ticker: str, start_date: str = "", end_date: str = "",
                  period: str = "daily") -> list[dict]:
        """获取K线数据"""
        try:
            import akshare as ak
            code = ticker.split(".")[0]
            suffix = ticker[-3:].upper()
            sym_prefix = "sh" if suffix == ".SS" else "sz"
            sina_sym = sym_prefix + code

            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
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
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "date": str(row.get("date", "")),
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", 0)),
                    })
                return records
        except Exception as e:
            logger.warning(f"获取K线失败 [{ticker}]: {e}")
        return []

    def get_kline_df(self, ticker: str, days: int = 250):
        """获取K线为DataFrame（内部使用）"""
        import pandas as pd
        records = self.get_kline(
            ticker,
            start_date=(datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
        )
        if records:
            return pd.DataFrame(records)
        return pd.DataFrame()

    # ═══════════════════════════════════════════════
    #  市场指数（实时）
    # ═══════════════════════════════════════════════

    def get_market_indices(self) -> list[dict]:
        """获取主要市场指数（实时）"""
        try:
            import akshare as ak
            df = ak.stock_zh_index_spot_em()
            # 取五大指数
            target_codes = ["000001", "399001", "000300", "399006", "000688"]
            target_names = {
                "000001": "上证指数", "399001": "深证成指",
                "000300": "沪深300", "399006": "创业板指",
                "000688": "科创50",
            }
            results = []
            for code in target_codes:
                row = df[df["代码"] == code]
                if not row.empty:
                    r = row.iloc[0]
                    results.append({
                        "name": target_names.get(code, str(r.get("名称", ""))),
                        "code": code,
                        "value": float(r.get("最新价", 0)),
                        "change": float(r.get("涨跌幅", 0)),
                        "change_amt": float(r.get("涨跌额", 0)),
                    })
            return results if results else self._static_indices()
        except Exception as e:
            logger.warning(f"获取指数失败: {e}")
            return self._static_indices()

    def _static_indices(self):
        return [
            {"name": "上证指数", "code": "000001", "value": None, "change": None, "change_amt": None, "static": True},
            {"name": "深证成指", "code": "399001", "value": None, "change": None, "change_amt": None, "static": True},
            {"name": "沪深300", "code": "000300", "value": None, "change": None, "change_amt": None, "static": True},
            {"name": "创业板指", "code": "399006", "value": None, "change": None, "change_amt": None, "static": True},
            {"name": "科创50", "code": "000688", "value": None, "change": None, "change_amt": None, "static": True},
        ]

    # ═══════════════════════════════════════════════
    #  行业板块表现
    # ═══════════════════════════════════════════════

    def get_sector_performance(self) -> list[dict]:
        """获取行业板块涨跌幅排行"""
        try:
            import akshare as ak
            df = ak.stock_board_industry_name_em()
            results = []
            for _, row in df.head(30).iterrows():
                results.append({
                    "name": str(row.get("板块名称", "")),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "up_count": int(row.get("上涨家数", 0)),
                    "down_count": int(row.get("下跌家数", 0)),
                    "leader": str(row.get("领涨股票", "")),
                })
            # 按涨跌幅排序
            results.sort(key=lambda x: x["change_pct"], reverse=True)
            return results
        except Exception as e:
            logger.warning(f"获取板块数据失败: {e}")
            return []

    # ═══════════════════════════════════════════════
    #  全市场快照（选股器核心数据源）
    # ═══════════════════════════════════════════════

    def get_all_stocks_snapshot(self, force_refresh: bool = False) -> list[dict]:
        """获取全A股快照（含PE/PB/市值/涨跌幅等，缓存5分钟）"""
        cache_key = "all_stocks_snapshot"
        now = time.time()
        if not force_refresh and cache_key in _cache and now - _cache[cache_key]["ts"] < 600:
            return _cache[cache_key]["data"]

        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            results = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                pe = row.get("市盈率-动态")
                pb = row.get("市净率")
                results.append({
                    "code": code,
                    "name": name,
                    "price": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "change_amt": float(row.get("涨跌额", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                    "turnover": float(row.get("换手率", 0)) if row.get("换手率") else 0,
                    "pe": float(pe) if pe and float(pe) > 0 else None,
                    "pb": float(pb) if pb and float(pb) > 0 else None,
                    "total_mv": float(row.get("总市值", 0)) if row.get("总市值") else 0,
                    "circ_mv": float(row.get("流通市值", 0)) if row.get("流通市值") else 0,
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                })
            _cache[cache_key] = {"ts": now, "data": results}
            logger.info(f"全市场快照更新: {len(results)} 只股票")
            return results
        except Exception as e:
            logger.error(f"获取全市场快照失败: {e}")
            # 返回缓存数据
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            return []

    # ═══════════════════════════════════════════════
    #  个股基本面
    # ═══════════════════════════════════════════════

    def get_stock_fundamentals(self, ticker: str) -> dict:
        """获取个股基本面数据"""
        code = ticker.split(".")[0]
        result = {
            "code": code, "name": "", "pe": None, "pb": None, "ps": None,
            "roe": None, "roa": None, "revenue_growth": None, "profit_growth": None,
            "gross_margin": None, "net_margin": None, "debt_ratio": None,
            "current_ratio": None, "eps": None, "bps": None, "dividend_yield": None,
            "total_mv": None, "circ_mv": None,
        }

        try:
            import akshare as ak

            # 用东方财富个股财务数据
            try:
                fin_df = ak.stock_financial_analysis_indicator(symbol=code)
                if fin_df is not None and not fin_df.empty:
                    latest = fin_df.iloc[0]
                    result["roe"] = float(latest.get("净资产收益率", 0)) if latest.get("净资产收益率") else None
                    result["eps"] = float(latest.get("每股收益", 0)) if latest.get("每股收益") else None
                    result["bps"] = float(latest.get("每股净资产", 0)) if latest.get("每股净资产") else None
                    result["gross_margin"] = float(latest.get("销售毛利率", 0)) if latest.get("销售毛利率") else None
                    result["net_margin"] = float(latest.get("销售净利率", 0)) if latest.get("销售净利率") else None
                    result["roa"] = float(latest.get("总资产净利润率", 0)) if latest.get("总资产净利润率") else None
            except Exception:
                pass

            # 从实时快照补充PE/PB/市值
            try:
                df = ak.stock_zh_a_spot_em()
                row = df[df["代码"] == code]
                if not row.empty:
                    r = row.iloc[0]
                    result["name"] = str(r.get("名称", ""))
                    pe = r.get("市盈率-动态")
                    result["pe"] = float(pe) if pe and float(pe) > 0 else None
                    pb = r.get("市净率")
                    result["pb"] = float(pb) if pb and float(pb) > 0 else None
                    result["total_mv"] = float(r.get("总市值", 0)) if r.get("总市值") else None
                    result["circ_mv"] = float(r.get("流通市值", 0)) if r.get("流通市值") else None
            except Exception:
                pass

            # 偿债能力
            try:
                debt_df = ak.stock_zcfz_em(symbol=code)
                if debt_df is not None and not debt_df.empty:
                    latest = debt_df.iloc[0]
                    # 资产负债率
                    for col in ["资产负债率", "负债合计", "资产总计"]:
                        if col in latest and "资产总计" in latest:
                            try:
                                ta = float(latest["资产总计"])
                                tl = float(latest["负债合计"])
                                result["debt_ratio"] = round(tl / ta * 100, 2) if ta > 0 else None
                                break
                            except (ValueError, KeyError):
                                pass
            except Exception:
                pass

            # 成长性
            try:
                growth_df = ak.stock_yjbb_em(symbol=code)
                if growth_df is not None and not growth_df.empty:
                    latest = growth_df.iloc[0]
                    result["revenue_growth"] = float(latest.get("营业收入同比增长", 0)) if latest.get("营业收入同比增长") else None
                    result["profit_growth"] = float(latest.get("净利润同比增长", 0)) if latest.get("净利润同比增长") else None
            except Exception:
                pass

            # 分红
            try:
                div_df = ak.stock_history_dividend_detail(symbol=code, indicator="分红")
                if div_df is not None and not div_df.empty:
                    latest_div = div_df.iloc[0]
                    price = result.get("price") or 1
                    div_per_share = float(latest_div.get("派息", 0)) if latest_div.get("派息") else 0
                    if div_per_share > 0 and result["pe"]:
                        result["dividend_yield"] = round(div_per_share / result["pe"] * 100, 2) if price else None
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"获取基本面失败 [{ticker}]: {e}")

        return result

    # ═══════════════════════════════════════════════
    #  新闻/公告
    # ═══════════════════════════════════════════════

    def get_stock_news(self, ticker: str, limit: int = 10) -> list[dict]:
        """获取个股相关新闻"""
        try:
            import akshare as ak
            code = ticker.split(".")[0]
            df = ak.stock_news_em(symbol=code)
            if df is not None and not df.empty:
                results = []
                for _, row in df.head(limit).iterrows():
                    results.append({
                        "title": str(row.get("新闻标题", "")),
                        "time": str(row.get("发布时间", "")),
                        "source": str(row.get("文章来源", "")),
                    })
                return results
        except Exception as e:
            logger.warning(f"获取新闻失败 [{ticker}]: {e}")
        return []

    def get_market_news(self, limit: int = 15) -> list[dict]:
        """获取市场要闻"""
        try:
            import akshare as ak
            df = ak.stock_info_global_news()
            if df is not None and not df.empty:
                results = []
                for _, row in df.head(limit).iterrows():
                    results.append({
                        "title": str(row.get("title", row.get("标题", ""))),
                        "time": str(row.get("time", row.get("时间", ""))),
                        "summary": str(row.get("summary", row.get("摘要", "")))[:100],
                    })
                return results
        except Exception as e:
            logger.warning(f"获取市场新闻失败: {e}")
        return []

    # ═══════════════════════════════════════════════
    #  资金流向（北向资金等）
    # ═══════════════════════════════════════════════

    def get_north_flow(self) -> dict:
        """获取北向资金流向"""
        try:
            import akshare as ak
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                return {
                    "date": str(latest.get("date", latest.get("日期", ""))),
                    "net_flow": float(latest.get("value", latest.get("净流入", 0))),
                }
        except Exception as e:
            logger.warning(f"获取北向资金失败: {e}")
        return {"date": "", "net_flow": 0}


# 全局单例
data_service = DataService()
