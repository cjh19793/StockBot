import { useEffect, useState } from "react";
import { fetchAnalysis, fetchModes, chartUrl } from "./api";
import TickerForm from "./components/TickerForm";
import AnalysisResult from "./components/AnalysisResult";
import ChartView from "./components/ChartView";
import "./App.css";

export default function App() {
  const [ticker, setTicker] = useState("");
  const [mode, setMode] = useState("기본");
  const [modes, setModes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [chart, setChart] = useState(null);

  useEffect(() => {
    fetchModes()
      .then((data) => setModes(data.analysis || []))
      .catch(() => {
        // 모드 목록 조회 실패해도 기본 옵션으로 폼은 계속 동작한다 (TickerForm 폴백 사용)
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
      <header className="app-header">
        <h1>StockBot</h1>
        <p>미국 주식 티커를 입력하면 기술적 분석 리포트와 차트를 보여줍니다.</p>
      </header>

      <TickerForm
        ticker={ticker}
        mode={mode}
        modes={modes}
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

      {result && (
        <>
          <AnalysisResult result={result} />
          {chart && <ChartView src={chart.src} alt={chart.alt} />}
        </>
      )}
    </div>
  );
}
