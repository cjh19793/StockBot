# StockBot 웹서비스 확장 — 코드 분석 & 작업 계획

작성일: 2026-09-10
대상 브랜치: `refactor/modular-structure`
목표 아키텍처:

```
사용자 → 웹사이트 → Python API 서버(FastAPI) → 기존 주식 분석 엔진 → 주식 데이터 조회 → 분석 결과 → 웹사이트 표시
```

기존 텔레그램 봇은 그대로 유지. 분석 로직은 재작성하지 않고 `core/` 한 곳에서 봇과 웹이 공유한다.

---

## 1. 현재 파일 구조

```
StockBot/
├── app.py            진입점 (bot.main 호출만)
├── bot.py            텔레그램 핸들러 + run_polling
├── analysis.py       리포트 문자열 + 차트 조립 (핵심 오케스트레이터)
├── config.py         상수 / 로깅 / 토큰 검증
├── util.py           yfinance 컬럼 평탄화, TTL 캐시 데코레이터
├── data.py           가격 데이터 조회 (yfinance)
├── indicators.py     기술적 지표 계산 (순수 함수)
├── signals.py        매수/매도 신호 스코어링 + 최종 판정
├── market.py         장 상태 / 공포탐욕지수 / 뉴스감성 / 실적일
├── charts.py         5단 차트 PNG 렌더링
├── montecarlo.py     과거구간 부트스트랩 시뮬레이션
├── tests/test_core.py 순수 함수 스모크 테스트
├── requirements.txt  의존성 (== 고정)
├── Procfile          worker: python app.py  (Railway)
└── docs/refactor-notes.md
```

이미 지난 리팩터로 모듈 분리가 잘 되어 있음. 웹 확장을 위해 새로 쪼갤 곳은 사실상 `analysis.py`와 `montecarlo.py` 두 개뿐.

---

## 2. 파일별 역할

| 파일 | 역할 | 성격 |
|---|---|---|
| `config.py` | `MODE_CONFIG`, `MC_CONFIG`, `MODE_ALIASES`, `TARGET_PCT`/`STOP_PCT`, 캐시 TTL, `require_token()`, 로깅 초기화 | 공용 (텔레그램 의존 없음, `require_token`만 봇 전용) |
| `util.py` | `flatten_columns()`, `ttl_cache()` | 순수 공용 |
| `data.py` | `get_df(ticker, mode)` OHLCV, `get_realtime_price(ticker)` | 공용 (데이터 조회 계층) |
| `indicators.py` | `calc_indicators(df)` MA5/20/60·볼린저·RSI·MACD·스토캐스틱, `get_value()` | 순수 공용 |
| `signals.py` | `detect_signal(df)` → (매수점수, 매수신호[], 매도점수, 매도신호[]), `final_judgment()` → 판정 라벨 | 대부분 공용 (표시 문자열 일부 섞임) |
| `market.py` | `get_market_status()`, `get_fear_greed()`, `get_news_sentiment()`, `get_earnings_date()` | 공용 (I/O + 데이터 반환) |
| `charts.py` | `build_chart(...)` → PNG `BytesIO` | 공용 (웹에서도 그대로 이미지로 재사용 가능) |
| `montecarlo.py` | `montecarlo(ticker, mode)` → 마크다운 문자열 | 계산부는 공용 / 출력부는 텔레그램용 |
| `analysis.py` | `analyze(ticker, mode)` → (마크다운 리포트 str, 차트 BytesIO) | 계산부는 공용 / 리포트 포맷은 텔레그램용 |
| `bot.py` | 티커 파싱, 모드 해석, `asyncio.to_thread`로 분석 실행, `reply_text`/`reply_photo` | 텔레그램 전용 |
| `app.py` | 진입점 | 텔레그램 전용 |

---

## 3. 기능별 코드 위치

| 기능 | 위치 |
|---|---|
| 주식 데이터 조회 | `data.py:13` `get_df`, `data.py:38` `get_realtime_price`, `market.py:121` `yf.Ticker().calendar`, `montecarlo.py:30` 별도 `yf.download` (조회 로직이 3곳에 분산) |
| 기술적 지표 계산 | `indicators.py:11` `calc_indicators` (전부 여기, 순수 함수) |
| 매수/매도 판단 | `signals.py:5` `detect_signal` (조건·점수), `signals.py:106` `final_judgment` (등급 라벨), `analysis.py:77-82` action 문구 파생 |
| 차트 생성 | `charts.py:13` `build_chart` (5단 서브플롯, `Figure` 직접 사용 → pyplot 전역상태 없음 = 웹/스레드 친화적) |
| 텔레그램 전송 | `bot.py` 전체 (`handle_message`의 `reply_text`/`reply_photo`), `app.py`. 리포트 문자열 조립이 `analysis.py:91-114`, `montecarlo.py:48-82`에 있음 — 전송은 아니지만 텔레그램 마크다운에 종속 |

