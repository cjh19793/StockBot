"use client";

import { LineChart, Line, ReferenceArea, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { shortDate, tickInterval } from "@/lib/chartData";
import ChartTooltip from "./ChartTooltip";
import { axisTick, GRID, COLORS } from "./theme";

export default function StochChart({ rows, interval, height = 110, full = false }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 6, right: full ? 44 : 8, left: 0, bottom: 0 }}>
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
        <YAxis domain={[0, 100]} tick={axisTick(full ? 12 : 10)} axisLine={false} tickLine={false} width={full ? 56 : 28} ticks={[20, 80]} />
        <ReferenceArea y1={80} y2={100} fill={COLORS.down} fillOpacity={0.1} stroke="none" />
        <ReferenceArea y1={0} y2={20} fill={COLORS.up} fillOpacity={0.1} stroke="none" />
        <ReferenceLine y={80} stroke={GRID} strokeDasharray="3 3" />
        <ReferenceLine y={20} stroke={GRID} strokeDasharray="3 3" />
        <Tooltip
          content={
            <ChartTooltip
              rows={[
                { key: "stochK", label: "%K", color: COLORS.price, digits: 1 },
                { key: "stochD", label: "%D", color: COLORS.ma20, digits: 1 },
              ]}
            />
          }
        />
        <Line dataKey="stochK" stroke={COLORS.price} strokeWidth={full ? 2 : 1.4} dot={false} isAnimationActive={false} />
        <Line dataKey="stochD" stroke={COLORS.ma20} strokeWidth={full ? 2 : 1.4} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
