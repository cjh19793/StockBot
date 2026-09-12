function fmt(n, digits = 2) {
  return typeof n === "number" ? n.toFixed(digits) : "-";
}

function judgmentTone(judgment) {
  if (judgment.includes("Buy")) return "tone-buy";
  if (judgment.includes("Sell")) return "tone-sell";
  return "tone-neutral";
}

export default function AnalysisResult({ result }) {
  const r = result;

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

      <div className="price-row">
        <div className="price-box">
          <span className="label">현재가</span>
          <span className="value">${fmt(r.price)}</span>
          <span className="sub">{r.price_is_realtime ? "실시간" : "전일 종가"}</span>
        </div>
        <div className="price-box">
          <span className="label">목표가 (+{(r.target_pct * 100).toFixed(0)}%)</span>
          <span className="value up">${fmt(r.target_price)}</span>
        </div>
        <div className="price-box">
          <span className="label">손절가 (-{(r.stop_pct * 100).toFixed(0)}%)</span>
          <span className="value down">${fmt(r.stop_loss)}</span>
        </div>
      </div>

      <div className="indicators-grid">
        <div><span className="label">RSI</span><span>{fmt(r.rsi, 1)}</span></div>
        <div><span className="label">MACD</span><span>{fmt(r.macd)}</span></div>
        <div><span className="label">Stoch %K</span><span>{fmt(r.stoch_k, 1)}</span></div>
        <div><span className="label">MA5</span><span>{fmt(r.ma5)}</span></div>
        <div><span className="label">MA20</span><span>{fmt(r.ma20)}</span></div>
        <div><span className="label">BB Upper</span><span>{fmt(r.bb_upper)}</span></div>
        <div><span className="label">BB Lower</span><span>{fmt(r.bb_lower)}</span></div>
        <div><span className="label">Volume</span><span>{Math.round(r.volume).toLocaleString()}</span></div>
      </div>

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
