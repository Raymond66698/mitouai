"""
沪深300成分股批量数据导入脚本

用法:
  python scripts/batch_csi300.py              # 全部300只
  python scripts/batch_csi300.py --limit 50   # 先导入50只测试

在 ECS 上运行:
  cd /opt/mitouai/backend
  source ../venv/bin/activate
  python scripts/batch_csi300.py
"""
import argparse
import sys
import os
import time

# 确保能导入 backend 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qlib_integration.data_pipeline import QlibDataPipeline


def get_csi300_components(limit: int = 0) -> list:
    """获取沪深300成分股列表"""
    import akshare as ak

    print("正在获取沪深300成分股列表...")
    try:
        # 尝试 csindex 接口
        df = ak.index_stock_cons_csindex(symbol="000300")
    except Exception:
        try:
            # 备用接口
            df = ak.index_stock_cons(symbol="000300")
        except Exception as e:
            print(f"获取成分股失败: {e}")
            return []

    # 提取股票代码
    code_col = None
    for col in df.columns:
        if "代码" in col or "code" in col.lower():
            code_col = col
            break

    if not code_col:
        # 尝试第一列
        code_col = df.columns[0]

    codes = df[code_col].astype(str).tolist()
    # 过滤: 只保留6位数字
    codes = [c.strip() for c in codes if len(c.strip()) == 6 and c.strip().isdigit()]

    if limit > 0:
        codes = codes[:limit]

    print(f"沪深300成分股: 共 {len(codes)} 只")
    return codes


def main():
    parser = argparse.ArgumentParser(description="批量导入沪深300成分股数据")
    parser.add_argument("--limit", type=int, default=0, help="限制导入数量（0=全部）")
    parser.add_argument("--data-dir", default="qlib_data", help="Qlib数据目录")
    args = parser.parse_args()

    # 获取成分股
    codes = get_csi300_components(args.limit)
    if not codes:
        print("无法获取成分股列表，退出")
        sys.exit(1)

    # 批量导入
    pipeline = QlibDataPipeline(qlib_data_dir=args.data_dir)
    print(f"\n开始批量导入 {len(codes)} 只股票...")
    print(f"预计耗时: {len(codes) * 0.5:.0f} 秒")
    print()

    result = pipeline.dump_all(codes)

    # 输出结果
    print("\n" + "=" * 60)
    print(f"导入完成!")
    print(f"  成功: {len(result['success'])} 只")
    print(f"  失败: {len(result['failed'])} 只")
    print(f"  交易日历: {result['calendar_days']} 天")
    print(f"  耗时: {result['elapsed_seconds']:.1f} 秒")

    if result['failed']:
        print(f"\n失败股票: {', '.join(result['failed'][:20])}")
        if len(result['failed']) > 20:
            print(f"  ...等 {len(result['failed'])} 只")

    # 打印状态
    status = pipeline.get_status()
    print(f"\n数据状态:")
    print(f"  总股票数: {status['stock_count']}")
    print(f"  日历天数: {status['calendar_days']}")
    print(f"  bin文件数: {status['bin_files']}")
    print(f"  总大小: {status['total_size_mb']} MB")


if __name__ == "__main__":
    main()
