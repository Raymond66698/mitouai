"""
多因子智能选股器服务
支持：条件筛选、多因子评分排名、自然语言选股、策略模板应用
"""
import json
import logging
import math
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger("mitouai.screener")

# 行业分类映射（简单版，基于代码前缀）
INDUSTRY_MAP = {}  # 运行时从 akshare 加载

# 选股条件默认权重
DEFAULT_WEIGHTS = {
    "value": 0.25,      # 价值因子（PE/PB/PS）
    "growth": 0.20,     # 成长因子（营收/利润增速）
    "quality": 0.25,    # 质量因子（ROE/利润率/负债）
    "momentum": 0.15,   # 动量因子（涨跌幅/换手率）
    "risk": 0.15,       # 风险因子（波动率/市值）
}


class StockScreener:
    """多因子选股器"""

    def __init__(self):
        from services.data_service import data_service as ds
        self.ds = ds

    def search_by_conditions(self, conditions: dict, top_n: int = 30) -> dict:
        """按条件筛选股票

        conditions 支持的字段:
            min_pe, max_pe: 市盈率范围
            min_pb, max_pb: 市净率范围
            min_roe, max_roe: ROE范围
            min_mv, max_mv: 总市值范围（亿）
            min_revenue_growth: 最低营收增速(%)
            min_profit_growth: 最低利润增速(%)
            max_debt_ratio: 最高资产负债率(%)
            min_dividend_yield: 最低股息率(%)
            min_turnover: 最低换手率(%)
            max_turnover: 最高换手率(%)
            change_min, change_max: 涨跌幅范围(%)
            sector: 行业名称关键词
            exclude_st: 排除ST（默认True）
            sort_by: 排序字段
            model: 大师策略模板ID（覆盖条件）
        """
        # 获取全市场快照
        stocks = self.ds.get_all_stocks_snapshot()
        if not stocks:
            return {"results": [], "total": 0, "message": "数据获取失败，请稍后重试"}

        filtered = []
        for s in stocks:
            if not self._pass_filters(s, conditions):
                continue
            # 计算综合得分
            score = self._calculate_score(s, conditions)
            s["score"] = round(score, 1)
            filtered.append(s)

        # 排序
        sort_by = conditions.get("sort_by", "score")
        reverse = sort_by != "pe"  # PE越低越好
        filtered.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        # 截取
        total = len(filtered)
        results = filtered[:top_n]

        # 添加排名
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return {
            "results": results,
            "total": total,
            "total_scanned": len(stocks),
            "timestamp": datetime.now().isoformat(),
        }

    def natural_language_search(self, query: str, top_n: int = 20) -> dict:
        """自然语言选股（用LLM解析意图转为条件）"""
        conditions = self._parse_nl_query(query)
        conditions["nl_query"] = query
        result = self.search_by_conditions(conditions, top_n)
        result["parsed_conditions"] = conditions
        return result

    def _parse_nl_query(self, query: str) -> dict:
        """用LLM解析自然语言选股意图 → 结构化条件"""
        try:
            from core.llm_client import llm

            prompt = f"""你是一个股票选股条件解析器。将用户的自然语言描述转换为JSON格式的筛选条件。

支持的字段（可选，不需要全部填写）:
- min_pe, max_pe: 市盈率范围（数字）
- min_pb, max_pb: 市净率范围（数字）
- min_roe: 最低ROE（百分比数字，如15表示15%）
- min_mv: 最低总市值（亿元，数字）
- max_mv: 最高总市值（亿元，数字）
- min_revenue_growth: 最低营收增速（百分比数字）
- min_profit_growth: 最低利润增速（百分比数字）
- max_debt_ratio: 最高资产负债率（百分比数字）
- min_dividend_yield: 最低股息率（百分比数字）
- min_turnover: 最低换手率（百分比数字）
- change_min, change_max: 涨跌幅范围（百分比数字，正数为涨）
- sector: 行业关键词（如"医药"、"新能源"、"白酒"、"半导体"等）
- exclude_st: 排除ST（默认true）
- sort_by: 排序字段（score/pe/pb/change_pct/market_cap）

用户输入: {query}

请只返回JSON，不要其他文字。如果你不确定某个条件，就不包含该字段。
示例输出: {{"min_pe": 5, "max_pe": 20, "min_roe": 15, "sector": "白酒"}}
"""

            messages = [{"role": "user", "content": prompt}]
            response = llm.chat(messages, temperature=0.1, max_tokens=500)

            # 提取 JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            conditions = json.loads(json_str)
            # 清理：只保留合法的数值
            clean = {}
            numeric_fields = [
                "min_pe", "max_pe", "min_pb", "max_pb", "min_roe",
                "min_mv", "max_mv", "min_revenue_growth", "min_profit_growth",
                "max_debt_ratio", "min_dividend_yield", "min_turnover", "max_turnover",
                "change_min", "change_max",
            ]
            for k, v in conditions.items():
                if k in numeric_fields:
                    try:
                        clean[k] = float(v)
                    except (ValueError, TypeError):
                        pass
                elif k in ("sector", "sort_by"):
                    clean[k] = str(v)
                elif k == "exclude_st":
                    clean[k] = bool(v)
            return clean
        except Exception as e:
            logger.warning(f"NL解析失败: {e}, 用关键词匹配")
            # LLM不可用时用简单关键词匹配
            return self._keyword_match(query)

    def _keyword_match(self, query: str) -> dict:
        """简单的关键词匹配回退方案"""
        conditions = {"exclude_st": True}
        q = query.lower()

        # PE相关
        if "低估值" in q or "低市盈率" in q or "便宜" in q:
            conditions["max_pe"] = 15
        elif "合理估值" in q:
            conditions["min_pe"] = 10
            conditions["max_pe"] = 30

        # PB
        if "破净" in q:
            conditions["max_pb"] = 1.0

        # ROE
        if "高roe" in q or "roe高" in q:
            conditions["min_roe"] = 15

        # 市值
        if "大盘" in q or "蓝筹" in q:
            conditions["min_mv"] = 500
        elif "小盘" in q:
            conditions["max_mv"] = 100
        elif "中盘" in q:
            conditions["min_mv"] = 50
            conditions["max_mv"] = 500

        # 成长
        if "高成长" in q or "成长股" in q:
            conditions["min_revenue_growth"] = 20
            conditions["min_profit_growth"] = 20

        # 股息
        if "高股息" in q or "分红" in q:
            conditions["min_dividend_yield"] = 2

        # 行业
        sectors = ["医药", "白酒", "新能源", "半导体", "芯片", "银行", "保险",
                    "地产", "军工", "农业", "消费", "科技", "汽车", "电力", "煤炭"]
        for s in sectors:
            if s in query:
                conditions["sector"] = s
                break

        # 跌幅
        if "超跌" in q:
            conditions["change_max"] = -5
        elif "涨幅" in q:
            conditions["change_min"] = 3

        # 活跃
        if "活跃" in q or "放量" in q:
            conditions["min_turnover"] = 3

        return conditions

    def _pass_filters(self, stock: dict, conditions: dict) -> bool:
        """检查股票是否通过所有筛选条件"""
        try:
            # ST排除
            if conditions.get("exclude_st", True):
                if "ST" in stock.get("name", "") or "*ST" in stock.get("name", ""):
                    return False

            # PE范围
            pe = stock.get("pe")
            if "min_pe" in conditions and (pe is None or pe < conditions["min_pe"]):
                return False
            if "max_pe" in conditions and (pe is None or pe > conditions["max_pe"]):
                return False
            # PE不能为负
            if ("min_pe" in conditions or "max_pe" in conditions) and pe and pe <= 0:
                return False

            # PB范围
            pb = stock.get("pb")
            if "min_pb" in conditions and (pb is None or pb < conditions["min_pb"]):
                return False
            if "max_pb" in conditions and (pb is None or pb > conditions["max_pb"]):
                return False
            if ("min_pb" in conditions or "max_pb" in conditions) and pb and pb <= 0:
                return False

            # 市值范围（亿元）
            mv = stock.get("total_mv", 0)
            mv_yi = mv / 1e8 if mv else 0
            if "min_mv" in conditions and mv_yi < conditions["min_mv"]:
                return False
            if "max_mv" in conditions and mv_yi > conditions["max_mv"]:
                return False

            # 涨跌幅
            chg = stock.get("change_pct", 0)
            if "change_min" in conditions and chg < conditions["change_min"]:
                return False
            if "change_max" in conditions and chg > conditions["change_max"]:
                return False

            # 换手率
            to = stock.get("turnover", 0)
            if "min_turnover" in conditions and to < conditions["min_turnover"]:
                return False
            if "max_turnover" in conditions and to > conditions["max_turnover"]:
                return False

            # 行业
            sector_kw = conditions.get("sector")
            if sector_kw:
                name = stock.get("name", "")
                code = stock.get("code", "")
                if sector_kw not in name and sector_kw not in code:
                    # 尝试按行业板块匹配
                    if not self._match_industry(code, sector_kw):
                        return False

        except Exception:
            return False

        return True

    def _match_industry(self, code: str, keyword: str) -> bool:
        """检查股票代码是否属于某行业"""
        # 使用板块成分股匹配
        cache_key = f"_ind_{keyword}"
        from services.data_service import _cache
        now = time.time()

        if cache_key in _cache and now - _cache[cache_key]["ts"] < 3600:
            codes = _cache[cache_key]["data"]
            return code in codes

        try:
            import akshare as ak
            # 搜索行业板块
            df = ak.stock_board_industry_name_em()
            matched_boards = []
            for _, row in df.iterrows():
                board_name = str(row.get("板块名称", ""))
                if keyword in board_name:
                    matched_boards.append(board_name)

            # 获取成分股
            all_codes = set()
            for board in matched_boards[:3]:  # 最多取3个匹配板块
                try:
                    cons = ak.stock_board_industry_cons_em(symbol=board)
                    for _, r in cons.iterrows():
                        all_codes.add(str(r.get("代码", "")))
                except Exception:
                    pass

            _cache[cache_key] = {"ts": now, "data": all_codes}
            return code in all_codes
        except Exception:
            return False

    def _calculate_score(self, stock: dict, conditions: dict) -> float:
        """计算多因子综合得分（0-100）"""
        score = 0.0
        count = 0

        # PE 得分：PE越低越好，但负PE不给分（排后面）
        pe = stock.get("pe")
        if pe and pe > 0 and pe < 200:
            # 0-15 PE → 高分, >50 PE → 低分
            pe_score = max(0, 100 - pe * 2)
            score += pe_score * 0.25
            count += 0.25

        # PB 得分
        pb = stock.get("pb")
        if pb and pb > 0 and pb < 50:
            pb_score = max(0, 100 - pb * 10)
            score += pb_score * 0.15
            count += 0.15

        # 市值适度加分（不要太小）
        mv = stock.get("total_mv", 0)
        if mv > 0:
            mv_yi = mv / 1e8
            if mv_yi > 10:
                mv_score = min(100, math.log10(mv_yi) * 30)
                score += mv_score * 0.10
                count += 0.10

        # 近期涨幅动量
        chg = stock.get("change_pct", 0)
        if -10 <= chg <= 10:
            chg_score = 50 + chg * 3  # 涨加分，跌减分
            score += max(0, chg_score) * 0.15
            count += 0.15

        # 换手率：适中最好
        to = stock.get("turnover", 0)
        if to > 0:
            if 1 <= to <= 10:
                to_score = 80
            elif to < 1:
                to_score = 30
            else:
                to_score = 50
            score += to_score * 0.10
            count += 0.10

        # 成交量（有量能）
        amount = stock.get("amount", 0)
        if amount > 0:
            amt_yi = amount / 1e8
            if amt_yi > 0.5:
                amt_score = min(100, amt_yi * 20)
                score += amt_score * 0.10
                count += 0.10

        # 价格不要太低（排除仙股）
        price = stock.get("price", 0)
        if price > 0:
            if price >= 3:
                score += 15
            count += 0.05

        # 归一化到100
        if count > 0:
            score = score / count
        return min(100, max(0, score))

    def apply_strategy_template(self, strategy_id: str, top_n: int = 30) -> dict:
        """应用策略模板进行选股"""
        # 策略模板到条件的映射
        strategy_conditions = {
            "buffett-value": {
                "min_roe": 15, "max_pe": 25, "max_pb": 5,
                "min_mv": 100, "exclude_st": True, "sort_by": "score",
            },
            "graham-value": {
                "max_pe": 10, "max_pb": 0.8, "min_mv": 10,
                "exclude_st": True, "sort_by": "pe",
            },
            "lynch-growth": {
                "max_pe": 35, "min_revenue_growth": 15,
                "min_profit_growth": 15, "exclude_st": True, "sort_by": "score",
            },
            "momentum-factor": {
                "min_turnover": 2, "change_min": 0, "exclude_st": True,
                "sort_by": "change_pct",
            },
            "value-factor": {
                "max_pe": 20, "max_pb": 3, "min_mv": 20,
                "exclude_st": True, "sort_by": "score",
            },
            "quality-factor": {
                "min_roe": 15, "min_mv": 50,
                "exclude_st": True, "sort_by": "score",
            },
            "lowvol-factor": {
                "max_turnover": 3, "change_min": -2, "change_max": 2,
                "min_mv": 50, "exclude_st": True, "sort_by": "score",
            },
        }

        conditions = strategy_conditions.get(strategy_id, {})
        if not conditions:
            return {"results": [], "total": 0, "message": f"未知策略: {strategy_id}"}

        result = self.search_by_conditions(conditions, top_n)
        result["strategy_id"] = strategy_id
        return result


# 全局单例
screener = StockScreener()
