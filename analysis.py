"""분석 리포트 + 차트 생성 (부가 정보는 병렬 조회)."""
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

import pytz

from charts import build_chart
from config import MODE_CONFIG, STOP_PCT, TARGET_PCT
from data import get_df, get_realtime_price
from indicators import calc_indicators, get_value
from market import (get_earnings_date, get_fear_greed, get_market_status,
                    get_news_sentiment)
from signals import detect_signal, final_judgment

log = logging.getLogger(__name__)
_KST = pytz.timezone("Asia/Seoul")


def analyze(ticker: str, mode: str = "기본"):
    """(리포트 문자열, PNG BytesIO). 데이터 없거나 오류 시 (None, None)."""
    try:
        return _analyze(ticker, mode)
    except Exception:
        log.exception("분석 실패: %s (%s)", ticker, mode)
        return None, None


def _analyze(ticker: str, mode: str):
    cfg = MODE_CONFIG.get(mode, MODE_CONFIG["기본"])
    label, bar_width = cfg["label"], cfg["bar_width"]

    df = get_df(ticker, mode)
    if df is None or df.empty:
        return None, None
    df = calc_indicators(df)

    # 부가 정보는 각각 네트워크 I/O — 병렬로 조회
    with ThreadPoolExecutor(max_workers=4) as ex:
        f_realtime = ex.submit(get_realtime_price, ticker)
        f_fg = ex.submit(get_fear_greed)
        f_news = ex.submit(get_news_sentiment, ticker)
        f_earnings = ex.submit(get_earnings_date, ticker)
        market, is_open = get_market_status()
        realtime = f_realtime.result()
        fg_score, fg_label = f_fg.result()
        sentiment, news_titles = f_news.result()
        earnings = f_earnings.result()

    if is_open and realtime:
        curr = realtime
        price_label = f"*{curr:.2f}* (실시간)"
    else:
        curr = get_value(df["Close"])
        price_label = f"*{curr:.2f}* (전일 종가)"

    rsi = get_value(df["RSI"])
    upper = get_value(df["Upper"])
    lower = get_value(df["Lower"])
    vol = get_value(df["Volume"])
    macd = get_value(df["MACD"])
    sk = get_value(df["Stoch_K"])
    ma5 = get_value(df["MA5"])
    ma20 = get_value(df["MA20"])

    now_str = df.index[-1].strftime("%Y-%m-%d") if mode == "기본" else str(df.index[-1])[:16]
    kt_str = datetime.datetime.now(_KST).strftime("%Y-%m-%d %H:%M (KST)")
    target_price = curr * (1 + TARGET_PCT)
    stop_loss = curr * (1 - STOP_PCT)

    buy_score, buy_signals, sell_score, sell_signals = detect_signal(df)
    judgment, _, chart_title = final_judgment(buy_score, sell_score)

    buy_text = "\n".join(f"[매수] {s}" for s in buy_signals) or "없음"
    sell_text = "\n".join(f"[매도] {s}" for s in sell_signals) or "없음"

    if "Buy" in judgment:
        action = "*Buy Timing* - Consider split buying"
    elif "Sell" in judgment:
        action = "*Sell Timing* - Consider split selling"
    else:
        action = "*Watch* - Wait for signal confirmation"

    fg_text = f"{fg_score}점 - {fg_label}" if fg_score is not None else "가져오기 실패"
    if sentiment:
        news_text = f"감성: {sentiment}\n" + "\n".join(f"  - {t}" for t in news_titles)
    else:
        news_text = "뉴스 없음"
    earnings_text = earnings or "정보 없음"

    report = (
        f"*[{ticker}] {label} 분석 리포트*\n"
        f"기준: {now_str} | 조회: {kt_str}\n"
        f"{market}\n"
        f"--------------------\n"
        f"현재가: {price_label}\n"
        f"목표가: {target_price:.2f} (+{TARGET_PCT * 100:.0f}%) | "
        f"손절가: {stop_loss:.2f} (-{STOP_PCT * 100:.0f}%)\n"
        f"거래량: {vol:,.0f}\n"
        f"RSI: {rsi:.1f} | MACD: {macd:.3f} | Stoch K: {sk:.1f}\n"
        f"MA5: {ma5:.2f} | MA20: {ma20:.2f}\n"
        f"BB상단: {upper:.2f} | BB하단: {lower:.2f}\n\n"
        f"--------------------\n"
        f"*시장 심리*\n"
        f"공포탐욕지수: {fg_text}\n"
        f"실적 발표: {earnings_text}\n\n"
        f"*뉴스 감성*\n"
        f"{news_text}\n\n"
        f"--------------------\n"
        f"*매수 신호 ({buy_score}점)*\n{buy_text}\n\n"
        f"*매도 신호 ({sell_score}점)*\n{sell_text}\n\n"
        f"--------------------\n"
        f"최종 판정: *{judgment}*\n{action}"
    )

    chart_buf = build_chart(
        df, ticker=ticker, label=label, now_str=now_str, market=market,
        chart_title=chart_title, target_price=target_price, stop_loss=stop_loss,
        buy_score=buy_score, sell_score=sell_score, bar_width=bar_width,
    )
    return report, chart_buf
