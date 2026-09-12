"""API 라우트.

동기 I/O(yfinance / matplotlib)를 쓰는 엔진 함수를 그대로 호출한다.
경로 함수를 `def`(async 아님)로 두면 FastAPI 가 스레드풀에서 실행하므로
이벤트 루프를 블로킹하지 않는다 — 전체를 async 로 재작성하지 않는다.
"""
import logging

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response

from charts import build_chart
from config import CACHE_TTL_CHART, MC_CONFIG, MODE_ALIASES, MODE_CONFIG
from engine import run_analysis
from montecarlo import run_montecarlo
from util import ttl_cache
from validation import is_valid_ticker, resolve_mode
from webapi import schemas

log = logging.getLogger(__name__)
router = APIRouter()


@ttl_cache(CACHE_TTL_CHART)
def _build_chart_png(ticker: str, mode: str) -> bytes:
    """티커+모드 기준 렌더링된 PNG 바이트. 캐싱으로 반복 요청 시 재분석·재렌더링 방지."""
    result = run_analysis(ticker, mode)
    buf = build_chart(
        result.df,
        ticker=result.ticker,
        label=result.label,
        now_str=result.now_str,
        market=result.market,
        chart_title=result.chart_title,
        target_price=result.target_price,
        stop_loss=result.stop_loss,
        buy_score=result.buy_score,
        sell_score=result.sell_score,
        bar_width=result.bar_width,
    )
    return buf.getvalue()


def _clean_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    if not is_valid_ticker(t):
        raise HTTPException(status_code=422, detail=f"올바르지 않은 티커 형식: {ticker!r}")
    return t


def _resolve_mode_param(raw: str | None, allowed) -> str:
    """쿼리의 mode 값을 표준 모드 이름으로. 기본값은 '기본'. 알 수 없으면 422."""
    if not raw:
        return "기본"
    canon = resolve_mode(raw.strip().upper(), allowed)
    if canon is None:
        raise HTTPException(
            status_code=422,
            detail=f"지원하지 않는 모드: {raw!r} (가능: {list(allowed)})",
        )
    return canon


@router.get("/health", response_model=schemas.HealthResponse, tags=["meta"])
def health():
    return schemas.HealthResponse(status="ok", service="stockbot-api")


@router.get("/api/modes", response_model=schemas.ModesResponse, tags=["meta"])
def modes():
    return schemas.ModesResponse(
        analysis=[
            schemas.AnalysisModeInfo(
                name=name, label=cfg["label"],
                interval=cfg["interval"], period=cfg["period"],
            )
            for name, cfg in MODE_CONFIG.items()
        ],
        montecarlo=[
            schemas.MonteCarloModeInfo(
                name=name, label=cfg["label"],
                period=cfg["period"], hold_days=cfg["hold_days"],
            )
            for name, cfg in MC_CONFIG.items()
        ],
        aliases=dict(MODE_ALIASES),
    )


@router.get(
    "/api/analyze/{ticker}",
    response_model=schemas.AnalysisResponse,
    tags=["analysis"],
)
def analyze(
    ticker: str = Path(..., description="미국 주식 티커 (예: AAPL)"),
    mode: str | None = Query(
        None, description="분석 모드: 기본/단타/스윙 또는 별칭(5m·1h·1d 등). 생략 시 기본"
    ),
):
    t = _clean_ticker(ticker)
    m = _resolve_mode_param(mode, MODE_CONFIG)
    result = run_analysis(t, m)  # TickerNotFound / UpstreamDataError → 예외 핸들러
    return schemas.AnalysisResponse.model_validate(result)


@router.get("/api/chart/{ticker}.png", tags=["analysis"])
def chart(
    ticker: str = Path(..., description="미국 주식 티커 (예: AAPL)"),
    mode: str | None = Query(None, description="분석 모드 (analyze 와 동일)"),
):
    t = _clean_ticker(ticker)
    m = _resolve_mode_param(mode, MODE_CONFIG)
    png = _build_chart_png(t, m)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": f"public, max-age={CACHE_TTL_CHART}"},
    )


@router.get(
    "/api/montecarlo/{ticker}",
    response_model=schemas.MonteCarloResponse,
    tags=["analysis"],
)
def montecarlo(
    ticker: str = Path(..., description="미국 주식 티커 (예: AAPL)"),
    mode: str | None = Query(
        None, description="몬테카를로 모드: 기본/단타/스윙/장기. 생략 시 기본"
    ),
    simulations: int = Query(1000, ge=100, le=10000, description="시뮬레이션 횟수"),
):
    t = _clean_ticker(ticker)
    m = _resolve_mode_param(mode, MC_CONFIG)
    result = run_montecarlo(t, m, simulations)
    return schemas.MonteCarloResponse.model_validate(result)
