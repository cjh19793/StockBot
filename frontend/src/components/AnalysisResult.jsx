import ScoreBadge from "./ScoreBadge";
import ScoreBar from "./ScoreBar";

function fmt(n, digits = 2) {
  return typeof n === "number" ? n.toFixed(digits) : "-";
}

function judgmentTone(judgment) {
  if (judgment.includes("Buy")) return "tone-buy";
  if (judgment.includes("Sell")) return "tone-sell";
  return "tone-neutral";
}

function fundamentalsRow(label, value) {
  return (
    <p className="meta">
      {label}: {typeof value === "number" ? `${value}점` : "데이터 없음"}
    </p>
  );
}

export default function AnalysisResult({ result }) {
  const r = result;
  const c = r.composite;
  const regime = r.market_regime;
  const fundamentals = r.fundamentals;

  return (
    <section className="analysis-result">
      <header className="result-header">
        <div>
          <h2>{r.ticker} <span className="badge">{r.label}</span></h2>
          <p className="meta">{r.now_str} · 조회 {r.asof_kst}</p>
          <p className="meta">{r.market}</p>
        </div>
        <div className={`judgment ${judgmentTone(r.judgment)}`}>{r.judgment}</div>
      </header>

      {/* 종합점수 — 가장 먼저 보이도록 최상단에 배치. 값은 전부 백엔드(P3) 산출물 그대로. */}
      <div className="composite-panel">
        <div className="composite-headline">
          <span className="composite-title">종합점수</span>
          <ScoreBadge total={c.total} label={c.label} size="lg" />
        </div>
        <div className="composite-breakdown">
          <ScoreBar label="기술적 분석" value={c.technical} />
          <ScoreBar label="시장환경" value={c.market} />
          <ScoreBar label="리스크(높을수록 안전)" value={c.risk} />
          <ScoreBar label="펀더멘털" value={c.fundamentals} />
        </div>
        {!c.market_available && (
          <p className="composite-note">
            시장환경 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다.
          </p>
        )}
        {!c.fundamentals_available && (
          <p className="composite-note">
            펀더멘털 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다.
          </p>
        )}
      </div>

      <div className="price-row">
        <div className="price-box">
          <span className="label">현재가</span>
          <span className="value">${fmt(r.price)}</span>
          <span className="sub">{r.price_is_realtime ? "실시간" : "전일 종가"}</span>
        </div>
        <div className="price-box">
          <span className="label">목표가 (+{(r.target_pct * 100).toFixed(1)}%)</span>
          <span className="value up">${fmt(r.target_price)}</span>
        </div>
        <div className="price-box">
          <span className="label">손절가 (-{(r.stop_pct * 100).toFixed(1)}%)</span>
          <span className="value down">${fmt(r.stop_loss)}</span>
        </div>
      </div>

      <div className="indicators-grid">
        <div><span className="label">RSI</span><span>{fmt(r.rsi, 1)}</span></div>
        <div><span className="label">MACD</span><span>{fmt(r.macd)}</span></div>
        <div><span className="label">Stoch %K</span><span>{fmt(r.stoch_k, 1)}</span></div>
        <div><span className="label">ATR</span><span>{fmt(r.atr)} ({(r.atr_pct * 100).toFixed(1)}%)</span></div>
        <div><span className="label">MA5</span><span>{fmt(r.ma5)}</span></div>
        <div><span className="label">MA20</span><span>{fmt(r.ma20)}</span></div>
        <div><span className="label">BB Upper</span><span>{fmt(r.bb_upper)}</span></div>
        <div><span className="label">BB Lower</span><span>{fmt(r.bb_lower)}</span></div>
        <div><span className="label">지지선</span><span>{fmt(r.support)}</span></div>
        <div><span className="label">저항선</span><span>{fmt(r.resistance)}</span></div>
        <div><span className="label">Volume</span><span>{Math.round(r.volume).toLocaleString()}</span></div>
      </div>

      {regime && (
        <div className="regime-row">
          <h3>시장환경 <span className="regime-label">{regime.label} ({regime.score}점)</span></h3>
          <p className="meta">S&amp;P500: {regime.sp500_trend}</p>
          <p className="meta">NASDAQ: {regime.nasdaq_trend}</p>
          <p className="meta">VIX: {fmt(regime.vix, 1)} ({regime.vix_level})</p>
        </div>
      )}

      {fundamentals && (
        <div className="regime-row">
          <h3>펀더멘털 <span className="regime-label">{fundamentals.label} ({fundamentals.overall}점)</span></h3>
          {fundamentalsRow("성장성", fundamentals.growth)}
          {fundamentalsRow("수익성", fundamentals.profitability)}
          {fundamentalsRow("밸류에이션", fundamentals.valuation)}
          {fundamentalsRow("재무건전성", fundamentals.financial_health)}
        </div>
      )}

      <div className="signals-row">
        <div className="signals-box buy">
          <h3>매수 신호 ({r.buy_score}점)</h3>
          {r.buy_signals.length > 0 ? (
            <ul>{r.buy_signals.map((s, i) => <li key={i}>{s}</li>)}</ul>
          ) : <p className="empty">없음</p>}
        </div>
        <div className="signals-box sell">
          <h3>매도 신호 ({r.sell_score}점)</h3>
          {r.sell_signals.length > 0 ? (
            <ul>{r.sell_signals.map((s, i) => <li key={i}>{s}</li>)}</ul>
          ) : <p className="empty">없음</p>}
        </div>
      </div>

      <div className="sentiment-row">
        {r.fear_greed_label && (
          <p><strong>공포탐욕지수</strong> {r.fear_greed_score} · {r.fear_greed_label}</p>
        )}
        {r.earnings && <p><strong>실적</strong> {r.earnings}</p>}
        {r.news_sentiment && <p><strong>뉴스 감성</strong> {r.news_sentiment}</p>}
        {r.news_titles.length > 0 && (
          <ul className="news-list">
            {r.news_titles.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        )}
      </div>
    </section>
  );
}
