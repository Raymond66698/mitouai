"""
SQLite → PostgreSQL 数据迁移脚本

用法:
  python migrate_to_postgres.py <postgres_url>

步骤:
  1. 从生产 SQLite 导出所有数据
  2. 用 SQLAlchemy 在 PostgreSQL 中创建表
  3. 导入数据
  4. 验证
"""
import sys
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate")

# ── SQLite 数据导出 ──


def export_sqlite(db_path: str) -> dict:
    """从 SQLite 导出所有表数据"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 获取所有表名
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]

    data = {}
    for table in tables:
        cur.execute(f"SELECT * FROM [{table}]")
        rows = [dict(r) for r in cur.fetchall()]
        if rows:
            data[table] = rows
            logger.info(f"  {table}: {len(rows)} rows")

    conn.close()
    return data


# ── PostgreSQL 导入 ──


def import_to_postgres(pg_url: str, data: dict):
    """将数据导入 PostgreSQL"""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(pg_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)

    # 创建表
    import sys as _sys
    import os as _os
    _backend_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "backend")
    _sys.path.insert(0, _backend_dir)

    import models  # noqa
    from models.base import Base
    Base.metadata.create_all(bind=engine)
    logger.info("PostgreSQL 表已创建")

    with Session() as db:
        total = 0
        for table_name, rows in data.items():
            if not rows:
                continue
            table = Base.metadata.tables.get(table_name)
            if table is None:
                logger.warning(f"  跳过未知表: {table_name}")
                continue

            # 用原始 SQL INSERT 避免 ORM 映射问题
            columns = list(rows[0].keys())
            col_names = ", ".join(columns)
            placeholders = ", ".join([f":{c}" for c in columns])

            for row in rows:
                # 转换 datetime 对象为 ISO 字符串
                clean = {}
                for k, v in row.items():
                    if isinstance(v, datetime):
                        clean[k] = v.isoformat()
                    elif isinstance(v, bytes):
                        clean[k] = v.decode("utf-8", errors="replace")
                    else:
                        clean[k] = v

                stmt = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})")
                try:
                    db.execute(stmt, clean)
                    total += 1
                except Exception as e:
                    logger.warning(f"  INSERT {table_name} 失败: {e} (row: {clean.get('id', '?')})")

        db.commit()
        logger.info(f"共导入 {total} 条记录")


# ── 验证 ──


def verify(pg_url: str, data: dict):
    """验证 PostgreSQL 数据完整性"""
    from sqlalchemy import create_engine, text

    engine = create_engine(pg_url, pool_pre_ping=True)
    with engine.connect() as conn:
        for table_name, rows in data.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            status = "OK" if count == len(rows) else f"MISMATCH (expected {len(rows)})"
            logger.info(f"  {table_name}: {count} rows — {status}")
    engine.dispose()


# ── 主流程 ──


def main():
    if len(sys.argv) < 2:
        print("用法: python migrate_to_postgres.py <postgres_url>")
        print("示例: python migrate_to_postgres.py postgresql://user:pass@host:5432/db")
        sys.exit(1)

    pg_url = sys.argv[1]
    db_path = "backend/data/mitouai.db"

    logger.info("=" * 60)
    logger.info("觅投AI — SQLite → PostgreSQL 数据迁移")
    logger.info("=" * 60)

    # 1. 导出
    logger.info("\n[1/4] 导出 SQLite 数据...")
    data = export_sqlite(db_path)
    total_rows = sum(len(v) for v in data.values())
    logger.info(f"  共 {len(data)} 个表, {total_rows} 条记录")

    # 2. 导入
    logger.info("\n[2/4] 导入 PostgreSQL...")
    import_to_postgres(pg_url, data)

    # 3. 验证
    logger.info("\n[3/4] 验证数据完整性...")
    verify(pg_url, data)

    # 4. 重置序列
    logger.info("\n[4/4] 完成！")
    logger.info(f"\n请在 ECS 上设置环境变量:")
    logger.info(f"  DATABASE_URL={pg_url}")
    logger.info(f"\n然后重启 gunicorn: pkill -9 -f gunicorn && cd /opt/mitouai/backend && nohup /opt/mitouai/venv/bin/gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 &")


if __name__ == "__main__":
    main()
