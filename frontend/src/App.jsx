import { useEffect, useState } from "react";
import { fetchAnalysis, fetchModes, chartUrl } from "./api";
import Header from "./components/Header";
import BottomNav from "./components/BottomNav";
import TickerForm from "./components/TickerForm";
import AnalysisResult from "./components/AnalysisResult";
import CompareView from "./components/CompareView";
import MonteCarloView from "./components/MonteCarloView";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("single"); // "single" | "compare" | "montecarlo"

  const [ticker, setTicker] = useState("");
  const [mode, setMode] = useState("기본");
  const [modes, setModes] = useState({ analysis: [], montecarlo: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [chart, setChart] = useState(null);

  useEffect(() => {
    fetchModes()
      .then((data) => setModes({ analysis: data.analysis || [], montecarlo: data.montecarlo || [] }))
      .catch(() => {
        // 모드 목록 조회 실패해도 각 화면의 폴백 옵션으로 계속 동작한다
      });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    const clean = ticker.trim().toUpperCase();
    if (!clean) return;

    setLoading(true);
    setError(null);
    try {
      const data = await fetchAnalysis(clean, mode);
      setResult(data);
      setChart({ src: chartUrl(clean, mode), alt: `${clean} ${mode} 차트` });
    } catch (err) {
      setResult(null);
      setChart(null);
      setError(err.message || "분석에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <Header tab={tab} onTabChange={setTab} />

      <main className="page">
        {tab === "single" && (
          <>
            <TickerForm
              ticker={ticker}
              mode={mode}
              modes={modes.analysis}
              loading={loading}
              onTickerChange={setTicker}
              onModeChange={setMode}
              onSubmit={handleSubmit}
            />

            {loading && (
              <p className="hint">
                분석 중입니다. 서버가 잠시 쉬고 있었다면 깨어나는 데 최대 1분 정도 걸릴 수 있어요.
              </p>
            )}

            {error && <p className="error-message">{error}</p>}

            {result && <AnalysisResult result={result} chart={chart} />}
          </>
        )}

        {tab === "compare" && <CompareView modes={modes.analysis} />}

        {tab === "montecarlo" && <MonteCarloView modes={modes.montecarlo} />}

        <p className="disclaimer">모든 결과는 참고용이며 투자 권유가 아닙니다.</p>
      </main>

      <BottomNav tab={tab} onTabChange={setTab} />
    </div>
  );
}
