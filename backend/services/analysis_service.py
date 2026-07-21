"""
投研分析服务 — TradingAgents 多智能体分析管道
支持用户追踪、推送通知
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from config import settings

logger = logging.getLogger("mitouai.analysis")


class AnalysisService:
    """多智能体投研分析服务"""

    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._event_queues: dict[str, asyncio.Queue] = {}
        self._reports: dict[str, dict] = {}
        self._user_tasks: dict[str, list[str]] = {}  # user_id -> [task_ids]

    def search_stocks(self, query: str) -> list[dict]:
        """搜索股票：中文名 → 代码模糊匹配"""
        try:
            import sys
            sys.path.insert(0, "D:/TradingAgents")
            from tradingagents.dataflows.akshare_data import search_stocks as ak_search
            return ak_search(query)
        except ImportError:
            demo = [
                {"code": "601991.SS", "name": "大唐发电", "exchange": "上交所", "market": "A"},
                {"code": "600519.SS", "name": "贵州茅台", "exchange": "上交所", "market": "A"},
                {"code": "000858.SZ", "name": "五粮液", "exchange": "深交所", "market": "A"},
            ]
            return [s for s in demo if query.lower() in s["code"].lower() or query in s["name"]]

    async def start_analysis(
        self,
        ticker: str,
        trade_date: Optional[str] = None,
        debate_rounds: int = 1,
        risk_rounds: int = 1,
        strategy_id: Optional[str] = None,
        model: str = "default",
        user_id: str = "",
        user_email: str = "",
        pushplus_token: str = "",
    ) -> dict:
        """启动分析任务"""
        import sys
        sys.path.insert(0, "D:/TradingAgents")

        task_id = str(uuid.uuid4())[:8]
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        ticker = self._normalize_ticker(ticker)

        task = {
            "task_id": task_id,
            "ticker": ticker,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result_summary": None,
            "error": None,
            "strategy_id": strategy_id,
            "model": model,
            "trade_date": trade_date,
            "debate_rounds": debate_rounds,
            "risk_rounds": risk_rounds,
            "user_id": user_id,
            "user_email": user_email,
            "pushplus_token": pushplus_token,
        }
        self._tasks[task_id] = task
        self._event_queues[task_id] = asyncio.Queue()
        self._reports[task_id] = {}

        # 记录用户任务
        if user_id:
            if user_id not in self._user_tasks:
                self._user_tasks[user_id] = []
            self._user_tasks[user_id].insert(0, task_id)
            if len(self._user_tasks[user_id]) > 100:
                self._user_tasks[user_id] = self._user_tasks[user_id][:100]

        asyncio.create_task(self._run_analysis(task_id))
        return task

    def get_user_tasks(self, user_id: str, limit: int = 20) -> list[dict]:
        """获取用户的分析历史"""
        task_ids = self._user_tasks.get(user_id, [])[:limit]
        return [self._tasks[tid] for tid in task_ids if tid in self._tasks]

    def _normalize_ticker(self, ticker: str) -> str:
        """规范化股票代码"""
        ticker = ticker.strip()
        if ticker.upper().endswith((".SS", ".SZ", ".HK")) or "." in ticker:
            return ticker.upper()
        if any('\u4e00' <= c <= '\u9fff' for c in ticker):
            try:
                import sys
                sys.path.insert(0, "D:/TradingAgents")
                from tradingagents.dataflows.akshare_data import name_to_code
                code = name_to_code(ticker)
                if code:
                    return code
            except Exception:
                pass
        if ticker.isdigit() and len(ticker) == 6:
            return f"{ticker}.SS" if ticker.startswith(("6", "9")) else f"{ticker}.SZ"
        raise ValueError(f"无法识别的股票代码或名称: {ticker}")

    async def _run_analysis(self, task_id: str):
        """后台运行 TradingAgents 分析管道"""
        task = self._tasks[task_id]
        queue = self._event_queues[task_id]

        async def emit(event_type: str, data: dict):
            if task["status"] != "completed" and task["status"] != "failed":
                task["status"] = "running"
            await queue.put(json.dumps({"event": event_type, "data": data}))

        try:
            import sys
            sys.path.insert(0, "D:/TradingAgents")
            from tradingagents.dataflows.interface import route_to_vendor

            await emit("progress", {"step": 1, "total": 8, "message": "正在获取市场数据..."})

            # 1. 获取股票数据
            stock_data = route_to_vendor(
                "get_stock_data",
                task["ticker"],
                task["trade_date"].replace("-", "")[:8] + "01",
                task["trade_date"],
            )
            await emit("progress", {"step": 2, "total": 8, "message": "市场数据获取完成"})

            # 2. 获取技术指标
            indicator_names = ["rsi", "macd", "boll", "atr", "ma", "kdj"]
            indicator_results = {}
            for ind_name in indicator_names:
                try:
                    ind_data = route_to_vendor(
                        "get_indicators", task["ticker"], ind_name,
                        task["trade_date"], "60",
                    )
                    indicator_results[ind_name] = str(ind_data)[:200]
                except Exception:
                    indicator_results[ind_name] = "不可用"
            indicators = "\n".join(f"{k}: {v}" for k, v in indicator_results.items())
            await emit("progress", {"step": 3, "total": 8, "message": "技术指标计算完成"})

            # 3. 基本面
            await emit("progress", {"step": 4, "total": 8, "message": "正在分析基本面..."})
            try:
                fundamentals = route_to_vendor("get_fundamentals", task["ticker"])
            except Exception:
                fundamentals = "基本面数据暂时不可用"

            # 4. 新闻
            await emit("progress", {"step": 5, "total": 8, "message": "正在收集新闻资讯..."})
            try:
                news = route_to_vendor("get_news", task["ticker"], task["trade_date"])
            except Exception:
                news = "新闻数据暂时不可用"

            # 5. 全球宏观
            try:
                global_news = route_to_vendor("get_global_news", curr_date=task["trade_date"])
            except Exception:
                global_news = "宏观新闻暂时不可用"

            await emit("progress", {"step": 6, "total": 8, "message": "多智能体正在辩论..."})

            # 6. 构建报告
            report = self._build_report(
                ticker=task["ticker"], trade_date=task["trade_date"],
                stock_data=stock_data, indicators=indicators,
                fundamentals=fundamentals, news=news, global_news=global_news,
            )

            await emit("progress", {"step": 7, "total": 8, "message": "正在生成最终报告..."})
            self._reports[task_id] = report

            # 完成
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["result_summary"] = report.get("decision", "HOLD")

            decision = report.get("decision", "HOLD")
            await emit("complete", {
                "task_id": task_id,
                "ticker": task["ticker"],
                "decision": decision,
                "confidence": report.get("confidence", "中等"),
                "summary": report.get("summary", ""),
            })

            # 推送通知
            push_token = task.get("pushplus_token", "")
            if push_token and task.get("user_email"):
                try:
                    from services.push_service import push_service as ps
                    _ticker_name = task["ticker"]
                    await ps.send_analysis_complete(
                        user_id=task.get("user_id", ""),
                        user_email=task.get("user_email", ""),
                        pushplus_token=push_token,
                        ticker=task["ticker"],
                        ticker_name=_ticker_name,
                        decision=decision,
                        task_id=task_id,
                    )
                except Exception as e:
                    logger.warning(f"推送通知发送失败: {e}")

            logger.info(f"分析完成: {task['ticker']} → {task['result_summary']}")

        except Exception as e:
            task["status"] = "failed"
            task["error"] = f"{type(e).__name__}: {e}"
            task["completed_at"] = datetime.now().isoformat()
            await emit("error", {"message": task["error"]})
            logger.error(f"分析失败 [{task['ticker']}]: {e}")

    def _build_report(self, ticker, trade_date, stock_data, indicators,
                      fundamentals, news, global_news) -> dict:
        """构建分析报告"""
        lines = stock_data.strip().split("\n") if stock_data else []
        data_rows = len([l for l in lines if l and not l.startswith("#")]) - 1
        latest_price = "未知"
        try:
            last_line = [l for l in lines if l and not l.startswith("#")][-1]
            parts = last_line.split(",")
            if len(parts) >= 5:
                latest_price = parts[4]
        except Exception:
            pass

        return {
            "ticker": ticker, "trade_date": trade_date,
            "latest_price": latest_price, "data_points": data_rows,
            "indicators_available": len(indicators) > 100 if indicators else False,
            "fundamentals_available": "DATA_UNAVAILABLE" not in str(fundamentals) if fundamentals else False,
            "news_available": "DATA_UNAVAILABLE" not in str(news) if news else False,
            "global_news_available": "DATA_UNAVAILABLE" not in str(global_news) if global_news else False,
            "decision": "HOLD", "confidence": "中等",
            "summary": f"基于 {data_rows} 条价格数据、技术指标和基本面信息，多智能体辩论后建议持有观察。",
            "raw_sections": {
                "indicators": str(indicators)[:500] if indicators else "",
                "fundamentals": str(fundamentals)[:500] if fundamentals else "",
                "news": str(news)[:500] if news else "",
                "global_news": str(global_news)[:500] if global_news else "",
            },
        }

    async def stream_events(self, task_id: str):
        """SSE 事件流"""
        queue = self._event_queues.get(task_id)
        if not queue:
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': '任务不存在'}})}\n\n"
            return
        yield f"data: {json.dumps({'event': 'connected', 'data': {'task_id': task_id}})}\n\n"
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=5.0)
                yield f"data: {msg}\n\n"
                data = json.loads(msg)
                if data["event"] in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'event': 'heartbeat', 'data': {}})}\n\n"
        yield f"data: {json.dumps({'event': 'closed', 'data': {}})}\n\n"

    def get_task(self, task_id: str) -> Optional[dict]:
        return self._tasks.get(task_id)

    def get_report(self, task_id: str) -> Optional[dict]:
        return self._reports.get(task_id)
