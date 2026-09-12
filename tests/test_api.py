"""webapi REST API 테스트 (네트워크 I/O 는 전부 목킹).

실행: python tests/test_api.py   (pytest 도 가능)
"""
import os
import sys
from contextlib import contextmanager
from unittest import mock

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402

import engine  # noqa: E402
import montecarlo as mc  # noqa: E402
from models import MarketRegime  # noqa: E402
from webapi.main import app  # noqa: E402

client = TestClient(app)


def _fake_df(n=180, seed=1, freq="D"):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    idx = pd.date_range("2025-01-01", periods=n, freq=freq)
    return pd.DataFrame(
        {
            "Open": close + rng.normal(0, 0.5, n),
            "High": close + rng.uniform(0, 2, n),
            "Low": close - rng.uniform(0, 2, n),
            "Close": close,
            "Volume": rng.uniform(1e6, 5e6, n),
        },
        index=idx,
    )


_DEFAULT = object()


@contextmanager
def mock_analysis(df=_DEFAULT):
    if df is _DEFAULT:
        df = _fake_df()

    def fake_get_df(t, mode="기본"):
        return None if df is None else df.copy()

    patches = [
        mock.patch.object(engine, "get_df", fake_get_df),
        mock.patch.object(engine, "get_realtime_price", lambda t: 123.45),
        mock.patch.object(engine, "get_market_status", lambda: ("[Closed] US Market Closed", False)),
        mock.patch.object(engine, "get_fear_greed", lambda: (40, "공포 - 매수 고려")),
        mock.patch.object(engine, "get_news_sentiment", lambda t: ("긍정 (2건)", ["AAPL up", "AAPL beats"])),
        mock.patch.object(engine, "get_earnings_date", lambda t: "실적 발표: 2025-02-01 (17일 후)"),
        mock.patch.object(engine, "get_market_regime", lambda: MarketRegime(
            label="상승장", score=72, sp500_trend="강한 상승 (20일 +2.1%)",
            nasdaq_trend="강한 상승 (20일 +3.0%)", vix=14.5, vix_level="낮음",
        )),
    ]
    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in reversed(patches):
            p.stop()


@contextmanager
def mock_montecarlo():
    import yfinance
    p1 = mock.patch.object(yfinance, "download", lambda *a, **k: _fake_df(250, seed=3))
    p2 = mock.patch("numpy.random.default_rng", lambda *a, **k: np.random.Generator(np.random.PCG64(42)))
    p1.start()
    p2.start()
    try:
        yield
    finally:
        p2.stop()
        p1.stop()


# --- tests ---

def test_health():
    r = client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"


def test_modes():
    r = client.get("/api/modes")
    assert r.status_code == 200, r.text
    body = r.json()
    names = {m["name"] for m in body["analysis"]}
    mc_names = {m["name"] for m in body["montecarlo"]}
    assert {"기본", "단타", "스윙"} <= names
    assert "장기" in mc_names and "장기" not in names
    assert body["aliases"]["5M"] == "단타"


def test_analyze_ok():
    with mock_analysis():
        r = client.get("/api/analyze/AAPL")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ticker"] == "AAPL"
    assert body["mode"] == "기본"
    assert "df" not in body
    assert isinstance(body["price"], (int, float))
    assert isinstance(body["buy_signals"], list)
    assert isinstance(body["news_titles"], list)
    assert body["judgment"]
    assert body["market_regime"]["label"] == "상승장"
    assert body["market_regime"]["score"] == 72
    assert 0 <= body["composite"]["total"] <= 100
    assert body["composite"]["label"] in {"Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"}
    assert body["composite"]["market_available"] is True   # market_regime 목킹돼 있으므로


def test_analyze_mode_alias():
    with mock_analysis():
        r = client.get("/api/analyze/AAPL", params={"mode": "5m"})
    assert r.status_code == 200, r.text
    assert r.json()["mode"] == "단타"


def test_analyze_rejects_mc_only_mode():
    with mock_analysis():
        r = client.get("/api/analyze/AAPL", params={"mode": "장기"})
    assert r.status_code == 422, r.text


def test_analyze_invalid_ticker():
    r = client.get("/api/analyze/not_a_ticker!!")
    assert r.status_code == 422, r.text


def test_analyze_ticker_not_found():
    with mock_analysis(df=None):
        r = client.get("/api/analyze/ZZZZ")
    assert r.status_code == 404, r.text


def test_chart_png():
    from webapi.routes import _build_chart_png
    _build_chart_png.cache_clear()
    with mock_analysis():
        r = client.get("/api/chart/AAPL.png")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_montecarlo_ok():
    from montecarlo import _get_mc_df
    _get_mc_df.cache_clear()
    with mock_montecarlo():
        r = client.get("/api/montecarlo/AAPL", params={"mode": "단타"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mc_mode"] == "단타"
    assert body["simulations"] == 1000
    assert len(body["holds"]) >= 1
    assert body["best_hold_days"] in [h["hold_days"] for h in body["holds"]]


def test_montecarlo_simulations_bounds():
    r = client.get("/api/montecarlo/AAPL", params={"simulations": 10})
    assert r.status_code == 422, r.text


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
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
