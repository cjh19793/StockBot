"""티커 / 모드 입력 검증 — 텔레그램 봇과 웹 API 공용.

기존 bot.py 의 _TICKER_RE / _MC_KEYWORDS / _resolve_mode 를 그대로 옮겨온 것.
"""
import re

from config import MODE_ALIASES, MODE_CONFIG

TICKER_RE = re.compile(r"^[A-Z0-9^][A-Z0-9.^-]{0,9}$")
MC_KEYWORDS = {"MC", "MONTE", "몬테"}


def is_valid_ticker(ticker: str) -> bool:
    """대문자 티커 형식 검증."""
    return bool(TICKER_RE.match(ticker))


def resolve_mode(token: str, allowed=MODE_CONFIG) -> str | None:
    """입력 별칭 → 표준 모드 이름. allowed(MODE_CONFIG / MC_CONFIG) 밖이면 None."""
    canon = MODE_ALIASES.get(token)
    return canon if canon in allowed else None
