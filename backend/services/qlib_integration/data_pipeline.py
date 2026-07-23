"""
akshare -> Qlib .bin 数据转换管道

将 A 股日线数据从 akshare 转为 Qlib 原生 .bin 格式，
使 Qlib 的 Alpha158 因子引擎可以直接运行。

目录结构:
  qlib_data/
  ├── calendars/
  │   └── day.txt            # 交易日历
  ├── features/
  │   └── sh600519/          # 每只股票一个目录 (小写)
  │       ├── open.day.bin
  │       ├── close.day.bin
  │       ├── high.day.bin
  │       ├── low.day.bin
  │       ├── volume.day.bin
  │       └── vwap.day.bin
  └── instruments/
      └── all.txt            # 股票列表 (symbol\tstart\tend)
"""
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("mitouai.qlib.pipeline")

# .bin 文件后缀
BIN_SUFFIX = ".day.bin"

# akshare 代码 -> Qlib 代码 的映射
# 6开头 -> sh, 0/3开头 -> sz, 8/4开头 -> bj
def to_qlib_symbol(code: str) -> str:
    """A股代码转Qlib格式: 600519 -> sh600519"""
    code = code.strip()
    if code.startswith(("6", "9")):
        return f"sh{code}"
    elif code.startswith(("0", "3")):
        return f"sz{code}"
    elif code.startswith(("8", "4")):
        return f"bj{code}"
    return f"sh{code}"


def qlib_symbol_to_code(symbol: str) -> str:
    """Qlib格式转A股代码: sh600519 -> 600519"""
    return symbol[2:]


