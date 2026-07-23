"""
Qlib 因子计算服务 — 觅投AI Phase 1

提供:
- Alpha158 因子计算（基于 Qlib 原生表达式引擎）
- 因子列表查询（含中文教学描述）
- 多股票因子对比
- 数据管道管理（拉取/更新/状态查询）
"""
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("mitouai.qlib.service")

# Qlib 数据目录
QLIB_DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "qlib_data")

# 单例锁
_init_lock = threading.Lock()
_qlib_initialized = False


def _ensure_qlib_init():
    """确保 Qlib 已初始化（线程安全，只初始化一次）"""
    global _qlib_initialized
    if _qlib_initialized:
        return
    with _init_lock:
        if _qlib_initialized:
            return
        try:
            import qlib
            qlib.init(provider_uri=QLIB_DATA_DIR, region="cn")
            _qlib_initialized = True
            logger.info("Qlib 初始化完成 (provider_uri=%s)", QLIB_DATA_DIR)
        except Exception as e:
            logger.error(f"Qlib 初始化失败: {e}")
            raise


class QlibFactorService:
    """Alpha158 因子计算服务"""

    def __init__(self):
        self._data_dir = QLIB_DATA_DIR
        self._pipeline = None

    @property
    def pipeline(self):
        """懒加载数据管道"""
        if self._pipeline is None:
            from .data_pipeline import QlibDataPipeline
            self._pipeline = QlibDataPipeline(self._data_dir)
        return self._pipeline

    # ═══════════════════════════════════════════════
    #  因子列表
    # ═══════════════════════════════════════════════

    def list_factors(self, category: str = None) -> list[dict]:
        """获取因子列表（含教学描述）

        Args:
            category: 筛选类别（price/momentum/trend/volatility/...），None=全部

        Returns:
            [{"name", "category", "category_label", "formula", "desc", "teaching"}, ...]
        """
        from .factor_descriptions import (
            FACTOR_DESCRIPTIONS, FACTOR_CATEGORIES, get_category_summary
        )

        results = []
        for name, info in FACTOR_DESCRIPTIONS.items():
            if category and info["category"] != category:
                continue
            results.append({
                "name": name,
                "category": info["category"],
                "category_label": FACTOR_CATEGORIES.get(info["category"], info["category"]),
                "formula": info["formula"],
                "desc": info["desc"],
                "teaching": info["teaching"],
            })
        return results

    def list_categories(self) -> dict:
        """获取因子类别统计"""
        from .factor_descriptions import get_category_summary
        return get_category_summary()

    # ═══════════════════════════════════════════════
    #  因子计算
    # ═══════════════════════════════════════════════

    def calculate_factors(self, ticker: str, factor_names: list[str] = None,
                          start_date: str = None, end_date: str = None,
                          last_n: int = 0) -> dict:
        """计算指定股票的 Alpha158 因子

        Args:
            ticker: 股票代码（如 600519.SS 或 600519）
            factor_names: 指定因子名列表，None=全部158个
            start_date: 开始日期
            end_date: 结束日期
            last_n: 只返回最近N天的数据（0=全部）

        Returns:
            {"ticker", "factors": [{"name", "value", "desc", ...}], "dates": [...], "matrix": [...]}
        """
        _ensure_qlib_init()
        from qlib.data import D
        from qlib.contrib.data.loader import Alpha158DL
        from .data_pipeline import to_qlib_symbol
        from .factor_descriptions import FACTOR_DESCRIPTIONS, FACTOR_CATEGORIES

        # 转换代码格式
        code = ticker.split(".")[0]
        symbol = to_qlib_symbol(code)

        # 获取因子配置
        all_fields, all_names = Alpha158DL.get_feature_config()

        # 筛选因子
        if factor_names:
            field_map = dict(zip(all_names, all_fields))
            selected_fields = []
            selected_names = []
            for name in factor_names:
                if name in field_map:
                    selected_fields.append(field_map[name])
                    selected_names.append(name)
            if not selected_fields:
                return {"error": f"未找到指定因子: {factor_names}"}
        else:
            selected_fields = all_fields
            selected_names = all_names

        # 默认日期范围
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 计算因子
        try:
            factor_df = D.features(
                [symbol], selected_fields,
                start_time=start_date, end_time=end_date,
            )
        except Exception as e:
            return {"error": f"因子计算失败: {e}", "ticker": ticker}

        if factor_df is None or factor_df.empty:
            return {"error": f"无数据，请先拉取 {ticker} 的行情数据",
                    "ticker": ticker, "hint": "使用 POST /api/quant/data/refresh 接口拉取数据"}

        factor_df.columns = selected_names

        # 只取最近N天
        if last_n > 0 and len(factor_df) > last_n:
            factor_df = factor_df.tail(last_n)

        # 构建返回数据
        dates = [str(d)[:10] for d in factor_df.index.get_level_values("datetime")]

        # 最新一日的因子值
        latest = factor_df.iloc[-1]
        factors = []
        for name in selected_names:
            info = FACTOR_DESCRIPTIONS.get(name, {})
            factors.append({
                "name": name,
                "value": round(float(latest[name]), 6) if pd.notna(latest[name]) else None,
                "category": info.get("category", "other"),
                "category_label": FACTOR_CATEGORIES.get(info.get("category", ""), "其他"),
                "desc": info.get("desc", name),
                "teaching": info.get("teaching", ""),
            })

        # 时间序列矩阵（用于前端图表）
        matrix = {}
        for name in selected_names:
            values = factor_df[name].values
            matrix[name] = {
                "dates": dates,
                "values": [round(float(v), 6) if pd.notna(v) else None for v in values],
            }

        return {
            "ticker": ticker,
            "symbol": symbol,
            "date": dates[-1] if dates else "",
            "date_range": {"start": dates[0] if dates else "", "end": dates[-1] if dates else ""},
            "total_factors": len(factors),
            "factors": factors,
            "time_series": matrix,
            "trading_days": len(dates),
        }

    def compare_factors(self, tickers: list[str], factor_name: str,
                        start_date: str = None, end_date: str = None,
                        last_n: int = 30) -> dict:
        """多股票单因子对比

        Args:
            tickers: 股票代码列表
            factor_name: 要对比的因子名
            last_n: 最近N天

        Returns:
            {"factor": factor_name, "stocks": [{"ticker", "values": [...]}], "dates": [...]}
        """
        _ensure_qlib_init()
        from qlib.data import D
        from qlib.contrib.data.loader import Alpha158DL
        from .data_pipeline import to_qlib_symbol
        from .factor_descriptions import FACTOR_DESCRIPTIONS, FACTOR_CATEGORIES

        all_fields, all_names = Alpha158DL.get_feature_config()
        if factor_name not in all_names:
            return {"error": f"未知因子: {factor_name}"}

        field_idx = all_names.index(factor_name)
        field_expr = all_fields[field_idx]

        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        symbols = []
        for ticker in tickers:
            code = ticker.split(".")[0]
            symbols.append(to_qlib_symbol(code))

        try:
            df = D.features(symbols, [field_expr],
                           start_time=start_date, end_time=end_date)
        except Exception as e:
            return {"error": f"对比计算失败: {e}"}

        if df is None or df.empty:
            return {"error": "无数据"}

        df.columns = [factor_name]

        # 最近N天
        if last_n > 0:
            # 按日期取最近N个交易日
            all_dates = sorted(df.index.get_level_values("datetime").unique())
            recent_dates = all_dates[-last_n:]
            df = df[df.index.get_level_values("datetime").isin(recent_dates)]

        dates = sorted(set(str(d)[:10] for d in df.index.get_level_values("datetime")))

        stocks = []
        for ticker, symbol in zip(tickers, symbols):
            try:
                stock_data = df.loc[symbol]
                stock_dates = [str(d)[:10] for d in stock_data.index]
                stock_values = [round(float(v), 6) if pd.notna(v) else None
                               for v in stock_data[factor_name].values]
                stocks.append({
                    "ticker": ticker,
                    "symbol": symbol,
                    "values": stock_values,
                    "dates": stock_dates,
                })
            except KeyError:
                stocks.append({"ticker": ticker, "symbol": symbol, "values": [], "dates": []})

        info = FACTOR_DESCRIPTIONS.get(factor_name, {})
        return {
            "factor": factor_name,
            "desc": info.get("desc", factor_name),
            "teaching": info.get("teaching", ""),
            "category": info.get("category", ""),
            "category_label": FACTOR_CATEGORIES.get(info.get("category", ""), ""),
            "dates": dates,
            "stocks": stocks,
        }

    # ═══════════════════════════════════════════════
    #  数据管道管理
    # ═══════════════════════════════════════════════

    def refresh_data(self, tickers: list[str], start_date: str = "",
                     end_date: str = "") -> dict:
        """拉取/更新股票数据"""
        results = {"success": [], "failed": []}
        for ticker in tickers:
            code = ticker.split(".")[0]
            result = self.pipeline.dump_single(code, start_date, end_date)
            if result.get("success"):
                results["success"].append({
                    "ticker": ticker,
                    "symbol": result.get("symbol"),
                    "records": result.get("records"),
                    "date_range": result.get("date_range"),
                })
            else:
                results["failed"].append({
                    "ticker": ticker,
                    "error": result.get("error"),
                })
        # 重置 Qlib 初始化状态，让下次调用重新加载
        global _qlib_initialized
        _qlib_initialized = False
        return results

    def get_data_status(self) -> dict:
        """获取数据管道状态"""
        return self.pipeline.get_status()

    def get_available_stocks(self) -> list[dict]:
        """获取已有数据的股票列表"""
        status = self.pipeline.get_status()
        return status.get("instruments", [])


# 全局单例
qlib_factor_service = QlibFactorService()
