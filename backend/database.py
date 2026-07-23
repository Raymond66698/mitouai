"""
数据库连接管理 — SQLAlchemy (sync)

支持 PostgreSQL（生产）和 SQLite（开发）自动切换。
通过 DATABASE_URL 环境变量控制，默认为 SQLite。
"""
import logging
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config import settings

logger = logging.getLogger("mitouai.database")

# ── 引擎创建 ──

_engine = None
_SessionLocal = None


def _create_engine():
    """根据 DATABASE_URL 创建引擎"""
    db_url = settings.DATABASE_URL

    if db_url.startswith("sqlite"):
        # SQLite: 确保目录存在，使用 StaticPool 避免多线程问题
        db_path = db_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DEBUG,
        )
        # SQLite WAL 模式 + 外键约束
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info("数据库引擎: SQLite (开发模式)")
    else:
        # PostgreSQL
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )
        logger.info("数据库引擎: PostgreSQL (生产模式)")

    return engine


def get_engine():
    """获取全局数据库引擎（延迟初始化）"""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """获取 Session 工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def get_db() -> Session:
    """获取数据库会话（FastAPI 依赖注入）"""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Session:
    """获取数据库会话（上下文管理器，用于非 FastAPI 场景）"""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库 — 创建所有表"""
    import models  # noqa: F401 — 触发所有模型注册到 Base.metadata
    from models.base import Base
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表已创建/验证")


def reset_db():
    """重置数据库 — 删除所有表（仅开发用！）"""
    import models  # noqa: F401
    from models.base import Base
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.warning("数据库已重置！")
