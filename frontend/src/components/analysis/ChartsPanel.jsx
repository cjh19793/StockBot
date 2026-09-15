import Card from "@/components/ui/Card";
import PriceChart from "@/components/charts/PriceChart";
import RsiChart from "@/components/charts/RsiChart";
import MacdChart from "@/components/charts/MacdChart";
import StochChart from "@/components/charts/StochChart";
import { toRows } from "@/lib/chartData";

export default function ChartsPanel({ series, result }) {
  const rows = toRows(series);

  return (
    <Card className="p-4 sm:p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">가격 &middot; MA5/MA20 &middot; 볼린저밴드</span>
        <span className="font-mono text-[11px] text-ink-faint">{series.interval}</span>
      </div>
      <PriceChart
        rows={rows}
        interval={series.interval}
        targetPrice={result.target_price}
        stopLoss={result.stop_loss}
        support={result.support}
        resistance={result.resistance}
      />

      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        <div>
          <div className="mb-1.5 font-mono text-[10.5px] uppercase tracking-wide text-ink-faint">RSI (14)</div>
          <RsiChart rows={rows} interval={series.interval} />
        </div>
        <div>
          <div className="mb-1.5 font-mono text-[10.5px] uppercase tracking-wide text-ink-faint">MACD</div>
          <MacdChart rows={rows} />
        </div>
        <div>
          <div className="mb-1.5 font-mono text-[10.5px] uppercase tracking-wide text-ink-faint">스토캐스틱</div>
          <StochChart rows={rows} />
        </div>
      </div>
    </Card>
  );
}
