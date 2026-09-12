# StockBot 리팩터 정리 (백업)

> 2026-09-09 세션에서 진행한 리뷰 · 리팩터 · 배포 관련 내용 백업.
> 브랜치: `refactor/modular-structure` / 커밋: `c809005`

---

## 1. 리팩터 개요

- **Before**: 단일 `app.py` 650줄
- **After**: 11개 모듈 + 진입점

| 파일 | 역할 |
| --- | --- |
| `config.py` | 설정·상수·로깅, 토큰 검증 (`require_token`) |
| `util.py` | yfinance 컬럼 평탄화(`flatten_columns`), TTL 캐시(`ttl_cache`) |
| `data.py` | 가격 데이터 조회 (`get_df`, `get_realtime_price`) |
| `indicators.py` | 지표 계산 (MA/BB/RSI/MACD/Stoch), `get_value` |
| `signals.py` | 매수·매도 신호 스코어링, 최종 판정 |
| `market.py` | 장 상태, 공포탐욕지수, 뉴스 감성, 실적일 |
| `charts.py` | 5단 차트 렌더링 (`build_chart`) |
| `montecarlo.py` | 과거 구간 부트스트랩 시뮬레이션 |
| `analysis.py` | 리포트+차트 조립 (부가 정보 병렬 조회) |
| `bot.py` | 텔레그램 핸들러 및 실행 |
| `app.py` | 진입점만 (`from bot import main`) |

---

## 2. 초기 리뷰에서 지적한 개선점 (전체)

### 🔴 중요 (동작·안정성)
1. **async 핸들러 안에서 블로킹 I/O** → 한 요청이 봇 전체를 멈춤
2. **`update.message.text` None 크래시** — 사진/스티커만 온 메시지, 빈 입력
3. **RSI 0 나눗셈** — 최근 14봉 전부 상승 시 `loss=0` → inf/NaN
4. **의존성 버전 미고정** + 최신 메이저에서 깨지기 쉬운 코드 (yfinance MultiIndex, `calendar` DataFrame 등)
5. **`TELEGRAM_TOKEN` 미검증** — 없으면 불친절하게 죽음
6. **bare `except:`** (`get_realtime_price`)

### 🟡 개선 (구조·품질)
7. 단일 파일 650줄 → 모듈 분리
8. 중복 코드 (MultiIndex 평탄화 3곳, 공포탐욕 라벨 2회, 모드 파싱 일반/MC 따로)
9. `print` 로깅 → `logging`
10. 네트워크 호출 직렬 실행 → 병렬화 + 캐시
11. matplotlib 전역 `plt` 상태 → `Figure` 직접
12. 뉴스 감성 = 부분문자열 매칭 (`'up' in 'upgrade'` 오탐)
13. "몬테카를로"가 사실 과거 구간 부트스트랩 (GBM 아님), 순수 파이썬 이중 루프
14. 매직넘버 산재 (목표 +5%, 손절 -3%, 스코어 임계값)
15. 한/영 혼용

### 🟢 사소
- `.gitignore` 없음
- `.mcp.json` (로컬 PyCharm 포트) 커밋됨
- `README`, `LICENSE` 없음
- 테스트 없음
- 섹션 번호 주석 1,2,3...6,7,10 건너뜀

---

## 3. 수정사항 → 파일 위치 매핑

### async 블로킹 해결
| 내용 | 위치 |
| --- | --- |
| `analyze` / `montecarlo` 를 스레드로 실행 | `bot.py` `await asyncio.to_thread(...)` (몬테카를로/분석 각각) |
| 부가정보(실시간가·공포탐욕·뉴스·실적) 병렬 조회 | `analysis.py` `_analyze()` 내 `ThreadPoolExecutor`, `ex.submit(...)` |
| 네트워크 결과 TTL 캐시 | `util.py` `ttl_cache` / 적용: `data.py`, `market.py` / TTL 값: `config.py` `CACHE_TTL_*` |

### 의존성·런타임 고정
| 내용 | 위치 |
| --- | --- |
| 버전 `==` 고정 | `requirements.txt` |
| Python 버전 (Railway → 3.13) | `.python-version` |
| `auto_adjust=True` 명시 | `data.py`, `montecarlo.py` |

### 입력 방어 · RSI · 토큰
| 내용 | 위치 |
| --- | --- |
| 토큰 검증 | `config.py` `require_token()`, 호출: `bot.py` `main()` |
| 비텍스트·빈 메시지 가드 | `bot.py` `handle_message()` 앞부분 |
| 티커 형식 검증 | `bot.py` `_TICKER_RE` |
| `/start` `/help` | `bot.py` `start()` + `CommandHandler` 등록 |
| RSI 0 나눗셈 | `indicators.py` `loss.replace(0, np.nan)` + `rsi.mask((loss==0)&(gain>0), 100.0)` |
| 스토캐스틱 0 나눗셈 | `indicators.py` `rng = (high14-low14).replace(0, np.nan)` |

