"""
策略回测引擎
支持：大师策略回测、技术策略回测、收益曲线、风险评估
"""
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger("mitouai.backtest")


class BacktestEngine:
    """策略回测引擎"""

    def __init__(self):
        from services.data_service import data_service as ds
        self.ds = ds

    def run(self, ticker: str, strategy: str, params: dict = None,
            start_date: str = None, end_date: str = None,
            initial_capital: float = 100000) -> dict:
        """运行回测

        strategy: "ma_crossover" | "momentum" | "buy_hold" | "rsi_reversal"
        """
        params = params or {}
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 获取数据
        df = self.ds.get_kline_df(ticker, days=400)
        if df.empty:
            return {"error": "数据获取失败"}

        # 只保留回测区间
        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        if df.empty:
            return {"error": "回测区间无数据"}

        # 计算基准收益
        benchmark_return = self._calc_return(df.iloc[0]["close"], df.iloc[-1]["close"])

        # 运行策略
        if strategy == "ma_crossover":
            result = self._backtest_ma_crossover(df, params, initial_capital)
        elif strategy == "momentum":
            result = self._backtest_momentum(df, params, initial_capital)
        elif strategy == "buy_hold":
            result = self._backtest_buy_hold(df, initial_capital)
        elif strategy == "rsi_reversal":
            result = self._backtest_rsi_reversal(df, params, initial_capital)
        else:
            return {"error": f"未知策略: {strategy}"}

        # 添加摘要
        result["benchmark_return"] = round(benchmark_return, 2)
        result["strategy"] = strategy
        result["ticker"] = ticker
        result["start_date"] = start_date
        result["end_date"] = end_date
        result["trading_days"] = len(df)
        result["params"] = params

        return result

    def run_benchmark_comparison(self, ticker: str, strategies: list[str] = None,
                                  start_date: str = None, end_date: str = None) -> dict:
        """多个策略对比回测"""
        if strategies is None:
            strategies = ["buy_hold", "ma_crossover", "momentum", "rsi_reversal"]

        results = {}
        for s in strategies:
            results[s] = self.run(ticker, s, start_date=start_date, end_date=end_date)
        return {"comparison": results}

    # ── 策略实现 ──

    def _backtest_buy_hold(self, df: pd.DataFrame, capital: float) -> dict:
        """买入持有策略"""
        start_price = df.iloc[0]["close"]
        end_price = df.iloc[-1]["close"]
        shares = int(capital / start_price)
        final_value = shares * end_price + (capital - shares * start_price)

        return self._compute_metrics(
            equity_curve=self._build_equity_curve(df, [(0, "buy"), (len(df)-1, "sell")], capital),
            final_value=final_value,
            capital=capital,
            trades=[{"type": "buy", "date": str(df.iloc[0]["date"])[:10],
                     "price": start_price, "shares": shares},
                    {"type": "sell", "date": str(df.iloc[-1]["date"])[:10],
                     "price": end_price, "shares": shares}],
            df=df,
        )

    def _backtest_ma_crossover(self, df: pd.DataFrame, params: dict,
                                 capital: float) -> dict:
        """均线交叉策略"""
        short = params.get("short_period", 5)
        long = params.get("long_period", 20)

        df = df.copy()
        df["ma_short"] = df["close"].rolling(short).mean()
        df["ma_long"] = df["close"].rolling(long).mean()
        df = df.dropna()

        signals = []
        for i in range(1, len(df)):
            if df["ma_short"].iloc[i] > df["ma_long"].iloc[i] and \
               df["ma_short"].iloc[i-1] <= df["ma_long"].iloc[i-1]:
                signals.append((i, "buy", float(df["close"].iloc[i])))
            elif df["ma_short"].iloc[i] < df["ma_long"].iloc[i] and \
                 df["ma_short"].iloc[i-1] >= df["ma_long"].iloc[i-1]:
                signals.append((i, "sell", float(df["close"].iloc[i])))

        return self._simulate_trades(df, signals, capital)

    def _backtest_momentum(self, df: pd.DataFrame, params: dict,
                             capital: float) -> dict:
        """动量策略：N日涨幅超过阈值买入，跌破M日低点卖出"""
        lookback = params.get("lookback_days", 20)
        threshold = params.get("threshold", 5)  # 百分比

        df = df.copy()
        df["returns"] = df["close"].pct_change(lookback) * 100
        df = df.dropna()

        signals = []
        position = False
        for i in range(1, len(df)):
            if not position and df["returns"].iloc[i] > threshold:
                signals.append((i, "buy", float(df["close"].iloc[i])))
                position = True
            elif position and df["returns"].iloc[i] < -threshold:
                signals.append((i, "sell", float(df["close"].iloc[i])))
                position = False

        if position:
            signals.append((len(df)-1, "sell", float(df["close"].iloc[-1])))

        return self._simulate_trades(df, signals, capital)

    def _backtest_rsi_reversal(self, df: pd.DataFrame, params: dict,
                                 capital: float) -> dict:
        """RSI反转策略：RSI<30超卖买入，RSI>70超买卖出"""
        period = params.get("rsi_period", 14)
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)

        df = df.copy()
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))
        df = df.dropna()

        signals = []
        position = False
        for i in range(1, len(df)):
            if not position and df["rsi"].iloc[i] < oversold:
                signals.append((i, "buy", float(df["close"].iloc[i])))
                position = True
            elif position and df["rsi"].iloc[i] > overbought:
                signals.append((i, "sell", float(df["close"].iloc[i])))
                position = False

        if position:
            signals.append((len(df)-1, "sell", float(df["close"].iloc[-1])))

        return self._simulate_trades(df, signals, capital)

    # ── 模拟交易 ──

    def _simulate_trades(self, df: pd.DataFrame, signals: list,
                           capital: float) -> dict:
        """执行交易模拟"""
        cash = capital
        shares = 0
        trades = []
        equity_points = [(0, capital)]

        for idx, sig_type, price in signals:
            date = str(df.iloc[idx]["date"])[:10]
            if sig_type == "buy" and cash > 0:
                shares = int(cash * 0.95 / price)  # 95%仓位
                cost = shares * price
                cash -= cost
                trades.append({
                    "type": "buy", "date": date, "price": round(price, 2),
                    "shares": shares, "cost": round(cost, 2),
                })
            elif sig_type == "sell" and shares > 0:
                revenue = shares * price
                cash += revenue
                trades.append({
                    "type": "sell", "date": date, "price": round(price, 2),
                    "shares": shares, "revenue": round(revenue, 2),
                })
                shares = 0

            equity = cash + shares * float(df.iloc[idx]["close"])
            equity_points.append((idx, equity))

        # 收盘平仓
        if shares > 0:
            final_price = float(df.iloc[-1]["close"])
            cash += shares * final_price
            trades.append({
                "type": "sell", "date": str(df.iloc[-1]["date"])[:10],
                "price": round(final_price, 2), "shares": shares,
                "revenue": round(shares * final_price, 2),
            })

        final_value = cash
        return self._compute_metrics(
            equity_curve=equity_points,
            final_value=final_value, capital=capital,
            trades=trades, df=df,
        )

    # ── 指标计算 ──

    def _compute_metrics(self, equity_curve: list, final_value: float,
                           capital: float, trades: list, df: pd.DataFrame) -> dict:
        """计算回测指标"""
        total_return = (final_value - capital) / capital * 100

        # 年化收益
        days = len(df)
        annual_return = ((1 + total_return / 100) ** (252 / max(days, 1)) - 1) * 100

        # 最大回撤
        max_drawdown = 0
        peak = capital
        for _, val in equity_curve:
            peak = max(peak, val)
            dd = (peak - val) / peak * 100
            max_drawdown = max(max_drawdown, dd)

        # 夏普比率
        returns = []
        for i in range(1, len(equity_curve)):
            prev = equity_curve[i-1][1]
            curr = equity_curve[i][1]
            if prev > 0:
                returns.append((curr - prev) / prev)
        if returns and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * math.sqrt(252)
        else:
            sharpe = 0

        # 胜率
        win_count = 0
        for i in range(0, len(trades)-1, 2):
            if i+1 < len(trades) and trades[i]["type"] == "buy" and trades[i+1]["type"] == "sell":
                buy_price = trades[i]["price"]
                sell_price = trades[i+1]["price"]
                if sell_price > buy_price:
                    win_count += 1
        trade_pairs = len(trades) // 2
        win_rate = (win_count / trade_pairs * 100) if trade_pairs > 0 else 0

        # 基准（买入持有）
        start_price = float(df.iloc[0]["close"])
        end_price = float(df.iloc[-1]["close"])
        benchmark_return = (end_price - start_price) / start_price * 100

        # 超额收益
        excess_return = total_return - benchmark_return

        # 权益曲线（简化，取关键点）
        curve = []
        for idx, val in equity_curve[:200]:  # 最多200个点
            curve.append({
                "date": str(df.iloc[min(idx, len(df)-1)]["date"])[:10],
                "value": round(val, 2),
            })

        # 评级
        if total_return > 20 and sharpe > 1 and max_drawdown < 20:
            rating = "A"
        elif total_return > 0 and sharpe > 0.5:
            rating = "B"
        elif total_return > -10:
            rating = "C"
        else:
            rating = "D"

        return {
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "win_rate": round(win_rate, 2),
            "trade_count": len(trades),
            "final_value": round(final_value, 2),
            "initial_capital": capital,
            "benchmark_return": round(benchmark_return, 2),
            "excess_return": round(excess_return, 2),
            "rating": rating,
            "equity_curve": curve,
            "trades": trades[:20],  # 最多显示20笔
        }

    def _build_equity_curve(self, df: pd.DataFrame, signals: list,
                              capital: float) -> list:
        """构建买入持有的权益曲线"""
        start_price = float(df.iloc[0]["close"])
        shares = int(capital / start_price)
        points = []
        for i in range(0, len(df), max(1, len(df) // 100)):
            val = capital - shares * start_price + shares * float(df.iloc[i]["close"])
            points.append((i, val))
        points.append((len(df)-1, capital - shares * start_price + shares * float(df.iloc[-1]["close"])))
        return points

    @staticmethod
    def _calc_return(start: float, end: float) -> float:
        return (end - start) / start * 100


# 全局单例
backtest_engine = BacktestEngine()
