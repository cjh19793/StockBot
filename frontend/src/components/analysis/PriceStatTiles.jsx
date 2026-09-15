import Card from "@/components/ui/Card";
import { fmtPrice } from "@/lib/format";

export default function PriceStatTiles({ result }) {
  const r = result;
  return (
    <div className="grid grid-cols-3 gap-3">
      <Card className="p-4">
        <div className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">현재가</div>
        <div className="mt-1.5 font-mono text-xl font-bold">{fmtPrice(r.price)}</div>
        <div className="mt-1 text-[11px] text-ink-faint">{r.price_is_realtime ? "실시간" : "전일 종가"}</div>
      </Card>
      <Card className="p-4">
        <div className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">
          목표가 (+{(r.target_pct * 100).toFixed(1)}%)
        </div>
        <div className="mt-1.5 font-mono text-xl font-bold text-up">{fmtPrice(r.target_price)}</div>
      </Card>
      <Card className="p-4">
        <div className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">
          손절가 (-{(r.stop_pct * 100).toFixed(1)}%)
        </div>
        <div className="mt-1.5 font-mono text-xl font-bold text-down">{fmtPrice(r.stop_loss)}</div>
      </Card>
    </div>
  );
}
