"""과거 구간 부트스트랩 시뮬레이션.

주의: GBM 등 확률과정 시뮬레이션이 아니라, 과거 가격 구간을 무작위로 표본추출해
보유기간별 수익률 분포를 추정한다. 표본 구간이 겹칠 수 있어 완전히 독립은 아니다.
"""
import logging

import numpy as np
import yfinance as yf

from config import MC_CONFIG
from util import flatten_columns

log = logging.getLogger(__name__)


def _grade(win_rate: float) -> str:
    if win_rate >= 65:
        return "Excellent"
    if win_rate >= 55:
        return "Good"
    if win_rate >= 45:
        return "Neutral"
    return "Caution"


def montecarlo(ticker: str, mc_mode: str = "기본", simulations: int = 1000):
    cfg = MC_CONFIG.get(mc_mode, MC_CONFIG["기본"])
    try:
        df = yf.download(
            ticker, period=cfg["period"], interval="1d", progress=False, auto_adjust=True
        )
    except Exception as exc:
        log.warning("몬테카를로 다운로드 실패 (%s): %s", ticker, exc)
        return None

    if df is None or df.empty:
        return None
    df = flatten_columns(df)
    if len(df) < 30:
        return None

    try:
        closes = df["Close"].to_numpy(dtype=float).ravel()
        n = len(closes)
        rng = np.random.default_rng()

        lines = [
            f"*[{ticker}] Monte Carlo - {cfg['label']}*",
            f"Simulations: {simulations} | Data: {cfg['period']}\n",
        ]
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

            lines.append(
                f"--- Hold {hold} days ---\n"
                f"Win Rate: {win_rate:.1f}% | Grade: {_grade(win_rate)}\n"
                f"Avg Return: {ret.mean():+.1f}%\n"
                f"Max Profit: {ret.max():+.1f}% | Max Loss: {ret.min():+.1f}%"
            )

        if best_period is None:
            return None

        lines.append(f"\nBest Period: {best_period} days (Win Rate: {best_winrate:.1f}%)")
        lines.append("\n*Caution: Based on past data.\nDoes not guarantee future returns.*")
        return "\n".join(lines)
    except Exception:
        log.exception("몬테카를로 계산 실패: %s (%s)", ticker, mc_mode)
        return None
