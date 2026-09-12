"""목표가/손절가 계산 (ATR 기반, 순수 함수 — I/O 없음).

이후 리스크 스코어링(추세/모멘텀/거래량/펀더멘털/시장환경과 함께 묶는 종합 리스크
카테고리)도 이 모듈에 모을 예정이라 engine.py 가 아닌 별도 파일로 분리했다.
"""
from config import (MODE_STOP_ATR_MULT, MODE_TARGET_ATR_MULT,
                    STOP_PCT_BOUNDS, TARGET_PCT_BOUNDS)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_target_stop(price: float, atr_pct: float, mode: str = "기본"):
    """가격 + ATR 비율(ATR/가격) + 모드 → (target_price, stop_loss, target_pct, stop_pct).

    모드가 알 수 없으면 '기본' 배수를 사용한다 (MODE_CONFIG.get 폴백과 동일한 관례).
    atr_pct 가 배수 적용 후 비상식적인 값이면 TARGET_PCT_BOUNDS/STOP_PCT_BOUNDS 로 클램프.
    """
    target_mult = MODE_TARGET_ATR_MULT.get(mode, MODE_TARGET_ATR_MULT["기본"])
    stop_mult = MODE_STOP_ATR_MULT.get(mode, MODE_STOP_ATR_MULT["기본"])

    raw_target_pct = target_mult * atr_pct
    raw_stop_pct = stop_mult * atr_pct

    target_pct = _clamp(raw_target_pct, *TARGET_PCT_BOUNDS)
    stop_pct = _clamp(raw_stop_pct, *STOP_PCT_BOUNDS)

    target_price = price * (1 + target_pct)
    stop_loss = price * (1 - stop_pct)
    return target_price, stop_loss, target_pct, stop_pct
