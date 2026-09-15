"use client";

import { LineChart, Line, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { shortDate, tickInterval } from "@/lib/chartData";
import ChartTooltip from "./ChartTooltip";

export default function RsiChart({ rows, interval, height = 110 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="date" hide />
        <YAxis domain={[0, 100]} tick={{ fill: "#545E70", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} width={28} ticks={[30, 70]} />
        <ReferenceLine y={70} stroke="#232937" strokeDasharray="3 3" />
        <ReferenceLine y={30} stroke="#232937" strokeDasharray="3 3" />
        <Tooltip content={<ChartTooltip rows={[{ key: "rsi", label: "RSI", color: "#58A6FF", digits: 1 }]} />} />
        <Line dataKey="rsi" stroke="#58A6FF" strokeWidth={1.6} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
