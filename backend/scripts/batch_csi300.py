"""
沪深300完整成分股批量数据导入脚本

用法:
  python scripts/batch_csi300.py                    # 全量导入300只×3年
  python scripts/batch_csi300.py --limit 20         # 先导入20只测试
  python scripts/batch_csi300.py --years 1          # 只拉1年数据
  python scripts/batch_csi300.py --refresh           # 增量刷新（每日盘后用）
  python scripts/batch_csi300.py --start-date 2024-01-01  # 自定义起始日期

在 ECS 上运行:
  cd /opt/mitouai/backend
  source /opt/mitouai/venv/bin/activate
  python scripts/batch_csi300.py              # 首次全量导入
  python scripts/batch_csi300.py --refresh    # 每日增量刷新
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 确保能导入 backend 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qlib_integration.data_pipeline import QlibDataPipeline


def load_stock_list(data_dir: str = "data") -> list[dict]:
    """从 JSON 文件加载沪深300成分股列表

    返回: [{"code": "000001", "name": "平安银行", "exchange": "SZ", ...}, ...]
    """
    json_path = os.path.join(data_dir, "csi300_stocks.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # JSON 文件不存在，使用内置核心列表（降级方案）
    print(f"[警告] {json_path} 不存在，使用内置核心成分股列表（56只）")
    CORE_STOCKS = [
        "600036", "601398", "601288", "601939", "600000", "601166", "600016",
        "000001", "601318", "601628", "600030", "601688", "600519", "000858",
        "000568", "600887", "600436", "000538", "603288", "300750", "002415",
        "000063", "002230", "300059", "603501", "603986", "002241", "002594",
        "600104", "601633", "601012", "600438", "601857", "600028", "601088",
        "600019", "601899", "600346", "600276", "300015", "300760", "000963",
        "000651", "000333", "600690", "600031", "600585", "600050", "601728",
        "601800", "601668", "601390", "000002", "001979", "600900", "600009",
    ]
    return [{"code": c, "name": "", "exchange": ""} for c in CORE_STOCKS]


def format_eta(seconds: float) -> str:
    """格式化预计剩余时间"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s}s"


def progress_callback(current, total, code, success):
    """进度回调：打印进度条和ETA"""
    pct = current / total * 100
    bar_len = 30
    filled = int(bar_len * current / total)
    bar = "=" * filled + "-" * (bar_len - filled)
    status = "OK" if success else "FAIL"
    print(f"\r  [{bar}] {current}/{total} ({pct:.0f}%) {code} {status}    ", end="", flush=True)
    if current == total:
        print()  # 换行


def main():
    parser = argparse.ArgumentParser(description="沪深300批量数据导入")
    parser.add_argument("--limit", type=int, default=0,
                        help="限制导入数量（0=全部300只）")
    parser.add_argument("--years", type=float, default=3,
                        help="历史数据年数（默认3年）")
    parser.add_argument("--start-date", default="",
                        help="自定义起始日期 YYYY-MM-DD（覆盖 --years）")
    parser.add_argument("--refresh", action="store_true",
                        help="增量刷新模式（重新拉取覆盖，用于每日更新）")
    parser.add_argument("--data-dir", default="qlib_data",
                        help="Qlib数据目录")
    parser.add_argument("--rate-limit", type=float, default=0.35,
                        help="请求间隔秒数（避免被封）")
    args = parser.parse_args()

    # 加载成分股列表
    stocks = load_stock_list()
    codes = [s["code"] for s in stocks]
    if args.limit > 0:
        codes = codes[:args.limit]

    print(f"沪深300成分股: 共 {len(codes)} 只")
    if args.start_date:
        start_date = args.start_date
        print(f"起始日期: {start_date}")
    else:
        start_date = (datetime.now() - timedelta(days=int(args.years * 365))).strftime("%Y-%m-%d")
        print(f"历史数据: {args.years} 年（从 {start_date} 起）")

    # 初始化管道
    pipeline = QlibDataPipeline(qlib_data_dir=args.data_dir)

    # 预估时间
    est_time = len(codes) * (args.rate_limit + 0.3)
    print(f"预计耗时: ~{format_eta(est_time)}")
    print()

    # 执行导入
    if args.refresh:
        print("=== 增量刷新模式 ===")
        result = pipeline.refresh_all(
            codes,
            rate_limit=args.rate_limit,
            progress_callback=progress_callback,
        )
    else:
        print("=== 全量导入模式 ===")
        result = pipeline.dump_all(
            codes,
            start_date=start_date,
            rate_limit=args.rate_limit,
            progress_callback=progress_callback,
        )

    # 输出结果
    elapsed = result.get("elapsed_seconds", 0)
    print("\n" + "=" * 60)
    print(f"导入完成!")
    print(f"  成功: {len(result['success'])} 只")
    print(f"  失败: {len(result['failed'])} 只")
    print(f"  交易日历: {result['calendar_days']} 天")
    print(f"  耗时: {format_eta(elapsed)}")

    if result['failed']:
        print(f"\n失败股票: {', '.join(result['failed'][:30])}")
        if len(result['failed']) > 30:
            print(f"  ...等 {len(result['failed'])} 只")

    # 打印状态
    status = pipeline.get_status()
    print(f"\n数据状态:")
    print(f"  总股票数: {status['stock_count']}")
    print(f"  日历天数: {status['calendar_days']}")
    print(f"  日历范围: {status['calendar_start']} ~ {status['calendar_end']}")
    print(f"  bin文件数: {status['bin_files']}")
    print(f"  总大小: {status['total_size_mb']} MB")

    # 写入日志文件（供 cron 记录）
    log_dir = Path("data")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "import_log.json"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "mode": "refresh" if args.refresh else "full",
        "total": len(codes),
        "success": len(result['success']),
        "failed": len(result['failed']),
        "failed_codes": result['failed'][:50],
        "calendar_days": result['calendar_days'],
        "elapsed_seconds": elapsed,
    }

    # 追加到日志文件
    logs = []
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except:
            logs = []
    logs.append(log_entry)
    # 只保留最近100条
    logs = logs[-100:]
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    return 0 if not result['failed'] else 1


if __name__ == "__main__":
    sys.exit(main())
