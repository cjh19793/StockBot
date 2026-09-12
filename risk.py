"""목표가/손절가 + 리스크 점수 계산 (ATR/지지저항 기반, 순수 함수 — I/O 없음)."""
import math

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


def _is_invalid(*values: float) -> bool:
    """None 이거나 NaN 이면 True (데이터 부족/조회 실패 감지용)."""
    for v in values:
        if v is None:
            return True
        try:
            if math.isnan(v):
                return True
        except TypeError:
            return True
    return False


def compute_risk_score(stop_pct: float, stop_loss: float, support: float, price: float) -> int:
    """변동성 안전도(70%) + 손절 구조 여유(30%) → 0~100 (높을수록 안전).

    입력값 중 하나라도 NaN/None/비정상(price<=0)이면 예외를 던지지 않고
    중립값 50을 반환한다 (데이터 부족 구간에서도 종합점수 계산이 끊기지 않도록).
    """
    if _is_invalid(stop_pct, stop_loss, support, price) or price <= 0:
        return 50

    stop_max, stop_min = STOP_PCT_BOUNDS[1], STOP_PCT_BOUNDS[0]
    vol_safety = _clamp(100 * (stop_max - stop_pct) / (stop_max - stop_min), 0, 100)

    if stop_loss <= support:
        buffer_score = 100.0
    else:
        denom = price - support
        if denom <= 0:
            # price <= support (돌파/이상치 등 구조 판단 불가) — 중립 처리
            buffer_score = 50.0
        else:
            ratio = _clamp((stop_loss - support) / denom, 0, 1)
            buffer_score = 100 * (1 - ratio)

    risk = vol_safety * 0.7 + buffer_score * 0.3
    return int(round(_clamp(risk, 0, 100)))
