import ScoreBadge from "@/components/ScoreBadge";
import { fmt, fmtPrice, judgmentTone, TONE_CLASSES } from "@/lib/format";

// results 는 백엔드 /api/compare 응답을 그대로 받는다. 여기서 하는 유일한 가공은
// 이미 내려온 composite.total 기준 정렬뿐 — 새 점수를 계산하지 않는다.
export default function CompareTable({ results }) {
  if (results.length === 0) return null;
  const sorted = [...results].sort((a, b) => b.composite.total - a.composite.total);

  return (
    <>
      {/* Desktop */}
      <div className="hidden overflow-x-auto rounded-lg border border-border sm:block">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="border-b border-border bg-bg-raised text-left text-[11px] uppercase tracking-wide text-ink-faint">
              <th className="px-4 py-3 font-medium">순위</th>
              <th className="px-4 py-3 font-medium">티커</th>
              <th className="px-4 py-3 font-medium">현재가</th>
              <th className="px-4 py-3 font-medium">종합점수</th>
              <th className="px-4 py-3 font-medium">기술</th>
              <th className="px-4 py-3 font-medium">시장환경</th>
              <th className="px-4 py-3 font-medium">리스크</th>
              <th className="px-4 py-3 font-medium">펀더멘털</th>
              <th className="px-4 py-3 font-medium">목표가</th>
              <th className="px-4 py-3 font-medium">손절가</th>
              <th className="px-4 py-3 font-medium">판정</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r, i) => (
              <tr key={r.ticker} className={`border-b border-border last:border-0 ${i === 0 ? "bg-amber/5" : ""}`}>
                <td className="px-4 py-3">
                  <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full font-mono text-[11px] ${i === 0 ? "bg-amber text-[#1A1000] font-bold" : "bg-bg-raised text-ink-dim"}`}>
                    {i + 1}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono font-semibold">{r.ticker}</td>
                <td className="px-4 py-3 font-mono">{fmtPrice(r.price)}</td>
                <td className="px-4 py-3"><ScoreBadge total={r.composite.total} label={r.composite.label} size="sm" /></td>
                <td className="px-4 py-3 font-mono">{r.composite.technical}</td>
                <td className="px-4 py-3 font-mono">{r.composite.market}</td>
                <td className="px-4 py-3 font-mono">{r.composite.risk}</td>
                <td className="px-4 py-3 font-mono">{r.composite.fundamentals}</td>
                <td className="px-4 py-3 font-mono text-up">{fmtPrice(r.target_price)}</td>
                <td className="px-4 py-3 font-mono text-down">{fmtPrice(r.stop_loss)}</td>
                <td className="px-4 py-3">
                  <span className={`rounded border px-2 py-0.5 font-mono text-[11.5px] ${TONE_CLASSES[judgmentTone(r.judgment)]}`}>{r.judgment}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile */}
      <div className="space-y-3 sm:hidden">
        {sorted.map((r, i) => (
          <div key={r.ticker} className={`rounded-lg border p-4 ${i === 0 ? "border-amber-dim bg-amber/5" : "border-border bg-bg-card"}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full font-mono text-[11px] ${i === 0 ? "bg-amber text-[#1A1000] font-bold" : "bg-bg-raised text-ink-dim"}`}>
                  {i + 1}
                </span>
                <div>
                  <div className="font-mono text-base font-semibold">{r.ticker}</div>
                  <div className="font-mono text-[12px] text-ink-dim">{fmtPrice(r.price)}</div>
                </div>
              </div>
              <ScoreBadge total={r.composite.total} label={r.composite.label} size="sm" />
            </div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-center">
              {[["기술", r.composite.technical], ["시장", r.composite.market], ["리스크", r.composite.risk], ["펀더멘털", r.composite.fundamentals]].map(([k, v]) => (
                <div key={k} className="rounded bg-bg-raised py-1.5">
                  <div className="text-[10px] text-ink-faint">{k}</div>
                  <div className="font-mono text-[13px]">{v}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between text-[12px]">
              <span>
                목표 <b className="font-mono text-up">{fmt(r.target_price)}</b> · 손절 <b className="font-mono text-down">{fmt(r.stop_loss)}</b>
              </span>
              <span className={`rounded border px-2 py-0.5 font-mono text-[11px] ${TONE_CLASSES[judgmentTone(r.judgment)]}`}>{r.judgment}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
