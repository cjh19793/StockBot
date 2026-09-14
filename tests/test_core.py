"""순수 함수 스모크 테스트. 실행: python tests/test_core.py (pytest 도 가능)."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import MC_CONFIG, MODE_CONFIG  # noqa: E402
from fundamentals import (_financial_health_score, _growth_score,  # noqa: E402
                          _interp, _profitability_score, _score_fundamentals,
                          _valuation_score)
from indicators import calc_indicators, get_value  # noqa: E402
from market import _score_regime, _trend_score, _vix_score  # noqa: E402
from models import (AnalysisResult, CompositeScore,  # noqa: E402
                    FundamentalsScore, MarketRegime, MonteCarloHold,
                    MonteCarloResult)
from report_format import (format_analysis_report,  # noqa: E402
                           format_montecarlo)
from risk import compute_risk_score, compute_target_stop  # noqa: E402
from scoring import (_fundamentals_subscore, _market_subscore,  # noqa: E402
                     _technical_subscore, compute_composite_score)
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
               "MACD_hist", "Stoch_K", "Stoch_D", "ATR", "ATR_Pct",
               "Support", "Resistance"]:
        assert col in df.columns, col
    assert not np.isinf(df["RSI"].to_numpy()).any(), "RSI 에 inf 가 있으면 안 됨"
    assert not np.isinf(df["ATR"].to_numpy()).any(), "ATR 에 inf 가 있으면 안 됨"


def test_atr_initial_nan_then_valid():
    # 첫 행은 전일 종가가 없어 TR 자체가 NaN → ATR 도 rolling(14) 창이 채워지기 전까진 NaN.
    # 정확한 NaN 개수를 하드코딩하지 않고, "초반 NaN → 이후 유효값" 패턴만 검증.
    df = calc_indicators(_sample_df(n=120))
    atr = df["ATR"]
    assert pd.isna(atr.iloc[0]), "첫 행은 전일 종가가 없어 NaN 이어야 함"
    tail_valid = atr.iloc[-1]
    assert not pd.isna(tail_valid) and tail_valid >= 0


def test_atr_zero_for_constant_price():
    # High=Low=Close 고정이면 True Range=0 → ATR 도 0 으로 수렴 (0 나눗셈/inf 없음)
    n = 40
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "Open": np.full(n, 100.0), "High": np.full(n, 100.0),
        "Low": np.full(n, 100.0), "Close": np.full(n, 100.0),
        "Volume": np.full(n, 1e6),
    }, index=idx)
    out = calc_indicators(df)
    assert get_value(out["ATR"]) == 0.0
    assert get_value(out["ATR_Pct"]) == 0.0


def test_support_resistance_nan_boundary_and_relationship():
    df = calc_indicators(_sample_df(n=60))
    support, resistance = df["Support"], df["Resistance"]
    # rolling(20) 은 처음 19개 행이 NaN — 정확히 그 구간만 NaN 이어야 함
    assert support.iloc[:19].isna().all()
    assert resistance.iloc[:19].isna().all()
    valid = support.iloc[19:].notna() & resistance.iloc[19:].notna()
    assert valid.any(), "유효 구간이 있어야 검증 가능"
    # Resistance(=구간 내 최고가) >= Support(=구간 내 최저가) 는 항상 성립 (High>=Low 이므로)
    # Close 가 그 사이에 있다고는 가정하지 않는다 — 돌파 시 벗어날 수 있음.
    v_sup = support.iloc[19:][valid]
    v_res = resistance.iloc[19:][valid]
    assert (v_res >= v_sup).all()


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


def test_trend_score_bands():
    # 가격>MA50>MA200, 모멘텀 중립
    assert _trend_score(110, 105, 100, 0.0) == 90
    # 가격>MA200 이지만 MA50<MA200 (약한 상승)
    assert _trend_score(105, 98, 100, 0.0) == 65
    # 가격<MA200 이지만 MA50>MA200 (약한 하락)
    assert _trend_score(95, 101, 100, 0.0) == 35
    # 가격<MA50<MA200 (강한 하락)
    assert _trend_score(90, 95, 100, 0.0) == 10
    # 모멘텀 보정 (+10 / -10, 0~100 클램프)
    assert _trend_score(110, 105, 100, 0.05) == 100
    assert _trend_score(90, 95, 100, -0.05) == 0


def test_vix_score_interpolation():
    assert _vix_score(10) == 90       # 낮은 변동성 상한
    assert _vix_score(50) == 10       # 공포 구간 하한
    assert _vix_score(17.5) == 80     # 15~20 구간 중간값 보간


def test_score_regime_bull_and_bear():
    bull = _score_regime(
        110, 105, 100, 0.04,   # S&P500: 강한 상승 + 모멘텀
        110, 105, 100, 0.04,   # NASDAQ: 동일
        12,                    # VIX 낮음
    )
    assert bull.label == "상승장"
    assert bull.score >= 65

    bear = _score_regime(
        90, 95, 100, -0.04,
        90, 95, 100, -0.04,
        35,
    )
    assert bear.label == "하락장"
    assert bear.score < 35


def test_compute_target_stop_normal_range():
    target_price, stop_loss, target_pct, stop_pct = compute_target_stop(100.0, 0.02, "기본")
    assert target_pct == pytest.approx(3.0 * 0.02)   # 클램프 안 걸림 (0.06)
    assert stop_pct == pytest.approx(1.5 * 0.02)      # 0.03
    assert target_price == pytest.approx(100.0 * 1.06)
    assert stop_loss == pytest.approx(100.0 * 0.97)


def test_compute_target_stop_clamps_upper_bound():
    # 매우 높은 변동성 → 상한(target 15%, stop 8%)으로 클램프
    _, _, target_pct, stop_pct = compute_target_stop(100.0, 0.10, "기본")
    assert target_pct == 0.15
    assert stop_pct == 0.08


def test_compute_target_stop_clamps_lower_bound():
    # 매우 낮은 변동성 → 하한(target 2%, stop 1%)으로 클램프
    _, _, target_pct, stop_pct = compute_target_stop(100.0, 0.0005, "기본")
    assert target_pct == 0.02
    assert stop_pct == 0.01


def test_compute_target_stop_unknown_mode_falls_back_to_default():
    a = compute_target_stop(100.0, 0.02, "존재안함")
    b = compute_target_stop(100.0, 0.02, "기본")
    assert a == b


def test_compute_risk_score_stop_below_support_is_safest():
    # 손절가가 지지선보다 아래 → 구조 여유 만점, 낮은 변동성이면 전체도 높음
    score = compute_risk_score(stop_pct=0.01, stop_loss=90.0, support=95.0, price=100.0)
    assert score == 100


def test_compute_risk_score_stop_above_support_penalized():
    safe = compute_risk_score(stop_pct=0.03, stop_loss=97.0, support=95.0, price=100.0)
    risky = compute_risk_score(stop_pct=0.03, stop_loss=99.0, support=95.0, price=100.0)
    # 손절가가 지지선보다 위이면서 현재가에 더 가까울수록(=지지선 여유가 적을수록) 더 위험
    assert risky < safe


def test_compute_risk_score_high_stop_pct_lowers_score():
    low_vol = compute_risk_score(stop_pct=0.01, stop_loss=90.0, support=80.0, price=100.0)
    high_vol = compute_risk_score(stop_pct=0.08, stop_loss=90.0, support=80.0, price=100.0)
    assert high_vol < low_vol


def test_compute_risk_score_invalid_inputs_fallback_neutral():
    assert compute_risk_score(float("nan"), 90.0, 95.0, 100.0) == 50
    assert compute_risk_score(0.03, 90.0, float("nan"), 100.0) == 50
    assert compute_risk_score(0.03, 90.0, 95.0, None) == 50
    assert compute_risk_score(0.03, 90.0, 95.0, 0) == 50   # price<=0 방어


def test_compute_risk_score_price_at_or_below_support_no_crash():
    # stop_loss > support 인데 price<=support 인 이상 케이스 — 구조 비율 계산 불가 시
    # 예외 없이 유효 범위(0~100) 값으로 폴백해야 함 (정확히 50이라고 가정하지 않음).
    score = compute_risk_score(stop_pct=0.03, stop_loss=105.0, support=100.0, price=100.0)
    assert 0 <= score <= 100


def test_technical_subscore_uses_asymmetric_max():
    # signals.detect_signal() 실측: buy 최대 10, sell 최대 9 (비대칭)
    assert _technical_subscore(0, 0) == 50
    assert _technical_subscore(10, 0) == 100   # 매수 만점 → 상한
    assert _technical_subscore(0, 9) == 0      # 매도 만점 → 하한
    assert _technical_subscore(5, 0) == 75     # 50 + 50*(5/10)


def test_market_subscore_none_fallback():
    assert _market_subscore(None) == (50, False)
    regime = MarketRegime(label="상승장", score=80, sp500_trend="", nasdaq_trend="", vix=14.0, vix_level="낮음")
    assert _market_subscore(regime) == (80, True)


def test_compute_composite_score_neutral_and_extremes():
    # fundamentals 생략(None) → market 과 동일하게 중립(50)/사용불가로 폴백
    neutral = compute_composite_score(0, 0, None, 50)
    assert neutral.total == 50
    assert neutral.label == "Neutral"
    assert neutral.market_available is False
    assert neutral.fundamentals == 50
    assert neutral.fundamentals_available is False

    bullish_regime = MarketRegime(label="상승장", score=90, sp500_trend="", nasdaq_trend="", vix=12.0, vix_level="낮음")
    bullish_fundamentals = FundamentalsScore(
        overall=90, label="우수", growth=90, profitability=90, valuation=90, financial_health=90,
    )
    strong = compute_composite_score(10, 0, bullish_regime, 90, bullish_fundamentals)
    assert strong.total == round(100 * 0.4 + 90 * 0.2 + 90 * 0.2 + 90 * 0.2)
    assert strong.label == "Strong Buy"
    assert strong.market_available is True
    assert strong.fundamentals == 90
    assert strong.fundamentals_available is True

    bearish_regime = MarketRegime(label="하락장", score=10, sp500_trend="", nasdaq_trend="", vix=35.0, vix_level="공포")
    weak = compute_composite_score(0, 9, bearish_regime, 10)  # fundamentals 생략
    assert weak.total == round(0 * 0.4 + 10 * 0.2 + 10 * 0.2 + 50 * 0.2)
    assert weak.label == "Strong Sell"
    assert weak.fundamentals_available is False


def test_fundamentals_subscore_none_fallback():
    assert _fundamentals_subscore(None) == (50, False)
    fs = FundamentalsScore(overall=80, label="우수", growth=80, profitability=80, valuation=80, financial_health=80)
    assert _fundamentals_subscore(fs) == (80, True)


def test_analysis_result_has_composite_field():
    r = _sample_result()
    assert isinstance(r.composite, CompositeScore)
    assert 0 <= r.composite.total <= 100
    assert r.fundamentals is None  # 기본값, _sample_result 는 펀더멘털을 지정하지 않음


# --- fundamentals.py ---

def test_interp_bounds_and_midpoint():
    points = [(0, 0), (10, 100)]
    assert _interp(-5, points) == 0     # 하한 클램프
    assert _interp(15, points) == 100   # 상한 클램프
    assert _interp(5, points) == 50     # 중간 선형보간


def test_growth_score_missing_fields_returns_none():
    assert _growth_score({}) is None
    assert _growth_score({"revenueGrowth": None}) is None


def test_growth_score_uses_available_metric_only():
    # revenueGrowth 만 있을 때: 0.10 → (0.0,50)~(0.10,75) 구간 상한 = 정확히 75
    assert _growth_score({"revenueGrowth": 0.10}) == 75
    # 둘 다 있으면 평균 (0.10→75, earningsGrowth 0.25→95) → round((75+95)/2)=85
    assert _growth_score({"revenueGrowth": 0.10, "earningsGrowth": 0.25}) == 85


def test_profitability_score_partial_data():
    assert _profitability_score({}) is None
    assert _profitability_score({"profitMargins": 0.20}) == 90


def test_valuation_score_ignores_non_positive_values():
    # PER<=0(적자)은 의미 없는 값이라 제외 — 다른 지표만으로 계산
    assert _valuation_score({"trailingPE": -5, "priceToBook": 1}) == 90
    assert _valuation_score({}) is None


def test_financial_health_score_partial_data():
    assert _financial_health_score({}) is None
    assert _financial_health_score({"currentRatio": 2.0}) == 90


def test_score_fundamentals_all_missing_returns_none():
    assert _score_fundamentals({}) is None


def test_score_fundamentals_full_profile_labels_excellent():
    info = {
        "revenueGrowth": 0.25, "earningsGrowth": 0.25,
        "profitMargins": 0.20, "returnOnEquity": 0.25, "operatingMargins": 0.20,
        "trailingPE": 10, "priceToBook": 1, "pegRatio": 0.5,
        "debtToEquity": 0, "currentRatio": 2.0, "quickRatio": 1.5,
    }
    fs = _score_fundamentals(info)
    assert isinstance(fs, FundamentalsScore)
    assert fs.overall >= 70
    assert fs.label == "우수"
    assert fs.growth is not None and fs.profitability is not None
    assert fs.valuation is not None and fs.financial_health is not None


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
        bb_upper=91.77, bb_lower=87.84,
        atr=1.85, atr_pct=0.0134, support=86.10, resistance=92.40,
        volume=4506843.0,
        buy_score=3, sell_score=0,
        buy_signals=["MACD 골든크로스 - 상승 전환 신호"], sell_signals=[],
        judgment="[Buy] Weak Buy", chart_title="[Buy] Weak Buy",
        composite=CompositeScore(total=65, label="Buy", technical=75, market=60, risk=55, market_available=True),
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
