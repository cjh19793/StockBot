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

### 배포 (Railway)

- 빌드: Nixpacks 가 `.python-version`(3.13) + `requirements.txt` 로 자동 구성
- 실행: `Procfile` 의 `worker: python app.py` (웹 포트 불필요, 폴링 방식)
- 변수: Railway 프로젝트 Variables 에 `TELEGRAM_TOKEN` 등록
- 인스턴스는 1개만 (텔레그램 폴링은 중복 실행 시 충돌)

## 모듈 구성

| 파일 | 역할 |
| --- | --- |
| `config.py` | 설정·상수·로깅, 토큰 검증 |
| `util.py` | yfinance 컬럼 평탄화, TTL 캐시 |
| `data.py` | 가격 데이터 조회 |
| `indicators.py` | 지표 계산 (MA/BB/RSI/MACD/Stoch) |
| `signals.py` | 매수·매도 신호 스코어링, 최종 판정 |
| `market.py` | 장 상태, 공포탐욕지수, 뉴스 감성, 실적일 |
| `charts.py` | 5단 차트 렌더링 |
| `montecarlo.py` | 과거 구간 부트스트랩 시뮬레이션 |
| `analysis.py` | 리포트+차트 조립 (부가 정보 병렬 조회) |
| `bot.py` | 텔레그램 핸들러 및 실행 |
| `app.py` | 진입점 |

## 테스트

```bash
python tests/test_core.py
```

## 면책

모든 출력은 참고용이며 투자 권유가 아니다. 뉴스 감성은 단순 키워드 매칭이고,
"몬테카를로" 는 과거 가격 구간 표본추출로 미래 수익을 보장하지 않는다.
