"""
每日AI市场播报服务
聚合：指数涨跌、成交额、北向资金、板块热力图、要闻摘要 → AI解读
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("mitouai.daily_brief")


class DailyBriefService:
    """每日播报服务"""

    def __init__(self):
        self._cache: dict = {}
        self._cache_ttl = 600  # 10分钟缓存

    def _get_data_service(self):
        from services.data_service import DataService
        return DataService()

    def _call_ai(self, prompt: str, system: str = "") -> str:
        """调用AI模型生成解读"""
        try:
            from config import settings
            import os

            api_key = settings.LLM_API_KEY or os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key:
                return ""

            import requests
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system or "你是一位专业的A股市场分析师，请用简洁专业的语言回答。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"AI调用失败: {resp.status_code}")
                return ""
        except Exception as e:
            logger.warning(f"AI调用异常: {e}")
            return ""

    # ═══════════════════════════════════════════════
    #  每日市场快照
    # ═══════════════════════════════════════════════

    def get_market_overview(self) -> dict:
        """获取市场全貌"""
        cache_key = "market_overview"
        now = time.time()
        if cache_key in self._cache and now - self._cache[cache_key]["ts"] < self._cache_ttl:
            return self._cache[cache_key]["data"]

        ds = self._get_data_service()

        result = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "indices": [],
            "market_stats": {},
            "north_flow": {},
            "top_sectors": [],
            "bottom_sectors": [],
        }

        # 指数
        try:
            result["indices"] = ds.get_market_indices()
        except Exception as e:
            logger.warning(f"获取指数失败: {e}")

        # 市场统计（涨跌家数、成交额）
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                up_count = len(df[df["涨跌幅"] > 0])
                down_count = len(df[df["涨跌幅"] < 0])
                flat_count = len(df) - up_count - down_count
                total_amount = df["成交额"].sum() / 1e8  # 转为亿
                result["market_stats"] = {
                    "total_stocks": len(df),
                    "up_count": up_count,
                    "down_count": down_count,
                    "flat_count": flat_count,
                    "total_amount_yi": round(total_amount, 0),
                    "up_ratio": round(up_count / len(df) * 100, 1) if len(df) > 0 else 0,
                }
        except Exception as e:
            logger.warning(f"获取市场统计失败: {e}")

        # 北向资金
        try:
            result["north_flow"] = ds.get_north_flow()
        except Exception as e:
            logger.warning(f"获取北向资金失败: {e}")

        # 板块排行
        try:
            sectors = ds.get_sector_performance()
            if sectors:
                result["top_sectors"] = sectors[:5]
                result["bottom_sectors"] = sectors[-5:]
        except Exception as e:
            logger.warning(f"获取板块排行失败: {e}")

        self._cache[cache_key] = {"ts": now, "data": result}
        return result

    # ═══════════════════════════════════════════════
    #  AI市场解读
    # ═══════════════════════════════════════════════

    def get_ai_interpretation(self) -> dict:
        """获取AI对当前市场的解读"""
        overview = self.get_market_overview()

        # 构建提示词
        idx_str = "\n".join([
            f"- {i['name']}: {i['value']:.0f} ({i['change']:+.2f}%)"
            for i in overview.get("indices", [])[:4]
        ])

        stats = overview.get("market_stats", {})
        stats_str = f"上涨{stats.get('up_count',0)}家, 下跌{stats.get('down_count',0)}家, 成交额{stats.get('total_amount_yi',0):.0f}亿"

        top_sec = ", ".join([
            f"{s['name']}({s['change_pct']:+.1f}%)"
            for s in overview.get("top_sectors", [])[:5]
        ])
        btm_sec = ", ".join([
            f"{s['name']}({s['change_pct']:+.1f}%)"
            for s in overview.get("bottom_sectors", [])[:5]
        ])

        nf = overview.get("north_flow", {})
        nf_str = f"北向资金净{'流入' if nf.get('net_flow',0) >= 0 else '流出'}{abs(nf.get('net_flow',0)):.1f}亿" if nf else ""

        prompt = f"""请根据以下A股市场数据，用中文写一段200字以内的市场综述：

【主要指数】
{idx_str}

【市场情绪】
{stats_str}

【领涨板块】
{top_sec}

【领跌板块】
{btm_sec}

【资金面】
{nf_str}

