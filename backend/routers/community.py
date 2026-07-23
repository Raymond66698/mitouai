"""策略社区路由"""
import json
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from services.community_service import community_service

router = APIRouter()


class ShareStrategyRequest(BaseModel):
    name: str
    description: str = ""
    conditions: dict = {}
    backtest: dict = {}
    strategy_id: str = None


class AddCommentRequest(BaseModel):
    content: str


@router.get("/strategies")
async def list_community_strategies(
    sort: str = Query("likes", description="排序: likes/newest/usage"),
    limit: int = Query(20),
    offset: int = Query(0),
):
    """获取社区策略列表"""
    return community_service.get_community_strategies(sort=sort, limit=limit, offset=offset)


@router.get("/strategies/{strategy_id}")
async def get_strategy_detail(strategy_id: str):
    """获取策略详情"""
    detail = community_service.get_strategy_detail(strategy_id)
    if not detail:
        return {"error": "策略不存在"}
    return detail


@router.post("/strategies/share")
async def share_strategy(req: ShareStrategyRequest, request: Request):
    """分享策略到社区"""
    # 从认证上下文获取 user_id（简化处理，实际从 token 解析）
    user_id = "demo_user"
    try:
        auth = request.headers.get("authorization", "")
        if auth:
            user_id = auth.replace("Bearer ", "")[:12]
    except:
        pass
    return community_service.share_strategy(
        user_id=user_id,
        name=req.name,
        description=req.description,
        conditions=req.conditions,
        backtest=req.backtest,
        strategy_id=req.strategy_id,
    )


@router.post("/strategies/{strategy_id}/like")
async def like_strategy(strategy_id: str, request: Request):
    """点赞策略"""
    user_id = "demo_user"
    try:
        auth = request.headers.get("authorization", "")
        if auth:
            user_id = auth.replace("Bearer ", "")[:12]
    except:
        pass
    return community_service.like_strategy(strategy_id, user_id)


@router.post("/strategies/{strategy_id}/comments")
async def add_comment(strategy_id: str, req: AddCommentRequest, request: Request):
    """添加评论"""
    user_id = "demo_user"
    user_name = "觅投用户"
    try:
        auth = request.headers.get("authorization", "")
        if auth:
            user_id = auth.replace("Bearer ", "")[:12]
    except:
        pass
    return community_service.add_comment(strategy_id, user_id, user_name, req.content)
