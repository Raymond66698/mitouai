"""
Tushare Pro 数据存储 ORM 模型

4张核心表:
- tushare_stock_basic: 股票基本信息
- tushare_daily_quote: 日线行情 (ts_code + trade_date 联合主键)
- tushare_trade_cal: 交易日历
- tushare_daily_basic: 每日指标 (PE/PB/市值等)
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Date, BigInteger, Boolean,
    PrimaryKeyConstraint, Index,
)
from models.base import Base


class StockBasic(Base):
    """股票基本信息"""
    __tablename__ = "tushare_stock_basic"

    ts_code = Column(String(20), primary_key=True, comment="TS代码")
    symbol = Column(String(10), index=True, comment="股票代码")
    name = Column(String(50), comment="股票名称")
    fullname = Column(String(100), comment="股票全称")
    enname = Column(String(100), comment="英文名称")
    area = Column(String(10), comment="地域")
    industry = Column(String(50), comment="所属行业")
    market = Column(String(20), comment="市场类型")
    exchange = Column(String(10), comment="交易所")
    list_status = Column(String(1), comment="上市状态 L上市 D退市 P暂停")
    list_date = Column(String(8), comment="上市日期 YYYYMMDD")
    delist_date = Column(String(8), comment="退市日期")
    updated_at = Column(Date, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class DailyQuote(Base):
    """日线行情数据"""
    __tablename__ = "tushare_daily_quote"
    __table_args__ = (
        PrimaryKeyConstraint("ts_code", "trade_date", name="pk_daily_quote"),
        Index("idx_dq_trade_date", "trade_date"),
        Index("idx_dq_ts_code", "ts_code"),
    )

    ts_code = Column(String(20), comment="TS代码")
    trade_date = Column(String(8), comment="交易日期 YYYYMMDD")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    pre_close = Column(Float, comment="昨收价")
    change = Column(Float, comment="涨跌额")
    pct_chg = Column(Float, comment="涨跌幅(%)")
    vol = Column(Float, comment="成交量(手)")
    amount = Column(Float, comment="成交额(千元)")
    updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)


class TradeCalendar(Base):
    """交易日历"""
    __tablename__ = "tushare_trade_cal"

    cal_date = Column(String(8), primary_key=True, comment="日历日期")
    exchange = Column(String(10), primary_key=True, comment="交易所 SSE/SZSE")
    is_open = Column(Boolean, comment="是否交易日")
    pretrade_date = Column(String(8), comment="上一交易日")


class DailyBasic(Base):
    """每日指标 (PE/PB/市值/换手率等)"""
    __tablename__ = "tushare_daily_basic"
    __table_args__ = (
        PrimaryKeyConstraint("ts_code", "trade_date", name="pk_daily_basic"),
        Index("idx_db_trade_date", "trade_date"),
    )

    ts_code = Column(String(20), comment="TS代码")
    trade_date = Column(String(8), comment="交易日期")
    close = Column(Float, comment="当日收盘价")
    turnover_rate = Column(Float, comment="换手率(%)")
    turnover_rate_f = Column(Float, comment="换手率(自由流通股)(%)")
    volume_ratio = Column(Float, comment="量比")
    pe = Column(Float, comment="市盈率(PE)")
    pe_ttm = Column(Float, comment="市盈率(TTM)")
    pb = Column(Float, comment="市净率(PB)")
    ps = Column(Float, comment="市销率(PS)")
    ps_ttm = Column(Float, comment="市销率(TTM)")
    dv_ratio = Column(Float, comment="股息率(%)")
    dv_ttm = Column(Float, comment="股息率(TTM)(%)")
    total_share = Column(Float, comment="总股本(万股)")
    float_share = Column(Float, comment="流通股本(万股)")
    free_share = Column(Float, comment="自由流通股本(万股)")
    total_mv = Column(Float, comment="总市值(万元)")
    circ_mv = Column(Float, comment="流通市值(万元)")
    updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)
