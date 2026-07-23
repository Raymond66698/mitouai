"""
Tushare Pro → PostgreSQL 数据同步管道

功能:
- 全量初始化: sync_stock_basic() + sync_daily() + sync_trade_cal() + sync_daily_basic()
- 增量更新: 仅拉取最近N天数据
- 重试 + 速率限制

数据流: Tushare API → PostgreSQL → Qlib .bin (因子计算)
"""
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from database import get_db_context
from models.tushare_models import StockBasic, DailyQuote, TradeCalendar, DailyBasic
from services.tushare_service import get_tushare

logger = logging.getLogger("mitouai.tushare.pipeline")


def _is_postgresql(db) -> bool:
    """判断是否是 PostgreSQL 数据库"""
    return "postgresql" in str(db.bind.url)


class TushareDataPipeline:
    """Tushare 数据同步管道"""

    def __init__(self):
        self._ts = get_tushare()
        self._progress_lock = threading.Lock()
        self._progress = {"current": 0, "total": 0, "status": "idle", "message": ""}

    # ═══════════════════════════════════════════════
    #  同步 - 股票基本信息
    # ═══════════════════════════════════════════════

    def sync_stock_basic(self) -> dict:
        """同步全部 A 股股票基本信息（全量覆盖）"""
        logger.info("=== 同步 stock_basic ===")
        start = time.time()

        df = self._ts.get_all_stock_basic()
        if df is None or len(df) == 0:
            return {"error": "stock_basic API 返回空数据"}

        # 确保列名符合模型
        col_map = {
            "ts_code": "ts_code", "symbol": "symbol", "name": "name",
            "fullname": "fullname", "enname": "enname", "area": "area",
            "industry": "industry", "market": "market", "exchange": "exchange",
            "list_status": "list_status", "list_date": "list_date",
            "delist_date": "delist_date",
        }
        # 只保留存在的列
        existing_cols = [c for c in col_map if c in df.columns]
        df = df[existing_cols].copy()

        with get_db_context() as db:
            pg = _is_postgresql(db)

            # 使用 upsert (INSERT ... ON CONFLICT DO UPDATE)
            records = df.to_dict("records")
            batch_size = 500
            total = len(records)

            for i in range(0, total, batch_size):
                batch = records[i:i + batch_size]
                if pg:
                    stmt = pg_insert(StockBasic).values(batch)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["ts_code"],
                        set_={
                            "name": stmt.excluded.name,
                            "fullname": stmt.excluded.fullname,
                            "area": stmt.excluded.area,
                            "industry": stmt.excluded.industry,
                            "list_status": stmt.excluded.list_status,
                            "delist_date": stmt.excluded.delist_date,
                            "updated_at": datetime.now(),
                        }
                    )
                else:
                    stmt = sqlite_insert(StockBasic).values(batch)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["ts_code"],
                        set_={
                            "name": stmt.excluded.name,
                            "fullname": stmt.excluded.fullname,
                            "area": stmt.excluded.area,
                            "industry": stmt.excluded.industry,
                            "list_status": stmt.excluded.list_status,
                            "delist_date": stmt.excluded.delist_date,
                            "updated_at": datetime.now(),
                        }
                    )
                db.execute(stmt)
                if (i + batch_size) % 2000 == 0 or i + batch_size >= total:
                    logger.info(f"  stock_basic: {min(i+batch_size, total)}/{total}")

            db.commit()

        elapsed = time.time() - start
        summary = {
            "table": "tushare_stock_basic",
            "total": total,
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info(f"stock_basic 同步完成: {total} 只, {elapsed:.1f}s")
        return summary

    # ═══════════════════════════════════════════════
    #  同步 - 交易日历
    # ═══════════════════════════════════════════════

    def sync_trade_cal(self, start_date: str = "", end_date: str = "") -> dict:
        """同步交易日历"""
        if not start_date:
            start_date = datetime.now().strftime("%Y0101")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=365)).strftime("%Y1231")

        logger.info(f"=== 同步 trade_cal: {start_date}~{end_date} ===")
        start = time.time()

        dfs = []
        for exchange in ["SSE", "SZSE"]:
            try:
                df = self._ts.get_trade_cal(exchange=exchange, start_date=start_date, end_date=end_date)
                if df is not None and len(df) > 0:
                    # 标准化列名
                    col_map = {
                        "exchange": "exchange", "cal_date": "cal_date",
                        "is_open": "is_open", "pretrade_date": "pretrade_date",
                    }
                    existing = [c for c in col_map if c in df.columns]
                    df = df[existing].copy()
                    dfs.append(df)
            except Exception as e:
                logger.error(f"trade_cal {exchange}: {e}")

        if not dfs:
            return {"error": "trade_cal 所有交易所均失败"}

        df_all = pd.concat(dfs, ignore_index=True)

        with get_db_context() as db:
            pg = _is_postgresql(db)
            records = df_all.to_dict("records")
            for batch_start in range(0, len(records), 1000):
                batch = records[batch_start:batch_start + 1000]
                if pg:
                    stmt = pg_insert(TradeCalendar).values(batch)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["cal_date", "exchange"],
                        set_={"is_open": stmt.excluded.is_open, "pretrade_date": stmt.excluded.pretrade_date},
                    )
                else:
                    stmt = sqlite_insert(TradeCalendar).values(batch)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["cal_date", "exchange"],
                        set_={"is_open": stmt.excluded.is_open, "pretrade_date": stmt.excluded.pretrade_date},
                    )
                db.execute(stmt)
            db.commit()

        elapsed = time.time() - start
        open_days = len(df_all[df_all.is_open == 1]) if "is_open" in df_all.columns else 0
        summary = {
            "table": "tushare_trade_cal",
            "total": len(df_all),
            "open_days": open_days,
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info(f"trade_cal 同步完成: {len(df_all)} 天, 交易日 {open_days}, {elapsed:.1f}s")
        return summary

    # ═══════════════════════════════════════════════
    #  同步 - 日线行情
    # ═══════════════════════════════════════════════

    def sync_daily(self, ts_code: str = "", start_date: str = "",
                   end_date: str = "", progress_callback: Optional[Callable] = None) -> dict:
        """同步日线行情

        如果不指定 ts_code，则自动获取全部上市股票并逐只拉取。
        Tushare 免费版单次最多返回约 4000 行，全市场需要逐只拉取。
        """
        if not start_date:
            # 默认从3年前开始（与 Qlib 因子计算对齐）
            start_date = (datetime.now() - timedelta(days=1095)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        logger.info(f"=== 同步 daily: {start_date}~{end_date} ===")
        start_ts = time.time()

        # 获取股票列表
        if ts_code:
            codes = [ts_code]
        else:
            with get_db_context() as db:
                stocks = db.query(StockBasic.ts_code).filter(
                    (StockBasic.list_status == "L") | (StockBasic.list_status == None)
                ).all()
                codes = [s.ts_code for s in stocks]

        if not codes:
            return {"error": "无可用股票列表，请先同步 stock_basic"}

        total = len(codes)
        success = 0
        failed = 0
        total_rows = 0

        with get_db_context() as db:
            pg = _is_postgresql(db)

            for i, code in enumerate(codes):
                try:
                    df = self._ts.get_daily(ts_code=code, start_date=start_date, end_date=end_date)
                    if df is None or len(df) == 0:
                        failed += 1
                        continue

                    # 标准化列名
                    col_map = {
                        "ts_code": "ts_code", "trade_date": "trade_date",
                        "open": "open", "high": "high", "low": "low", "close": "close",
                        "pre_close": "pre_close", "change": "change", "pct_chg": "pct_chg",
                        "vol": "vol", "amount": "amount",
                    }
                    existing = [c for c in col_map if c in df.columns]
                    df_sub = df[existing].copy()

                    # 填充 NaN
                    df_sub = df_sub.where(pd.notnull(df_sub), None)

                    records = df_sub.to_dict("records")
                    if pg:
                        stmt = pg_insert(DailyQuote).values(records)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["ts_code", "trade_date"],
                            set_={
                                "open": stmt.excluded.open,
                                "high": stmt.excluded.high,
                                "low": stmt.excluded.low,
                                "close": stmt.excluded.close,
                                "pre_close": stmt.excluded.pre_close,
                                "change": stmt.excluded.change,
                                "pct_chg": stmt.excluded.pct_chg,
                                "vol": stmt.excluded.vol,
                                "amount": stmt.excluded.amount,
                                "updated_at": datetime.now(),
                            }
                        )
                    else:
                        stmt = sqlite_insert(DailyQuote).values(records)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["ts_code", "trade_date"],
                            set_={
                                "open": stmt.excluded.open,
                                "high": stmt.excluded.high,
                                "low": stmt.excluded.low,
                                "close": stmt.excluded.close,
                                "pre_close": stmt.excluded.pre_close,
                                "change": stmt.excluded.change,
                                "pct_chg": stmt.excluded.pct_chg,
                                "vol": stmt.excluded.vol,
                                "amount": stmt.excluded.amount,
                                "updated_at": datetime.now(),
                            }
                        )
                    db.execute(stmt)
                    db.commit()

                    success += 1
                    total_rows += len(records)

                except Exception as e:
                    logger.error(f"daily {code}: {e}")
                    failed += 1
                    db.rollback()

                # 进度日志
                if (i + 1) % 100 == 0 or i + 1 == total:
                    elapsed = time.time() - start_ts
                    rate = (i + 1) / (elapsed + 1e-6)
                    eta = (total - i - 1) / (rate + 1e-6)
                    logger.info(f"  daily: {i+1}/{total} ({rate:.1f}只/s, 预计剩余 {eta:.0f}s)")

                if progress_callback:
                    progress_callback(i + 1, total, code, True)

        elapsed = time.time() - start_ts
        summary = {
            "table": "tushare_daily_quote",
            "total_stocks": total,
            "success": success,
            "failed": failed,
            "total_rows": total_rows,
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info(f"daily 同步完成: {success}/{total} 只, {total_rows} 行, {elapsed:.1f}s")
        return summary

    # ═══════════════════════════════════════════════
    #  同步 - 每日指标
    # ═══════════════════════════════════════════════

    def sync_daily_basic(self, start_date: str = "", end_date: str = "",
                         progress_callback: Optional[Callable] = None) -> dict:
        """同步每日指标（PE/PB/市值/换手率）

        按日期批量拉取，比逐只股票拉取更高效。
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=1095)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        logger.info(f"=== 同步 daily_basic: {start_date}~{end_date} ===")
        start_ts = time.time()

        # 获取交易日列表
        with get_db_context() as db:
            trade_dates = [
                row[0] for row in db.query(TradeCalendar.cal_date)
                .filter(TradeCalendar.is_open == True,
                        TradeCalendar.cal_date >= start_date,
                        TradeCalendar.cal_date <= end_date)
                .order_by(TradeCalendar.cal_date).all()
            ]

        if not trade_dates:
            # 如果没有交易日历，按自然天生成
            logger.warning("交易日历为空，按自然天拉取")
            trade_dates = [
                (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                for i in range(min(1095, 1095), 0, -1)
            ]

        total = len(trade_dates)
        total_rows = 0
        success = 0
        failed = 0

        with get_db_context() as db:
            pg = _is_postgresql(db)

            for i, td in enumerate(trade_dates):
                try:
                    df = self._ts.get_daily_basic(trade_date=td)
                    if df is None or len(df) == 0:
                        continue

                    col_map = {
                        "ts_code": "ts_code", "trade_date": "trade_date",
                        "close": "close", "turnover_rate": "turnover_rate",
                        "turnover_rate_f": "turnover_rate_f", "volume_ratio": "volume_ratio",
                        "pe": "pe", "pe_ttm": "pe_ttm", "pb": "pb",
                        "ps": "ps", "ps_ttm": "ps_ttm", "dv_ratio": "dv_ratio",
                        "dv_ttm": "dv_ttm", "total_share": "total_share",
                        "float_share": "float_share", "free_share": "free_share",
                        "total_mv": "total_mv", "circ_mv": "circ_mv",
                    }
                    existing = [c for c in col_map if c in df.columns]
                    df_sub = df[existing].copy()
                    df_sub = df_sub.where(pd.notnull(df_sub), None)

                    records = df_sub.to_dict("records")
                    if pg:
                        stmt = pg_insert(DailyBasic).values(records)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["ts_code", "trade_date"],
                            set_={
                                "close": stmt.excluded.close,
                                "turnover_rate": stmt.excluded.turnover_rate,
                                "turnover_rate_f": stmt.excluded.turnover_rate_f,
                                "volume_ratio": stmt.excluded.volume_ratio,
                                "pe": stmt.excluded.pe,
                                "pe_ttm": stmt.excluded.pe_ttm,
                                "pb": stmt.excluded.pb,
                                "ps": stmt.excluded.ps,
                                "ps_ttm": stmt.excluded.ps_ttm,
                                "dv_ratio": stmt.excluded.dv_ratio,
                                "dv_ttm": stmt.excluded.dv_ttm,
                                "total_share": stmt.excluded.total_share,
                                "float_share": stmt.excluded.float_share,
                                "free_share": stmt.excluded.free_share,
                                "total_mv": stmt.excluded.total_mv,
                                "circ_mv": stmt.excluded.circ_mv,
                                "updated_at": datetime.now(),
                            }
                        )
                    else:
                        stmt = sqlite_insert(DailyBasic).values(records)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["ts_code", "trade_date"],
                            set_={
                                "close": stmt.excluded.close,
                                "turnover_rate": stmt.excluded.turnover_rate,
                                "turnover_rate_f": stmt.excluded.turnover_rate_f,
                                "volume_ratio": stmt.excluded.volume_ratio,
                                "pe": stmt.excluded.pe,
                                "pe_ttm": stmt.excluded.pe_ttm,
                                "pb": stmt.excluded.pb,
                                "ps": stmt.excluded.ps,
                                "ps_ttm": stmt.excluded.ps_ttm,
                                "dv_ratio": stmt.excluded.dv_ratio,
                                "dv_ttm": stmt.excluded.dv_ttm,
                                "total_share": stmt.excluded.total_share,
                                "float_share": stmt.excluded.float_share,
                                "free_share": stmt.excluded.free_share,
                                "total_mv": stmt.excluded.total_mv,
                                "circ_mv": stmt.excluded.circ_mv,
                                "updated_at": datetime.now(),
                            }
                        )
                    db.execute(stmt)
                    db.commit()

                    success += 1
                    total_rows += len(records)

                except Exception as e:
                    logger.error(f"daily_basic {td}: {e}")
                    failed += 1
                    db.rollback()

                if (i + 1) % 30 == 0 or i + 1 == total:
                    elapsed = time.time() - start_ts
                    logger.info(f"  daily_basic: {i+1}/{total} 天, {total_rows} 行, {elapsed:.1f}s")

                if progress_callback:
                    progress_callback(i + 1, total, td, True)

        elapsed = time.time() - start_ts
        summary = {
            "table": "tushare_daily_basic",
            "total_dates": total,
            "success": success,
            "failed": failed,
            "total_rows": total_rows,
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info(f"daily_basic 同步完成: {success}/{total} 天, {total_rows} 行, {elapsed:.1f}s")
        return summary

    # ═══════════════════════════════════════════════
    #  全量初始化
    # ═══════════════════════════════════════════════

    def sync_all(self, daily_count: int = 0,
                 progress_callback: Optional[Callable] = None) -> dict:
        """执行全量数据初始化

        顺序: stock_basic → trade_cal → daily_basic → daily
        daily_count: 限制同步前N只股票（0=全部，用于测试）
        """
        logger.info("========================================")
        logger.info("  开始 Tushare 全量数据初始化")
        logger.info("========================================")
        start = time.time()

        results = {}

        # 1. 股票基本信息
        self._progress = {"current": 0, "total": 4, "status": "stock_basic", "message": "同步股票基本信息..."}
        if progress_callback:
            progress_callback("stock_basic", "同步股票基本信息...", 0)
        r = self.sync_stock_basic()
        results["stock_basic"] = r
        if "error" in r:
            return results

        # 2. 交易日历
        self._progress = {"current": 1, "total": 4, "status": "trade_cal", "message": "同步交易日历..."}
        if progress_callback:
            progress_callback("trade_cal", "同步交易日历...", 25)
        r = self.sync_trade_cal()
        results["trade_cal"] = r

        # 3. 每日指标
        self._progress = {"current": 2, "total": 4, "status": "daily_basic", "message": "同步每日指标(PE/PB/市值)..."}
        if progress_callback:
            progress_callback("daily_basic", "同步每日指标...", 50)
        r = self.sync_daily_basic()
        results["daily_basic"] = r

        # 4. 日线行情
        self._progress = {"current": 3, "total": 4, "status": "daily", "message": "同步日线行情..."}
        if progress_callback:
            progress_callback("daily", "同步日线行情...", 75)
        r = self.sync_daily()
        results["daily"] = r

        self._progress = {"current": 4, "total": 4, "status": "done", "message": "全量初始化完成"}
        if progress_callback:
            progress_callback("done", "全量初始化完成", 100)

        elapsed = time.time() - start
        results["total_elapsed_seconds"] = round(elapsed, 1)
        logger.info(f"========================================")
        logger.info(f"  全量初始化完成! 总耗时 {elapsed:.1f}s")
        logger.info(f"========================================")
        return results

    # ═══════════════════════════════════════════════
    #  增量更新 (每日盘后调用)
    # ═══════════════════════════════════════════════

    def sync_daily_incremental(self, days_back: int = 5) -> dict:
        """增量更新日线行情（最近N天）"""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        return self.sync_daily(start_date=start_date)

    def sync_daily_basic_incremental(self, days_back: int = 5) -> dict:
        """增量更新每日指标（最近N天）"""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        return self.sync_daily_basic(start_date=start_date)

    # ═══════════════════════════════════════════════
    #  状态查询
    # ═══════════════════════════════════════════════

    def get_stats(self) -> dict:
        """获取数据同步状态"""
        with get_db_context() as db:
            stock_count = db.query(StockBasic).count()
            quote_count = db.query(DailyQuote).count()
            cal_count = db.query(TradeCalendar).count()
            basic_count = db.query(DailyBasic).count()

            # 最新交易日期
            latest_quote = db.query(DailyQuote.trade_date)\
                .order_by(DailyQuote.trade_date.desc()).first()
            latest_basic = db.query(DailyBasic.trade_date)\
                .order_by(DailyBasic.trade_date.desc()).first()

        return {
            "stocks": stock_count,
            "daily_quotes": quote_count,
            "trade_calendars": cal_count,
            "daily_basics": basic_count,
            "latest_quote_date": latest_quote[0] if latest_quote else None,
            "latest_basic_date": latest_basic[0] if latest_basic else None,
            "progress": self._progress,
        }

    def get_progress(self) -> dict:
        """获取当前同步进度"""
        return self._progress


# 全局单例
_pipeline_instance = None


def get_pipeline() -> TushareDataPipeline:
    """获取数据管道单例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = TushareDataPipeline()
    return _pipeline_instance
