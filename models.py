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
class FundamentalsScore:
    """재무 데이터(yfinance Ticker.info) 기반 펀더멘털 점수 (0~100).

    4개 하위 축(성장성/수익성/밸류에이션/재무건전성) 각각 계산 가능한 원자 지표가
    하나도 없으면 해당 축은 None. overall 은 None 이 아닌 축들의 평균이며, 하나도
    없으면(전부 None) get_fundamentals() 가 이 dataclass 자체를 만들지 않고 None 을
    반환한다 (market_regime 과 동일한 "조회 실패/데이터 없음 → None" 관례).
    """

    overall: int            # 0~100, 계산 가능한 하위 축 평균
    label: str               # "우수"/"양호"/"보통"/"주의"/"위험"
    growth: int | None            # 성장성 (매출/이익 성장률)
    profitability: int | None     # 수익성 (마진/ROE)
    valuation: int | None         # 밸류에이션 (PER/PBR/PEG, 낮을수록 고점수)
    financial_health: int | None  # 재무건전성 (부채비율/유동비율)


@dataclass
class CompositeScore:
    """기술/시장환경/리스크/펀더멘털(P5)을 가중합한 종합점수 (0~100).

    fundamentals/fundamentals_available 은 기본값을 둬서(P5 이전) 기존 코드가
    이 6개 필드만으로 CompositeScore 를 만들던 자리를 그대로 둬도 깨지지 않게 한다.
    """

    total: int          # 0~100
    label: str          # "Strong Buy" / "Buy" / "Neutral" / "Sell" / "Strong Sell"
    technical: int       # 0~100, signals.detect_signal() 매핑
    market: int           # 0~100, market_regime.score 또는 중립(50) 폴백
    risk: int              # 0~100, 높을수록 안전(낮은 리스크)
    market_available: bool  # market_regime 조회 성공 여부 (실패 시 market=50 폴백 사용)
    fundamentals: int = 50               # 0~100, fundamentals.overall 또는 중립(50) 폴백
    fundamentals_available: bool = True  # fundamentals 조회 성공 여부 (실패 시 fundamentals=50 폴백 사용)


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
    judgment: str                  # final_judgment 라벨, 예: "[Buy] Weak Buy" (변경 없음)
    chart_title: str
    composite: CompositeScore      # 종합점수 — judgment 와 별개의 신규 지표

    # 시장 심리
    fear_greed_score: int | None
    fear_greed_label: str | None
    earnings: str | None
    news_sentiment: str | None
    news_titles: list[str]
    market_regime: MarketRegime | None = None
    fundamentals: FundamentalsScore | None = None

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