class QlibDataPipeline:
    """akshare -> Qlib .bin 数据管道"""

    def __init__(self, qlib_data_dir: str = "qlib_data"):
        self.qlib_dir = Path(qlib_data_dir)
        self.features_dir = self.qlib_dir / "features"
        self.calendars_dir = self.qlib_dir / "calendars"
        self.instruments_dir = self.qlib_dir / "instruments"

        # 确保目录存在
        for d in [self.features_dir, self.calendars_dir, self.instruments_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════
    #  数据拉取 (akshare)
    # ═══════════════════════════════════════════════

    def fetch_stock_data(self, code: str, start_date: str = "",
                         end_date: str = "") -> pd.DataFrame:
        """从 akshare 拉取单只股票的日线数据

        返回标准化的 DataFrame:
          columns: date, open, close, high, low, volume, vwap
          index: 0-based int
        """
        import akshare as ak

        if not start_date:
            start_date = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )

        if df is None or df.empty:
            logger.warning(f"akshare 返回空数据: {code}")
            return pd.DataFrame()

        # 标准化列名
        col_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
        }
        df = df.rename(columns=col_map)

        # 计算 VWAP (成交额/成交量, akshare成交量单位是"手"=100股)
        df["vwap"] = df["amount"] / (df["volume"] * 100 + 1e-12)

        # 只保留需要的列
        keep_cols = ["date", "open", "close", "high", "low", "volume", "vwap"]
        df = df[[c for c in keep_cols if c in df.columns]].copy()

        # 日期格式统一
        df["date"] = pd.to_datetime(df["date"])

        # 数值类型确保
        for col in ["open", "close", "high", "low", "volume", "vwap"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["open", "close", "high", "low"]).reset_index(drop=True)
        return df

    def fetch_multi_stocks(self, codes: list[str],
                           start_date: str = "", end_date: str = "") -> dict[str, pd.DataFrame]:
        """批量拉取多只股票数据"""
        results = {}
        for i, code in enumerate(codes):
            try:
                df = self.fetch_stock_data(code, start_date, end_date)
                if not df.empty:
                    results[code] = df
                    logger.info(f"[{i+1}/{len(codes)}] {code}: {len(df)} 条数据")
                else:
                    logger.warning(f"[{i+1}/{len(codes)}] {code}: 无数据")
            except Exception as e:
                logger.error(f"[{i+1}/{len(codes)}] {code}: {e}")
            # 避免请求过快
            if i < len(codes) - 1:
                time.sleep(0.3)
        return results

    # ═══════════════════════════════════════════════
    #  日历构建
    # ═══════════════════════════════════════════════

    def build_calendar(self, all_data: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
        """从所有股票数据中构建交易日历"""
        all_dates = set()
        for df in all_data.values():
            all_dates.update(df["date"].tolist())
        calendar = sorted(all_dates)
        logger.info(f"日历构建完成: {len(calendar)} 个交易日")
        return calendar

    def save_calendar(self, calendar: list[pd.Timestamp]):
        """保存日历文件"""
        cal_path = self.calendars_dir / "day.txt"
        with open(cal_path, "w", encoding="utf-8") as f:
            for dt in calendar:
                f.write(dt.strftime("%Y-%m-%d") + "\n")
        logger.info(f"日历已保存: {cal_path}")

    def load_calendar(self) -> list[pd.Timestamp]:
        """读取已有日历"""
        cal_path = self.calendars_dir / "day.txt"
        if not cal_path.exists():
            return []
        dates = []
        with open(cal_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    dates.append(pd.Timestamp(line))
        return dates

    # ═══════════════════════════════════════════════
    #  二进制文件写入
    # ═══════════════════════════════════════════════

    def _write_bin(self, symbol: str, field: str,
                   values: np.ndarray, date_index: int):
        """写入单个字段的 .bin 文件

        格式: [date_index, val_0, val_1, ...] 全部 float32 小端
        """
        sym_dir = self.features_dir / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)

        bin_path = sym_dir / f"{field.lower()}{BIN_SUFFIX}"

        # date_index 作为第一个元素
        full_array = np.hstack([np.array([date_index], dtype=np.float32),
                                values.astype(np.float32)])
        full_array.astype("<f").tofile(str(bin_path.resolve()))

    def _align_to_calendar(self, df: pd.DataFrame,
                           calendar: list[pd.Timestamp]) -> pd.DataFrame:
        """将股票数据对齐到全局日历（缺失日填 NaN）"""
        df = df.copy()
        df = df.set_index("date")
        # 只保留在日历范围内的日期
        cal_in_range = [d for d in calendar if df.index.min() <= d <= df.index.max()]
        cal_df = pd.DataFrame(index=cal_in_range)
        return df.reindex(cal_df.index)

    # ═══════════════════════════════════════════════
    #  股票信息文件
    # ═══════════════════════════════════════════════

    def save_instruments(self, all_data: dict[str, pd.DataFrame]):
        """保存 instruments/all.txt"""
        inst_path = self.instruments_dir / "all.txt"
        with open(inst_path, "w", encoding="utf-8") as f:
            for code, df in all_data.items():
                symbol = to_qlib_symbol(code)
                start = df["date"].min().strftime("%Y-%m-%d")
                end = df["date"].max().strftime("%Y-%m-%d")
                f.write(f"{symbol}\t{start}\t{end}\n")
        logger.info(f"股票列表已保存: {inst_path} ({len(all_data)} 只)")

    # ═══════════════════════════════════════════════
    #  完整转储流程
    # ═══════════════════════════════════════════════

    def dump_all(self, codes: list[str], start_date: str = "",
                 end_date: str = "") -> dict:
        """完整数据转储流程

        1. 拉取所有股票数据
        2. 构建日历
        3. 写入 .bin 文件
        4. 写入 instruments

        返回: {"success": [...], "failed": [...], "calendar_days": N}
        """
        start_ts = time.time()
        logger.info(f"=== 开始数据转储: {len(codes)} 只股票 ===")

        # 1. 拉取数据
        all_data = self.fetch_multi_stocks(codes, start_date, end_date)
        if not all_data:
            return {"success": [], "failed": codes, "calendar_days": 0,
                    "error": "所有股票数据拉取失败"}

        # 2. 构建日历
        calendar = self.build_calendar(all_data)
        self.save_calendar(calendar)

        # 3. 写入 .bin 文件
        fields = ["open", "close", "high", "low", "volume", "vwap"]
        success = []
        failed = []

        for code, df in all_data.items():
            symbol = to_qlib_symbol(code)
            try:
                # 对齐到日历
                aligned = self._align_to_calendar(df, calendar)
                if aligned.empty:
                    failed.append(code)
                    continue

                # 计算 date_index
                date_index = calendar.index(aligned.index.min())

                # 写入每个字段
                for field in fields:
                    if field in aligned.columns:
                        values = aligned[field].values
                        self._write_bin(symbol, field, values, date_index)

                success.append(code)
                logger.info(f"  {symbol}: {len(aligned)} 条 -> .bin OK")
            except Exception as e:
                logger.error(f"  {symbol}: 写入失败 - {e}")
                failed.append(code)

        # 4. 保存 instruments
        self.save_instruments(all_data)

        elapsed = time.time() - start_ts
        logger.info(f"=== 转储完成: {len(success)} 成功, {len(failed)} 失败, "
                     f"耗时 {elapsed:.1f}s ===")

        return {
            "success": success,
            "failed": failed,
            "calendar_days": len(calendar),
            "elapsed_seconds": round(elapsed, 1),
        }

    def dump_single(self, code: str, start_date: str = "",
                    end_date: str = "") -> dict:
        """转储单只股票（增量更新日历和instruments）"""
        df = self.fetch_stock_data(code, start_date, end_date)
        if df.empty:
            return {"success": False, "error": "数据拉取失败"}

        # 读取或构建日历
        existing_calendar = self.load_calendar()
        if existing_calendar:
            # 合并新日期
            new_dates = set(df["date"].tolist()) - set(existing_calendar)
            if new_dates:
                calendar = sorted(existing_calendar + list(new_dates))
            else:
                calendar = existing_calendar
        else:
            calendar = self.build_calendar({code: df})

        self.save_calendar(calendar)

        # 对齐并写入
        symbol = to_qlib_symbol(code)
        aligned = self._align_to_calendar(df, calendar)
        if aligned.empty:
            return {"success": False, "error": "数据无法对齐到日历"}

        date_index = calendar.index(aligned.index.min())
        fields = ["open", "close", "high", "low", "volume", "vwap"]
        for field in fields:
            if field in aligned.columns:
                values = aligned[field].values
                self._write_bin(symbol, field, values, date_index)

        # 更新 instruments
        self._update_instruments(code, df)

        logger.info(f"{symbol}: {len(aligned)} 条数据已写入")
        return {"success": True, "symbol": symbol, "records": len(aligned),
                "date_range": f"{aligned.index.min()} ~ {aligned.index.max()}"}

    def _update_instruments(self, code: str, df: pd.DataFrame):
        """更新 instruments 文件中单只股票的记录"""
        inst_path = self.instruments_dir / "all.txt"
        symbol = to_qlib_symbol(code)
        start = df["date"].min().strftime("%Y-%m-%d")
        end = df["date"].max().strftime("%Y-%m-%d")

        lines = []
        found = False
        if inst_path.exists():
            with open(inst_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if parts[0] == symbol:
                        lines.append(f"{symbol}\t{start}\t{end}\n")
                        found = True
                    else:
                        lines.append(line)
        if not found:
            lines.append(f"{symbol}\t{start}\t{end}\n")

        with open(inst_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    # ═══════════════════════════════════════════════
    #  状态查询
    # ═══════════════════════════════════════════════

    def get_status(self) -> dict:
        """获取数据管道状态"""
        calendar = self.load_calendar()
        instruments = []
        inst_path = self.instruments_dir / "all.txt"
        if inst_path.exists():
            with open(inst_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 3:
                        instruments.append({
                            "symbol": parts[0],
                            "code": qlib_symbol_to_code(parts[0]),
                            "start": parts[1],
                            "end": parts[2],
                        })

        # 统计 .bin 文件大小
        total_size = 0
        bin_count = 0
        if self.features_dir.exists():
            for root, dirs, files in os.walk(self.features_dir):
                for f in files:
                    if f.endswith(BIN_SUFFIX):
                        total_size += os.path.getsize(os.path.join(root, f))
                        bin_count += 1

        return {
            "data_dir": str(self.qlib_dir),
            "calendar_days": len(calendar),
            "calendar_start": str(calendar[0])[:10] if calendar else None,
            "calendar_end": str(calendar[-1])[:10] if calendar else None,
            "stock_count": len(instruments),
            "instruments": instruments,
            "bin_files": bin_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        }
