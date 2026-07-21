"""
投研分析路由 — TradingAgents 多智能体分析入口
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from models.schemas import (
    AnalysisRequest,
    AnalysisTaskResponse,
    AnalysisStatus,
    StockSearchResponse,
    StockSearchResult,
)
from core.dependencies import get_current_user, require_quota, get_optional_user
from services.analysis_service import AnalysisService
from services.user_service import UserService

logger = logging.getLogger("mitouai.analysis")
router = APIRouter(prefix="/api/analysis", tags=["投研分析"])
analysis_service = AnalysisService()


@router.get("/search", response_model=StockSearchResponse)
async def search_stock(q: str = Query("", description="股票代码或名称")):
    """搜索股票（无需登录）"""
    if not q or len(q.strip()) < 1:
        return StockSearchResponse(results=[], total=0)
    results = analysis_service.search_stocks(q.strip())
    return StockSearchResponse(
        results=[StockSearchResult(**r) for r in results],
        total=len(results),
    )


@router.post("/start", response_model=AnalysisTaskResponse)
async def start_analysis(
    req: AnalysisRequest,
    user: dict = Depends(require_quota),
):
    """启动多智能体投研分析任务（需登录 + 配额）"""
    try:
        # 消耗配额
        usr_svc = UserService()
        usr_svc.consume_quota(user["id"])

        # 获取推送设置
        notifications = usr_svc.get_notification_settings(user["id"])
        pushplus_token = notifications.get("pushplus_token", "") if notifications.get("analysis_complete", True) else ""
        user_email = user.get("email", "")

        task = await analysis_service.start_analysis(
            ticker=req.ticker,
            trade_date=req.trade_date,
            debate_rounds=req.debate_rounds,
            risk_rounds=req.risk_rounds,
            strategy_id=req.strategy_id,
            model=req.model,
            user_id=user.get("id"),
            user_email=user_email,
            pushplus_token=pushplus_token,
        )
        return AnalysisTaskResponse(**task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析启动失败: {e}")


@router.get("/status/{task_id}", response_model=AnalysisTaskResponse)
async def get_analysis_status(task_id: str):
    """查询分析任务状态"""
    task = analysis_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return AnalysisTaskResponse(**task)


@router.get("/stream/{task_id}")
async def stream_analysis(task_id: str):
    """SSE 实时推送分析进度"""
    async def event_stream():
        async for event in analysis_service.stream_events(task_id):
            yield event
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/report/{task_id}")
async def get_report(task_id: str):
    """获取分析报告全文"""
    task = analysis_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="分析尚未完成")
    report = analysis_service.get_report(task_id)
    return {"task_id": task_id, "report": report}


@router.get("/history")
async def get_history(
    limit: int = Query(20, description="每页数量"),
    user: dict = Depends(get_current_user),
):
    """获取个人分析历史"""
    tasks = analysis_service.get_user_tasks(user.get("id"), limit)
    return {"tasks": tasks, "total": len(tasks)}
