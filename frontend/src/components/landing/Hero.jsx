"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import PriceChart from "@/components/charts/PriceChart";
import RsiChart from "@/components/charts/RsiChart";
import MacdChart from "@/components/charts/MacdChart";
import { toRows } from "@/lib/chartData";
import { generateDemoSeries } from "@/lib/demoSeries";
import { fetchAnalysis, fetchSeries } from "@/lib/api";
import { judgmentTone, TONE_CLASSES } from "@/lib/format";

const DEMO_TICKER = "AAPL";

function findSignal(result, keyword) {
  const all = [...(result.buy_signals || []), ...(result.sell_signals || [])];
  return all.find((s) => s.includes(keyword)) || null;
}

export default function Hero() {
  const [state, setState] = useState({ status: "loading", result: null, series: null });
  const demoSeries = useMemo(() => generateDemoSeries(), []);

  useEffect(() => {
    let alive = true;
    Promise.all([fetchAnalysis(DEMO_TICKER, "기본"), fetchSeries(DEMO_TICKER, "기본")])
      .then(([result, series]) => {
        if (alive) setState({ status: "ready", result, series });
      })
      .catch(() => {
        if (alive) setState((s) => ({ ...s, status: "error" }));
      });
    return () => {
      alive = false;
    };
  }, []);

  const ready = state.status === "ready";
  const r = state.result;
  const rows = ready ? toRows(state.series) : toRows(demoSeries);

  const change = ready
    ? (() => {
        const closes = state.series.close.filter((v) => v != null);
        const prev = closes[closes.length - 2];
        const curr = r.price ?? closes[closes.length - 1];
        if (prev == null) return null;
        return { abs: curr - prev, pct: ((curr - prev) / prev) * 100 };
      })()
    : null;

  const macdSignalText = ready ? findSignal(r, "MACD") : null;
  const bbSignalText = ready ? findSignal(r, "볼린저") : null;

  return (
    <div className="grid gap-12 border-b border-border pb-16 pt-10 sm:pb-20 sm:pt-16 lg:grid-cols-[1.05fr_1fr] lg:items-center">
      <div>
        <div className="mb-5 flex items-center gap-2 font-mono text-[12.5px] text-ink-faint">
          <span className={`h-2 w-2 rounded-full ${ready ? "bg-up" : "bg-ink-faint"}`} />
          {ready ? "실시간 시세 연동 중" : "분석 엔진 연동 중..."}
        </div>
        <h1 className="text-[32px] font-semibold leading-[1.2] tracking-tight sm:text-[44px] sm:leading-[1.18]">
          지표를 보여주는 게 아니라<br />
          <span className="text-amber">판단</span>을 내려주는 주식 분석
        </h1>
        <p className="mt-5 max-w-[440px] text-[15px] leading-relaxed text-ink-dim sm:text-base">
          RSI · MACD · 볼린저밴드 · 스토캐스틱을 조합해 매수/매도 신호를 계산하고,
          몬테카를로 시뮬레이션으로 앞으로의 변동 구간까지 웹에서 바로 확인하세요.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link href="/analyze" className="rounded-md bg-amber px-6 py-3.5 font-semibold text-[#1A1000] transition-opacity hover:opacity-90">
            웹에서 바로 시작
          </Link>
          <a href="#features" className="rounded-md border border-border px-5 py-3.5 font-medium text-ink transition-colors hover:border-ink-faint">
            기능 살펴보기
          </a>
        </div>
        <div className="mt-4 font-mono text-[12.5px] text-ink-faint">무료 · 로그인 없이 바로 사용</div>
      </div>

      <div className="rounded-lg border border-border bg-bg-card p-5">
        <div className="mb-1.5 flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate font-mono text-[13px] font-semibold text-ink-dim">
              {ready ? `${r.ticker} · ${r.label}` : "종목 불러오는 중..."}
            </div>
            <div className="mt-1 font-mono text-[22px] font-bold">
              {ready ? `$${r.price.toFixed(2)}` : <span className="inline-block h-6 w-24 animate-pulse rounded bg-bg-raised" />}
            </div>
            {change && (
              <div className={`mt-0.5 font-mono text-[12.5px] ${change.abs >= 0 ? "text-up" : "text-down"}`}>
                {change.abs >= 0 ? "▲" : "▼"} {Math.abs(change.abs).toFixed(2)} ({change.pct >= 0 ? "+" : ""}
                {change.pct.toFixed(2)}%)
              </div>
            )}
          </div>
          {ready && (
            <span className={`shrink-0 whitespace-nowrap rounded border px-2.5 py-1 font-mono text-[11px] ${TONE_CLASSES[judgmentTone(r.judgment)]}`}>
              {r.judgment}
            </span>
          )}
        </div>

        <PriceChart rows={rows} interval="1d" compact height={140} />

        <div className="mt-3 grid grid-cols-2 gap-2.5">
          <div>
            <div className="mb-1 font-mono text-[10px] text-ink-faint">RSI (14)</div>
            <RsiChart rows={rows} height={44} />
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] text-ink-faint">MACD</div>
            <MacdChart rows={rows} height={44} />
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-border pt-3.5 font-mono text-[11px] text-ink-faint sm:grid-cols-4">
          <div>
            RSI
            <div className={`mt-0.5 text-[13px] font-semibold ${ready && r.rsi <= 40 ? "text-up" : ready && r.rsi >= 60 ? "text-down" : "text-ink"}`}>
              {ready ? r.rsi.toFixed(1) : "-"}
            </div>
          </div>
          <div>
            MACD
            <div className="mt-0.5 truncate text-[13px] font-semibold text-ink">{macdSignalText ? macdSignalText.split(" - ")[0] : ready ? "중립" : "-"}</div>
          </div>
          <div>
            볼린저
            <div className="mt-0.5 truncate text-[13px] font-semibold text-ink">{bbSignalText ? bbSignalText.split(" - ")[0] : ready ? "밴드 중간" : "-"}</div>
          </div>
          <div>
            종합점수
            <div className="mt-0.5 text-[13px] font-semibold text-amber">{ready ? `${r.composite.total} · ${r.composite.label}` : "-"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
