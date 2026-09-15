import { judgmentTone, TONE_CLASSES } from "@/lib/format";

export default function ResultHeader({ result }) {
  const r = result;
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <div className="flex items-center gap-2.5">
          <h1 className="font-mono text-2xl font-bold">{r.ticker}</h1>
          <span className="rounded border border-border px-2 py-0.5 font-mono text-[11px] text-ink-dim">{r.label}</span>
        </div>
        <p className="mt-1.5 text-[12.5px] text-ink-faint">{r.now_str} · 조회 {r.asof_kst}</p>
        <p className="text-[12.5px] text-ink-faint">{r.market}{r.is_market_open ? " · 개장중" : ""}</p>
      </div>
      <span className={`rounded-md border px-3 py-1.5 font-mono text-[13px] font-semibold ${TONE_CLASSES[judgmentTone(r.judgment)]}`}>
        {r.judgment}
      </span>
    </div>
  );
}
