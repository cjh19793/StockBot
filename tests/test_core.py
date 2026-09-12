"""순수 함수 스모크 테스트. 실행: python tests/test_core.py (pytest 도 가능)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import MC_CONFIG, MODE_CONFIG  # noqa: E402
from indicators import calc_indicators, get_value  # noqa: E402
from models import (AnalysisResult, MonteCarloHold,  # noqa: E402
                    MonteCarloResult)
from report_format import (format_analysis_report,  # noqa: E402
                           format_montecarlo)
from signals import detect_signal, final_judgment  # noqa: E402
from validation import is_valid_ticker, resolve_mode  # noqa: E402


def _sample_df(n=120, seed=0):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    high = close + rng.uniform(0, 1, n)
    low = close - rng.uniform(0, 1, n)
    open_ = close + rng.normal(0, 0.5, n)
    vol = rng.uniform(1e6, 5e6, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )


def test_indicators_columns_and_no_inf():
    df = calc_indicators(_sample_df())
    for col in ["MA5", "MA20", "Upper", "Lower", "RSI", "MACD", "MACD_signal",
               "MACD_hist", "Stoch_K", "Stoch_D"]:
        assert col in df.columns, col
    assert not np.isinf(df["RSI"].to_numpy()).any(), "RSI 에 inf 가 있으면 안 됨"


def test_rsi_no_zero_division_on_monotonic_rise():
    # 계속 오르기만 하면 loss=0 → 0 나눗셈 위험 구간
    n = 60
    df = pd.DataFrame({
        "Open": np.arange(n) + 100.0,
        "High": np.arange(n) + 100.5,
        "Low": np.arange(n) + 99.5,
        "Close": np.arange(n) + 100.0,
        "Volume": np.full(n, 1e6),
    }, index=pd.date_range("2024-01-01", periods=n, freq="D"))
    out = calc_indicators(df)
    rsi = get_value(out["RSI"])
    assert rsi == 100.0, rsi


def test_calc_indicators_does_not_mutate_input():
    df = _sample_df()
    cols_before = list(df.columns)
    calc_indicators(df)
    assert list(df.columns) == cols_before


def test_final_judgment():
    assert final_judgment(0, 0)[0] == "[Neutral] Watch"
    assert "Buy" in final_judgment(5, 1)[0]
    assert "Sell" in final_judgment(1, 5)[0]
    assert final_judgment(3, 3)[0] == "[Neutral] Balance"


def test_detect_signal_runs():
    df = calc_indicators(_sample_df())
    buy_score, buy_sig, sell_score, sell_sig = detect_signal(df)
    assert isinstance(buy_score, int) and isinstance(sell_score, int)
    assert len(buy_sig) >= 0 and len(sell_sig) >= 0


def test_validation_ticker_and_mode():
    assert is_valid_ticker("AAPL")
    assert is_valid_ticker("BRK-B")
    assert is_valid_ticker("^GSPC")
    assert not is_valid_ticker("aapl")
    assert not is_valid_ticker("TOOLONGTICKER")
    assert not is_valid_ticker("")
    # 별칭 → 표준 모드
    assert resolve_mode("5M", MODE_CONFIG) == "단타"
    assert resolve_mode("일봉", MODE_CONFIG) == "기본"
    assert resolve_mode("1H", MODE_CONFIG) == "스윙"
    # "장기" 는 몬테카를로 전용 → 일반 분석 모드에는 없음
    assert resolve_mode("장기", MODE_CONFIG) is None
    assert resolve_mode("장기", MC_CONFIG) == "장기"
    assert resolve_mode("헛소리", MODE_CONFIG) is None


def _sample_result(**over):
    base = dict(
        ticker="AAPL", mode="기본", label="Daily (Basic)", bar_width=0.6,
        now_str="2025-01-15", asof_kst="2025-01-15 10:30 (KST)",
        market="[Open] US Market Trading", is_market_open=True,
        price=137.77, price_is_realtime=True, target_price=144.66, stop_loss=133.64,
        target_pct=0.05, stop_pct=0.03,
        rsi=50.2, macd=-0.509, stoch_k=48.9, ma5=89.24, ma20=89.81,
        bb_upper=91.77, bb_lower=87.84, volume=4506843.0,
        buy_score=3, sell_score=0,
        buy_signals=["MACD 골든크로스 - 상승 전환 신호"], sell_signals=[],
        judgment="[Buy] Weak Buy", chart_title="[Buy] Weak Buy",
        fear_greed_score=40, fear_greed_label="공포 - 매수 고려",
        earnings="실적 발표: 2025-02-01 (17일 후)",
        news_sentiment="긍정 (3건)", news_titles=["AAPL surges"],
    )
    base.update(over)
    return AnalysisResult(**base)


def test_format_analysis_report_structure():
    txt = format_analysis_report(_sample_result())
    assert txt.startswith("*[AAPL] Daily (Basic) 분석 리포트*")
    assert "현재가: *137.77* (실시간)" in txt
    assert "*매수 신호 (3점)*" in txt
    assert "최종 판정: *[Buy] Weak Buy*" in txt
    assert "*Buy Timing* - Consider split buying" in txt
    # 전일 종가 / 신호 없음 분기
    txt2 = format_analysis_report(_sample_result(price_is_realtime=False, buy_signals=[]))
    assert "(전일 종가)" in txt2
    assert "*매수 신호 (3점)*\n없음" in txt2


def test_format_montecarlo_structure():
    r = MonteCarloResult(
        ticker="AAPL", mc_mode="기본", label="Basic (7/30/90 days)", period="1y",
        simulations=1000,
        holds=[
            MonteCarloHold(7, 55.0, "Good", 1.2, 8.0, -5.0),
            MonteCarloHold(30, 60.0, "Good", 3.4, 20.0, -12.0),
        ],
        best_hold_days=30, best_win_rate=60.0,
    )
    txt = format_montecarlo(r)
    assert txt.startswith("*[AAPL] Monte Carlo - Basic (7/30/90 days)*")
    assert "--- Hold 7 days ---" in txt
    assert "Win Rate: 60.0% | Grade: Good" in txt
    assert "Best Period: 30 days (Win Rate: 60.0%)" in txt
    assert txt.rstrip().endswith("Does not guarantee future returns.*")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    sys.exit(1 if failed else 0)