---

## 4. 재사용 가능 코드 vs 분리 필요 코드

### 그대로 웹 API에서 재사용 가능 (수정 거의 없음)
- `indicators.py` — 완전 순수
- `data.py` — 데이터 조회 계층, 그대로 사용
- `market.py` — 구조화된 값 반환
- `charts.py` — `BytesIO` 반환 → 웹에서 `image/png` 응답으로 그대로 사용
- `signals.detect_signal` — df 받아 점수/신호 리스트 반환 (신호 문구가 한국어지만 API 응답으로 그대로 내보내도 무방)
- `montecarlo.py`의 계산 루프 (`montecarlo.py:43-80`)
- `util.py`, `config.py`의 상수

### 텔레그램에 종속 → 분리 필요

| 대상 | 문제 | 조치 |
|---|---|---|
| `analysis.py:91-114` | 최종 산출물이 텔레그램 마크다운 문자열 하나. 웹은 JSON(숫자·구조체) 필요 | 계산 결과를 dataclass로 반환하는 `run_analysis()`로 분리, 마크다운 조립은 별도 포매터 |
| `montecarlo.py:48-82` | 결과가 마크다운 문자열 | `run_montecarlo()` → dataclass 반환, 텍스트 포맷 분리 |
| `analysis.py:22-26`, `montecarlo.py:83-85` | 모든 예외를 삼켜 `None` 반환 | 웹은 "잘못된 티커(404)" vs "데이터 소스 장애(502)" 구분 필요 → 타입 있는 예외 도입 |
| `signals.final_judgment` | 판정 라벨 + 색상 문자열("blue")을 함께 반환 | 코어는 점수→enum(BUY/SELL/NEUTRAL)+등급만, 색상은 포매터/프론트로 |
| `bot.py:16` `_TICKER_RE`, `bot.py:29` 모드 해석 | 입력 검증이 봇 안에 있음 | `core`로 올려 API·봇 공용 |
| `config.py:5` `logging.basicConfig` | import 시 전역 로깅 설정 (uvicorn과 충돌 소지) | 로깅 설정은 각 진입점(app.py / web)으로 이동 |
| `config.py:11` `TELEGRAM_TOKEN` | import 시 읽지만 `require_token()`은 지연 호출 → API는 토큰 없이도 import 가능 (문제 없음, 확인 완료) |

---

## 5. 웹서비스 확장을 위해 수정해야 할 부분

1. **분석 엔진의 "출력"을 구조체로.** `analyze()`는 현재 `(str, BytesIO)` 반환. 계산부를 떼어 `AnalysisResult` dataclass(현재가, 목표가/손절가, RSI/MACD/Stoch/MA/BB 값, 매수·매도 신호 리스트, 점수, 판정 enum, 시장심리, 뉴스)로 반환. 텔레그램 마크다운은 이 구조체를 받는 얇은 포매터가 담당.
2. **차트를 별도 리소스로.** 웹은 리포트(JSON)와 차트(PNG)를 다른 엔드포인트로. `build_chart`는 그대로, `BytesIO`→`bytes` 정리. 렌더링이 느리므로 `(ticker, mode)` 키로 PNG 캐시.
3. **에러 타입 도입.** `core/errors.py`에 `TickerNotFound`, `UpstreamDataError`. 엔진은 예외를 던지고, 봇 래퍼는 잡아 기존처럼 `None` 반환(동작 유지), API는 HTTP 상태코드로 매핑.
4. **동기 I/O 처리.** yfinance·requests·matplotlib 전부 블로킹. FastAPI에서는 경로 함수를 `def`(자동 스레드풀) 또는 `await asyncio.to_thread(...)`로. `analysis.py`의 `ThreadPoolExecutor` 병렬 조회는 유지.
5. **입력 검증 공용화.** 티커 정규식·모드 별칭을 `core`로 이동. 모드 canonical 값에 영문 별칭 추가(`daily`/`scalping`/`swing`/`long`) — URL 쿼리용.
6. **공개 대비.** CORS, 레이트리밋(slowapi 등), 캐시 강화(yfinance 과호출·차단 방지), 면책 문구 응답 포함.
7. **캐시 범위.** `ttl_cache`는 프로세스 내부. uvicorn 워커 2개 이상이면 캐시·yfinance 부하 중복 → 초기엔 워커 1개, 트래픽 늘면 Redis 등 공유 캐시로.
8. **배포.** Railway에 웹 프로세스 추가(`Procfile`에 `web:` 라인 또는 별도 서비스). 텔레그램 봇은 폴링이라 반드시 1인스턴스 유지, 웹은 별도 스케일.

