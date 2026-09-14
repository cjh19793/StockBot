import { useState } from "react";
import { fetchMonteCarlo } from "../api";

const FALLBACK_MODES = [
  { name: "기본", label: "Basic (7/30/90 days)" },
  { name: "단타", label: "Scalping (1/3/7 days)" },
  { name: "스윙", label: "Swing (7/14/30 days)" },
  { name: "장기", label: "Long-term (90/180/365 days)" },
];

const GRADE_TONE = {
  Excellent: "excellent",
  Good: "good",
  Neutral: "neutral",
  Caution: "caution",
};

function fmtPct(n) {
  return typeof n === "number" ? `${n >= 0 ? "+" : ""}${n.toFixed(1)}%` : "-";
}

export default function MonteCarloView({ modes }) {
  const [ticker, setTicker] = useState("");
  const [mode, setMode] = useState("기본");
  const [simulations, setSimulations] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const modeOptions = modes.length > 0 ? modes : FALLBACK_MODES;
  const currentLabel = modeOptions.find((m) => m.name === mode)?.label || "";

  async function handleSubmit(e) {
    e.preventDefault();
    const clean = ticker.trim().toUpperCase();
    if (!clean) return;

    setLoading(true);
    setError(null);
    try {
      const data = await fetchMonteCarlo(clean, mode, simulations);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err.message || "몬테카를로 시뮬레이션에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const best = result ? result.holds.find((h) => h.hold_days === result.best_hold_days) : null;

  return (
    <section className="view-stack">
      <form className="search-card" onSubmit={handleSubmit}>
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="mc-ticker">티커</label>
          <div className="input">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              id="mc-ticker"
              type="text"
              inputMode="text"
              autoCapitalize="characters"
              autoComplete="off"
              placeholder="예: AAPL"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              maxLength={10}
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="mc-mode">몬테카를로 모드</label>
          <div className="segmented" role="radiogroup" aria-label="몬테카를로 모드">
            {modeOptions.map((m) => (
              <button
                type="button"
                key={m.name}
                role="radio"
                aria-checked={mode === m.name}
                className={`seg ${mode === m.name ? "active" : ""}`}
                onClick={() => setMode(m.name)}
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label htmlFor="mc-sims">시뮬레이션 횟수</label>
          <div className="input" style={{ maxWidth: 140 }}>
            <input
              id="mc-sims"
              type="number"
              min={100}
              max={10000}
              step={100}
              value={simulations}
              onChange={(e) => setSimulations(Number(e.target.value))}
            />
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading || !ticker.trim()}>
          {loading ? "시뮬레이션 중..." : "시뮬레이션 실행"}
        </button>
      </form>

      {loading && (
        <p className="hint">
          부트스트랩 시뮬레이션을 실행 중입니다. 서버가 잠시 쉬고 있었다면 최대 1분 정도 걸릴 수 있어요.
        </p>
      )}

      {error && <p className="error-message">{error}</p>}

      {result && (
        <>
          <div className="page-title">
            <h1>{result.ticker} · 몬테카를로 시뮬레이션</h1>
            <p>{currentLabel || result.label} · 과거 가격 구간 부트스트랩 표본추출 {result.simulations.toLocaleString()}회</p>
          </div>

          {best && (
            <div className="card best-card">
              <div>
                <div className="l">최적 보유기간</div>
                <div className="big">{result.best_hold_days}일 보유</div>
              </div>
              <div className="win">
                <div className="num">{result.best_win_rate.toFixed(1)}%</div>
                <div className="cap">승률</div>
              </div>
            </div>
          )}

          <div className="hold-grid">
            {result.holds.map((h) => (
              <div
                className={`card hold-card ${h.hold_days === result.best_hold_days ? "best" : ""}`}
                key={h.hold_days}
              >
                <div className="head">
                  <h3>{h.hold_days}일 보유</h3>
                  <span className={`grade ${GRADE_TONE[h.grade] || "neutral"}`}>{h.grade}</span>
                </div>
                <div className="winrate">{h.win_rate.toFixed(1)}%</div>
                <div className="winrate-label">승률</div>
                <div className="hold-kv"><span className="k">평균 수익률</span><span className={`v ${h.avg_return >= 0 ? "up" : "down"}`}>{fmtPct(h.avg_return)}</span></div>
                <div className="hold-kv"><span className="k">최대 수익</span><span className="v up">{fmtPct(h.max_profit)}</span></div>
                <div className="hold-kv"><span className="k">최대 손실</span><span className="v down">{fmtPct(h.max_loss)}</span></div>
              </div>
            ))}
          </div>

          <div className="method-card">
            과거 가격 구간을 무작위로 표본추출(부트스트랩)해 각 보유기간 종료 시점의 수익률 분포를 시뮬레이션한 결과입니다.
            GBM(기하 브라운 운동) 같은 확률 모형이 아니며, 미래 수익을 보장하지 않습니다.
          </div>
        </>
      )}
    </section>
  );
}
