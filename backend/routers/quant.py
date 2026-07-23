"""
量化因子 API — 觅投AI 策略小课堂
基于 Qlib Alpha158 因子库，提供教学级量化因子计算和展示

⚠️ 合规声明：所有因子数据仅用于金融知识教育展示，不构成投资建议
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("mitouai.quant")

router = APIRouter()


# ═══════════════════════════════════════════════
#  因子列表
# ═══════════════════════════════════════════════

@router.get("/factors")
async def list_factors(
    category: Optional[str] = Query(None, description="筛选类别: price/momentum/trend/volatility/quantile/rank/correlation/volume"),
):
    """获取 Alpha158 因子列表（含中文教学描述）

    用于策略小课堂的因子百科展示。
    """
    try:
        from services.qlib_integration.factor_service import qlib_factor_service

        factors = qlib_factor_service.list_factors(category=category)
        categories = qlib_factor_service.list_categories()

        return {
            "total": len(factors),
            "categories": categories,
            "factors": factors,
            "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
        }
    except Exception as e:
        logger.error(f"获取因子列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """获取因子类别统计"""
    try:
        from services.qlib_integration.factor_service import qlib_factor_service
        return qlib_factor_service.list_categories()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
#  因子计算
# ═══════════════════════════════════════════════

@router.get("/factors/{ticker}")
async def calculate_factors(
    ticker: str,
    factor_names: Optional[str] = Query(None, description="逗号分隔的因子名，如 KMID,ROC5,MA20。留空=全部158个"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    last_n: int = Query(0, description="只返回最近N天数据，0=全部"),
):
    """计算指定股票的 Alpha158 因子

    示例:
    - GET /api/quant/factors/600519.SS?last_n=5
    - GET /api/quant/factors/600519.SS?factor_names=KMID,ROC5,MA20&last_n=10
    """
    try:
        from services.qlib_integration.factor_service import qlib_factor_service

        names = None
        if factor_names:
            names = [n.strip() for n in factor_names.split(",") if n.strip()]

        result = qlib_factor_service.calculate_factors(
            ticker=ticker,
            factor_names=names,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"因子计算失败 [{ticker}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
#  多股票对比
# ═══════════════════════════════════════════════

@router.get("/compare")
async def compare_factors(
    tickers: str = Query(..., description="逗号分隔的股票代码，如 600519.SS,000001.SZ"),
    factor: str = Query(..., description="要对比的因子名，如 RSV5"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    last_n: int = Query(30, description="最近N天"),
):
    """多股票单因子对比

    示例: GET /api/quant/compare?tickers=600519.SS,000001.SZ&factor=RSV5&last_n=30
    """
    try:
        from services.qlib_integration.factor_service import qlib_factor_service

        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        if len(ticker_list) < 2:
            raise HTTPException(status_code=400, detail="至少需要2只股票进行对比")

        result = qlib_factor_service.compare_factors(
            tickers=ticker_list,
            factor_name=factor,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n,
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"因子对比失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
#  基本面数据
# ═══════════════════════════════════════════════

@router.get("/fundamentals/{code}")
async def get_fundamentals(code: str):
    """获取股票基本面数据（PE/PB/市值/行业等）

    示例: GET /api/quant/fundamentals/600519

    ⚠️ 仅用于金融知识教育展示，不构成投资建议
    """
    try:
        from services.qlib_integration.fundamental_service import fundamental_service

        code = code.strip()
        # 支持 600519.SS 格式，提取纯代码
        if "." in code:
            code = code.split(".")[0]

        data = fundamental_service.get_fundamentals(code)
        return data
    except Exception as e:
        logger.error(f"获取基本面数据失败 [{code}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fundamentals")
async def fundamentals_ranking(
    codes: str = Query(..., description="逗号分隔的股票代码，如 600519,000001"),
    metric: str = Query("pe_ttm", description="排名指标: pe_ttm/pb/ps_ttm/dv_ratio"),
):
    """多股票估值排名

    示例: GET /api/quant/fundamentals?codes=600519,000001,601398&metric=pe_ttm
    """
    try:
        from services.qlib_integration.fundamental_service import fundamental_service

        code_list = [c.strip().split(".")[0] for c in codes.split(",") if c.strip()]
        if len(code_list) < 2:
            raise HTTPException(status_code=400, detail="至少需要2只股票")

        result = fundamental_service.get_valuation_ranking(code_list, metric)
        result["disclaimer"] = "本数据仅用于金融知识教育展示，不构成投资建议"
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"估值排名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
#  数据管道管理
# ═══════════════════════════════════════════════

@router.get("/data/status")
async def data_status():
    """获取 Qlib 数据管道状态

    返回已入库的股票列表、日历天数、.bin 文件数量等。
    """
    try:
        from services.qlib_integration.factor_service import qlib_factor_service
        return qlib_factor_service.get_data_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/stocks")
async def available_stocks():
    """获取已有数据的股票列表"""
    try:
        from services.qlib_integration.factor_service import qlib_factor_service
        stocks = qlib_factor_service.get_available_stocks()
        return {"total": len(stocks), "stocks": stocks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/refresh")
async def refresh_data(
    tickers: str = Query(..., description="逗号分隔的股票代码，如 600519.SS,000001.SZ"),
    start_date: str = Query("", description="开始日期 YYYYMMDD 或 YYYY-MM-DD"),
    end_date: str = Query("", description="结束日期"),
):
    """拉取/更新股票数据（akshare -> Qlib .bin）

    示例: POST /api/quant/data/refresh?tickers=600519.SS,000001.SZ
    """
    try:
        from services.qlib_integration.factor_service import qlib_factor_service

        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        result = qlib_factor_service.refresh_data(
            tickers=ticker_list,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "success_count": len(result["success"]),
            "failed_count": len(result["failed"]),
            "details": result,
            "message": f"成功更新 {len(result['success'])} 只股票" if result["success"]
                       else "更新失败，请检查股票代码",
        }
    except Exception as e:
        logger.error(f"数据更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
#  策略小课堂 — 教学内容
# ═══════════════════════════════════════════════

@router.get("/classroom/{factor_name}")
async def factor_classroom(factor_name: str):
    """策略小课堂 — 单因子深度解读

    返回因子的公式、中文释义、教学解读，以及示例股票的因子值。
    """
    try:
        from services.qlib_integration.factor_service import qlib_factor_service
        from services.qlib_integration.factor_descriptions import (
            FACTOR_DESCRIPTIONS, FACTOR_CATEGORIES
        )

        if factor_name not in FACTOR_DESCRIPTIONS:
            raise HTTPException(status_code=404, detail=f"未知因子: {factor_name}")

        info = FACTOR_DESCRIPTIONS[factor_name]
        category_label = FACTOR_CATEGORIES.get(info["category"], info["category"])

        # 如果有数据，计算示例
        example = None
        try:
            stocks = qlib_factor_service.get_available_stocks()
            if stocks:
                sample_ticker = stocks[0]["code"]
                sample_symbol = stocks[0]["symbol"]
                result = qlib_factor_service.calculate_factors(
                    ticker=sample_ticker,
                    factor_names=[factor_name],
                    last_n=10,
                )
                if "error" not in result and result.get("time_series"):
                    ts = result["time_series"][factor_name]
                    example = {
                        "ticker": sample_ticker,
                        "dates": ts["dates"],
                        "values": ts["values"],
                        "latest_value": result["factors"][0]["value"] if result["factors"] else None,
                    }
        except Exception as e:
            logger.warning(f"获取示例数据失败: {e}")

        return {
            "factor": factor_name,
            "category": info["category"],
            "category_label": category_label,
            "formula": info["formula"],
            "desc": info["desc"],
            "teaching": info["teaching"],
            "example": example,
            "disclaimer": "本数据仅用于金融知识教育展示，不构成投资建议",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