请简明扼要地分析市场走势、资金动向和风格切换。不要使用markdown标题。"""

        ai_text = self._call_ai(prompt, "你是A股市场首席分析师，用简洁专业的语言解读市场，每条用一句话概括核心要点。")

        return {
            "overview": overview,
            "ai_summary": ai_text or self._fallback_summary(overview),
            "generated_at": datetime.now().isoformat(),
        }

    def _fallback_summary(self, overview: dict) -> str:
        """AI不可用时的兜底摘要"""
        indices = overview.get("indices", [])
        stats = overview.get("market_stats", {})
        top_sec = overview.get("top_sectors", [])

        parts = []
        if indices:
            up_idx = [i for i in indices if i.get("change", 0) > 0]
            down_idx = [i for i in indices if i.get("change", 0) < 0]
            if len(up_idx) > len(down_idx):
                parts.append("今日市场整体偏强，多数指数收红。")
            else:
                parts.append("今日市场震荡调整，指数表现分化。")

        if stats:
            parts.append(f"两市共{stats.get('up_count',0)}只个股上涨，{stats.get('down_count',0)}只下跌，成交额约{stats.get('total_amount_yi',0):.0f}亿元。")

        if top_sec:
            parts.append(f"领涨板块为{top_sec[0]['name']}（{top_sec[0]['change_pct']:+.1f}%）。")

        return " ".join(parts) if parts else "市场数据更新中，请稍后刷新。"

    # ═══════════════════════════════════════════════
    #  个股事件提醒
    # ═══════════════════════════════════════════════

    def get_today_events(self, limit: int = 20) -> list[dict]:
        """获取今日重要事件（财报预告、限售解禁、股东大会等）"""
        events = []
        try:
            import akshare as ak

            # 财报披露
            try:
                df = ak.stock_yjbb_em(date=datetime.now().strftime("%Y%m%d"))
                if df is not None and not df.empty:
                    for _, row in df.head(10).iterrows():
                        events.append({
                            "type": "财报",
                            "code": str(row.get("股票代码", "")),
                            "name": str(row.get("股票简称", "")),
                            "title": f"财报披露",
                            "detail": f"营收同比增长{row.get('营业收入同比增长','--')}，净利同比增长{row.get('净利润同比增长','--')}",
                            "date": str(row.get("报告期", "")),
                        })
            except Exception:
                pass

            # 限售解禁
            try:
                df2 = ak.stock_restricted_release_queue_em(symbol="全部")
                if df2 is not None and not df2.empty:
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    for _, row in df2.head(10).iterrows():
                        if str(row.get("解禁日期", "")) == today_str:
                            events.append({
                                "type": "解禁",
                                "code": str(row.get("股票代码", "")),
                                "name": str(row.get("股票简称", "")),
                                "title": f"限售股解禁",
                                "detail": f"解禁数量{row.get('解禁数量','--')}股",
                                "date": today_str,
                            })
            except Exception:
                pass

            # 分红实施
            try:
                df3 = ak.stock_dividents_em()
                if df3 is not None and not df3.empty:
                    for _, row in df3.head(10).iterrows():
                        events.append({
                            "type": "分红",
                            "code": str(row.get("代码", "")),
                            "name": str(row.get("名称", "")),
                            "title": f"分红方案",
                            "detail": str(row.get("方案进度", row.get("分红方案", ""))),
                            "date": str(row.get("除权除息日", "")),
                        })
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"获取今日事件失败: {e}")

        # 按日期排序，取最近
        events.sort(key=lambda x: x.get("date", ""), reverse=True)
        return events[:limit]

    # ═══════════════════════════════════════════════
    #  概念板块异动
    # ═══════════════════════════════════════════════

    def get_concept_movers(self) -> list[dict]:
        """获取概念板块异动排行"""
        try:
            import akshare as ak
            df = ak.stock_board_concept_name_em()
            results = []
            for _, row in df.head(20).iterrows():
                results.append({
                    "name": str(row.get("板块名称", "")),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "up_count": int(row.get("上涨家数", 0)),
                    "down_count": int(row.get("下跌家数", 0)),
                    "leader": str(row.get("领涨股票", "")),
                    "turnover": float(row.get("换手率", 0)) if row.get("换手率") else 0,
                })
            results.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
            return results[:15]
        except Exception as e:
            logger.warning(f"获取概念板块失败: {e}")
            return []


# 单例
daily_brief_service = DailyBriefService()
