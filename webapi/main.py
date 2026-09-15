"""FastAPI 앱 진입점.

로컬 실행:
    uvicorn webapi.main:app --reload
    (또는  python -m webapi.main)

기존 텔레그램 봇(app.py)과는 완전히 별개 프로세스다.
"""
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS
from errors import AnalysisError, TickerNotFound, UpstreamDataError
from webapi.routes import router

log = logging.getLogger("webapi")

app = FastAPI(
    title="StockBot API",
    version="0.1.0",
    description="기존 주식 분석 엔진(engine.run_analysis / montecarlo.run_montecarlo)을 "
    "재사용하는 REST API. 텔레그램 봇과 동일한 분석 로직.",
)

log.info("CORS 허용 도메인: %s", CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 기본 "*" — 배포 시 CORS_ORIGINS 환경변수로 제한
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - start) * 1000
    log.info(
        "%s %s -> %d (%.1fms)",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


@app.exception_handler(TickerNotFound)
async def _handle_ticker_not_found(request: Request, exc: TickerNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": f"티커 데이터를 찾을 수 없습니다: {exc}"},
    )


@app.exception_handler(UpstreamDataError)
async def _handle_upstream_error(request: Request, exc: UpstreamDataError):
    return JSONResponse(
        status_code=502,
        content={"detail": f"외부 데이터 소스 오류입니다. 잠시 후 다시 시도해주세요. ({exc})"},
    )


@app.exception_handler(AnalysisError)
async def _handle_analysis_error(request: Request, exc: AnalysisError):
    log.exception("분석 엔진 오류: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "분석 처리 중 오류가 발생했습니다."})


@app.exception_handler(Exception)
async def _handle_unexpected_error(request: Request, exc: Exception):
    log.exception("처리되지 않은 오류: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "서버 내부 오류가 발생했습니다."})


app.include_router(router)

# Next.js 프론트(frontend/out, 정적 export 결과물을 미리 빌드해 커밋함 — Render
# 빌드 환경엔 Node 가 없음)를 같은 서비스에서 정적으로 서빙한다. /health, /api/*,
# /docs 등은 위에서 먼저 등록됐으므로 우선 매칭되고, 그 외 경로만 이 아래로 떨어져
# 각 라우트의 index.html 로 간다 (next.config.mjs 의 trailingSlash:true 덕에
# /analyze 요청도 frontend/out/analyze/index.html 로 해석됨).
# 로컬에서 API만 띄우는 기존 개발 흐름(`uvicorn webapi.main:app --reload`)은
# out 이 없으면 그냥 마운트를 건너뛰고 그대로 동작한다.
_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "out")
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
    log.info("프론트엔드 정적 파일 서빙: %s", _FRONTEND_DIST)
else:
    log.info("frontend/out 없음 — API만 서빙 (프론트 빌드 필요 시 frontend/에서 npm run build)")


def main():
    import uvicorn

    uvicorn.run("webapi.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
