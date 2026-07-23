"""
独立每日指标(daily_basic)同步脚本 — 绕过 gunicorn 超时限制
用法: python3 sync_daily_basic.py
"""
import sys, os, logging, time

# 确保 backend 在 path 中
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
)

# 强制设置环境变量（不依赖 .env）
os.environ.setdefault("DATABASE_URL", "postgresql://mitouai:Mitouai%402026%21@127.0.0.1:5432/mitouai")
os.environ.setdefault("TUSHARE_TOKEN", "3e29e21d6ea34793cc84d1a0fc20905d70a5f4ef81e8055fbe4113fc")

from services.data_pipeline_tushare import TushareDataPipeline

start = time.time()
pipeline = TushareDataPipeline()

# 全量同步 daily_basic（3年数据）
result = pipeline.sync_daily_basic()
elapsed = time.time() - start
print(f"\nSYNC RESULT: {result}")
print(f"ELAPSED: {elapsed:.1f}s ({elapsed/60:.1f}min)")
