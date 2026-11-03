"use client";

import { LineChart, Line, ReferenceArea, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { shortDate, tickInterval } from "@/lib/chartData";
import ChartTooltip from "./ChartTooltip";
import { axisTick, GRID, COLORS } from "./theme";

// full: /analyze 용 큰 표시 (X축 날짜, 넓은 여백). 랜딩의 작은 차트는 기본값 유지.
export default function RsiChart({ rows, interval, height = 110, full = false }) {
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
        <YAxis domain={[0, 100]} tick={axisTick(full ? 12 : 10)} axisLine={false} tickLine={false} width={full ? 56 : 28} ticks={[30, 70]} />
        <ReferenceArea y1={70} y2={100} fill={COLORS.down} fillOpacity={0.1} stroke="none" />
        <ReferenceArea y1={0} y2={30} fill={COLORS.up} fillOpacity={0.1} stroke="none" />
        <ReferenceLine y={70} stroke={GRID} strokeDasharray="3 3" />
        <ReferenceLine y={30} stroke={GRID} strokeDasharray="3 3" />
        <Tooltip content={<ChartTooltip rows={[{ key: "rsi", label: "RSI", color: COLORS.ma20, digits: 1 }]} />} />
        <Line dataKey="rsi" stroke={COLORS.ma20} strokeWidth={full ? 2 : 1.6} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
