"""장 상태 및 시장 심리 지표 (공포탐욕지수, 뉴스 감성, 실적일)."""
import datetime
import logging
import re

import pandas as pd
import pytz
import requests
import yfinance as yf

from config import CACHE_TTL_EARNINGS, CACHE_TTL_MARKET
from util import ttl_cache

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
