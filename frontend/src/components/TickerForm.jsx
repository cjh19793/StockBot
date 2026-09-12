const FALLBACK_MODES = [
  { name: "기본", label: "Daily (Basic)" },
  { name: "단타", label: "5min (Scalping)" },
  { name: "스윙", label: "1hour (Swing)" },
];

export default function TickerForm({ ticker, mode, modes, loading, onTickerChange, onModeChange, onSubmit }) {
  const modeOptions = modes.length > 0 ? modes : FALLBACK_MODES;

  return (
    <form className="ticker-form" onSubmit={onSubmit}>
      <div className="field">
        <label htmlFor="ticker">티커</label>
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

      <div className="field">
        <label htmlFor="mode">분석 모드</label>
        <select id="mode" value={mode} onChange={(e) => onModeChange(e.target.value)}>
          {modeOptions.map((m) => (
            <option key={m.name} value={m.name}>
              {m.name} ({m.label})
            </option>
          ))}
        </select>
      </div>

      <button type="submit" disabled={loading || !ticker.trim()}>
        {loading ? "분석 중..." : "분석하기"}
      </button>
    </form>
  );
}
