"""
沪深300核心成分股批量数据导入脚本

用法:
  python scripts/batch_csi300.py              # 全部
  python scripts/batch_csi300.py --limit 20   # 先导入20只测试

在 ECS 上运行:
  cd /opt/mitouai/backend
  source /opt/mitouai/venv/bin/activate
  python scripts/batch_csi300.py
"""
import argparse
import sys
import os
import time

# 确保能导入 backend 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qlib_integration.data_pipeline import QlibDataPipeline


# ── 沪深300核心成分股（硬编码，避免 akshare 指数接口慢/不稳定） ──
# 按行业分类，覆盖金融/消费/科技/能源/医药/材料等主要板块
CORE_STOCKS = [
    # ── 银行/金融 ──
    "600036",  # 招商银行
    "601398",  # 工商银行
    "601288",  # 农业银行
    "601939",  # 建设银行
    "600000",  # 浦发银行
    "601166",  # 兴业银行
    "600016",  # 民生银行
    "000001",  # 平安银行
    "601318",  # 中国平安
    "601628",  # 中国人寿
    "600030",  # 中信证券
    "601688",  # 华泰证券
    # ── 食品饮料 ──
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    "000568",  # 泸州老窖
    "600887",  # 伊利股份
    "600436",  # 片仔癀
    "000538",  # 云南白药
    "603288",  # 海天味业
    # ── 科技/电子 ──
    "300750",  # 宁德时代
    "002415",  # 海康威视
    "000063",  # 中兴通讯
    "002230",  # 科大讯飞
    "300059",  # 东方财富
    "603501",  # 韦尔股份
    "603986",  # 兆易创新
    "002241",  # 歌尔股份
    # ── 新能源/汽车 ──
    "002594",  # 比亚迪
    "600104",  # 上汽集团
    "601633",  # 长城汽车
    "601012",  # 隆基绿能
    "600438",  # 通威股份
    # ── 能源/化工 ──
    "601857",  # 中国石油
    "600028",  # 中国石化
    "601088",  # 中国神华
    "600019",  # 宝钢股份
    "601899",  # 紫金矿业
    "600346",  # 恒力石化
    # ── 医药健康 ──
    "600276",  # 恒瑞医药
    "300015",  # 爱尔眼科
    "300760",  # 迈瑞医疗
    "000963",  # 华东医药
    # ── 消费/家电 ──
    "000651",  # 格力电器
    "000333",  # 美的集团
    "600690",  # 海尔智家
    "600031",  # 三一重工
    "600585",  # 海螺水泥
    # ── 通信/基建 ──
    "600050",  # 中国联通
    "601728",  # 中国电信
    "601800",  # 中国交建
    "601668",  # 中国建筑
    "601390",  # 中国中铁
    # ── 地产/公用 ──
    "000002",  # 万科A
    "001979",  # 招商蛇口
    "600900",  # 长江电力
    "600009",  # 上海机场
]


def get_stock_list(limit: int = 0) -> list:
    """获取股票列表"""
    codes = CORE_STOCKS.copy()
    if limit > 0:
        codes = codes[:limit]
    print(f"核心成分股: 共 {len(codes)} 只")
    return codes


def main():
    parser = argparse.ArgumentParser(description="批量导入核心成分股数据")
    parser.add_argument("--limit", type=int, default=0, help="限制导入数量（0=全部）")
    parser.add_argument("--data-dir", default="qlib_data", help="Qlib数据目录")
    args = parser.parse_args()

    # 获取成分股
    codes = get_stock_list(args.limit)
    if not codes:
        print("股票列表为空，退出")
        sys.exit(1)

    # 批量导入
    pipeline = QlibDataPipeline(qlib_data_dir=args.data_dir)
    print(f"\n开始批量导入 {len(codes)} 只股票...")
    print(f"预计耗时: {len(codes) * 0.5:.0f} 秒")
    print()

    result = pipeline.dump_all(codes)

    # 输出结果
    elapsed = result.get("elapsed_seconds", 0)
    print("\n" + "=" * 60)
    print(f"导入完成!")
    print(f"  成功: {len(result['success'])} 只")
    print(f"  失败: {len(result['failed'])} 只")
    print(f"  交易日历: {result['calendar_days']} 天")
    print(f"  耗时: {elapsed:.1f} 秒")

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
