"""분석 엔진의 구조화된 결과 (표현/포맷 로직 없음).

텔레그램 봇과 웹 API 가 공유한다. 텔레그램은 report_format 으로 문자열을 만들고,
웹 API 는 이 dataclass 를 Pydantic 스키마로 직렬화한다(차트용 df 는 제외).
"""
from dataclasses import dataclass, field


@dataclass
class MarketRegime:
    """시장 전체 상황 (S&P500/NASDAQ 추세 + VIX 변동성 기반)."""

    label: str          # "상승장" / "횡보장" / "하락장"
    score: int          # 0~100 (높을수록 우호적)
    sp500_trend: str    # 사람이 읽는 설명, 예: "강한 상승 (20일 +3.2%)"
    nasdaq_trend: str
    vix: float
    vix_level: str      # "낮음" / "보통" / "경계" / "공포"


@dataclass
class AnalysisResult:
    """단일 티커/모드 분석 결과."""

    ticker: str
    mode: str
    label: str                     # MODE_CONFIG[mode]["label"]
    bar_width: float               # 차트 막대 폭 (MODE_CONFIG)

    # 시점 / 시장
    now_str: str                   # 데이터 기준 시각 문자열
    asof_kst: str                  # 조회 시각 (KST) 문자열
    market: str                    # get_market_status() 문자열
    is_market_open: bool

    # 가격
    price: float
    price_is_realtime: bool        # True=실시간, False=전일 종가
    target_price: float
    stop_loss: float
    target_pct: float
    stop_pct: float

    # 지표 스냅샷 (마지막 값)
    rsi: float
    macd: float
    stoch_k: float
    ma5: float
    ma20: float
    bb_upper: float
    bb_lower: float
    atr: float
    atr_pct: float
    support: float
    resistance: float
    volume: float

    # 신호 / 판정
    buy_score: int
    sell_score: int
    buy_signals: list[str]
    sell_signals: list[str]
    judgment: str                  # final_judgment 라벨, 예: "[Buy] Weak Buy"
    chart_title: str

    # 시장 심리
    fear_greed_score: int | None
    fear_greed_label: str | None
    earnings: str | None
    news_sentiment: str | None
    news_titles: list[str]
    market_regime: MarketRegime | None = None

    # 차트 렌더링용 지표 포함 DataFrame (직렬화 대상 아님)
    df: object = field(default=None, repr=False)


@dataclass
class MonteCarloHold:
    """보유기간 하나에 대한 부트스트랩 통계."""

    hold_days: int
    win_rate: float
    grade: str
    avg_return: float
    max_profit: float
    max_loss: float


@dataclass
class MonteCarloResult:
    """과거 구간 부트스트랩 시뮬레이션 결과."""

    ticker: str
    mc_mode: str
    label: str
    period: str
    simulations: int
    holds: list[MonteCarloHold]
    best_hold_days: int
    best_win_rate: float
