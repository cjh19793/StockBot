"""장 상태 및 시장 심리 지표 (공포탐욕지수, 뉴스 감성, 실적일)."""
import datetime
import logging
import re

import pandas as pd
import pytz
import requests
import yfinance as yf

from config import CACHE_TTL_EARNINGS, CACHE_TTL_MARKET
from models import MarketRegime
from util import flatten_columns, ttl_cache

log = logging.getLogger(__name__)

_NY = pytz.timezone("America/New_York")


def get_market_status():
    et = datetime.datetime.now(_NY)
    et_hour = et.hour + et.minute / 60
    if et.weekday() < 5 and 9.5 <= et_hour < 16:
        return "[Open] US Market Trading", True
    if et.weekday() < 5 and (4 <= et_hour < 9.5 or 16 <= et_hour < 20):
        return "[Extended] Pre/After Market", False
    return "[Closed] US Market Closed", False


def _fg_label(score: int) -> str:
    if score <= 25:
        return "극도의 공포 - 매수 기회"
    if score <= 45:
        return "공포 - 매수 고려"
    if score <= 55:
        return "중립"
    if score <= 75:
        return "탐욕 - 매도 고려"
    return "극도의 탐욕 - 매도 주의"


@ttl_cache(CACHE_TTL_MARKET)
def get_fear_greed():
    """(점수, 라벨). CNN 실패 시 alternative.me 로 폴백. 둘 다 실패 시 (None, None)."""
    try:
        res = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            timeout=5,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://edition.cnn.com/",
            },
        )
        score = round(float(res.json()["fear_and_greed"]["score"]))
        return score, _fg_label(score)
    except Exception as exc:
        log.warning("CNN 공포탐욕지수 실패: %s", exc)

    try:
        res = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json", timeout=5
        )
        score = int(res.json()["data"][0]["value"])
        return score, _fg_label(score)
    except Exception as exc:
        log.warning("alternative.me 공포탐욕지수 실패: %s", exc)
        return None, None


_POSITIVE = {
    "beat", "beats", "surge", "surges", "gain", "gains", "rise", "rises", "up",
    "high", "growth", "profit", "record", "strong", "buy", "upgrade", "upgrades",
    "bullish", "soar", "soars", "jump", "jumps", "rally", "outperform",
}
_NEGATIVE = {
    "miss", "misses", "fall", "falls", "drop", "drops", "down", "low", "loss",
    "losses", "weak", "sell", "downgrade", "downgrades", "bearish", "cut", "cuts",
    "risk", "risks", "warn", "warns", "plunge", "plunges", "slump", "tumble",
}
_WORD_RE = re.compile(r"[a-z']+")


