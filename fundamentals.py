"""펀더멘털(재무) 점수 — 성장성/수익성/밸류에이션/재무건전성 (P5).

yfinance Ticker.info 하나로 4개 축을 계산한다. info 필드는 종목/거래소마다
빠지는 게 흔해서(ETF, 신규 상장, 해외 상장 등) 축 하나하나, 지표 하나하나가
없어도 죽지 않고 "있는 것만" 평균낸다 — 전부 없으면 None 을 반환해
market_regime 과 동일하게 "조회 실패" 취급되게 한다(호출부에서 중립 50 폴백).
"""
import logging

import yfinance as yf

from config import CACHE_TTL_FUNDAMENTALS
from models import FundamentalsScore
from util import ttl_cache

log = logging.getLogger(__name__)


def _interp(value: float, points: list[tuple[float, float]]) -> float:
    """구간표 선형보간 (market._vix_score 와 동일한 방식). points 는 x 오름차순."""
    if value <= points[0][0]:
        return points[0][1]
    if value >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= value <= x1:
            return y0 + (value - x0) / (x1 - x0) * (y1 - y0)
    return points[-1][1]  # 도달 불가 (방어용)


def _avg(scores: list[float | None]) -> int | None:
    """None 을 제외한 평균, 전부 None 이면 None."""
    present = [s for s in scores if s is not None]
    if not present:
        return None
    return int(round(sum(present) / len(present)))


def _growth_score(info: dict) -> int | None:
    revenue = info.get("revenueGrowth")
    earnings = info.get("earningsGrowth")
    if earnings is None:
        earnings = info.get("earningsQuarterlyGrowth")

    points = [(-0.20, 10), (0.0, 50), (0.10, 75), (0.25, 95)]
    rev_score = _interp(revenue, points) if isinstance(revenue, (int, float)) else None
    earn_score = _interp(earnings, points) if isinstance(earnings, (int, float)) else None
    return _avg([rev_score, earn_score])


def _profitability_score(info: dict) -> int | None:
    margin = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    op_margin = info.get("operatingMargins")

    margin_points = [(-0.10, 10), (0.0, 40), (0.10, 70), (0.20, 90)]
    roe_points = [(0.0, 20), (0.05, 45), (0.15, 70), (0.25, 90)]

    m_score = _interp(margin, margin_points) if isinstance(margin, (int, float)) else None
    r_score = _interp(roe, roe_points) if isinstance(roe, (int, float)) else None
    o_score = _interp(op_margin, margin_points) if isinstance(op_margin, (int, float)) else None
    return _avg([m_score, r_score, o_score])


def _valuation_score(info: dict) -> int | None:
    """PER/PBR/PEG — 낮을수록 저평가(고점수). 적자 등으로 음수/0 인 값은 의미가 없어 제외."""
    pe = info.get("trailingPE") or info.get("forwardPE")
    pb = info.get("priceToBook")
    peg = info.get("pegRatio") or info.get("trailingPegRatio")

    pe_points = [(10, 90), (15, 80), (25, 60), (35, 40), (50, 20)]
    pb_points = [(1, 90), (3, 70), (6, 45), (10, 25)]
    peg_points = [(0.5, 90), (1, 80), (1.5, 60), (2, 40), (3, 20)]

    pe_score = _interp(pe, pe_points) if isinstance(pe, (int, float)) and pe > 0 else None
    pb_score = _interp(pb, pb_points) if isinstance(pb, (int, float)) and pb > 0 else None
    peg_score = _interp(peg, peg_points) if isinstance(peg, (int, float)) and peg > 0 else None
    return _avg([pe_score, pb_score, peg_score])


def _financial_health_score(info: dict) -> int | None:
    """부채비율(debtToEquity, % 단위)/유동비율/당좌비율 — 안전할수록 고점수."""
    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    quick_ratio = info.get("quickRatio")

    # debtToEquity 는 yfinance 기준 % 값 (예: 80.0 = 부채가 자기자본의 0.8배).
    # _interp() 는 points 가 x 오름차순이어야 하므로 낮은 부채비율(고점수)부터 나열.
    dte_points = [(0, 90), (50, 75), (100, 50), (150, 30), (250, 10)]
    current_points = [(0.5, 15), (1.0, 50), (1.5, 75), (2.0, 90)]
    quick_points = [(0.3, 20), (0.5, 40), (1.0, 75), (1.5, 90)]

    dte_score = _interp(debt_to_equity, dte_points) if isinstance(debt_to_equity, (int, float)) and debt_to_equity >= 0 else None
    cur_score = _interp(current_ratio, current_points) if isinstance(current_ratio, (int, float)) and current_ratio >= 0 else None
    quick_score = _interp(quick_ratio, quick_points) if isinstance(quick_ratio, (int, float)) and quick_ratio >= 0 else None
    return _avg([dte_score, cur_score, quick_score])


def _label_for(overall: int) -> str:
    if overall >= 70:
        return "우수"
    if overall >= 55:
        return "양호"
    if overall >= 45:
        return "보통"
    if overall >= 30:
        return "주의"
    return "위험"


def _score_fundamentals(info: dict) -> FundamentalsScore | None:
    """info 딕셔너리 → FundamentalsScore. 순수 함수 (네트워크 I/O 없음)."""
    growth = _growth_score(info)
    profitability = _profitability_score(info)
    valuation = _valuation_score(info)
    financial_health = _financial_health_score(info)

    overall = _avg([growth, profitability, valuation, financial_health])
    if overall is None:
        return None

    return FundamentalsScore(
        overall=overall,
        label=_label_for(overall),
        growth=growth,
        profitability=profitability,
        valuation=valuation,
        financial_health=financial_health,
    )


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_fundamentals(ticker: str) -> FundamentalsScore | None:
    """티커 → FundamentalsScore. 조회 실패/유의미한 지표 전무 시 None.

    yf.Ticker.info 는 요청량이 큰 편이라 CACHE_TTL_FUNDAMENTALS(6시간)로 길게
    캐싱한다 — 재무 데이터는 분기 실적 주기로만 바뀌므로 신선도를 크게 잃지 않는다.
    """
    try:
        info = yf.Ticker(ticker).info
    except Exception as exc:
        log.warning("펀더멘털 조회 실패 (%s): %s", ticker, exc)
        return None

    if not info or not isinstance(info, dict):
        return None

    try:
        return _score_fundamentals(info)
    except Exception as exc:
        log.warning("펀더멘털 스코어링 실패 (%s): %s", ticker, exc)
        return None