---

## 6. FastAPI 기준 리팩터 구조 제안

핵심 원칙: 분석 로직은 한 줄도 다시 안 짠다. 기존 함수를 `core/`로 옮기고 그 위에 표현 계층(텔레그램 / 웹)만 올린다.

```
stockbot/
├── core/                      ← 순수 분석 엔진 (텔레그램·웹 모두 여기에 의존)
│   ├── config.py              기존 그대로 (logging.basicConfig만 제거)
│   ├── util.py                기존 그대로
│   ├── data.py                기존 그대로
│   ├── indicators.py          기존 그대로
│   ├── signals.py             final_judgment 라벨/색상 → 포매터로 이동
│   ├── market.py              기존 그대로
│   ├── charts.py              BytesIO→bytes 정리
│   ├── montecarlo.py          계산부만 남기고 run_montecarlo() → dataclass
│   ├── models.py       (신규) AnalysisResult, SignalItem, MonteCarloResult dataclass
│   ├── errors.py       (신규) TickerNotFound, UpstreamDataError
│   ├── validation.py   (신규) 티커 정규식, 모드 별칭 해석 (bot.py에서 이동)
│   └── engine.py       (신규) run_analysis(ticker, mode) -> AnalysisResult
│                              (지금 analysis._analyze 의 "계산 부분"만 이동)
│
├── telegram_bot/              ← 표현 계층 A (기존 봇, 동작 유지)
│   ├── formatting.py   (신규) AnalysisResult/MonteCarloResult -> 마크다운 문자열
│   │                          (지금 analysis.py:91-114, montecarlo.py:48-82 이동)
│   └── handlers.py            기존 bot.py. run_analysis() 호출 후 formatting 적용
│
├── webapi/                    ← 표현 계층 B (신규)
│   ├── main.py                FastAPI 앱, CORS, 예외 핸들러, 로깅
│   ├── routes.py              엔드포인트
│   ├── schemas.py             Pydantic 모델 (core.models dataclass 미러링)
│   └── rate_limit.py          레이트리밋 (공개 시)
│
├── app.py                     봇 진입점 (telegram_bot.handlers.main 호출) — 거의 그대로
├── web.py 또는 uvicorn webapi.main:app   웹 진입점
└── tests/                     import 경로만 core.* 로 수정
```

### 엔드포인트안

| 메서드 | 경로 | 반환 | 재사용하는 기존 코드 |
|---|---|---|---|
| `GET` | `/health` | 상태 | — |
| `GET` | `/api/analyze/{ticker}?mode=daily` | `AnalysisResult` JSON | `engine.run_analysis` → `data.get_df` + `indicators` + `signals` + `market` |
| `GET` | `/api/chart/{ticker}.png?mode=daily` | `image/png` | `charts.build_chart` (그대로) |
| `GET` | `/api/montecarlo/{ticker}?mode=basic` | `MonteCarloResult` JSON | `montecarlo.run_montecarlo` |
| `GET` | `/api/modes` | 지원 모드 목록 | `config.MODE_CONFIG` |

데이터 흐름:
`프론트 → FastAPI(routes) → engine.run_analysis → data/market 조회 → indicators/signals 계산 → AnalysisResult → schemas 직렬화 → 프론트`

의존성 추가: `fastapi`, `uvicorn[standard]` (pydantic 포함). 공개 시 `slowapi` 정도.

---

## 7. 단계별 작업 계획

### Phase 0 — 준비 (코드 변경 없음)
- [x] 현 구조 분석 (이 문서)
- [x] 계획을 `docs/web-expansion-plan.md`로 저장

