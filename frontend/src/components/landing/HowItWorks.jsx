"use client";

import { useMemo } from "react";
import PriceChart from "@/components/charts/PriceChart";
import { toRows } from "@/lib/chartData";
import { generateDemoSeries } from "@/lib/demoSeries";

const STEPS = [
  { n: "01", title: "티커 입력", desc: "분석하고 싶은 종목의 티커와 모드(단타/스윙/기본)를 선택합니다." },
  { n: "02", title: "지표 계산", desc: "RSI · MACD · 볼린저밴드 · 스토캐스틱을 서버에서 실시간으로 계산합니다." },
  { n: "03", title: "신호 확인", desc: "매수/매도 신호와 종합점수, 목표가·손절가를 한 화면에서 바로 확인합니다." },
];

export default function HowItWorks() {
  const demoSeries = useMemo(() => generateDemoSeries(50, 101), []);
  const rows = toRows(demoSeries);

  return (
    <section className="border-b border-border py-16 sm:py-20">
      <div className="mb-3.5 font-mono text-[12.5px] text-amber">동작 방식</div>
      <h2 className="max-w-[560px] text-[26px] font-semibold tracking-tight sm:text-[30px]">
        설치할 앱도, 따로 배울 것도 없습니다
      </h2>
      <p className="mt-4 max-w-[520px] text-[15px] text-ink-dim">
        브라우저에서 티커 하나만 입력하면 끝입니다.
      </p>

      <div className="mt-12 grid gap-7 rounded-lg border border-border bg-bg-card p-7 lg:grid-cols-[280px_1fr]">
        <div className="space-y-6">
          {STEPS.map((s) => (
            <div key={s.n} className="flex gap-3.5">
              <span className="font-mono text-[13px] text-amber">{s.n}</span>
              <div>
                <div className="text-[14px] font-semibold">{s.title}</div>
                <p className="mt-1 text-[13px] leading-relaxed text-ink-dim">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
        <div>
          <PriceChart rows={rows} interval="1d" compact height={220} />
        </div>
      </div>
    </section>
  );
}
