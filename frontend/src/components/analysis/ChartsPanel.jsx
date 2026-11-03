import Card from "@/components/ui/Card";
import PriceChart from "@/components/charts/PriceChart";
import RsiChart from "@/components/charts/RsiChart";
import MacdChart from "@/components/charts/MacdChart";
import StochChart from "@/components/charts/StochChart";
import { COLORS } from "@/components/charts/theme";
import { toRows } from "@/lib/chartData";

function LegendItem({ color, label, dashed = false, thick = false }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <svg width="22" height="8" aria-hidden="true">
        <line x1="0" y1="4" x2="22" y2="4" stroke={color} strokeWidth={thick ? 3 : 1.5} strokeDasharray={dashed ? "4 3" : undefined} />
      </svg>
      {label}
    </span>
  );
}

function SubChart({ title, hint, children }) {
  return (
    <section className="border-t border-border pt-4">
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-4">
        <h3 className="text-[14px] font-semibold text-ink">{title}</h3>
        {hint && <span className="text-[12.5px] text-ink-label">{hint}</span>}
      </div>
      {children}
    </section>
  );
}

const SUB_HEIGHT = 170;

export default function ChartsPanel({ series, result }) {
  const rows = toRows(series);

  return (
    <Card className="p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-ink-label">
          <LegendItem color={COLORS.price} label="가격" thick />
          <LegendItem color={COLORS.ma5} label="MA5" />
          <LegendItem color={COLORS.ma20} label="MA20" />
          <LegendItem color={COLORS.band} label="볼린저밴드" dashed />
        </div>
        <span className="text-[13px] text-ink-label">{series.interval}</span>
      </div>
      <PriceChart
        rows={rows}
        interval={series.interval}
        targetPrice={result.target_price}
        stopLoss={result.stop_loss}
        support={result.support}
        resistance={result.resistance}
        height={450}
      />

      <div className="mt-5 space-y-4">
        <SubChart title="RSI (14)" hint="70 이상 과매수 · 30 이하 과매도">
          <RsiChart rows={rows} interval={series.interval} height={SUB_HEIGHT} full />
        </SubChart>
        <SubChart title="MACD">
          <MacdChart rows={rows} interval={series.interval} height={SUB_HEIGHT} full />
        </SubChart>
        <SubChart title="스토캐스틱" hint="80 이상 과매수 · 20 이하 과매도">
          <StochChart rows={rows} interval={series.interval} height={SUB_HEIGHT} full />
        </SubChart>
      </div>
    </Card>
  );
}
