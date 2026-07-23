"""
Tushare 数据管理 API 路由

提供:
- POST /api/tushare/sync/stock-basic    同步股票基本信息
- POST /api/tushare/sync/daily           同步日线行情
- POST /api/tushare/sync/daily-basic     同步每日指标
- POST /api/tushare/sync/trade-cal       同步交易日历
- POST /api/tushare/sync/all             全量初始化
- GET  /api/tushare/stats                数据同步状态
"""
import threading
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException

from services.data_pipeline_tushare import get_pipeline

logger = logging.getLogger("mitouai.routers.tushare")

router = APIRouter(tags=["Tushare数据管理"])

# 同步锁，防止并发执行
_sync_lock = threading.Lock()
_sync_running = False


def _run_sync(func_name: str):
    """后台执行同步任务"""
    global _sync_running
    try:
        _sync_running = True
        pipeline = get_pipeline()
        if func_name == "stock_basic":
            pipeline.sync_stock_basic()
        elif func_name == "daily":
            pipeline.sync_daily()
        elif func_name == "daily_basic":
            pipeline.sync_daily_basic()
        elif func_name == "trade_cal":
            pipeline.sync_trade_cal()
        elif func_name == "all":
            pipeline.sync_all()
        elif func_name == "daily_incremental":
            pipeline.sync_daily_incremental()
        logger.info(f"后台同步完成: {func_name}")
    except Exception as e:
        logger.error(f"后台同步失败 [{func_name}]: {e}")
    finally:
        _sync_running = False


@router.get("/stats")
async def get_stats():
    """获取数据同步状态"""
    return get_pipeline().get_stats()


@router.post("/sync/stock-basic")
async def sync_stock_basic(background_tasks: BackgroundTasks):
    """同步股票基本信息"""
    if _sync_running:
        raise HTTPException(409, "已有同步任务正在执行，请稍后再试")
    background_tasks.add_task(_run_sync, "stock_basic")
    return {"message": "stock_basic 同步已加入后台执行", "status": "started"}


@router.post("/sync/daily")
async def sync_daily(background_tasks: BackgroundTasks,
                     ts_code: str = "", days_back: int = 0):
    """同步日线行情

    Args:
        ts_code: 指定股票代码 (空=全部)
        days_back: 最近N天增量 (0=3年全量)
    """
    if _sync_running:
        raise HTTPException(409, "已有同步任务正在执行，请稍后再试")

    if days_back > 0:
        # 增量更新
        def run():
            try:
                global _sync_running
                _sync_running = True
                get_pipeline().sync_daily_incremental(days_back)
            finally:
                _sync_running = False
        background_tasks.add_task(run)
        return {"message": f"daily 增量同步(最近{days_back}天)已加入后台执行", "status": "started"}
    else:
        background_tasks.add_task(_run_sync, "daily")
        return {"message": "daily 全量同步已加入后台执行", "status": "started"}


@router.post("/sync/daily-basic")
async def sync_daily_basic(background_tasks: BackgroundTasks):
    """同步每日指标 (PE/PB/市值/换手率)"""
    if _sync_running:
        raise HTTPException(409, "已有同步任务正在执行，请稍后再试")
    background_tasks.add_task(_run_sync, "daily_basic")
    return {"message": "daily_basic 同步已加入后台执行", "status": "started"}


@router.post("/sync/trade-cal")
async def sync_trade_cal(background_tasks: BackgroundTasks):
    """同步交易日历"""
    if _sync_running:
        raise HTTPException(409, "已有同步任务正在执行，请稍后再试")
    background_tasks.add_task(_run_sync, "trade_cal")
    return {"message": "trade_cal 同步已加入后台执行", "status": "started"}


@router.post("/sync/all")
async def sync_all(background_tasks: BackgroundTasks):
    """全量初始化 (stock_basic → trade_cal → daily_basic → daily)"""
    if _sync_running:
        raise HTTPException(409, "已有同步任务正在执行，请稍后再试")
    background_tasks.add_task(_run_sync, "all")
    return {
        "message": "全量同步已加入后台执行",
        "order": ["stock_basic", "trade_cal", "daily_basic", "daily"],
        "note": "全量约需30-60分钟 (取决于股票数量)，请通过 GET /stats 查看进度",
        "status": "started",
    }


@router.post("/sync/incremental")
async def sync_incremental(background_tasks: BackgroundTasks, days_back: int = 5):
    """增量更新（盘后调用）"""
    if _sync_running:
        raise HTTPException(409, "已有同步任务正在执行，请稍后再试")

    def run():
        try:
            global _sync_running
            _sync_running = True
            pipeline = get_pipeline()
            pipeline.sync_daily_incremental(days_back)
            pipeline.sync_daily_basic_incremental(days_back)
        finally:
            _sync_running = False

    background_tasks.add_task(run)
    return {"message": f"增量同步(最近{days_back}天)已加入后台执行", "status": "started"}
