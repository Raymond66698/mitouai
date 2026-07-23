"""SQLAlchemy 模型包 — 导入所有模型以确保 Base.metadata 完整"""
from models.base import Base
from models.user import User, UserApiKey
from models.token import TokenBalance, TokenTransaction
from models.note import Note
from models.watchlist import Watchlist, Portfolio, Trade
from models.community import SharedStrategy, StrategyLike, StrategyComment
from models.analysis import AnalysisTask, AnalysisReport
from models.notification import Notification

__all__ = [
    "Base",
    "User", "UserApiKey",
    "TokenBalance", "TokenTransaction",
    "Note",
    "Watchlist", "Portfolio", "Trade",
    "SharedStrategy", "StrategyLike", "StrategyComment",
    "AnalysisTask", "AnalysisReport",
    "Notification",
]
