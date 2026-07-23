"""
觅投AI (mitouai) — 主入口
FastAPI 应用，多模块：投研分析 / 策略超市 / 用户管理 / 行情数据 / 订阅 / 通知
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import analysis, strategies, market, users, auth, subscriptions, notifications, screener, backtest, daily_brief, watchlist, research, hkus, capital_flow, industry_chain, community, tokens, quant, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("mitouai")
    logger.info(f"  {settings.PROJECT_TITLE} v{settings.VERSION} 启动中...")
    logger.info(f"  默认模型: {settings.DEFAULT_MODEL}")
    logger.info(f"  订阅套餐: {len(settings.SUBSCRIPTION_PLANS)} 个")
    # 确保 data 目录存在
    from pathlib import Path
    Path("data").mkdir(parents=True, exist_ok=True)
    yield
    logger.info("  觅投AI 关闭")


app = FastAPI(
    title=settings.PROJECT_TITLE,
    version=settings.VERSION,
    description="AI驱动的多智能体投资分析平台 — 策略超市 + 大师方法论 + 量化因子 + 订阅服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["投研分析"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["策略超市"])
app.include_router(market.router, prefix="/api/market", tags=["行情数据"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["订阅"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知"])
app.include_router(screener.router, prefix="/api/screener", tags=["选股器"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["回测"])
app.include_router(daily_brief.router, prefix="/api/brief", tags=["每日播报"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["自选组合"])
app.include_router(research.router, prefix="/api/research", tags=["研报聚合"])
app.include_router(hkus.router, prefix="/api/hkus", tags=["港美股"])
app.include_router(capital_flow.router, prefix="/api/capital", tags=["资金流向"])
app.include_router(industry_chain.router, prefix="/api/chain", tags=["产业链"])
app.include_router(community.router, prefix="/api/community", tags=["策略社区"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["Token管理"])
app.include_router(quant.router, prefix="/api/quant", tags=["量化因子"])
app.include_router(notes.router, prefix="/api/notes", tags=["知识笔记"])


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_TITLE,
        "version": settings.VERSION,
        "domain": settings.DOMAIN,
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
