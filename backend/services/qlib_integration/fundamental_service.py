"""
基本面数据服务 — 从 akshare 获取 A 股基本面指标

提供 PE/PB/PS/股息率/市值 等估值指标，用于策略小课堂的基本面展示。

⚠️ 合规声明：所有数据仅用于金融知识教育展示，不构成投资建议
"""
import logging
import time
from typing import Optional

import pandas as pd

logger = logging.getLogger("mitouai.qlib.fundamentals")


class FundamentalService:
    """A股基本面数据服务"""

    # 估值指标中文名映射
    INDICATOR_NAMES = {
        "pe_ttm": "市盈率(TTM)",
        "pb": "市净率",
        "ps_ttm": "市销率(TTM)",
        "dv_ratio": "股息率",
        "total_mv": "总市值",
    }

    def get_fundamentals(self, code: str) -> dict:
        """获取单只股票的基本面数据

        Args:
            code: 6位A股代码，如 600519

        Returns:
            {
                "code": "600519",
                "name": "贵州茅台",
                "pe_ttm": 30.5,
                "pb": 10.2,
                "ps_ttm": 15.8,
                "dv_ratio": 1.2,
                "total_mv": 200000000000,  # 元
                "total_mv_yi": 2000,  # 亿元
                "industry": "白酒",
                "disclaimer": "..."
            }
        """
        import akshare as ak

        result = {
            "code": code,
            "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
        }

        # 1. 获取实时行情中的 PE/PB/市值
        try:
            # stock_zh_a_spot_em 获取全部A股实时行情（含PE/PB）
            # 使用 stock_individual_info_em 获取个股信息
            df_spot = self._get_spot_data(code)
            if df_spot is not None and not df_spot.empty:
                result.update(df_spot)
        except Exception as e:
            logger.warning(f"获取实时行情失败 {code}: {e}")

        # 2. 获取估值历史数据（PE/PB/PS）
        try:
            val_data = self._get_valuation_history(code)
            if val_data:
                result["valuation_history"] = val_data
        except Exception as e:
            logger.warning(f"获取估值历史失败 {code}: {e}")

        # 3. 获取行业信息
        try:
            industry = self._get_industry(code)
            if industry:
                result["industry"] = industry
        except Exception as e:
            logger.warning(f"获取行业信息失败 {code}: {e}")

        return result

    def _get_spot_data(self, code: str) -> Optional[dict]:
        """从实时行情获取 PE/PB/市值"""
        import akshare as ak

        try:
            # stock_a_indicator_lg 提供 PE/PB/股息率
            df = ak.stock_a_indicator_lg(symbol=code)
            if df is not None and not df.empty:
                latest = df.iloc[-1].to_dict()
                return {
                    "pe_ttm": round(float(latest.get("pe_ttm", 0)), 2) if latest.get("pe_ttm") else None,
                    "pb": round(float(latest.get("pb", 0)), 2) if latest.get("pb") else None,
                    "ps_ttm": round(float(latest.get("ps_ttm", 0)), 2) if latest.get("ps_ttm") else None,
                    "dv_ratio": round(float(latest.get("dv_ratio", 0)), 2) if latest.get("dv_ratio") else None,
                    "dv_ttm": round(float(latest.get("dv_ttm", 0)), 2) if latest.get("dv_ttm") else None,
                    "total_mv": float(latest.get("total_mv", 0)) if latest.get("total_mv") else None,
                }
        except Exception as e:
            logger.debug(f"stock_a_indicator_lg 失败 {code}: {e}")

        # 降级方案：从 stock_zh_a_spot_em 获取
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                row = df[df["代码"] == code]
                if not row.empty:
                    r = row.iloc[0]
                    total_mv = float(r.get("总市值", 0)) if r.get("总市值") else 0
                    return {
                        "name": str(r.get("名称", "")),
                        "pe_ttm": round(float(r.get("市盈率-动态", 0)), 2) if r.get("市盈率-动态") else None,
                        "pb": round(float(r.get("市净率", 0)), 2) if r.get("市净率") else None,
                        "total_mv": total_mv,
                        "total_mv_yi": round(total_mv / 1e8, 2) if total_mv else None,
                        "price": round(float(r.get("最新价", 0)), 2) if r.get("最新价") else None,
                        "change_pct": round(float(r.get("涨跌幅", 0)), 2) if r.get("涨跌幅") else None,
                    }
        except Exception as e:
            logger.debug(f"stock_zh_a_spot_em 失败 {code}: {e}")

        return None

    def _get_valuation_history(self, code: str) -> Optional[list]:
        """获取 PE 历史数据（近1年）"""
        import akshare as ak

        try:
            # stock_zh_valuation_baidu 提供估值历史
            df = ak.stock_zh_valuation_baidu(
                symbol=code,
                indicator="市盈率(TTM)",
                period="近一年",
            )
            if df is not None and not df.empty:
                # 取最近30个数据点
                df = df.tail(30)
                return [
                    {"date": str(row.get("日期", "")),
                     "pe_ttm": round(float(row.get("值", 0)), 2)}
                    for _, row in df.iterrows()
                ]
        except Exception as e:
            logger.debug(f"stock_zh_valuation_baidu 失败 {code}: {e}")

        return None

    def _get_industry(self, code: str) -> Optional[str]:
        """获取股票所属行业"""
        import akshare as ak

        try:
            # stock_zyjs_ths 提供主营介绍和行业
            df = ak.stock_zyjs_ths(symbol=code)
            if df is not None and not df.empty:
                return str(df.iloc[0].get("行业", ""))
        except Exception as e:
            logger.debug(f"stock_zyjs_ths 失败 {code}: {e}")

        return None

    def get_fundamentals_batch(self, codes: list[str]) -> dict:
        """批量获取基本面数据"""
        results = {}
        for i, code in enumerate(codes):
            try:
                data = self.get_fundamentals(code)
                results[code] = data
                logger.info(f"[{i+1}/{len(codes)}] {code}: 基本面数据获取成功")
            except Exception as e:
                logger.error(f"[{i+1}/{len(codes)}] {code}: {e}")
                results[code] = {"code": code, "error": str(e)}
            if i < len(codes) - 1:
                time.sleep(0.3)
        return results

    def get_valuation_ranking(self, codes: list[str],
                               metric: str = "pe_ttm") -> dict:
        """获取股票估值排名

        Args:
            codes: 股票代码列表
            metric: 排名指标 (pe_ttm/pb/ps_ttm/dv_ratio)

        Returns:
            {"metric": "pe_ttm", "ranking": [{"code": ..., "value": ...}, ...]}
        """
        data = self.get_fundamentals_batch(codes)
        ranking = []
        for code, info in data.items():
            val = info.get(metric)
            if val is not None:
                ranking.append({"code": code, "name": info.get("name", ""), "value": val})

        # 按 metric 排序
        reverse = metric in ["dv_ratio", "dv_ttm"]  # 股息率越高越好
        ranking.sort(key=lambda x: x["value"], reverse=reverse)

        return {"metric": metric, "ranking": ranking}


# 全局单例
fundamental_service = FundamentalService()
