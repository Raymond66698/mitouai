"""
每日盘后增量同步脚本 — 由 crontab 在每个交易日 16:30 调用

功能:
1. 增量同步日线行情（最近5天，覆盖节假日）
2. 增量同步每日指标（最近5天）
3. 增量刷新 Qlib .bin 数据（最近30天成分股）
4. 写入日志到 /opt/mitouai/logs/

用法: python3 sync_incremental.py
"""
import sys, os, logging, time
from datetime import datetime

# 确保 backend 在 path 中
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# 日志配置
log_dir = "/opt/mitouai/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"incremental_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8'),
    ],
)
logger = logging.getLogger("incremental_sync")

# 强制设置环境变量
os.environ.setdefault("DATABASE_URL", "postgresql://mitouai:Mitouai%402026%21@127.0.0.1:5432/mitouai")
os.environ.setdefault("TUSHARE_TOKEN", "3e29e21d6ea34793cc84d1a0fc20905d70a5f4ef81e8055fbe4113fc")

from services.data_pipeline_tushare import TushareDataPipeline
from database import get_db_context
from models.tushare_models import TradeCalendar

def is_trading_day() -> bool:
    """检查今天是否是交易日"""
    today = datetime.now().strftime("%Y%m%d")
    with get_db_context() as db:
        cal = db.query(TradeCalendar).filter(
            TradeCalendar.cal_date == today,
            TradeCalendar.is_open == True,
        ).first()
    if cal:
        logger.info(f"今日 {today} 是交易日，开始增量同步")
        return True
    else:
        logger.info(f"今日 {today} 非交易日，跳过同步")
        return False

def main():
    logger.info("=" * 50)
    logger.info("  开始每日增量同步")
    logger.info("=" * 50)
    start = time.time()

    # 非交易日跳过
    if not is_trading_day():
        logger.info("非交易日，退出。")
        return

    pipeline = TushareDataPipeline()

    # 1. 增量同步日线行情（最近5天）
    logger.info("--- 1. 增量同步日线行情 ---")
    r1 = pipeline.sync_daily_incremental(days_back=5)
    logger.info(f"日线增量结果: {r1}")

    # 2. 增量同步每日指标（最近5天）
    logger.info("--- 2. 增量同步每日指标 ---")
    r2 = pipeline.sync_daily_basic_incremental(days_back=5)
    logger.info(f"指标增量结果: {r2}")

    # 3. 增量刷新 Qlib .bin 数据
    logger.info("--- 3. 增量刷新 Qlib .bin 数据 ---")
    try:
        from services.qlib_integration.data_pipeline import QlibDataPipeline
        from models.tushare_models import StockBasic

        # 获取沪深300成分股（Qlib因子计算用）
        with get_db_context() as db:
            stocks = db.query(StockBasic.ts_code, StockBasic.symbol).filter(
                StockBasic.list_status == "L"
            ).limit(300).all()
            codes = [s.symbol for s in stocks]

        qlib_pipeline = QlibDataPipeline(qlib_data_dir="/opt/mitouai/backend/qlib_data")
        r3 = qlib_pipeline.refresh_from_tushare_db(codes, days_back=30)
        logger.info(f"Qlib刷新结果: {r3}")
    except Exception as e:
        logger.error(f"Qlib刷新失败: {e}")
        r3 = {"error": str(e)}

    elapsed = time.time() - start
    logger.info("=" * 50)
    logger.info(f"  增量同步完成! 总耗时 {elapsed:.1f}s ({elapsed/60:.1f}min)")
    logger.info("=" * 50)

    # 汇总
    summary = {
        "daily": r1,
        "daily_basic": r2,
        "qlib": r3,
        "elapsed_seconds": round(elapsed, 1),
    }
    logger.info(f"SUMMARY: {summary}")

if __name__ == "__main__":
    main()
