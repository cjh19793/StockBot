const FALLBACK_MODES = [
  { name: "기본", label: "Daily (Basic)" },
  { name: "단타", label: "5min (Scalping)" },
  { name: "스윙", label: "1hour (Swing)" },
];

export default function TickerForm({ ticker, mode, modes, loading, onTickerChange, onModeChange, onSubmit }) {
  const modeOptions = modes.length > 0 ? modes : FALLBACK_MODES;

  return (
    <form className="search-card" onSubmit={onSubmit}>
      <div className="field" style={{ flex: 1 }}>
        <label htmlFor="ticker">티커</label>
        <div className="input">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            id="ticker"
            type="text"
            inputMode="text"
            autoCapitalize="characters"
            autoComplete="off"
            placeholder="예: AAPL"
            value={ticker}
            onChange={(e) => onTickerChange(e.target.value)}
            maxLength={10}
          />
        </div>
      </div>

      <div className="field">
        <label htmlFor="mode">분석 모드</label>
        <div className="segmented" role="radiogroup" aria-label="분석 모드">
          {modeOptions.map((m) => (
            <button
              type="button"
              key={m.name}
              role="radio"
              aria-checked={mode === m.name}
              className={`seg ${mode === m.name ? "active" : ""}`}
              onClick={() => onModeChange(m.name)}
            >
              {m.name}
            </button>
          ))}
        </div>
      </div>

      <button type="submit" className="btn-primary" disabled={loading || !ticker.trim()}>
        {loading ? "분석 중..." : "분석하기"}
      </button>
    </form>
  );
}
