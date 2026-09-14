import { useState } from "react";
import { fetchCompare } from "../api";
import CompareTable from "./CompareTable";
import CompareErrors from "./CompareErrors";

const FALLBACK_MODES = [
  { name: "기본", label: "Daily (Basic)" },
  { name: "단타", label: "5min (Scalping)" },
  { name: "스윙", label: "1hour (Swing)" },
];

export default function CompareView({ modes }) {
  const [tickersInput, setTickersInput] = useState("AAPL,MSFT,GOOGL");
  const [mode, setMode] = useState("기본");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const modeOptions = modes.length > 0 ? modes : FALLBACK_MODES;

  async function handleSubmit(e) {
    e.preventDefault();
    const tickers = tickersInput
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);

    if (tickers.length < 2 || tickers.length > 10) {
      setError("비교할 티커는 2~10개를 콤마로 구분해 입력해주세요.");
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await fetchCompare(tickers, mode);
      setData(result);
    } catch (err) {
      setData(null);
      setError(err.message || "비교 분석에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="view-stack">
      <form className="search-card" onSubmit={handleSubmit}>
        <div className="field" style={{ flex: 2 }}>
          <label htmlFor="compare-tickers">비교할 티커 (콤마로 구분, 2~10개)</label>
          <div className="input">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              id="compare-tickers"
              type="text"
              autoCapitalize="characters"
              autoComplete="off"
              placeholder="예: AAPL,MSFT,GOOGL"
              value={tickersInput}
              onChange={(e) => setTickersInput(e.target.value)}
            />
          </div>
        </div>
        <div className="field">
          <label htmlFor="compare-mode">분석 모드</label>
          <div className="segmented" role="radiogroup" aria-label="분석 모드">
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
        <button type="submit" className="btn-primary" disabled={loading || !tickersInput.trim()}>
          {loading ? "비교 중..." : "비교하기"}
        </button>
      </form>

      {loading && (
        <p className="hint">
          여러 종목을 동시에 분석 중입니다. 서버가 잠시 쉬고 있었다면 최대 1분 정도 걸릴 수 있어요.
        </p>
      )}

      {error && <p className="error-message">{error}</p>}

      {data && (
        <>
          <div className="page-title">
            <h1>종목 비교 결과</h1>
            <p>종합점수 기준 내림차순 정렬 · {data.results.length}개 종목</p>
          </div>
          <CompareTable results={data.results} />
          <CompareErrors errors={data.errors} />
          {data.results.length === 0 && data.errors.length > 0 && (
            <p className="error-message">비교 요청한 모든 종목의 분석에 실패했습니다.</p>
          )}
        </>
      )}
    </section>
  );
}
