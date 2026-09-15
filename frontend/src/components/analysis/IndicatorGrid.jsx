import { fmt, fmtInt } from "@/lib/format";

function Tile({ k, v }) {
  return (
    <div className="rounded-md border border-border bg-bg-raised px-3 py-2.5">
      <div className="text-[10.5px] uppercase tracking-wide text-ink-faint">{k}</div>
      <div className="mt-0.5 font-mono text-[13px] font-medium">{v}</div>
    </div>
  );
}

export default function IndicatorGrid({ result }) {
  const r = result;
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      <Tile k="RSI" v={fmt(r.rsi, 1)} />
      <Tile k="MACD" v={fmt(r.macd)} />
      <Tile k="Stoch %K" v={fmt(r.stoch_k, 1)} />
      <Tile k="ATR" v={`${fmt(r.atr)} (${(r.atr_pct * 100).toFixed(1)}%)`} />
      <Tile k="MA5" v={fmt(r.ma5)} />
      <Tile k="MA20" v={fmt(r.ma20)} />
      <Tile k="BB Upper" v={fmt(r.bb_upper)} />
      <Tile k="BB Lower" v={fmt(r.bb_lower)} />
      <Tile k="지지선" v={fmt(r.support)} />
      <Tile k="저항선" v={fmt(r.resistance)} />
      <Tile k="거래량" v={fmtInt(r.volume)} />
    </div>
  );
}
