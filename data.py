"""가격 데이터 조회 (yfinance)."""
import logging

import pandas as pd
import yfinance as yf

from config import CACHE_TTL_OHLC, CACHE_TTL_REALTIME, MODE_CONFIG
from util import flatten_columns, ttl_cache

log = logging.getLogger(__name__)


@ttl_cache(CACHE_TTL_OHLC)
def get_df(ticker: str, mode: str = "기본"):
    """모드별 OHLCV 데이터프레임. 실패 시 None."""
    cfg = MODE_CONFIG.get(mode, MODE_CONFIG["기본"])
    try:
        df = yf.download(
            ticker,
            period=cfg["period"],
            interval=cfg["interval"],
            progress=False,
            auto_adjust=True,
        )
    except Exception as exc:
        log.warning("yfinance 다운로드 실패 (%s/%s): %s", ticker, mode, exc)
        return None

    if df is None or df.empty:
        return None

    df = flatten_columns(df)
    if mode == "기본":
        df.index = pd.to_datetime(df.index).normalize()
    return df


@ttl_cache(CACHE_TTL_REALTIME)
def get_realtime_price(ticker: str):
    """가장 최근 5분봉 종가. 실패 시 None."""
    try:
        df = yf.download(
            ticker, period="1d", interval="5m", progress=False, auto_adjust=True
        )
    except Exception as exc:
        log.warning("실시간 가격 조회 실패 (%s): %s", ticker, exc)
        return None

    if df is None or df.empty:
        return None

    df = flatten_columns(df)
    return float(df["Close"].iloc[-1])
