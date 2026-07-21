"""
觅投AI (mitouai) — 全局配置
所有敏感信息通过环境变量注入，开发用 .env，生产用云平台环境变量面板。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


class Settings:
    # ── 项目元信息 ──
    PROJECT_NAME: str = "mitouai"
    PROJECT_TITLE: str = "觅投AI"
    VERSION: str = "0.2.0"
    DOMAIN: str = os.getenv("MITOUAI_DOMAIN", "mitouai.com")

    # ── 服务器 ──
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── 数据库 (Supabase PostgreSQL 或 SQLite) ──
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///data/mitouai.db",
    )

    # ── AI 模型 ──
    LITELLM_API_BASE: str = os.getenv("LITELLM_API_BASE", "http://localhost:4000")
    LITELLM_MASTER_KEY: str = os.getenv("LITELLM_MASTER_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "default")
    PREMIUM_MODEL: str = os.getenv("PREMIUM_MODEL", "premium")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # ── JWT 认证 ──
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET",
        "mitouai-dev-secret-change-in-production-2026",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 72

    # ── 市场数据 ──
    AKSHARE_CACHE_TTL: int = int(os.getenv("AKSHARE_CACHE_TTL", "3600"))

    # ── 分析任务 ──
    ANALYSIS_TIMEOUT: int = int(os.getenv("ANALYSIS_TIMEOUT", "600"))
    MAX_DEBATE_ROUNDS: int = int(os.getenv("MAX_DEBATE_ROUNDS", "3"))
    MAX_RISK_ROUNDS: int = int(os.getenv("MAX_RISK_ROUNDS", "2"))

    # ── 订阅套餐 ──
    SUBSCRIPTION_PLANS: dict = {
        "free": {
            "name": "免费版",
            "price": 0,
            "price_unit": "",
            "daily_analyses": 3,
            "models": ["deepseek-chat"],
            "features": [
                "基础股票搜索",
                "标准分析报告",
                "3个策略模板",
                "大盘指数查看",
            ],
            "bring_your_own_key": False,
            "priority_queue": False,
        },
        "pro": {
            "name": "专业版",
            "price": 39,
            "price_unit": "月",
            "daily_analyses": 50,
            "models": ["deepseek-chat", "gpt-4o-mini"],
            "features": [
                "无限策略模板",
                "策略组合分析",
                "高级分析报告",
                "历史分析对比",
                "T+0 实时监控",
                "手机推送通知",
            ],
            "bring_your_own_key": False,
            "priority_queue": False,
        },
        "max": {
            "name": "大师版",
            "price": 99,
            "price_unit": "月",
            "daily_analyses": -1,
            "models": ["deepseek-chat", "gpt-4o", "deepseek-reasoner"],
            "features": [
                "无限分析次数",
                "全模型自由选择",
                "策略自由组合",
                "数据导出/API接口",
                "优先分析队列",
                "专属数据源",
                "手机推送通知",
            ],
            "bring_your_own_key": True,
            "priority_queue": True,
        },
    }

    # ── 推送通知 ──
    PUSHPLUS_TOKEN: str = os.getenv("PUSHPLUS_TOKEN", "")
    PUSHPLUS_URL: str = "https://www.pushplus.plus/send"

    # ── CORS ──
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,https://mitouai.com,https://www.mitouai.com"
    ).split(",")


settings = Settings()
