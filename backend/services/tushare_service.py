"""
Tushare Pro SDK 封装服务

功能:
- 统一速率限制 (200次/分钟 = ~0.3s/次)
- 重试机制 (3次, 指数退避)
- 封装常用数据接口

依赖: pip install tushare
"""
import logging
import time
import threading
from typing import Optional

import tushare as ts

logger = logging.getLogger("mitouai.tushare")

# Tushare 速率限制: 免费版 200次/分钟 → ~0.3s/次，留余量用0.35s
DEFAULT_RATE_LIMIT = 0.35
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 秒


class TushareService:
    """Tushare Pro 数据服务（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, token: str | None = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, token: str | None = None):
        if self._initialized:
            return
        if not token:
            from config import settings
            token = getattr(settings, 'TUSHARE_TOKEN', '')
            if not token:
                raise ValueError("TUSHARE_TOKEN 未配置")

        self._pro = ts.pro_api(token)
        self._last_call = time.monotonic()
        self._min_interval = DEFAULT_RATE_LIMIT
        self._initialized = True
        logger.info("TushareService 初始化完成")

    @property
    def pro(self):
        """获取 ts.pro_api 实例（自动速率限制）"""
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()
        return self._pro

    def _call_with_retry(self, func, func_name: str, **kwargs):
        """带重试机制的 API 调用"""
        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                result = func(**kwargs)
                return result
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BASE_DELAY * (attempt + 1)
                    logger.warning(f"[{func_name}] 第{attempt+1}次调用失败, {wait}s后重试: {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"[{func_name}] {MAX_RETRIES}次重试均失败: {e}")
        raise last_err

    # ═══════════════════════════════════════════════
    #  股票基本信息
    # ═══════════════════════════════════════════════

    def get_stock_basic(self, exchange: str = "", list_status: str = "L",
                        fields: str = "ts_code,symbol,name,area,industry,list_date,list_status,fullname,enname,market,exchange,delist_date") -> "pd.DataFrame":
        """获取股票基本信息列表

        Args:
            exchange: 交易所代码 (SSE上交所/SZSE深交所/BSE北交所), 空=全部
            list_status: L=上市, D=退市, P=暂停上市
        """
        return self._call_with_retry(
            self.pro.query, "stock_basic",
            api_name="stock_basic",
            exchange=exchange,
            list_status=list_status,
            fields=fields,
        )

    # ═══════════════════════════════════════════════
    #  日线行情
    # ═══════════════════════════════════════════════

    def get_daily(self, ts_code: str = "", trade_date: str = "",
                  start_date: str = "", end_date: str = "",
                  fields: str = "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount") -> "pd.DataFrame":
        """获取日线行情数据

        Args:
            ts_code: 股票代码 (如 000001.SZ), 空=全市场
            trade_date: 交易日期 (YYYYMMDD)
            start_date: 起始日期
            end_date: 结束日期
        """
        kwargs = {"api_name": "daily", "fields": fields}
        if ts_code:
            kwargs["ts_code"] = ts_code
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        return self._call_with_retry(self.pro.query, "daily", **kwargs)

    # ═══════════════════════════════════════════════
    #  交易日历
    # ═══════════════════════════════════════════════

    def get_trade_cal(self, exchange: str = "SSE",
                      start_date: str = "", end_date: str = "",
                      fields: str = "exchange,cal_date,is_open,pretrade_date") -> "pd.DataFrame":
        """获取交易日历"""
        return self._call_with_retry(
            self.pro.query, "trade_cal",
            api_name="trade_cal",
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
        )

    # ═══════════════════════════════════════════════
    #  每日指标 (PE/PB/市值/换手率等)
    # ═══════════════════════════════════════════════

    def get_daily_basic(self, ts_code: str = "", trade_date: str = "",
                        start_date: str = "", end_date: str = "",
                        fields: str = "ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv") -> "pd.DataFrame":
        """获取每日指标（PE/PB/市值/换手率等）"""
        kwargs = {"api_name": "daily_basic", "fields": fields}
        if ts_code:
            kwargs["ts_code"] = ts_code
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        return self._call_with_retry(self.pro.query, "daily_basic", **kwargs)

    # ═══════════════════════════════════════════════
    #  财务数据 (利润表/资产负债表/现金流量表)
    # ═══════════════════════════════════════════════

    def get_income(self, ts_code: str, start_date: str = "", end_date: str = "",
                   period: str = "", fields: str = "") -> "pd.DataFrame":
        """获取利润表"""
        kwargs = {"api_name": "income", "ts_code": ts_code}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        if period:
            kwargs["period"] = period
        if fields:
            kwargs["fields"] = fields
        return self._call_with_retry(self.pro.query, "income", **kwargs)

    def get_balancesheet(self, ts_code: str, start_date: str = "", end_date: str = "",
                         period: str = "", fields: str = "") -> "pd.DataFrame":
        """获取资产负债表"""
        kwargs = {"api_name": "balancesheet", "ts_code": ts_code}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        if period:
            kwargs["period"] = period
        if fields:
            kwargs["fields"] = fields
        return self._call_with_retry(self.pro.query, "balancesheet", **kwargs)

    def get_cashflow(self, ts_code: str, start_date: str = "", end_date: str = "",
                     period: str = "", fields: str = "") -> "pd.DataFrame":
        """获取现金流量表"""
        kwargs = {"api_name": "cashflow", "ts_code": ts_code}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        if period:
            kwargs["period"] = period
        if fields:
            kwargs["fields"] = fields
        return self._call_with_retry(self.pro.query, "cashflow", **kwargs)

    # ═══════════════════════════════════════════════
    #  复权因子 / 前复权K线
    # ═══════════════════════════════════════════════

    def get_adj_factor(self, ts_code: str = "", trade_date: str = "",
                       start_date: str = "", end_date: str = ""):
        """获取复权因子"""
        kwargs = {"api_name": "adj_factor"}
        if ts_code:
            kwargs["ts_code"] = ts_code
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        return self._call_with_retry(self.pro.query, "adj_factor", **kwargs)

    # ═══════════════════════════════════════════════
    #  股票列表（全量，包含沪/深/北交所）
    # ═══════════════════════════════════════════════

    def get_all_stock_basic(self) -> "pd.DataFrame":
        """获取全部 A 股上市股票（沪+深+北）"""
        dfs = []
        for exchange in ["SSE", "SZSE", "BSE"]:
            try:
                df = self.get_stock_basic(exchange=exchange)
                if df is not None and len(df) > 0:
                    dfs.append(df)
                    logger.info(f"{exchange}: {len(df)} 只")
            except Exception as e:
                logger.error(f"{exchange} 获取失败: {e}")
        if not dfs:
            return pd.DataFrame()
        import pandas as pd
        return pd.concat(dfs, ignore_index=True)

    # ═══════════════════════════════════════════════
    #  工具方法
    # ═══════════════════════════════════════════════

    def get_token_info(self) -> dict:
        """获取 Token 使用信息（余量+等级）"""
        # Tushare 没有直接的 token info API，通过 stock_basic limit=1 测试
        try:
            df = self.get_stock_basic(limit=1)
            return {"status": "ok", "sample_stocks": len(df) if df is not None else 0}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# 全局单例获取
_svc_instance = None


def get_tushare() -> TushareService:
    """获取 Tushare 服务单例"""
    global _svc_instance
    if _svc_instance is None:
        _svc_instance = TushareService()
    return _svc_instance
