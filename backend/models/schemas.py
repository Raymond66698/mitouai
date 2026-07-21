"""
觅投AI — Pydantic 数据模型
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


# ── 股票 ──
class StockSearchResult(BaseModel):
    code: str = Field(..., description="股票代码，如 601991.SS")
    name: str = Field(..., description="股票名称，如 大唐发电")
    exchange: str = Field("", description="交易所：上交所/深交所")
    market: str = Field("A", description="市场：A(A股)/HK(港股)/US(美股)")


class StockSearchResponse(BaseModel):
    results: list[StockSearchResult]
    total: int


# ── 认证 ──
class RegisterRequest(BaseModel):
    email: str = Field(..., description="邮箱", examples=["user@example.com"])
    password: str = Field(..., min_length=6, max_length=128, description="密码，至少6位")
    display_name: str = Field("", description="显示名称")


class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class AuthResponse(BaseModel):
    success: bool
    message: str = ""
    user: Optional[dict] = None
    access_token: Optional[str] = None


# ── 用户 ──
class UserProfile(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    plan: str = "free"
    plan_name: str = "免费版"
    plan_features: list[str] = []
    plan_price: int = 0
    daily_analyses_used: int = 0
    daily_analyses_limit: int | str = 3
    total_analyses: int = 0
    created_at: Optional[str] = None


class QuotaResponse(BaseModel):
    plan: str
    plan_name: str
    daily_used: int
    daily_limit: int | str
    remaining: int | str
    total_analyses: int


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(..., description="显示名称")


class SetKeyRequest(BaseModel):
    provider: str = Field("deepseek", description="模型提供商: deepseek/openai/anthropic")
    api_key: str = Field(..., description="API Key")


# ── 分析请求/响应 ──
class AnalysisRequest(BaseModel):
    ticker: str = Field(..., description="股票代码", examples=["601991.SS"])
    trade_date: Optional[str] = Field(None, description="分析日期 YYYY-MM-DD，默认今天")
    debate_rounds: int = Field(1, ge=1, le=5, description="多空辩论轮数")
    risk_rounds: int = Field(1, ge=1, le=3, description="风险辩论轮数")
    strategy_id: Optional[str] = Field(None, description="使用的策略模板 ID")
    model: Optional[str] = Field("default", description="使用的 AI 模型")


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisTaskResponse(BaseModel):
    task_id: str
    ticker: str
    status: AnalysisStatus
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_summary: Optional[str] = None
    error: Optional[str] = None


# ── 策略模板 ──
class StrategyCategory(str, Enum):
    MASTER = "master"
    QUANT = "quant"
    TECHNICAL = "technical"
    CUSTOM = "custom"


class StrategyTemplate(BaseModel):
    id: str
    name: str
    category: StrategyCategory
    description: str = ""
    author: str = ""
    tags: list[str] = []
    config_schema: dict = {}
    default_config: dict = {}
    icon: str = ""


class StrategyListResponse(BaseModel):
    strategies: list[StrategyTemplate]
    total: int


# ── 订阅 ──
class PlanInfo(BaseModel):
    id: str
    name: str
    price: int
    price_unit: str
    daily_analyses: int | str
    models: list[str]
    features: list[str]
    bring_your_own_key: bool


class PlansResponse(BaseModel):
    plans: list[PlanInfo]
    current_plan: str = "free"


class UpgradeRequest(BaseModel):
    plan: str = Field(..., description="目标套餐: free/pro/max")


class UpgradeResponse(BaseModel):
    success: bool
    message: str
    new_plan: str
    new_plan_name: str


# ── 推送通知 ──
class NotificationSettingsUpdate(BaseModel):
    pushplus_token: Optional[str] = None
    email_notify: Optional[bool] = None
    analysis_complete: Optional[bool] = None
    breaking_news: Optional[bool] = None


class NotificationItem(BaseModel):
    type: str
    title: str
    content: str
    task_id: Optional[str] = None
    ticker: Optional[str] = None
    decision: Optional[str] = None
    read: bool = False
    created_at: str


# ── 通用响应 ──
class APIResponse(BaseModel):
    success: bool
    message: str = ""
    data: dict = {}
