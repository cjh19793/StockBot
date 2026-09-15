import Card from "@/components/ui/Card";
import { fmtPct } from "@/lib/format";

const GRADE_CLASSES = {
  Excellent: "text-up bg-up/10 border-up/30",
  Good: "text-info bg-info/10 border-info/30",
  Neutral: "text-ink-dim bg-white/5 border-border",
  Caution: "text-down bg-down/10 border-down/30",
};

export default function HoldCard({ hold, best }) {
  const h = hold;
  return (
    <Card className={best ? "border-amber-dim bg-amber/5" : ""}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-mono text-[14px] font-semibold">{h.hold_days}일 보유</h3>
        <span className={`rounded border px-2 py-0.5 font-mono text-[11px] ${GRADE_CLASSES[h.grade] || GRADE_CLASSES.Neutral}`}>{h.grade}</span>
      </div>
      <div className="font-mono text-3xl font-bold">{h.win_rate.toFixed(1)}%</div>
      <div className="mb-4 text-[11.5px] text-ink-faint">승률</div>
      <div className="space-y-1.5 border-t border-border pt-3 text-[12.5px]">
        <div className="flex justify-between"><span className="text-ink-faint">평균 수익률</span><span className={`font-mono ${h.avg_return >= 0 ? "text-up" : "text-down"}`}>{fmtPct(h.avg_return)}</span></div>
        <div className="flex justify-between"><span className="text-ink-faint">최대 수익</span><span className="font-mono text-up">{fmtPct(h.max_profit)}</span></div>
        <div className="flex justify-between"><span className="text-ink-faint">최대 손실</span><span className="font-mono text-down">{fmtPct(h.max_loss)}</span></div>
      </div>
    </Card>
  );
}
