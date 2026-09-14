# StockBot

미국 주식 티커를 입력하면 기술적 지표 기반 분석 리포트와 차트를 보내주는 텔레그램 봇.

## 사용법 (텔레그램 메시지)

| 입력 | 동작 |
| --- | --- |
| `AAPL` | 기본(일봉) 분석 |
| `AAPL 단타` | 5분봉 분석 (`5m` / `5분` 도 가능) |
| `AAPL 스윙` | 1시간봉 분석 (`1h` / `1시간` 도 가능) |
| `AAPL mc` | 몬테카를로(부트스트랩) 시뮬레이션 — 기본 |
| `AAPL mc 스윙` | 몬테카를로 — `단타` / `스윙` / `장기` 선택 |
| `/help` | 사용법 표시 |

## 실행

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
export TELEGRAM_TOKEN=<봇 토큰>   # Windows: $env:TELEGRAM_TOKEN=...
python app.py
```

`TELEGRAM_TOKEN` 은 환경변수로만 주입한다 (코드/저장소에 두지 않는다).

### 웹 API (로컬)

```bash
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn webapi.main:app --reload   # http://127.0.0.1:8000
# 문서: /docs  (Swagger UI)
```

봇과는 별개 프로세스이며 `TELEGRAM_TOKEN` 이 필요 없다.

| 엔드포인트 | 설명 |
| --- | --- |
| `GET /health` | 상태 확인 |
| `GET /api/modes` | 지원 분석/몬테카를로 모드 + 별칭 |
| `GET /api/analyze/{ticker}?mode=` | 분석 결과 JSON (`engine.run_analysis`, P3 종합점수 + P5 펀더멘털 포함) |
| `GET /api/chart/{ticker}.png?mode=` | 분석 차트 PNG (`charts.build_chart`) |
| `GET /api/montecarlo/{ticker}?mode=&simulations=` | 부트스트랩 시뮬레이션 JSON |
| `GET /api/compare?tickers=A,B,C&mode=` | 2~10개 종목 비교 JSON (`results`/`errors` — 실패 종목이 있어도 나머지는 정상 반환) |

`mode` 는 봇과 동일한 값/별칭(`기본`·`단타`·`스윙`, `5m`·`1h`·`1d` …, MC 는 `장기` 추가). 없으면 `기본`.
`TickerNotFound` → 404, `UpstreamDataError` → 502, 잘못된 티커/모드 → 422.

### 웹 프론트엔드 (React/Vite)

`frontend/` — 종합점수/기술·시장환경·리스크·펀더멘털/목표가·손절가/차트를 보여주는 단일 분석 화면과
`/api/compare` 를 사용하는 종목 비교 화면(2~10개, 점수순 정렬, 개별 오류 표시)으로 구성.
프론트는 백엔드 계산값을 표시만 하며 점수/판정을 자체적으로 계산하지 않는다.

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173, API는 VITE_API_BASE_URL(.env) 사용
```

배포 시에는 `webapi/main.py` 가 **같은 FastAPI 서비스**에서 `frontend/dist` 를 정적으로
서빙한다(새 서비스 추가 없음). Render 빌드 환경에 Node 가 없어 이 방식을 쓰므로,
프론트 소스를 바꾸면 반드시 아래처럼 다시 빌드해 `frontend/dist` 를 함께 커밋해야 배포에 반영된다.

```bash
cd frontend && npm run build   # frontend/dist 갱신 → git add frontend/dist 후 커밋
```

### 배포 (Render — 웹 API + 프론트)

`render.yaml` 블루프린트, Free 플랜. `pip install -r requirements.txt` 만 빌드하고
`uvicorn webapi.main:app` 이 API와 (미리 빌드된) 프론트를 함께 서빙한다.
`CORS_ORIGINS` 환경변수로 허용 도메인 제한 가능(기본 `*`).

### 배포 (Railway — 텔레그램 봇)

- 빌드: Nixpacks 가 `.python-version`(3.13) + `requirements.txt` 로 자동 구성
- 실행: `Procfile` 의 `worker: python app.py` (웹 포트 불필요, 폴링 방식)
- 변수: Railway 프로젝트 Variables 에 `TELEGRAM_TOKEN` 등록
- 인스턴스는 1개만 (텔레그램 폴링은 중복 실행 시 충돌)

## 모듈 구성

분석 엔진(공용) / 표현 계층(텔레그램) 분리:

| 파일 | 역할 | 계층 |
| --- | --- | --- |
| `config.py` | 설정·상수·로깅, 토큰 검증 | 공용 |
| `util.py` | yfinance 컬럼 평탄화, TTL 캐시 | 공용 |
| `data.py` | 가격 데이터 조회 | 공용 |
| `indicators.py` | 지표 계산 (MA/BB/RSI/MACD/Stoch) | 공용 |
| `signals.py` | 매수·매도 신호 스코어링, 최종 판정 | 공용 |
| `market.py` | 장 상태, 공포탐욕지수, 뉴스 감성, 실적일, 시장 국면(P4) | 공용 |
| `risk.py` | ATR 기반 목표가/손절가, 리스크 점수(P4) | 공용 |
| `scoring.py` | 종합점수(0~100) 산출 — 기술/시장환경/리스크/펀더멘털(P5) 가중합 | 공용 |
| `fundamentals.py` | 펀더멘털 점수(P5) — 성장성/수익성/밸류에이션/재무건전성 (`yf.Ticker.info`) | 공용 |
| `charts.py` | 5단 차트 렌더링 (PNG) | 공용 |
| `models.py` | `AnalysisResult` / `MonteCarloResult` / `FundamentalsScore` dataclass | 공용 |
| `errors.py` | 분석 엔진 예외 | 공용 |
| `validation.py` | 티커/모드 입력 검증 | 공용 |
| `engine.py` | `run_analysis()` — 분석 결과 계산 | 공용 엔진 |
| `montecarlo.py` | `run_montecarlo()` 계산 + `montecarlo()` 텔레그램 래퍼 | 공용 엔진 / 텔레그램 |
| `report_format.py` | 결과 → 텔레그램 마크다운 문자열 | 텔레그램 |
| `analysis.py` | `analyze()` — 리포트+차트 조립 (텔레그램 래퍼) | 텔레그램 |
| `bot.py` | 텔레그램 핸들러 및 실행 | 텔레그램 |
| `app.py` | 진입점 | 텔레그램 |

## 테스트

```bash
python tests/test_core.py   # 순수 함수 (지표/시그널/스코어링/펀더멘털/포맷)
python tests/test_api.py    # 웹 API (네트워크 I/O 목킹)
# 또는: pytest tests/
```

## 면책

모든 출력은 참고용이며 투자 권유가 아니다. 뉴스 감성은 단순 키워드 매칭이고,
"몬테카를로" 는 과거 가격 구간 표본추출로 미래 수익을 보장하지 않는다. 펀더멘털 점수(P5)는
`yf.Ticker.info` 의 성장률/마진/PER·PBR·PEG/부채·유동비율을 단순 구간표로 점수화한 것으로,
업종별 특성을 반영하지 않는 대략적인 참고 지표다. ETF·신규 상장·해외 상장 등은 일부 또는
전체 지표가 없을 수 있으며, 이 경우 계산 가능한 지표만으로 평균을 내거나(부분 결측) 중립값
50으로 폴백한다(전체 결측).
