"use client";

import { useEffect, useState } from "react";
import Card from "@/components/ui/Card";
import TickerInput from "@/components/TickerInput";
import ModeSegmented from "@/components/ModeSegmented";
import { Hint, ErrorMessage } from "@/components/ui/StatusMessage";
import HoldCard from "@/components/montecarlo/HoldCard";
import WinRateChart from "@/components/montecarlo/WinRateChart";
import { fetchMonteCarlo, fetchModes } from "@/lib/api";
import { FALLBACK_MC_MODES } from "@/lib/modes";

export default function MonteCarloPage() {
  const [ticker, setTicker] = useState("");
  const [mode, setMode] = useState("기본");
  const [simulations, setSimulations] = useState(1000);
  const [modes, setModes] = useState(FALLBACK_MC_MODES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchModes()
      .then((d) => d.montecarlo?.length && setModes(d.montecarlo))
      .catch(() => {});
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    const clean = ticker.trim().toUpperCase();
    if (!clean) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await fetchMonteCarlo(clean, mode, simulations));
    } catch (err) {
      setResult(null);
      setError(err.message || "몬테카를로 시뮬레이션에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const currentLabel = modes.find((m) => m.name === mode)?.label || "";
  const best = result ? result.holds.find((h) => h.hold_days === result.best_hold_days) : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">몬테카를로 시뮬레이션</h1>
        <p className="mt-1.5 text-[14px] text-ink-dim">과거 가격 구간을 부트스트랩 표본추출해 보유기간별 승률 분포를 계산합니다.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <div className="min-w-[160px]">
            <label htmlFor="mc-ticker" className="mb-1.5 block text-[12.5px] text-ink-faint">티커</label>
            <TickerInput id="mc-ticker" value={ticker} onChange={setTicker} maxLength={10} />
          </div>
          <div>
            <label className="mb-1.5 block text-[12.5px] text-ink-faint">몬테카를로 모드</label>
            <ModeSegmented modes={modes} value={mode} onChange={setMode} ariaLabel="몬테카를로 모드" />
          </div>
          <div className="w-32">
            <label htmlFor="mc-sims" className="mb-1.5 block text-[12.5px] text-ink-faint">시뮬레이션 횟수</label>
            <input
              id="mc-sims"
              type="number"
              min={100}
              max={10000}
              step={100}
              value={simulations}
              onChange={(e) => setSimulations(Number(e.target.value))}
              className="w-full rounded-md border border-border bg-bg-raised px-3 py-2.5 font-mono text-sm focus:border-amber-dim focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !ticker.trim()}
            className="rounded-md bg-amber px-5 py-2.5 font-semibold text-[#1A1000] transition-opacity disabled:opacity-40"
          >
            {loading ? "시뮬레이션 중..." : "시뮬레이션 실행"}
          </button>
        </form>
      </Card>

      {loading && <Hint>부트스트랩 시뮬레이션을 실행 중입니다. 서버가 잠시 쉬고 있었다면 최대 1분 정도 걸릴 수 있어요.</Hint>}
      {error && <ErrorMessage>{error}</ErrorMessage>}

      {result && (
        <div className="space-y-5">
          <div>
            <h2 className="font-mono text-xl font-semibold">{result.ticker} · 몬테카를로 시뮬레이션</h2>
            <p className="text-[13px] text-ink-faint">
              {currentLabel || result.label} · 과거 가격 구간 부트스트랩 표본추출 {result.simulations.toLocaleString()}회
            </p>
          </div>

          {best && (
            <Card className="flex items-center justify-between border-amber-dim bg-amber/5">
              <div>
                <div className="text-[12px] text-ink-faint">최적 보유기간</div>
                <div className="font-mono text-2xl font-bold">{result.best_hold_days}일 보유</div>
              </div>
              <div className="text-right">
                <div className="font-mono text-3xl font-bold text-amber">{result.best_win_rate.toFixed(1)}%</div>
                <div className="text-[12px] text-ink-faint">승률</div>
              </div>
            </Card>
          )}

          <Card>
            <div className="mb-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">보유기간별 승률</div>
            <WinRateChart holds={result.holds} />
          </Card>

          <div className="grid gap-3 sm:grid-cols-3">
            {result.holds.map((h) => (
              <HoldCard key={h.hold_days} hold={h} best={h.hold_days === result.best_hold_days} />
            ))}
          </div>

          <p className="text-[12px] leading-relaxed text-ink-faint">
            과거 가격 구간을 무작위로 표본추출(부트스트랩)해 각 보유기간 종료 시점의 수익률 분포를 시뮬레이션한 결과입니다.
            GBM(기하 브라운 운동) 같은 확률 모형이 아니며, 미래 수익을 보장하지 않습니다.
          </p>
        </div>
      )}
    </div>
  );
}
