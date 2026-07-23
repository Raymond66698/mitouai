"""
资金流向 + 龙虎榜 + 融资融券数据服务
"""
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger("mitouai.capital")

_cache: dict = {}


def _get_cache(key, ttl=300):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < ttl:
        return _cache[key]["data"]
    return None


def _set_cache(key, data):
    _cache[key] = {"ts": time.time(), "data": data}


class CapitalFlowService:

    # ═══════════════════════════════════════
    #  北向资金
    # ═══════════════════════════════════════

    def get_north_flow_today(self) -> dict:
        """今日北向资金流向"""
        try:
            import akshare as ak
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                net = float(latest.get("value", latest.get("当日成交净买额", 0)))
                date_str = str(latest.get("date", latest.get("日期", "")))
                # 最近5日
                last5 = []
                for _, r in df.tail(5).iterrows():
                    last5.append({
                        "date": str(r.get("date", r.get("日期", ""))),
                        "net_flow": float(r.get("value", r.get("当日成交净买额", 0))),
                    })
                return {
                    "date": date_str,
                    "net_flow": round(net, 2),
                    "unit": "亿元",
                    "recent_5days": last5,
                    "cumulative_20d": round(float(df.tail(20)["value"].sum()) if "value" in df.columns else 0, 2),
                }
        except Exception as e:
            logger.warning(f"获取北向资金失败: {e}")
        return {"date": "", "net_flow": 0, "unit": "亿元", "recent_5days": [], "cumulative_20d": 0}

    def get_north_flow_detail(self) -> list[dict]:
        """北向资金个股/行业明细（沪股通+深股通前十）"""
        try:
            import akshare as ak
            # 沪股通
            sh = ak.stock_hsgt_individual_em(stock_type="沪股通")
            sh_top = []
            if sh is not None and not sh.empty:
                for _, r in sh.head(10).iterrows():
                    sh_top.append({
                        "code": str(r.get("代码", "")),
                        "name": str(r.get("名称", "")),
                        "net_flow": float(r.get("净买入", r.get("净买入股数", 0))),
                        "market": "沪股通",
                    })

            sz = ak.stock_hsgt_individual_em(stock_type="深股通")
            sz_top = []
            if sz is not None and not sz.empty:
                for _, r in sz.head(10).iterrows():
                    sz_top.append({
                        "code": str(r.get("代码", "")),
                        "name": str(r.get("名称", "")),
                        "net_flow": float(r.get("净买入", r.get("净买入股数", 0))),
                        "market": "深股通",
                    })

            # 合并排序
            all_items = sh_top + sz_top
            all_items.sort(key=lambda x: abs(x["net_flow"]), reverse=True)
            return all_items[:20]
        except Exception as e:
            logger.warning(f"获取北向资金明细失败: {e}")
            return []

    def get_north_flow_sector(self) -> list[dict]:
        """北向资金行业流向"""
        try:
            import akshare as ak
            df = ak.stock_hsgt_sector_em()
            if df is not None and not df.empty:
                results = []
                for _, r in df.head(15).iterrows():
                    results.append({
                        "sector": str(r.get("名称", r.get("板块", ""))),
                        "net_flow": float(r.get("净流入", r.get("当日净买额", 0))),
                        "change_pct": float(r.get("涨跌幅", 0)) if r.get("涨跌幅") else 0,
                    })
                results.sort(key=lambda x: x["net_flow"], reverse=True)
                return results
        except Exception as e:
            logger.warning(f"获取北向行业流向失败: {e}")
            return []

    # ═══════════════════════════════════════
    #  主力资金流向
    # ═══════════════════════════════════════

    def get_major_capital_flow(self) -> dict:
        """主力资金流向（全市场 + 行业排行）"""
        result = {"summary": {}, "top_stocks": [], "sectors": []}
        try:
            import akshare as ak
            # 全市场资金流
            df_market = ak.stock_market_fund_flow()
            if df_market is not None and not df_market.empty:
                latest = df_market.iloc[-1] if len(df_market) > 0 else df_market.iloc[0]
                result["summary"] = {
                    "date": str(latest.get("日期", "")),
                    "main_net_inflow": float(latest.get("主力净流入-净额", 0)),
                    "super_large_net": float(latest.get("超大单净流入-净额", 0)),
                    "large_net": float(latest.get("大单净流入-净额", 0)),
                }

            # 个股排行
            df_individual = ak.stock_individual_fund_flow_rank(indicator="今日")
            if df_individual is not None and not df_individual.empty:
                for _, r in df_individual.head(10).iterrows():
                    result["top_stocks"].append({
                        "code": str(r.get("代码", "")),
                        "name": str(r.get("名称", "")),
                        "main_net": float(r.get("主力净流入-净额", 0)),
                    })

            # 行业排行
            df_sector = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            if df_sector is not None and not df_sector.empty:
                for _, r in df_sector.head(10).iterrows():
                    result["sectors"].append({
                        "name": str(r.get("名称", "")),
                        "main_net": float(r.get("主力净流入-净额", 0)),
                    })
            result["sectors"].sort(key=lambda x: x["main_net"], reverse=True)
        except Exception as e:
            logger.warning(f"获取主力资金流向失败: {e}")
        return result

    # ═══════════════════════════════════════
    #  龙虎榜
    # ═══════════════════════════════════════

    def get_dragon_tiger_list(self, date: str = "") -> list[dict]:
        """获取龙虎榜数据"""
        try:
            import akshare as ak
            if not date:
                date = datetime.now().strftime("%Y%m%d")
            else:
                date = date.replace("-", "")

            df = ak.stock_sina_lhb_detail_daily(trade_date=date)
            if df is not None and not df.empty:
                results = []
                for _, r in df.head(30).iterrows():
                    results.append({
                        "code": str(r.get("代码", "")),
                        "name": str(r.get("名称", "")),
                        "reason": str(r.get("上榜原因", "")),
                        "close": float(r.get("收盘价", 0)),
                        "change_pct": float(r.get("涨跌幅", 0)),
                        "turnover": float(r.get("换手率", 0)) if r.get("换手率") else 0,
                        "buy_amount": float(r.get("买入额", 0)) if r.get("买入额") else 0,
                        "sell_amount": float(r.get("卖出额", 0)) if r.get("卖出额") else 0,
                    })
                return results
        except Exception as e:
            logger.warning(f"获取龙虎榜失败: {e}")
            return self._fallback_dragon_tiger()

    def _fallback_dragon_tiger(self) -> list[dict]:
        """龙虎榜兜底数据"""
        return []

    def get_dragon_tiger_institutions(self) -> list[dict]:
        """龙虎榜机构席位分析"""
        try:
            import akshare as ak
            df = ak.stock_lhb_stock_statistic_em()
            if df is not None and not df.empty:
                results = []
                for _, r in df.head(20).iterrows():
                    results.append({
                        "code": str(r.get("代码", "")),
                        "name": str(r.get("名称", "")),
                        "appear_count": int(r.get("上榜次数", 0)) if r.get("上榜次数") else 0,
                        "total_buy": float(r.get("买入总计", 0)) if r.get("买入总计") else 0,
                        "total_sell": float(r.get("卖出总计", 0)) if r.get("卖出总计") else 0,
                    })
                return results
        except Exception:
            return []

    # ═══════════════════════════════════════
    #  融资融券
    # ═══════════════════════════════════════

    def get_margin_trading(self) -> dict:
        """融资融券数据"""
        try:
            import akshare as ak
            df = ak.stock_margin_detail_sse(start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
                                            end_date=datetime.now().strftime("%Y%m%d"))
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                total = float(df.iloc[-1:]["融资余额"].sum()) if "融资余额" in df.columns else 0
                return {
                    "date": str(latest.get("信用交易日期", latest.get("日期", ""))),
                    "margin_balance": float(latest.get("融资余额", 0)),
                    "short_balance": float(latest.get("融券余量金额", 0)) if "融券余量金额" in latest else 0,
                }
        except Exception as e:
            logger.warning(f"获取融资融券失败: {e}")
        return {"margin_balance": 0, "short_balance": 0}


capital_flow_service = CapitalFlowService()
