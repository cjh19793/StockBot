"use client";

import { ComposedChart, Bar, Cell, Line, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { shortDate, tickInterval } from "@/lib/chartData";
import ChartTooltip from "./ChartTooltip";
import { axisTick, GRID, COLORS } from "./theme";

export default function MacdChart({ rows, interval, height = 110, full = false }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={{ top: 6, right: full ? 44 : 8, left: 0, bottom: 0 }}>
        <XAxis
          dataKey="date"
          hide={!full}
          tickFormatter={(d) => shortDate(d, interval)}
          interval={tickInterval(rows.length)}
          tick={axisTick(12)}
          axisLine={{ stroke: GRID }}
          tickLine={false}
          padding={{ right: 8 }}
        />
        <YAxis tick={axisTick(full ? 12 : 10)} axisLine={false} tickLine={false} width={full ? 56 : 32} tickFormatter={full ? (v) => v.toFixed(1) : undefined} />
        <ReferenceLine y={0} stroke="#3A4356" />
        <Tooltip
          content={
            <ChartTooltip
              rows={[
                { key: "macd", label: "MACD", color: COLORS.price },
                { key: "macdSignal", label: "Signal", color: COLORS.ma20 },
                { key: "macdHist", label: "Hist", color: "#AAB3C5" },
              ]}
            />
          }
        />
        <Bar dataKey="macdHist" isAnimationActive={false}>
          {rows.map((r, i) => (
            <Cell key={i} fill={r.macdHist >= 0 ? COLORS.up : COLORS.down} fillOpacity={0.85} />
          ))}
        </Bar>
        <Line dataKey="macd" stroke={COLORS.price} strokeWidth={full ? 2 : 1.4} dot={false} isAnimationActive={false} />
        <Line dataKey="macdSignal" stroke={COLORS.ma20} strokeWidth={full ? 2 : 1.4} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
