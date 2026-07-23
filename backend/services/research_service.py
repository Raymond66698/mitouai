"""
AI研报聚合服务
聚合多家券商研报、提炼核心观点、一致预期、机构评级
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("mitouai.research")


class ResearchService:
    """研报聚合服务"""

    def __init__(self):
        self._cache: dict = {}
        self._cache_ttl = 1800  # 30分钟缓存

    def _call_ai(self, prompt: str, system: str = "") -> str:
        """调用AI"""
        try:
            from config import settings
            import os, requests

            api_key = settings.LLM_API_KEY or os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key:
                return ""

            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system or "你是资深证券分析师，擅长提炼研报核心观点。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"AI调用异常: {e}")
        return ""

    # ═══════════════════════════════════════════════
    #  个股研报聚合
    # ═══════════════════════════════════════════════

    def get_stock_research(self, ticker: str) -> dict:
        """获取个股研报聚合"""
        code = ticker.split(".")[0]
        result = {
            "ticker": ticker,
            "reports": [],
            "ai_summary": "",
            "consensus": {},
            "ratings_summary": {},
        }

        try:
            import akshare as ak

            # 获取最近研报
            df = ak.stock_research_report_em(symbol=code)
            if df is not None and not df.empty:
                reports = []
                for _, row in df.head(15).iterrows():
                    reports.append({
                        "title": str(row.get("研究报告名称", "")),
                        "org": str(row.get("研究机构", "")),
                        "author": str(row.get("作者", "")),
                        "date": str(row.get("发布日期", "")),
                        "rating": str(row.get("评级", row.get("投资评级", ""))),
                        "target_price": float(row.get("目标价", 0)) if row.get("目标价") else None,
                        "current_price": float(row.get("最新价", 0)) if row.get("最新价") else None,
                        "pages": int(row.get("页数", 0)) if row.get("页数") else None,
                    })
                result["reports"] = reports

                # 统计评级分布
                rating_counts = {}
                for r in reports:
                    rating = r.get("rating", "未评级")
                    rating_counts[rating] = rating_counts.get(rating, 0) + 1
                result["ratings_summary"] = rating_counts

                # AI提炼核心观点
                if len(reports) >= 3:
                    recent_reports = reports[:8]
                    report_text = "\n\n".join([
                        f"[{r['org']}] {r['title']} - 评级:{r['rating']} 目标价:{r.get('target_price','未给出')}"
                        for r in recent_reports
                    ])
                    prompt = f"""以下是{ticker}最近的券商研报标题和评级：

{report_text}

请用200字以内中文总结：
1. 多数机构对这只股票的核心观点是什么
2. 目标价的区间和中枢
3. 主要看多逻辑和风险提示
不要使用markdown标题。"""
                    result["ai_summary"] = self._call_ai(prompt, "你是资深证券分析师。")

            # 一致预期
            try:
                cn_df = ak.stock_profit_forecast_em(symbol=code)
                if cn_df is not None and not cn_df.empty:
                    latest = cn_df.iloc[-1]
                    result["consensus"] = {
                        "revenue_forecast": float(latest.get("预测营业收入", 0)) if latest.get("预测营业收入") else None,
                        "profit_forecast": float(latest.get("预测净利润", 0)) if latest.get("预测净利润") else None,
                        "eps_forecast": float(latest.get("预测每股收益", 0)) if latest.get("预测每股收益") else None,
                        "pe_forecast": float(latest.get("预测市盈率", 0)) if latest.get("预测市盈率") else None,
                        "institutions": int(latest.get("预测机构数", 0)) if latest.get("预测机构数") else 0,
                    }
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"获取研报失败 [{ticker}]: {e}")

        return result

    # ═══════════════════════════════════════════════
    #  热门研报（全市场）
    # ═══════════════════════════════════════════════

    def get_hot_research(self, limit: int = 20) -> list[dict]:
        """获取今日热门研报"""
        cache_key = "hot_research"
        now = time.time()
        if cache_key in self._cache and now - self._cache[cache_key]["ts"] < self._cache_ttl:
            return self._cache[cache_key]["data"]

        reports = []
        try:
            import akshare as ak
            # 获取全部最新研报
            df = ak.stock_research_report_em()
            if df is not None and not df.empty:
                for _, row in df.head(limit).iterrows():
                    reports.append({
                        "title": str(row.get("研究报告名称", "")),
                        "org": str(row.get("研究机构", "")),
                        "author": str(row.get("作者", "")),
                        "date": str(row.get("发布日期", "")),
                        "code": str(row.get("股票代码", "")),
                        "name": str(row.get("股票简称", "")),
                        "rating": str(row.get("评级", row.get("投资评级", ""))),
                        "target_price": float(row.get("目标价", 0)) if row.get("目标价") else None,
                    })
        except Exception as e:
            logger.warning(f"获取热门研报失败: {e}")

        self._cache[cache_key] = {"ts": now, "data": reports}
        return reports

    # ═══════════════════════════════════════════════
    #  产业链分析
    # ═══════════════════════════════════════════════

    def get_industry_chain(self, ticker: str) -> dict:
        """获取个股产业链相关数据"""
        code = ticker.split(".")[0]
        result = {
            "ticker": ticker,
            "industry": "",
            "peers": [],
            "suppliers": [],
            "customers": [],
        }

        try:
            import akshare as ak

            # 行业分类
            try:
                ind_df = ak.stock_board_industry_cons_em(symbol="申万行业")
                if ind_df is not None and not ind_df.empty:
                    row = ind_df[ind_df["代码"] == code]
                    if not row.empty:
                        result["industry"] = str(row.iloc[0].get("板块名称", ""))
            except Exception:
                pass

            # 同行业可比公司
            try:
                if result["industry"]:
                    peers_df = ak.stock_board_industry_cons_em(symbol=result["industry"])
                    if peers_df is not None and not peers_df.empty:
                        result["peers"] = [
                            {"code": str(r.get("代码", "")), "name": str(r.get("名称", ""))}
                            for _, r in peers_df.head(20).iterrows()
                        ]
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"获取产业链数据失败 [{ticker}]: {e}")

        return result


# 单例
research_service = ResearchService()
