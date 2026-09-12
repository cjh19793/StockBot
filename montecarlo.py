"""과거 구간 부트스트랩 시뮬레이션.

주의: GBM 등 확률과정 시뮬레이션이 아니라, 과거 가격 구간을 무작위로 표본추출해
보유기간별 수익률 분포를 추정한다. 표본 구간이 겹칠 수 있어 완전히 독립은 아니다.

run_montecarlo: 계산 → MonteCarloResult (텔레그램/웹 공용)
montecarlo:     텔레그램 래퍼 (마크다운 문자열, 오류 시 None) — 기존 동작 유지
"""
import logging

import numpy as np
import yfinance as yf

from config import CACHE_TTL_MONTECARLO, MC_CONFIG
from errors import AnalysisError, TickerNotFound, UpstreamDataError
from models import MonteCarloHold, MonteCarloResult
from report_format import format_montecarlo
from util import flatten_columns, ttl_cache

log = logging.getLogger(__name__)


def _grade(win_rate: float) -> str:
    if win_rate >= 65:
        return "Excellent"
    if win_rate >= 55:
        return "Good"
    if win_rate >= 45:
        return "Neutral"
    return "Caution"


@ttl_cache(CACHE_TTL_MONTECARLO)
def _get_mc_df(ticker: str, period: str):
    """(ticker, period) 기준 일봉 데이터. 캐싱으로 동일 요청 반복 시 yfinance 재호출 방지."""
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        return None
    return flatten_columns(df)


def run_montecarlo(
    ticker: str, mc_mode: str = "기본", simulations: int = 1000
) -> MonteCarloResult:
    """계산 결과를 MonteCarloResult 로 반환.

    데이터 부족 시 TickerNotFound, 다운로드 오류 시 UpstreamDataError.
    """
    cfg = MC_CONFIG.get(mc_mode, MC_CONFIG["기본"])
    try:
        df = _get_mc_df(ticker, cfg["period"])
    except Exception as exc:
        log.warning("몬테카를로 다운로드 실패 (%s): %s", ticker, exc)
        raise UpstreamDataError(ticker) from exc

    if df is None:
        raise TickerNotFound(ticker)
    if len(df) < 30:
        raise TickerNotFound(ticker)

    closes = df["Close"].to_numpy(dtype=float).ravel()
    n = len(closes)
    rng = np.random.default_rng()

    holds: list[MonteCarloHold] = []
    best_period, best_winrate = None, 0.0

    for hold in cfg["hold_days"]:
        max_idx = n - hold - 1
        if max_idx <= 0:
            continue
        buy_idx = rng.integers(0, max_idx + 1, size=simulations)
        buy = closes[buy_idx]
        sell = closes[buy_idx + hold]
        valid = buy > 0
        if not valid.any():
            continue
        ret = (sell[valid] - buy[valid]) / buy[valid] * 100

        win_rate = float((ret > 0).mean() * 100)
        if win_rate > best_winrate:
            best_winrate, best_period = win_rate, hold

        holds.append(
            MonteCarloHold(
                hold_days=hold,
                win_rate=win_rate,
                grade=_grade(win_rate),
                avg_return=float(ret.mean()),
                max_profit=float(ret.max()),
                max_loss=float(ret.min()),
            )
        )

    if best_period is None:
        raise TickerNotFound(ticker)

    return MonteCarloResult(
        ticker=ticker,
        mc_mode=mc_mode,
        label=cfg["label"],
        period=cfg["period"],
        simulations=simulations,
        holds=holds,
        best_hold_days=best_period,
        best_win_rate=best_winrate,
    )


def montecarlo(ticker: str, mc_mode: str = "기본", simulations: int = 1000):
    """마크다운 문자열. 데이터 없거나 오류 시 None (기존 동작 유지)."""
    try:
        return format_montecarlo(run_montecarlo(ticker, mc_mode, simulations))
    except AnalysisError:
        return None
    except Exception:
        log.exception("몬테카를로 계산 실패: %s (%s)", ticker, mc_mode)
        return None
