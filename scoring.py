"""종합점수 계산 (기술/시장환경/리스크 가중합, 순수 함수 — I/O 없음).

signals.detect_signal() / signals.final_judgment() 는 그대로 두고 건드리지 않는다.
여기서는 이미 계산된 buy_score/sell_score/market_regime/risk_score 를 0~100 으로
정규화해 합치기만 한다.
"""
from config import BUY_SCORE_MAX, COMPOSITE_BANDS, COMPOSITE_WEIGHTS, SELL_SCORE_MAX
from models import CompositeScore


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _technical_subscore(buy_score: int, sell_score: int) -> int:
    """buy_score/sell_score(비대칭 최대치) → 0~100, 50=중립.

    signals.detect_signal() 실측 최대점수: buy=10, sell=9 (매도쪽 거래량 조건에
    완화 elif 단계가 없어 비대칭). 각자의 최대치로 나눠 비율을 맞춘 뒤 합산해야
    양쪽 다 만점일 때 0/100 에 정확히 도달한다 (공통 상수 하나로 나누면 어긋남).
    """
    net = buy_score / BUY_SCORE_MAX - sell_score / SELL_SCORE_MAX
    return int(round(_clamp(50 + 50 * net, 0, 100)))


def _market_subscore(market_regime) -> tuple[int, bool]:
    """market_regime.score 또는 조회 실패 시 중립(50, 사용불가 플래그)."""
    if market_regime is None:
        return 50, False
    return market_regime.score, True


def _fundamentals_subscore(fundamentals) -> tuple[int, bool]:
    """fundamentals.overall 또는 조회 실패 시 중립(50, 사용불가 플래그)."""
    if fundamentals is None:
        return 50, False
    return fundamentals.overall, True


def _label_for(total: int) -> str:
    for threshold, label in COMPOSITE_BANDS:
        if total >= threshold:
            return label
    return COMPOSITE_BANDS[-1][1]


def compute_composite_score(
    buy_score: int, sell_score: int, market_regime, risk_score: int, fundamentals=None,
) -> CompositeScore:
    """기술(40%) + 시장환경(20%) + 리스크(20%) + 펀더멘털(20%) 가중합 → CompositeScore.

    risk_score 는 risk.compute_risk_score() 결과를 그대로 받는다 (이 함수는
    리스크를 재계산하지 않음 — 중복 계산 방지). fundamentals 는 fundamentals.get_fundamentals()
    결과(FundamentalsScore | None)를 그대로 받는다. 생략(None) 시 market_regime 과 동일하게
    중립(50)으로 폴백한다.
    """
    technical = _technical_subscore(buy_score, sell_score)
    market, market_available = _market_subscore(market_regime)
    fundamentals_score, fundamentals_available = _fundamentals_subscore(fundamentals)

    w = COMPOSITE_WEIGHTS
    total = int(round(_clamp(
        technical * w["technical"] + market * w["market"] + risk_score * w["risk"]
        + fundamentals_score * w["fundamentals"],
        0, 100,
    )))

    return CompositeScore(
        total=total,
        label=_label_for(total),
        technical=technical,
        market=market,
        risk=risk_score,
        market_available=market_available,
        fundamentals=fundamentals_score,
        fundamentals_available=fundamentals_available,
    )
