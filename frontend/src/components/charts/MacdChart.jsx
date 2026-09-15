"use client";

import { ComposedChart, Bar, Cell, Line, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import ChartTooltip from "./ChartTooltip";

export default function MacdChart({ rows, height = 110 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="date" hide />
        <YAxis tick={{ fill: "#545E70", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} width={32} />
        <ReferenceLine y={0} stroke="#232937" />
        <Tooltip
          content={
            <ChartTooltip
              rows={[
                { key: "macd", label: "MACD", color: "#FFB454" },
                { key: "macdSignal", label: "Signal", color: "#58A6FF" },
                { key: "macdHist", label: "Hist", color: "#8891A3" },
              ]}
            />
          }
        />
        <Bar dataKey="macdHist" isAnimationActive={false}>
          {rows.map((r, i) => (
            <Cell key={i} fill={r.macdHist >= 0 ? "#3DDC84" : "#FF6B6B"} fillOpacity={0.85} />
          ))}
        </Bar>
        <Line dataKey="macd" stroke="#FFB454" strokeWidth={1.4} dot={false} isAnimationActive={false} />
        <Line dataKey="macdSignal" stroke="#58A6FF" strokeWidth={1.4} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
