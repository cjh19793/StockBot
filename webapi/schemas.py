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

    fear_greed_score: int | None
    fear_greed_label: str | None
    earnings: str | None
    news_sentiment: str | None
    news_titles: list[str]
    market_regime: MarketRegimeResponse | None = None


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
