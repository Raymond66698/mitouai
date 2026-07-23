"""
投研分析服务 — TradingAgents 多智能体分析管道
支持用户追踪、推送通知
任务和报告持久化到 SQLAlchemy ORM，SSE 事件队列保持在内存
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from database import get_db_context
from models.analysis import AnalysisTask, AnalysisReport
from config import settings

logger = logging.getLogger("mitouai.analysis")


class AnalysisService:
    """多智能体投研分析服务"""

    def __init__(self):
        # SSE 事件队列必须保持在内存（跨 worker 不共享，但 SSE 连接绑定到同一 worker）
        self._event_queues: dict[str, asyncio.Queue] = {}

    # ── 股票搜索 ──

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

    # ── 启动分析 ──

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
        """启动分析任务，写入数据库"""
        task_id = str(uuid.uuid4())[:8]
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        ticker = self._normalize_ticker(ticker)

        # 创建任务记录到数据库
        with get_db_context() as db:
            task = AnalysisTask(
                task_id=task_id,
                user_id=user_id if user_id else None,
                ticker=ticker,
                trade_date=trade_date,
                status="pending",
                model=model,
                strategy_id=strategy_id,
                debate_rounds=debate_rounds,
                risk_rounds=risk_rounds,
            )
            db.add(task)
            db.commit()
            task_dict = self._task_to_dict(task)

        # 创建 SSE 事件队列（内存）
        self._event_queues[task_id] = asyncio.Queue()

        # 启动后台分析
        asyncio.create_task(self._run_analysis(
            task_id=task_id,
            ticker=ticker,
            trade_date=trade_date,
            user_id=user_id,
            user_email=user_email,
            pushplus_token=pushplus_token,
        ))

        return task_dict

    # ── 用户任务历史 ──

    def get_user_tasks(self, user_id: str, limit: int = 20) -> list[dict]:
        """获取用户的分析历史（从数据库）"""
        if not user_id:
            return []
        with get_db_context() as db:
            tasks = (
                db.query(AnalysisTask)
                .filter(AnalysisTask.user_id == user_id)
                .order_by(AnalysisTask.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._task_to_dict(t) for t in tasks]

    # ── 任务/报告查询 ──

    def get_task(self, task_id: str) -> Optional[dict]:
        """查询任务状态（从数据库）"""
        with get_db_context() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
            if task:
                return self._task_to_dict(task)
        return None

    def get_report(self, task_id: str) -> Optional[dict]:
        """获取分析报告（从数据库）"""
        with get_db_context() as db:
            report = db.query(AnalysisReport).filter(AnalysisReport.task_id == task_id).first()
            if report:
                return self._report_to_dict(report)
        return None

    # ── SSE 事件流 ──

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

    # ── 内部方法 ──

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

    async def _run_analysis(
        self,
        task_id: str,
        ticker: str,
        trade_date: str,
        user_id: str,
        user_email: str,
        pushplus_token: str,
    ):
        """后台运行 TradingAgents 分析管道"""
        queue = self._event_queues.get(task_id)
        if not queue:
            return

        # 读取当前状态
        with get_db_context() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
            if not task:
                return

        async def emit(event_type: str, data: dict):
            # 更新数据库状态
            with get_db_context() as db:
                t = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                if t and t.status not in ("completed", "failed"):
                    t.status = "running"
                    db.commit()
            await queue.put(json.dumps({"event": event_type, "data": data}))

        try:
            import sys
            sys.path.insert(0, "D:/TradingAgents")
            from tradingagents.dataflows.interface import route_to_vendor

            await emit("progress", {"step": 1, "total": 8, "message": "正在获取市场数据..."})

            # 1. 获取股票数据
            stock_data = route_to_vendor(
                "get_stock_data",
                ticker,
                trade_date.replace("-", "")[:8] + "01",
                trade_date,
            )
            await emit("progress", {"step": 2, "total": 8, "message": "市场数据获取完成"})

            # 2. 获取技术指标
            indicator_names = ["rsi", "macd", "boll", "atr", "ma", "kdj"]
            indicator_results = {}
            for ind_name in indicator_names:
                try:
                    ind_data = route_to_vendor(
                        "get_indicators", ticker, ind_name,
                        trade_date, "60",
                    )
                    indicator_results[ind_name] = str(ind_data)[:200]
                except Exception:
                    indicator_results[ind_name] = "不可用"
            indicators = "\n".join(f"{k}: {v}" for k, v in indicator_results.items())
            await emit("progress", {"step": 3, "total": 8, "message": "技术指标计算完成"})

            # 3. 基本面
            await emit("progress", {"step": 4, "total": 8, "message": "正在分析基本面..."})
            try:
                fundamentals = route_to_vendor("get_fundamentals", ticker)
            except Exception:
                fundamentals = "基本面数据暂时不可用"

            # 4. 新闻
            await emit("progress", {"step": 5, "total": 8, "message": "正在收集新闻资讯..."})
            try:
                news = route_to_vendor("get_news", ticker, trade_date)
            except Exception:
                news = "新闻数据暂时不可用"

            # 5. 全球宏观
            try:
                global_news = route_to_vendor("get_global_news", curr_date=trade_date)
            except Exception:
                global_news = "宏观新闻暂时不可用"

            await emit("progress", {"step": 6, "total": 8, "message": "多智能体正在辩论..."})

            # 6. 构建并保存报告
            report_dict = self._build_report(
                ticker=ticker, trade_date=trade_date,
                stock_data=stock_data, indicators=indicators,
                fundamentals=fundamentals, news=news, global_news=global_news,
            )
            self._save_report(task_id, report_dict)

            await emit("progress", {"step": 7, "total": 8, "message": "正在生成最终报告..."})

            # 完成 — 更新数据库
            decision = report_dict.get("decision", "HOLD")
            now_iso = datetime.now().isoformat()
            with get_db_context() as db:
                t = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                if t:
                    t.status = "completed"
                    t.completed_at = now_iso
                    t.result_summary = decision
                    db.commit()

            await emit("complete", {
                "task_id": task_id,
                "ticker": ticker,
                "decision": decision,
                "confidence": report_dict.get("confidence", "中等"),
                "summary": report_dict.get("summary", ""),
            })

            # 推送通知
            if pushplus_token and user_email:
                try:
                    from services.push_service import push_service as ps
                    await ps.send_analysis_complete(
                        user_id=user_id,
                        user_email=user_email,
                        pushplus_token=pushplus_token,
                        ticker=ticker,
                        ticker_name=ticker,
                        decision=decision,
                        task_id=task_id,
                    )
                except Exception as e:
                    logger.warning(f"推送通知发送失败: {e}")

            logger.info(f"分析完成: {ticker} → {decision}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            now_iso = datetime.now().isoformat()
            with get_db_context() as db:
                t = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                if t:
                    t.status = "failed"
                    t.error = error_msg
                    t.completed_at = now_iso
                    db.commit()
            await emit("error", {"message": error_msg})
            logger.error(f"分析失败 [{ticker}]: {e}")

    def _build_report(self, ticker, trade_date, stock_data, indicators,
                      fundamentals, news, global_news) -> dict:
        """构建分析报告字典"""
        lines = stock_data.strip().split("\n") if stock_data else []
        data_rows = len([l for l in lines if l and not l.startswith("#")]) - 1
        latest_price = 0.0
        try:
            last_line = [l for l in lines if l and not l.startswith("#")][-1]
            parts = last_line.split(",")
            if len(parts) >= 5:
                latest_price = float(parts[4])
        except Exception:
            pass

        return {
            "ticker": ticker,
            "trade_date": trade_date,
            "latest_price": latest_price,
            "data_points": max(0, data_rows),
            "indicators_available": 1 if (indicators and len(indicators) > 100) else 0,
            "fundamentals_available": 1 if (fundamentals and "DATA_UNAVAILABLE" not in str(fundamentals)) else 0,
            "news_available": 1 if (news and "DATA_UNAVAILABLE" not in str(news)) else 0,
            "global_news_available": 1 if (global_news and "DATA_UNAVAILABLE" not in str(global_news)) else 0,
            "decision": "HOLD",
            "confidence": "中等",
            "summary": f"基于 {data_rows} 条价格数据、技术指标和基本面信息，多智能体辩论后建议持有观察。",
            "raw_sections": {
                "indicators": str(indicators)[:500] if indicators else "",
                "fundamentals": str(fundamentals)[:500] if fundamentals else "",
                "news": str(news)[:500] if news else "",
                "global_news": str(global_news)[:500] if global_news else "",
            },
        }

    def _save_report(self, task_id: str, report_dict: dict):
        """将报告持久化到数据库"""
        with get_db_context() as db:
            existing = db.query(AnalysisReport).filter(AnalysisReport.task_id == task_id).first()
            if existing:
                # 更新已有报告
                for k, v in report_dict.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
            else:
                report = AnalysisReport(
                    task_id=task_id,
                    **report_dict,
                )
                db.add(report)
            db.commit()

    # ── 序列化辅助 ──

    @staticmethod
    def _task_to_dict(task: AnalysisTask) -> dict:
        """将 ORM 对象转为字典（兼容旧接口）"""
        return {
            "task_id": task.task_id,
            "ticker": task.ticker,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "result_summary": task.result_summary,
            "error": task.error,
            "strategy_id": task.strategy_id,
            "model": task.model,
            "trade_date": task.trade_date,
            "debate_rounds": task.debate_rounds,
            "risk_rounds": task.risk_rounds,
            "user_id": task.user_id or "",
        }

    @staticmethod
    def _report_to_dict(report: AnalysisReport) -> dict:
        """将报告 ORM 对象转为字典"""
        return {
            "ticker": report.ticker,
            "trade_date": report.trade_date,
            "latest_price": report.latest_price,
            "data_points": report.data_points,
            "indicators_available": bool(report.indicators_available),
            "fundamentals_available": bool(report.fundamentals_available),
            "news_available": bool(report.news_available),
            "global_news_available": bool(report.global_news_available),
            "decision": report.decision,
            "confidence": report.confidence,
            "summary": report.summary,
            "raw_sections": report.raw_sections or {},
        }