@ttl_cache(CACHE_TTL_MARKET)
def get_news_sentiment(ticker: str):
    """(감성 문자열, 헤드라인 목록). 뉴스 없거나 실패 시 (None, [])."""
    try:
        res = requests.get(
            f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=5",
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        news = res.json().get("news", [])
    except Exception as exc:
        log.warning("뉴스 감성 조회 실패 (%s): %s", ticker, exc)
        return None, []

    if not news:
        return None, []

    pos = neg = 0
    titles = []
    for item in news[:5]:
        title = item.get("title", "")
        titles.append(title)
        words = set(_WORD_RE.findall(title.lower()))
        pos += len(words & _POSITIVE)
        neg += len(words & _NEGATIVE)

    if pos > neg:
        sentiment = f"긍정 ({pos}건)"
    elif neg > pos:
        sentiment = f"부정 ({neg}건)"
    else:
        sentiment = "중립"
    return sentiment, titles[:3]


@ttl_cache(CACHE_TTL_EARNINGS)
def get_earnings_date(ticker: str):
    """다음 실적 발표일 안내 문자열. 정보 없으면 None."""
    try:
        calendar = yf.Ticker(ticker).calendar
    except Exception as exc:
        log.warning("실적 발표일 조회 실패 (%s): %s", ticker, exc)
        return None

    earn_date = None
    if isinstance(calendar, dict):
        earn_date = calendar.get("Earnings Date")
    elif isinstance(calendar, pd.DataFrame) and "Earnings Date" in calendar.index:
        earn_date = calendar.loc["Earnings Date"].tolist()

    if not earn_date:
        return None
    if isinstance(earn_date, (list, tuple)):
        earn_date = earn_date[0]

    try:
        earn_date = pd.Timestamp(earn_date).date()
    except (ValueError, TypeError):
        return None

    days_left = (earn_date - datetime.date.today()).days
    if days_left < 0:
        return f"지난 실적: {earn_date}"
    if days_left == 0:
        return "오늘 실적 발표!"
    if days_left <= 7:
        return f"실적 발표 {days_left}일 후 ({earn_date}) - 주의"
    return f"실적 발표: {earn_date} ({days_left}일 후)"


def _trend_label(above_ma200: bool, golden: bool) -> str:
    if above_ma200 and golden:
        return "강한 상승"
    if above_ma200:
        return "약한 상승"
    if golden:
        return "약한 하락"
    return "강한 하락"


def _trend_score(price: float, ma50: float, ma200: float, ret20: float) -> float:
    """지수 추세 점수 (0~100). 가격/MA50/MA200 배열 + 20일 모멘텀 보정."""
    above_ma200 = price > ma200
    golden = ma50 > ma200
    base = {
        (True, True): 90,
        (True, False): 65,
        (False, True): 35,
        (False, False): 10,
    }[(above_ma200, golden)]

    if ret20 >= 0.03:
        adj = 10
    elif ret20 <= -0.03:
        adj = -10
    else:
        adj = 0
    return max(0.0, min(100.0, base + adj))


def _vix_level(vix: float) -> str:
    if vix < 15:
        return "낮음"
    if vix < 20:
        return "보통"
    if vix < 30:
        return "경계"
    return "공포"


def _vix_score(vix: float) -> float:
    """VIX 점수 (0~100, 낮은 변동성일수록 높음). 구간 사이는 선형보간."""
    points = [(15, 90), (20, 70), (30, 40), (40, 10)]
    if vix <= points[0][0]:
        return float(points[0][1])
    if vix >= points[-1][0]:
        return float(points[-1][1])
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= vix <= x1:
            return y0 + (vix - x0) / (x1 - x0) * (y1 - y0)
    return float(points[-1][1])  # 도달 불가 (방어용)


def _score_regime(
    sp500_price: float, sp500_ma50: float, sp500_ma200: float, sp500_ret20: float,
    nasdaq_price: float, nasdaq_ma50: float, nasdaq_ma200: float, nasdaq_ret20: float,
    vix: float,
) -> MarketRegime:
    """지수/VIX 원자값 → MarketRegime. 순수 함수 (네트워크 I/O 없음)."""
    sp_score = _trend_score(sp500_price, sp500_ma50, sp500_ma200, sp500_ret20)
    nasdaq_score = _trend_score(nasdaq_price, nasdaq_ma50, nasdaq_ma200, nasdaq_ret20)
    trend_score = (sp_score + nasdaq_score) / 2
    vix_score = _vix_score(vix)

    score = round(trend_score * 0.65 + vix_score * 0.35)
    score = max(0, min(100, score))

    if score >= 65:
        label = "상승장"
    elif score >= 35:
        label = "횡보장"
    else:
        label = "하락장"

    sp500_trend = f"{_trend_label(sp500_price > sp500_ma200, sp500_ma50 > sp500_ma200)} (20일 {sp500_ret20 * 100:+.1f}%)"
    nasdaq_trend = f"{_trend_label(nasdaq_price > nasdaq_ma200, nasdaq_ma50 > nasdaq_ma200)} (20일 {nasdaq_ret20 * 100:+.1f}%)"

    return MarketRegime(
        label=label,
        score=score,
        sp500_trend=sp500_trend,
        nasdaq_trend=nasdaq_trend,
        vix=vix,
        vix_level=_vix_level(vix),
    )


def _index_snapshot(symbol: str):
    """(price, ma50, ma200, ret20) — 지수 다운로드 실패/데이터 부족 시 None."""
    df = yf.download(symbol, period="1y", interval="1d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        return None
    df = flatten_columns(df)
    close = df["Close"].dropna()
    if len(close) < 200:
        return None

    price = float(close.iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1])
    if any(pd.isna(v) for v in (price, ma50, ma200)):
        return None
    ret20 = float(close.iloc[-1] / close.iloc[-21] - 1) if len(close) >= 21 else 0.0
    return price, ma50, ma200, ret20


@ttl_cache(CACHE_TTL_MARKET)
def get_market_regime() -> MarketRegime | None:
    """S&P500/NASDAQ 추세 + VIX 로 시장 전체 상황 판단. 조회/계산 실패 시 None."""
    try:
        sp500 = _index_snapshot("^GSPC")
        nasdaq = _index_snapshot("^IXIC")
        vix_df = yf.download("^VIX", period="5d", interval="1d", progress=False, auto_adjust=True)
    except Exception as exc:
        log.warning("시장 지수 조회 실패: %s", exc)
        return None

    if sp500 is None or nasdaq is None:
        log.warning("시장 지수 데이터 부족 (S&P500/NASDAQ)")
        return None
    if vix_df is None or vix_df.empty:
        log.warning("VIX 조회 실패")
        return None

    vix_df = flatten_columns(vix_df)
    vix = float(vix_df["Close"].dropna().iloc[-1])

    try:
        return _score_regime(*sp500, *nasdaq, vix)
    except Exception as exc:
        log.warning("시장 상황 스코어링 실패: %s", exc)
        return None
