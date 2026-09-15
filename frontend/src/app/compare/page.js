"use client";

import { useEffect, useState } from "react";
import Card from "@/components/ui/Card";
import ModeSegmented from "@/components/ModeSegmented";
import { Hint, ErrorMessage } from "@/components/ui/StatusMessage";
import CompareTable from "@/components/compare/CompareTable";
import CompareErrors from "@/components/compare/CompareErrors";
import { fetchCompare, fetchModes } from "@/lib/api";
import { FALLBACK_ANALYSIS_MODES } from "@/lib/modes";

export default function ComparePage() {
  const [tickersInput, setTickersInput] = useState("AAPL,MSFT,GOOGL");
  const [mode, setMode] = useState("기본");
  const [modes, setModes] = useState(FALLBACK_ANALYSIS_MODES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchModes()
      .then((d) => d.analysis?.length && setModes(d.analysis))
      .catch(() => {});
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    const tickers = tickersInput.split(",").map((t) => t.trim().toUpperCase()).filter(Boolean);
    if (tickers.length < 2 || tickers.length > 10) {
      setError("비교할 티커는 2~10개를 콤마로 구분해 입력해주세요.");
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await fetchCompare(tickers, mode));
    } catch (err) {
      setData(null);
      setError(err.message || "비교 분석에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">종목 비교</h1>
        <p className="mt-1.5 text-[14px] text-ink-dim">여러 종목을 동시에 분석해 종합점수 기준으로 나란히 비교합니다.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <div className="min-w-[240px] flex-[2]">
            <label htmlFor="compare-tickers" className="mb-1.5 block text-[12.5px] text-ink-faint">
              비교할 티커 (콤마로 구분, 2~10개)
            </label>
            <div className="flex items-center gap-2 rounded-md border border-border bg-bg-raised px-3 py-2.5 focus-within:border-amber-dim">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="shrink-0 text-ink-faint">
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
                className="w-full bg-transparent font-mono text-sm placeholder:text-ink-faint focus:outline-none"
              />
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-[12.5px] text-ink-faint">분석 모드</label>
            <ModeSegmented modes={modes} value={mode} onChange={setMode} ariaLabel="분석 모드" />
          </div>
          <button
            type="submit"
            disabled={loading || !tickersInput.trim()}
            className="rounded-md bg-amber px-5 py-2.5 font-semibold text-[#1A1000] transition-opacity disabled:opacity-40"
          >
            {loading ? "비교 중..." : "비교하기"}
          </button>
        </form>
      </Card>

      {loading && <Hint>여러 종목을 동시에 분석 중입니다. 서버가 잠시 쉬고 있었다면 최대 1분 정도 걸릴 수 있어요.</Hint>}
      {error && <ErrorMessage>{error}</ErrorMessage>}

      {data && (
        <div className="space-y-4">
          <p className="text-[13px] text-ink-faint">종합점수 기준 내림차순 정렬 · {data.results.length}개 종목</p>
          <CompareTable results={data.results} />
          <CompareErrors errors={data.errors} />
          {data.results.length === 0 && data.errors.length > 0 && (
            <ErrorMessage>비교 요청한 모든 종목의 분석에 실패했습니다.</ErrorMessage>
          )}
        </div>
      )}
    </div>
  );
}
