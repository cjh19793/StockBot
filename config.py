"""전역 설정, 상수, 로깅 초기화."""
import logging
import os

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 텔레그램 토큰은 환경변수에서만 읽는다 (코드/저장소에 두지 않는다).
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")


def require_token() -> str:
    """토큰이 없으면 명확한 에러로 즉시 중단."""
    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "환경변수 TELEGRAM_TOKEN 이 설정되지 않았습니다. "
            "봇을 실행하기 전에 TELEGRAM_TOKEN 을 지정하세요."
        )
    return TELEGRAM_TOKEN


# 분석 모드: interval / period / 차트 바 폭
MODE_CONFIG = {
    "단타": {"interval": "5m", "period": "5d",  "label": "5min (Scalping)", "bar_width": 0.003},
    "스윙": {"interval": "1h", "period": "60d", "label": "1hour (Swing)",   "bar_width": 0.03},
    "기본": {"interval": "1d", "period": "6mo", "label": "Daily (Basic)",   "bar_width": 0.6},
}

# 몬테카를로 모드
MC_CONFIG = {
    "단타": {"period": "3mo", "hold_days": [1, 3, 7],      "label": "Scalping (1/3/7 days)"},
    "스윙": {"period": "6mo", "hold_days": [7, 14, 30],    "label": "Swing (7/14/30 days)"},
    "기본": {"period": "1y",  "hold_days": [7, 30, 90],    "label": "Basic (7/30/90 days)"},
    "장기": {"period": "2y",  "hold_days": [90, 180, 365], "label": "Long-term (90/180/365 days)"},
}

# 사용자 입력 별칭 → 표준 모드 이름
MODE_ALIASES = {
    "단타": "단타", "5M": "단타", "5분": "단타",
    "스윙": "스윙", "1H": "스윙", "1시간": "스윙",
    "기본": "기본", "1D": "기본", "일봉": "기본",
    "장기": "장기", "LONG": "장기",
}

# 매매 파라미터 — 목표가/손절가는 고정 %가 아니라 ATR(변동성) 기반으로 계산한다.
# 모드별 ATR 배수: 짧은 호흡일수록 배수를 좁게.
MODE_TARGET_ATR_MULT = {"단타": 1.5, "스윙": 2.5, "기본": 3.0}
MODE_STOP_ATR_MULT = {"단타": 1.0, "스윙": 1.5, "기본": 1.5}
# 위 배수 적용 후 비상식적인 값이 나오지 않도록 클램프 (min, max)
TARGET_PCT_BOUNDS = (0.02, 0.15)
STOP_PCT_BOUNDS = (0.01, 0.08)

# 종합점수(0~100) — signals.detect_signal() 실측 최대점수로 정규화.
# 매수/매도 조건이 비대칭(매도쪽 거래량 조건에 elif 완화단계가 없음)이라
# BUY_SCORE_MAX(10) != SELL_SCORE_MAX(9). 두 지표를 늘리거나 배점을 바꾸면
# 이 값도 함께 갱신해야 한다 (signals.py 변경 시 재확인 필요).
BUY_SCORE_MAX = 10
SELL_SCORE_MAX = 9

# 기술/시장환경/리스크/펀더멘털 가중합. 합이 1.0. 백테스트(P8)에서 재실험할 수 있도록 상수로 분리.
# P5(펀더멘털) 추가 전 비율(기술:시장:리스크 = 2:1:1)을 그대로 유지한 채 20%p를 떼어
# 펀더멘털에 배분 (0.5→0.4, 0.25→0.2, 0.25→0.2, 신규 0.2).
COMPOSITE_WEIGHTS = {"technical": 0.4, "market": 0.2, "risk": 0.2, "fundamentals": 0.2}

# 종합점수 → 라벨. 내림차순으로 첫 매치 사용.
COMPOSITE_BANDS = [
    (70, "Strong Buy"),
    (55, "Buy"),
    (45, "Neutral"),
    (30, "Sell"),
    (0, "Strong Sell"),
]

# 조회 결과 TTL 캐시 (초)
CACHE_TTL_OHLC = 90
CACHE_TTL_REALTIME = 30
CACHE_TTL_MARKET = 300
CACHE_TTL_EARNINGS = 3600
CACHE_TTL_MONTECARLO = 300  # 몬테카를로용 일봉 다운로드 (yfinance 과호출 방지)
CACHE_TTL_CHART = 90        # 렌더링된 차트 PNG (요청마다 재렌더링 방지)
# 펀더멘털(yf.Ticker.info)은 분기 실적 주기로만 바뀌므로 다른 조회보다 훨씬 길게 캐싱해
# Render Free 티어에서 반복 조회로 인한 yfinance 과호출/레이트리밋을 피한다.
CACHE_TTL_FUNDAMENTALS = 21600  # 6시간

# 웹 API CORS 허용 도메인. 콤마로 구분된 목록, 기본값 "*"(전체 허용 — 로컬/초기 배포용).
# 프론트 도메인이 정해지면 예: CORS_ORIGINS="https://stockbot.example.com,https://app.example.com"
_cors_raw = os.environ.get("CORS_ORIGINS", "*").strip()
CORS_ORIGINS = ["*"] if _cors_raw == "*" else [o.strip() for o in _cors_raw.split(",") if o.strip()]
