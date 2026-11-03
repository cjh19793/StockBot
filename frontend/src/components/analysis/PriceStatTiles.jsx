import Card from "@/components/ui/Card";
import { fmtPrice, scoreTone, TONE_CLASSES } from "@/lib/format";

function Label({ children }) {
  return <div className="text-[14px] font-medium text-ink-label">{children}</div>;
}

// 최상단 핵심 4개: 현재가 / 목표가 / 손절가 / 종합점수. 값은 백엔드 결과를 그대로 표시한다.
export default function PriceStatTiles({ result }) {
  const r = result;
  const c = r.composite;
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Card className="p-5">
        <Label>현재가</Label>
        <div className="mt-2 text-[34px] font-bold leading-none tabular-nums">{fmtPrice(r.price)}</div>
        <div className="mt-2 text-[13px] text-ink-label">{r.price_is_realtime ? "실시간" : "전일 종가"}</div>
      </Card>
      <Card className="p-5">
        <Label>목표가 (+{(r.target_pct * 100).toFixed(1)}%)</Label>
        <div className="mt-2 text-[34px] font-bold leading-none tabular-nums text-up">{fmtPrice(r.target_price)}</div>
      </Card>
      <Card className="p-5">
        <Label>손절가 (-{(r.stop_pct * 100).toFixed(1)}%)</Label>
        <div className="mt-2 text-[34px] font-bold leading-none tabular-nums text-down">{fmtPrice(r.stop_loss)}</div>
      </Card>
      <Card className="p-5">
        <Label>종합점수</Label>
        <div className="mt-2 flex items-baseline gap-2.5">
          <span className="text-[34px] font-bold leading-none tabular-nums">{c.total}</span>
          <span className={`rounded-md border px-2.5 py-1 text-[14px] font-semibold ${TONE_CLASSES[scoreTone(c.label)]}`}>{c.label}</span>
        </div>
      </Card>
    </div>
  );
}
