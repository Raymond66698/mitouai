"""
基本面数据服务 — 从 akshare 获取 A 股基本面指标

使用 stock_zh_a_spot_em 一次性拉取全市场数据并缓存（每2小时刷新），
避免逐只查询导致的超时问题。

⚠️ 合规声明：所有数据仅用于金融知识教育展示，不构成投资建议
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger("mitouai.qlib.fundamentals")


class FundamentalService:
    """A股基本面数据服务（带缓存）"""

    _cache = None          # 缓存的全市场数据 DataFrame
    _cache_time = None     # 缓存时间
    _cache_ttl = 7200      # 缓存有效期（秒），2小时

    def _ensure_cache(self):
        """确保缓存有效，过期则刷新"""
        if self._cache is not None and self._cache_time is not None:
            age = (datetime.now() - self._cache_time).total_seconds()
            if age < self._cache_ttl:
                return True

        # 刷新缓存
        try:
            import akshare as ak
            logger.info("刷新全市场基本面数据缓存...")
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                self._cache = df
                self._cache_time = datetime.now()
                logger.info(f"缓存刷新完成: {len(df)} 只股票")
                return True
            else:
                logger.warning("stock_zh_a_spot_em 返回空数据")
                return False
        except Exception as e:
            logger.error(f"刷新缓存失败: {e}")
            return False

    def get_fundamentals(self, code: str) -> dict:
        """获取单只股票的基本面数据

        Args:
            code: 6位A股代码，如 600519

        Returns:
            {
                "code": "600519",
                "name": "贵州茅台",
                "price": 1680.0,
                "change_pct": 1.23,
                "pe_ttm": 30.5,
                "pb": 10.2,
                "total_mv": 200000000000,
                "total_mv_yi": 2000,
                "volume": 12345600,
                "amount": 2000000000,
                "turnover_rate": 0.5,
                "disclaimer": "..."
            }
        """
        code = code.strip()
        if "." in code:
            code = code.split(".")[0]

        result = {
            "code": code,
            "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
        }

        if not self._ensure_cache():
            result["error"] = "数据源暂时不可用"
            return result

        # 从缓存中查找
        try:
            row = self._cache[self._cache["代码"] == code]
            if row.empty:
                result["error"] = f"未找到股票 {code}"
                return result

            r = row.iloc[0]
            total_mv = float(r.get("总市值", 0)) if pd.notna(r.get("总市值")) else 0
            circ_mv = float(r.get("流通市值", 0)) if pd.notna(r.get("流通市值")) else 0

            result.update({
                "name": str(r.get("名称", "")),
                "price": round(float(r.get("最新价", 0)), 2) if pd.notna(r.get("最新价")) else None,
                "change_pct": round(float(r.get("涨跌幅", 0)), 2) if pd.notna(r.get("涨跌幅")) else None,
                "change_amount": round(float(r.get("涨跌额", 0)), 2) if pd.notna(r.get("涨跌额")) else None,
                "volume": int(float(r.get("成交量", 0))) if pd.notna(r.get("成交量")) else None,
                "amount": float(r.get("成交额", 0)) if pd.notna(r.get("成交额")) else None,
                "amplitude": round(float(r.get("振幅", 0)), 2) if pd.notna(r.get("振幅")) else None,
                "turnover_rate": round(float(r.get("换手率", 0)), 2) if pd.notna(r.get("换手率")) else None,
                "pe_ttm": round(float(r.get("市盈率-动态", 0)), 2) if pd.notna(r.get("市盈率-动态")) else None,
                "pb": round(float(r.get("市净率", 0)), 2) if pd.notna(r.get("市净率")) else None,
                "total_mv": total_mv,
                "total_mv_yi": round(total_mv / 1e8, 2) if total_mv else None,
                "circ_mv": circ_mv,
                "circ_mv_yi": round(circ_mv / 1e8, 2) if circ_mv else None,
                "volume_ratio": round(float(r.get("量比", 0)), 2) if pd.notna(r.get("量比")) else None,
                "high_5min": round(float(r.get("5分钟涨跌", 0)), 2) if pd.notna(r.get("5分钟涨跌")) else None,
                "speed_60d": round(float(r.get("60日涨跌幅", 0)), 2) if pd.notna(r.get("60日涨跌幅")) else None,
                "speed_ytd": round(float(r.get("年初至今涨跌幅", 0)), 2) if pd.notna(r.get("年初至今涨跌幅")) else None,
            })
        except Exception as e:
            logger.error(f"解析基本面数据失败 {code}: {e}")
            result["error"] = str(e)

        result["cache_time"] = self._cache_time.strftime("%Y-%m-%d %H:%M") if self._cache_time else None
        return result

    def get_fundamentals_batch(self, codes: list[str]) -> list:
        """批量获取基本面数据（从缓存读取，速度极快）"""
        if not self._ensure_cache():
            return [{"code": c, "error": "数据源不可用"} for c in codes]

        results = []
        for code in codes:
            code = code.strip().split(".")[0]
            results.append(self.get_fundamentals(code))
        return results

    def get_valuation_ranking(self, codes: list[str],
                               metric: str = "pe_ttm") -> dict:
        """获取股票估值排名

        Args:
            codes: 股票代码列表
            metric: 排名指标 (pe_ttm/pb)

        Returns:
            {"metric": "pe_ttm", "ranking": [{"code": ..., "value": ...}, ...]}
        """
        data = self.get_fundamentals_batch(codes)
        ranking = []
        for info in data:
            val = info.get(metric)
            if val is not None and val > 0:  # 排除负值（亏损）和0
                ranking.append({
                    "code": info["code"],
                    "name": info.get("name", ""),
                    "value": val,
                    "price": info.get("price"),
                    "change_pct": info.get("change_pct"),
                })

        # 按 metric 排序（PE/PB 越低越便宜）
        reverse = False
        ranking.sort(key=lambda x: x["value"], reverse=reverse)

        return {
            "metric": metric,
            "metric_name": {"pe_ttm": "市盈率(TTM)", "pb": "市净率"}.get(metric, metric),
            "ranking": ranking,
            "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
        }

    def get_market_overview(self) -> dict:
        """获取市场整体概况（从缓存统计）"""
        if not self._ensure_cache():
            return {"error": "数据源不可用"}

        df = self._cache
        try:
            return {
                "total_stocks": len(df),
                "avg_pe": round(float(df["市盈率-动态"].dropna().mean()), 2),
                "median_pe": round(float(df["市盈率-动态"].dropna().median()), 2),
                "avg_pb": round(float(df["市净率"].dropna().mean()), 2),
                "median_pb": round(float(df["市净率"].dropna().median()), 2),
                "total_market_cap_yi": round(float(df["总市值"].dropna().sum()) / 1e8, 0),
                "up_count": int((df["涨跌幅"] > 0).sum()),
                "down_count": int((df["涨跌幅"] < 0).sum()),
                "flat_count": int((df["涨跌幅"] == 0).sum()),
                "cache_time": self._cache_time.strftime("%Y-%m-%d %H:%M") if self._cache_time else None,
                "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_top_stocks(self, metric: str = "pe_ttm", n: int = 10,
                       ascending: bool = True) -> dict:
        """获取市场估值 Top N 股票

        Args:
            metric: 排名指标 (pe_ttm / pb / total_mv / turnover_rate / change_pct)
            n: 返回数量
            ascending: True=从低到高(最便宜), False=从高到低(最贵)

        Returns:
            {"metric": ..., "direction": "cheapest"/"most_expensive", "stocks": [...]}
        """
        if not self._ensure_cache():
            return {"error": "数据源不可用"}

        col_map = {
            "pe_ttm": "市盈率-动态",
            "pb": "市净率",
            "total_mv": "总市值",
            "turnover_rate": "换手率",
            "change_pct": "涨跌幅",
        }
        col = col_map.get(metric, "市盈率-动态")

        df = self._cache
        try:
            # 过滤掉 NaN 和 <= 0 的值（亏损股PE为负或0）
            valid = df[df[col].notna() & (df[col] > 0)].copy()
            valid = valid.sort_values(col, ascending=ascending).head(n)

            stocks = []
            for _, r in valid.iterrows():
                total_mv = float(r.get("总市值", 0)) if pd.notna(r.get("总市值")) else 0
                stocks.append({
                    "code": str(r.get("代码", "")),
                    "name": str(r.get("名称", "")),
                    "price": round(float(r.get("最新价", 0)), 2) if pd.notna(r.get("最新价")) else None,
                    "change_pct": round(float(r.get("涨跌幅", 0)), 2) if pd.notna(r.get("涨跌幅")) else None,
                    "pe_ttm": round(float(r.get("市盈率-动态", 0)), 2) if pd.notna(r.get("市盈率-动态")) else None,
                    "pb": round(float(r.get("市净率", 0)), 2) if pd.notna(r.get("市净率")) else None,
                    "total_mv_yi": round(total_mv / 1e8, 2) if total_mv else None,
                    "turnover_rate": round(float(r.get("换手率", 0)), 2) if pd.notna(r.get("换手率")) else None,
                })

            return {
                "metric": metric,
                "metric_name": {"pe_ttm": "市盈率(TTM)", "pb": "市净率",
                                "total_mv": "总市值", "turnover_rate": "换手率",
                                "change_pct": "涨跌幅"}.get(metric, metric),
                "direction": "cheapest" if ascending else "most_expensive",
                "count": len(stocks),
                "stocks": stocks,
                "cache_time": self._cache_time.strftime("%Y-%m-%d %H:%M") if self._cache_time else None,
                "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
            }
        except Exception as e:
            logger.error(f"获取Top股票失败: {e}")
            return {"error": str(e)}

    def get_market_breadth(self) -> dict:
        """获取市场涨跌分布详情（按涨幅区间统计）"""
        if not self._ensure_cache():
            return {"error": "数据源不可用"}

        df = self._cache
        try:
            change = df["涨跌幅"].dropna()
            return {
                "total": len(change),
                "up_count": int((change > 0).sum()),
                "down_count": int((change < 0).sum()),
                "flat_count": int((change == 0).sum()),
                "limit_up": int((change >= 9.8).sum()),
                "limit_down": int((change <= -9.8).sum()),
                "big_up": int(((change >= 5) & (change < 9.8)).sum()),
                "big_down": int(((change <= -5) & (change > -9.8)).sum()),
                "mid_up": int(((change >= 2) & (change < 5)).sum()),
                "mid_down": int(((change <= -2) & (change > -5)).sum()),
                "small_up": int(((change > 0) & (change < 2)).sum()),
                "small_down": int(((change < 0) & (change > -2)).sum()),
                "cache_time": self._cache_time.strftime("%Y-%m-%d %H:%M") if self._cache_time else None,
            }
        except Exception as e:
            return {"error": str(e)}


# 全局单例
fundamental_service = FundamentalService()
