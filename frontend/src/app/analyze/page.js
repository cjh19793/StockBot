"use client";

import { useEffect, useState } from "react";
import Card from "@/components/ui/Card";
import TickerInput from "@/components/TickerInput";
import ModeSegmented from "@/components/ModeSegmented";
import { Hint, ErrorMessage } from "@/components/ui/StatusMessage";
import AnalysisView from "@/components/analysis/AnalysisView";
import { fetchAnalysis, fetchModes, fetchSeries } from "@/lib/api";
import { FALLBACK_ANALYSIS_MODES } from "@/lib/modes";

export default function AnalyzePage() {
  const [ticker, setTicker] = useState("");
  const [mode, setMode] = useState("기본");
  const [modes, setModes] = useState(FALLBACK_ANALYSIS_MODES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [series, setSeries] = useState(null);

  useEffect(() => {
    fetchModes()
      .then((data) => data.analysis?.length && setModes(data.analysis))
      .catch(() => {
        // 모드 목록 조회 실패해도 폴백 옵션으로 계속 동작한다
      });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    const clean = ticker.trim().toUpperCase();
    if (!clean) return;

    setLoading(true);
    setError(null);
    try {
      const [analysis, seriesData] = await Promise.all([
        fetchAnalysis(clean, mode),
        fetchSeries(clean, mode),
      ]);
      setResult(analysis);
      setSeries(seriesData);
    } catch (err) {
      setResult(null);
      setSeries(null);
      setError(err.message || "분석에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">종목 분석</h1>
        <p className="mt-1.5 text-[14px] text-ink-dim">티커를 입력하면 기술적 지표를 조합해 매수/매도 신호를 계산합니다.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <div className="min-w-[200px] flex-1">
            <label htmlFor="ticker" className="mb-1.5 block text-[12.5px] text-ink-faint">티커</label>
            <TickerInput id="ticker" value={ticker} onChange={setTicker} maxLength={10} />
          </div>
          <div>
            <label className="mb-1.5 block text-[12.5px] text-ink-faint">분석 모드</label>
            <ModeSegmented modes={modes} value={mode} onChange={setMode} ariaLabel="분석 모드" />
          </div>
          <button
            type="submit"
            disabled={loading || !ticker.trim()}
            className="rounded-md bg-amber px-5 py-2.5 font-semibold text-[#1A1000] transition-opacity disabled:opacity-40"
          >
            {loading ? "분석 중..." : "분석하기"}
          </button>
        </form>
      </Card>

      {loading && <Hint>분석 중입니다. 서버가 잠시 쉬고 있었다면 깨어나는 데 최대 1분 정도 걸릴 수 있어요.</Hint>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {result && series && <AnalysisView result={result} series={series} />}

      <p className="pt-2 text-center text-[12px] text-ink-faint">모든 결과는 참고용이며 투자 권유가 아닙니다.</p>
    </div>
  );
}
