import ScoreBadge from "./ScoreBadge";
import ScoreBar from "./ScoreBar";
import ChartView from "./ChartView";
import { judgmentTone } from "../judgmentTone";

function fmt(n, digits = 2) {
  return typeof n === "number" ? n.toFixed(digits) : "-";
}

function fundamentalsRow(label, value) {
  return (
    <div className="fund-item">
      <span className="k">{label}</span>
      <span className="v">{typeof value === "number" ? `${value}점` : "데이터 없음"}</span>
    </div>
  );
}

export default function AnalysisResult({ result, chart }) {
  const r = result;
  const c = r.composite;
  const regime = r.market_regime;
  const fundamentals = r.fundamentals;

  return (
    <section className="analysis-result">
      <header className="result-header">
        <div>
          <div className="result-title">
            <h1>{r.ticker}</h1>
            <span className="mode-badge">{r.label}</span>
          </div>
          <p className="meta-line">{r.now_str} · 조회 {r.asof_kst}</p>
          <p className="meta-line">{r.market}{r.is_market_open ? " · 개장중" : ""}</p>
        </div>
        <div className={`pill ${judgmentTone(r.judgment)}`}>{r.judgment}</div>
      </header>

      {/* 종합점수 — 가장 먼저 보이도록 최상단에 배치. 값은 전부 백엔드(P3) 산출물 그대로. */}
      <div className="card composite-panel">
        <div className="composite-head">
          <span className="label">종합점수</span>
          <ScoreBadge total={c.total} label={c.label} size="lg" />
        </div>
        <div className="bars">
          <ScoreBar label="기술적 분석" value={c.technical} />
          <ScoreBar label="시장환경" value={c.market} />
          <ScoreBar label="리스크 (높을수록 안전)" value={c.risk} />
          <ScoreBar label="펀더멘털" value={c.fundamentals} />
        </div>
        {!c.market_available && (
          <p className="composite-note">시장환경 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다.</p>
        )}
        {!c.fundamentals_available && (
          <p className="composite-note">펀더멘털 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다.</p>
        )}
      </div>

      <div className="price-row">
        <div className="card price-tile">
          <span className="label">현재가</span>
          <span className="value">${fmt(r.price)}</span>
          <span className="sub">{r.price_is_realtime ? "실시간" : "전일 종가"}</span>
        </div>
        <div className="card price-tile">
          <span className="label">목표가 (+{(r.target_pct * 100).toFixed(1)}%)</span>
          <span className="value up">${fmt(r.target_price)}</span>
        </div>
        <div className="card price-tile">
          <span className="label">손절가 (-{(r.stop_pct * 100).toFixed(1)}%)</span>
          <span className="value down">${fmt(r.stop_loss)}</span>
        </div>
      </div>

      <div className="main-grid">
        <div className="col">
          <div className="card indicators">
            <h2 className="section-title">기술 지표</h2>
            <div className="indicators-grid">
              <div className="indicator-tile"><span className="k">RSI</span><span className="v">{fmt(r.rsi, 1)}</span></div>
              <div className="indicator-tile"><span className="k">MACD</span><span className="v">{fmt(r.macd)}</span></div>
              <div className="indicator-tile"><span className="k">Stoch %K</span><span className="v">{fmt(r.stoch_k, 1)}</span></div>
              <div className="indicator-tile"><span className="k">ATR</span><span className="v">{fmt(r.atr)} ({(r.atr_pct * 100).toFixed(1)}%)</span></div>
              <div className="indicator-tile"><span className="k">MA5</span><span className="v">{fmt(r.ma5)}</span></div>
              <div className="indicator-tile"><span className="k">MA20</span><span className="v">{fmt(r.ma20)}</span></div>
              <div className="indicator-tile"><span className="k">BB Upper</span><span className="v">{fmt(r.bb_upper)}</span></div>
              <div className="indicator-tile"><span className="k">BB Lower</span><span className="v">{fmt(r.bb_lower)}</span></div>
              <div className="indicator-tile"><span className="k">지지선</span><span className="v">{fmt(r.support)}</span></div>
              <div className="indicator-tile"><span className="k">저항선</span><span className="v">{fmt(r.resistance)}</span></div>
              <div className="indicator-tile"><span className="k">Volume</span><span className="v">{Math.round(r.volume).toLocaleString()}</span></div>
            </div>
          </div>

          {chart && (
            <div className="card chart-card">
              <h2 className="section-title">5단 차트</h2>
              <ChartView src={chart.src} alt={chart.alt} />
            </div>
          )}
        </div>

        <div className="col">
          {regime && (
            <div className="card side-card">
              <div className="row-head">
                <h3>시장환경</h3>
                <span className="chip-score">{regime.label} ({regime.score}점)</span>
              </div>
              <div className="kv"><span className="k">S&amp;P 500</span><span className="v">{regime.sp500_trend}</span></div>
              <div className="kv"><span className="k">NASDAQ</span><span className="v">{regime.nasdaq_trend}</span></div>
              <div className="kv"><span className="k">VIX</span><span className="v">{fmt(regime.vix, 1)} ({regime.vix_level})</span></div>
            </div>
          )}

          {fundamentals && (
            <div className="card side-card">
              <div className="row-head">
                <h3>펀더멘털</h3>
                <span className="chip-score">{fundamentals.label} ({fundamentals.overall}점)</span>
              </div>
              <div className="fund-grid">
                {fundamentalsRow("성장성", fundamentals.growth)}
                {fundamentalsRow("수익성", fundamentals.profitability)}
                {fundamentalsRow("밸류에이션", fundamentals.valuation)}
                {fundamentalsRow("재무건전성", fundamentals.financial_health)}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="signals-row">
        <div className="card signal-card buy">
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 19V5" /><path d="M5 12l7-7 7 7" /></svg>
            매수 신호 ({r.buy_score}점)
          </h3>
          {r.buy_signals.length > 0 ? (
            <ul>{r.buy_signals.map((s, i) => <li key={i}>{s}</li>)}</ul>
          ) : <p className="empty">없음</p>}
        </div>
        <div className="card signal-card sell">
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14" /><path d="M19 12l-7 7-7-7" /></svg>
            매도 신호 ({r.sell_score}점)
          </h3>
          {r.sell_signals.length > 0 ? (
            <ul>{r.sell_signals.map((s, i) => <li key={i}>{s}</li>)}</ul>
          ) : <p className="empty">없음</p>}
        </div>
      </div>

      <div className="card sentiment-card">
        <div className="sentiment-row">
          {r.fear_greed_label && (
            <div className="sentiment-item"><span className="k">공포탐욕지수</span><span className="v">{r.fear_greed_score} · {r.fear_greed_label}</span></div>
          )}
          {r.earnings && <div className="sentiment-item"><span className="k">실적</span><span className="v">{r.earnings}</span></div>}
          {r.news_sentiment && <div className="sentiment-item"><span className="k">뉴스 감성</span><span className="v">{r.news_sentiment}</span></div>}
        </div>
        {r.news_titles.length > 0 && (
          <ul className="news-list">
            {r.news_titles.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        )}
      </div>
    </section>
  );
}
