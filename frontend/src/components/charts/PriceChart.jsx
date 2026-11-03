"use client";

import {
  ComposedChart, Area, Line, ReferenceLine, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { shortDate, tickInterval } from "@/lib/chartData";
import ChartTooltip from "./ChartTooltip";
import { axisTick, GRID, COLORS } from "./theme";

// 표시 범위: 가격/이동평균/볼린저/목표가/손절가 중 실제 값의 최저~최고에 4% 여백.
function priceDomain(rows, targetPrice, stopLoss) {
  const vals = [];
  for (const r of rows) {
    for (const k of ["close", "ma5", "ma20", "bbUpper", "bbLower"]) {
      if (typeof r[k] === "number" && Number.isFinite(r[k])) vals.push(r[k]);
    }
  }
  for (const v of [targetPrice, stopLoss]) if (typeof v === "number" && Number.isFinite(v)) vals.push(v);
  if (vals.length === 0) return ["auto", "auto"];
  return [Math.min(...vals) * 0.96, Math.max(...vals) * 1.04];
}

function tickDigits(domain) {
  if (typeof domain[0] !== "number") return 0;
  const span = domain[1] - domain[0];
  return span < 10 ? 2 : span < 50 ? 1 : 0;
}

const REF_LABEL = { fontSize: 12, fontWeight: 600 };

export default function PriceChart({ rows, interval, targetPrice, stopLoss, support, resistance, height = 300, compact = false }) {
  const domain = priceDomain(rows, targetPrice, stopLoss);
  const digits = tickDigits(domain);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={compact ? { top: 4, right: 0, left: 0, bottom: 0 } : { top: 12, right: 44, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.price} stopOpacity={0.22} />
            <stop offset="100%" stopColor={COLORS.price} stopOpacity={0} />
          </linearGradient>
        </defs>
        {!compact && <CartesianGrid stroke={GRID} vertical={false} />}
        <XAxis
          dataKey="date"
          hide={compact}
          tickFormatter={(d) => shortDate(d, interval)}
          interval={tickInterval(rows.length)}
          tick={axisTick(12)}
          axisLine={{ stroke: GRID }}
          tickLine={false}
          padding={{ right: 8 }}
        />
        <YAxis
          domain={domain}
          hide={compact}
          tick={axisTick(12)}
          axisLine={false}
          tickLine={false}
          width={56}
          tickFormatter={(v) => v.toFixed(digits)}
        />
        <Tooltip
          content={
            <ChartTooltip
              rows={[
                { key: "close", label: "종가", color: COLORS.price },
                { key: "ma5", label: "MA5", color: COLORS.ma5 },
                { key: "ma20", label: "MA20", color: COLORS.ma20 },
              ]}
            />
          }
        />

        {/* 볼린저 밴드: 얇은 점선 */}
        <Line dataKey="bbUpper" stroke={COLORS.band} strokeWidth={1} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
        <Line dataKey="bbLower" stroke={COLORS.band} strokeWidth={1} strokeDasharray="4 4" dot={false} isAnimationActive={false} />

        {/* MA: 얇은 실선 */}
        <Line dataKey="ma5" stroke={COLORS.ma5} strokeWidth={1.25} dot={false} isAnimationActive={false} />
        <Line dataKey="ma20" stroke={COLORS.ma20} strokeWidth={1.25} dot={false} isAnimationActive={false} />

        {/* 가격: 굵은 선 (랜딩용 compact 는 기존 채움 유지) */}
        {compact ? (
          <Area dataKey="close" stroke={COLORS.price} strokeWidth={2} fill="url(#priceFill)" isAnimationActive={false} />
        ) : (
          <Line dataKey="close" stroke={COLORS.price} strokeWidth={3} dot={false} isAnimationActive={false} />
        )}

        {support != null && (
          <ReferenceLine y={support} stroke="#8C97AB" strokeDasharray="2 4" label={{ ...REF_LABEL, value: "지지", position: "insideBottomLeft", fill: "#C5CCDA" }} />
        )}
        {resistance != null && (
          <ReferenceLine y={resistance} stroke="#8C97AB" strokeDasharray="2 4" label={{ ...REF_LABEL, value: "저항", position: "insideTopLeft", fill: "#C5CCDA" }} />
        )}
        {targetPrice != null && (
          <ReferenceLine y={targetPrice} stroke={COLORS.up} strokeDasharray="6 4" label={{ ...REF_LABEL, value: "목표가", position: "insideTopRight", fill: COLORS.up }} />
        )}
        {stopLoss != null && (
          <ReferenceLine y={stopLoss} stroke={COLORS.down} strokeDasharray="6 4" label={{ ...REF_LABEL, value: "손절가", position: "insideBottomRight", fill: COLORS.down }} />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