### Phase 1 — 엔진/표현 분리 (내부 리팩터, 동작 100% 유지) — ✅ 완료 (2026-09-10)

결정: `core/` 패키지 이동은 diff/비교를 어렵게 해서 **제자리 분리**로 진행 (core/ 이동은 Phase 1.5/2로 미룸).

- [x] `models.py` 신규 — `AnalysisResult` / `MonteCarloResult` / `MonteCarloHold` dataclass
- [x] `errors.py` 신규 — `AnalysisError` / `TickerNotFound` / `UpstreamDataError`
- [x] `validation.py` 신규 — `TICKER_RE` / `MC_KEYWORDS` / `is_valid_ticker` / `resolve_mode` (bot.py에서 이동)
- [x] `engine.py` 신규 — `run_analysis(ticker, mode) -> AnalysisResult` (analysis._analyze 계산부 그대로 이동)
- [x] `report_format.py` 신규(텔레그램 전용) — `format_analysis_report` / `format_montecarlo` (f-string 그대로 이동)
- [x] `montecarlo.py` — `run_montecarlo() -> MonteCarloResult` 분리, `montecarlo()`는 얇은 래퍼
- [x] `analysis.py` — `analyze()`는 `run_analysis` + `format_analysis_report` + `build_chart` 조립 래퍼로 축소, 시그니처/None 동작 유지
- [x] `bot.py` — import 소스만 변경, 핸들러 로직(31행 이후) 무변경
- [x] `config.py` / `util.py` / `data.py` / `indicators.py` / `signals.py` / `market.py` / `charts.py` / `app.py` — 무변경
- [x] 골든 스냅샷 회귀 테스트: I/O·시간·난수 고정 후 analyze 3시나리오 + montecarlo 3모드의 리포트 문자열 + 차트 PNG sha256 전후 완전 일치 확인
- [x] 단위 테스트 5 → 8개 (validation / 포매터 추가), 전부 PASS

### Phase 2 — FastAPI 서버 추가 — ✅ 완료 (2026-09-10)

- [x] `webapi/` 패키지: `__init__.py` / `main.py` / `routes.py` / `schemas.py`
- [x] `schemas.py` — `AnalysisResponse` / `MonteCarloResponse`(+Hold) / `ModesResponse` / `HealthResponse`.
      `from_attributes=True` 로 dataclass 에서 직접 검증, `df`·`bar_width` 제외
- [x] 엔드포인트 5개: `GET /health`, `/api/modes`, `/api/analyze/{ticker}`,
      `/api/chart/{ticker}.png`, `/api/montecarlo/{ticker}` (모두 `def` = 스레드풀, async 재작성 안 함)
- [x] 예외 핸들러: `TickerNotFound`→404, `UpstreamDataError`→502, 기타 `AnalysisError`→500,
      잘못된 티커/모드→422. CORS `allow_origins=["*"]` (로컬용, 배포 시 제한)
- [x] `requirements.txt` — `fastapi==0.141.1`, `uvicorn[standard]==0.52.4`
- [x] `engine`/`montecarlo`/`validation` 재사용, 텔레그램 코드 의존 0
- [x] 테스트: `tests/test_api.py` 10개(목킹) + 실서버(uvicorn) 기동 후 실제 yfinance 로
      analyze/chart/montecarlo/404/422 확인. Phase 1 회귀(test_core 8개 + 골든 스냅샷) 재확인 통과
- 배포/Procfile `web:` 추가는 하지 않음 (Phase 3)

### Phase 3 — 배포/공개 대비
- Railway 웹 서비스 추가 (봇 worker와 별개), 워커 1개
- 차트 PNG 캐시, 레이트리밋, 면책 문구
- yfinance 안정성 검토 (캐시 TTL 상향 / 폴백)

### Phase 4 — 프론트엔드 (이후 별도)

---

## 유지 보장 사항 (텔레그램 봇)

리팩터 전후로 다음이 동일하게 유지된다:
- 리포트 마크다운 문자열, 5단 차트, 몬테카를로 출력
- 모드: 기본/단타/스윙/장기 및 별칭 (`5m`/`5분`, `1h`/`1시간`, `1d`/`일봉`, `long`)
- 명령어: `/start`, `/help`, `TICKER [모드]`, `TICKER mc [모드]`
- Railway 배포 방식: `worker: python app.py` 폴링, 1인스턴스
