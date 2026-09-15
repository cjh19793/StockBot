"use client";

import { LineChart, Line, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import ChartTooltip from "./ChartTooltip";

export default function StochChart({ rows, height = 110 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <XAxis dataKey="date" hide />
        <YAxis domain={[0, 100]} tick={{ fill: "#545E70", fontSize: 10, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} width={28} ticks={[20, 80]} />
        <ReferenceLine y={80} stroke="#232937" strokeDasharray="3 3" />
        <ReferenceLine y={20} stroke="#232937" strokeDasharray="3 3" />
        <Tooltip
          content={
            <ChartTooltip
              rows={[
                { key: "stochK", label: "%K", color: "#FFB454", digits: 1 },
                { key: "stochD", label: "%D", color: "#58A6FF", digits: 1 },
              ]}
            />
          }
        />
        <Line dataKey="stochK" stroke="#FFB454" strokeWidth={1.4} dot={false} isAnimationActive={false} />
        <Line dataKey="stochD" stroke="#58A6FF" strokeWidth={1.4} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
