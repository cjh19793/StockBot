"""순수 함수 스모크 테스트. 실행: python tests/test_core.py (pytest 도 가능)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from indicators import calc_indicators, get_value  # noqa: E402
from signals import detect_signal, final_judgment  # noqa: E402


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
