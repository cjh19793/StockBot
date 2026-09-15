"""API 응답 스키마 (Pydantic).

models.AnalysisResult / MonteCarloResult 를 그대로 미러링한다.
- DataFrame(AnalysisResult.df)은 포함하지 않는다.
- bar_width 는 차트 렌더링 내부값이라 노출하지 않는다.
`from_attributes=True` 로 dataclass 인스턴스에서 직접 검증한다.
"""
from pydantic import BaseModel, ConfigDict


class MarketRegimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    score: int
    sp500_trend: str
    nasdaq_trend: str
    vix: float
    vix_level: str


class FundamentalsScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overall: int
    label: str
    growth: int | None
    profitability: int | None
    valuation: int | None
    financial_health: int | None


class CompositeScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    label: str
    technical: int
    market: int
    risk: int
    market_available: bool
    fundamentals: int
    fundamentals_available: bool


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    mode: str
    label: str

    now_str: str
    asof_kst: str
    market: str
    is_market_open: bool

    price: float
    price_is_realtime: bool
    target_price: float
    stop_loss: float
    target_pct: float
    stop_pct: float

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

    buy_score: int
    sell_score: int
    buy_signals: list[str]
    sell_signals: list[str]
    judgment: str
    chart_title: str
    composite: CompositeScoreResponse

    fear_greed_score: int | None
    fear_greed_label: str | None
    earnings: str | None
    news_sentiment: str | None
    news_titles: list[str]
    market_regime: MarketRegimeResponse | None = None
    fundamentals: FundamentalsScoreResponse | None = None


class CompareItemError(BaseModel):
    ticker: str
    error: str
    status_code: int


class CompareResponse(BaseModel):
    mode: str
    results: list[AnalysisResponse]
    errors: list[CompareItemError]


class MonteCarloHoldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hold_days: int
    win_rate: float
    grade: str
    avg_return: float
    max_profit: float
    max_loss: float


class MonteCarloResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    mc_mode: str
    label: str
    period: str
    simulations: int
    holds: list[MonteCarloHoldResponse]
    best_hold_days: int
    best_win_rate: float


class AnalysisModeInfo(BaseModel):
    name: str
    label: str
    interval: str
    period: str


class MonteCarloModeInfo(BaseModel):
    name: str
    label: str
    period: str
    hold_days: list[int]


class ModesResponse(BaseModel):
    analysis: list[AnalysisModeInfo]
    montecarlo: list[MonteCarloModeInfo]
    aliases: dict[str, str]


class HealthResponse(BaseModel):
    status: str
    service: str


class SeriesResponse(BaseModel):
    """차트용 시계열 (프론트에서 recharts 등으로 직접 렌더링).

    engine.run_analysis() 가 만드는 지표 포함 DataFrame을 그대로 배열로 펼친 것.
    NaN(지표 계산에 필요한 초기 구간 등)은 null 로 내려간다.
    기존 AnalysisResponse(스냅샷 값)는 그대로 두고 이 스키마는 순수 추가.
    """

    ticker: str
    mode: str
    interval: str
    dates: list[str]
    open: list[float | None]
    high: list[float | None]
    low: list[float | None]
    close: list[float | None]
    volume: list[float | None]
    ma5: list[float | None]
    ma20: list[float | None]
    ma60: list[float | None]
    bb_upper: list[float | None]
    bb_lower: list[float | None]
    rsi: list[float | None]
    macd: list[float | None]
    macd_signal: list[float | None]
    macd_hist: list[float | None]
    stoch_k: list[float | None]
    stoch_d: list[float | None]
    atr: list[float | None]
    support: list[float | None]
    resistance: list[float | None]