### 모듈 분리 · 중복 제거
| 내용 | 위치 |
| --- | --- |
| `calc_indicators` 입력 미변경 | `indicators.py` `df = df.copy()` |
| MultiIndex 평탄화 통합 | `util.py` `flatten_columns` → `data.py`, `montecarlo.py` |
| 공포탐욕 라벨 통합 | `market.py` `_fg_label` |
| 모드 파싱 통합 | `config.py` `MODE_ALIASES` + `bot.py` `_resolve_mode` |
| 매매 상수 분리 | `config.py` `TARGET_PCT` / `STOP_PCT` → `analysis.py` |

### 로깅 · 기타 품질
| 내용 | 위치 |
| --- | --- |
| `print` → `logging` | `config.py` `basicConfig`, 각 모듈 `logging.getLogger(__name__)` |
| error handler 사용자 알림 | `bot.py` `error_handler()` |
| pyplot 전역 상태 제거 | `charts.py` `Figure(...)` 직접 사용 |
| 뉴스 감성 단어 경계 매칭 | `market.py` `_WORD_RE` + `set(...) & _POSITIVE` |
| 실적일 yfinance 버전 대응 | `market.py` `isinstance(calendar, dict / DataFrame)` |
| 몬테카를로 벡터화 + docstring | `montecarlo.py` `rng.integers(...)`, 파일 상단 docstring |

### 거래량 신호 (유지, 변경 없음)
`signals.py` `detect_signal()` — `거래량 폭증`(2배, +2점) / `거래량 급증`(1.5배, +1점).
원본과 동일. 별도 스캐너가 아니라 조회한 티커의 매수 스코어 요소.

### 부수 파일
`.gitignore`, `README.md`, `tests/test_core.py`

---

## 4. "급등주 탐지" 관련

원본 `app.py` 에 스캐너/스케줄러/JobQueue/watchlist/알림 기능은 **애초에 없음**
(`급등|스캔|scan|JobQueue|run_repeating|schedule|watchlist|알림|notify` 검색 결과 0건).
봇은 처음부터 **반응형 전용** — 사용자가 티커를 보낼 때만 분석. 지울 것 없음.

---

## 5. 배포 (Railway)

- 빌드: Nixpacks 가 `.python-version`(3.13) + `requirements.txt` 로 자동 구성
- 실행: `Procfile` 의 `worker: python app.py` (웹 포트 불필요, 폴링 방식)
- 변수: Railway 프로젝트 Variables 에 `TELEGRAM_TOKEN` 등록
- 인스턴스는 **1개만** (텔레그램 폴링 중복 실행 시 `Conflict` 에러)

### Python 버전을 3.13 으로 정한 이유
- numpy 2.5.3 가 최소 **3.12** 요구 (pandas 3.0 / matplotlib 3.11 은 3.11+)
- Python 3.14 는 2025-10 릴리스 → Railway Nixpacks 의 고정 nixpkgs 스냅샷에 아직 없을 가능성 → 빌드 실패 또는 기본값 폴백
- 3.13 은 Railway 안정 지원 + 모든 의존성 호환

### Railway Variables 에 TELEGRAM_TOKEN 등록됐는지 확인

**웹 대시보드**
1. railway.app → 프로젝트 → 서비스 카드(StockBot) 클릭
2. **Variables** 탭
3. `TELEGRAM_TOKEN` 존재 확인 (눈 아이콘으로 값 표시). 없으면 **+ New Variable** 로 추가 → 자동 재배포
4. 서비스 여러 개면 **봇이 실행되는 서비스**의 Variables 여야 함

**Railway CLI**
```bash
npm i -g @railway/cli
railway login
railway link
railway variables       # TELEGRAM_TOKEN 있는지 확인
```

**실제 주입 확인 (Deploy Logs)**
- 정상: `텔레그램 봇 시작` 로그 후 계속 실행
- 토큰 누락: `RuntimeError: 환경변수 TELEGRAM_TOKEN 이 설정되지 않았습니다.` 로 즉시 크래시

---

## 6. main 에 반영 / 되돌리기

```bash
# 반영 (Railway 가 main 배포 시)
git checkout main
git merge refactor/modular-structure
git push

# 되돌리기
git checkout main
git branch -D refactor/modular-structure
```

---

## 7. 검증 완료 항목

- `python tests/test_core.py` — 5개 통과 (RSI 0나눗셈, 판정, 입력 미변경 등)
- 라이브 데이터로 `analyze('AAPL','기본')` → 리포트 + 362KB PNG 정상
- `montecarlo('AAPL','기본')` 정상
- 전체 모듈 `py_compile` 통과
- 토큰 미설정 시 `require_token()` RuntimeError 발생 확인
