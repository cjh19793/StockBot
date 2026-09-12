"""주식 분석 엔진 — 구조화된 결과 계산 (텔레그램/웹 공용, 표현 로직 없음).

기존 analysis._analyze 의 '계산' 부분을 그대로 옮겨온 것. 알고리즘 변경 없음.
문자열 리포트 조립은 report_format, 차트는 charts 가 담당한다.
"""
import datetime
import logging
import math
from concurrent.futures import ThreadPoolExecutor

import pytz

from config import MODE_CONFIG
from data import get_df, get_realtime_price
from errors import TickerNotFound
from indicators import calc_indicators, get_value
from market import (get_earnings_date, get_fear_greed, get_market_regime,
                    get_market_status, get_news_sentiment)
from models import AnalysisResult
from risk import compute_target_stop
from signals import detect_signal, final_judgment

log = logging.getLogger(__name__)
_KST = pytz.timezone("Asia/Seoul")


def run_analysis(ticker: str, mode: str = "기본") -> AnalysisResult:
    """티커 + 모드 → AnalysisResult.

    가격 데이터가 없으면 TickerNotFound 를 던진다.
    """
    cfg = MODE_CONFIG.get(mode, MODE_CONFIG["기본"])
    label, bar_width = cfg["label"], cfg["bar_width"]

    df = get_df(ticker, mode)
    if df is None or df.empty:
        raise TickerNotFound(ticker)
    df = calc_indicators(df)

    # 부가 정보는 각각 네트워크 I/O — 병렬로 조회
    with ThreadPoolExecutor(max_workers=5) as ex:
        f_realtime = ex.submit(get_realtime_price, ticker)
        f_fg = ex.submit(get_fear_greed)
        f_news = ex.submit(get_news_sentiment, ticker)
        f_earnings = ex.submit(get_earnings_date, ticker)
        f_regime = ex.submit(get_market_regime)
        market, is_open = get_market_status()
        realtime = f_realtime.result()
        fg_score, fg_label = f_fg.result()
        sentiment, news_titles = f_news.result()
        earnings = f_earnings.result()
        regime = f_regime.result()

    if is_open and realtime:
        curr = realtime
        price_is_realtime = True
    else:
        curr = get_value(df["Close"])
        price_is_realtime = False

    now_str = df.index[-1].strftime("%Y-%m-%d") if mode == "기본" else str(df.index[-1])[:16]
    kt_str = datetime.datetime.now(_KST).strftime("%Y-%m-%d %H:%M (KST)")

    atr = get_value(df["ATR"])
    support = get_value(df["Support"])
    resistance = get_value(df["Resistance"])
    # curr(실시간가/전일종가) 기준 변동성 비율. ATR 이 NaN(데이터 부족)이면 0으로
    # 폴백해 클램프 하한(TARGET_PCT_BOUNDS/STOP_PCT_BOUNDS 최소값)이 적용되게 한다.
    atr_pct = 0.0 if (not curr or math.isnan(atr)) else atr / curr
    target_price, stop_loss, target_pct, stop_pct = compute_target_stop(curr, atr_pct, mode)

    buy_score, buy_signals, sell_score, sell_signals = detect_signal(df)
    judgment, _, chart_title = final_judgment(buy_score, sell_score)

    return AnalysisResult(
        ticker=ticker,
        mode=mode,
        label=label,
        bar_width=bar_width,
        now_str=now_str,
        asof_kst=kt_str,
        market=market,
        is_market_open=is_open,
        price=float(curr),
        price_is_realtime=price_is_realtime,
        target_price=target_price,
        stop_loss=stop_loss,
        target_pct=target_pct,
        stop_pct=stop_pct,
        rsi=get_value(df["RSI"]),
        macd=get_value(df["MACD"]),
        stoch_k=get_value(df["Stoch_K"]),
        ma5=get_value(df["MA5"]),
        ma20=get_value(df["MA20"]),
        bb_upper=get_value(df["Upper"]),
        bb_lower=get_value(df["Lower"]),
        atr=atr,
        atr_pct=atr_pct,
        support=support,
        resistance=resistance,
        volume=get_value(df["Volume"]),
        buy_score=buy_score,
        sell_score=sell_score,
        buy_signals=list(buy_signals),
        sell_signals=list(sell_signals),
        judgment=judgment,
        chart_title=chart_title,
        fear_greed_score=fg_score,
        fear_greed_label=fg_label,
        earnings=earnings,
        news_sentiment=sentiment,
        news_titles=list(news_titles),
        market_regime=regime,
        df=df,
    )
