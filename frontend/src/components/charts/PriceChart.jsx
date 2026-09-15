"use client";

import {
  ComposedChart, Area, Line, ReferenceLine, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { shortDate, tickInterval } from "@/lib/chartData";
import ChartTooltip from "./ChartTooltip";

export default function PriceChart({ rows, interval, targetPrice, stopLoss, support, resistance, height = 300, compact = false }) {
  const closes = rows.map((r) => r.close).filter((v) => v != null);
  const domainMin = Math.min(...closes, targetPrice ?? Infinity, stopLoss ?? Infinity, support ?? Infinity) * 0.98;
  const domainMax = Math.max(...closes, targetPrice ?? -Infinity, resistance ?? -Infinity) * 1.02;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={compact ? { top: 4, right: 0, left: 0, bottom: 0 } : { top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FFB454" stopOpacity={0.22} />
            <stop offset="100%" stopColor="#FFB454" stopOpacity={0} />
          </linearGradient>
        </defs>
        {!compact && <CartesianGrid stroke="#232937" vertical={false} />}
        <XAxis
          dataKey="date"
          hide={compact}
          tickFormatter={(d) => shortDate(d, interval)}
          interval={tickInterval(rows.length)}
          tick={{ fill: "#545E70", fontSize: 11, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#232937" }}
          tickLine={false}
        />
        <YAxis
          domain={[domainMin, domainMax]}
          hide={compact}
          tick={{ fill: "#545E70", fontSize: 11, fontFamily: "var(--font-mono)" }}
          axisLine={false}
          tickLine={false}
          width={56}
          tickFormatter={(v) => v.toFixed(0)}
        />
        <Tooltip
          content={
            <ChartTooltip
              rows={[
                { key: "close", label: "종가", color: "#FFB454" },
                { key: "ma5", label: "MA5", color: "#8891A3" },
                { key: "ma20", label: "MA20", color: "#58A6FF" },
              ]}
            />
          }
        />

        {/* 볼린저 밴드: lower를 투명 base로 깔고, band(upper-lower)를 스택으로 쌓아 밴드처럼 보이게 */}
        <Area dataKey="bbLower" stackId="bb" stroke="none" fill="transparent" isAnimationActive={false} />
        <Area
          dataKey="bbBand"
          stackId="bb"
          stroke="#3A4356"
          strokeWidth={1}
          fill="#3A4356"
          fillOpacity={0.16}
          isAnimationActive={false}
        />

        <Area dataKey="close" stroke="#FFB454" strokeWidth={2} fill="url(#priceFill)" isAnimationActive={false} />
        <Line dataKey="ma5" stroke="#8891A3" strokeWidth={1.3} dot={false} isAnimationActive={false} />
        <Line dataKey="ma20" stroke="#58A6FF" strokeWidth={1.3} dot={false} isAnimationActive={false} />

        {support != null && (
          <ReferenceLine y={support} stroke="#545E70" strokeDasharray="3 3" label={{ value: "지지", position: "insideBottomLeft", fill: "#545E70", fontSize: 10 }} />
        )}
        {resistance != null && (
          <ReferenceLine y={resistance} stroke="#545E70" strokeDasharray="3 3" label={{ value: "저항", position: "insideTopLeft", fill: "#545E70", fontSize: 10 }} />
        )}
        {targetPrice != null && (
          <ReferenceLine y={targetPrice} stroke="#3DDC84" strokeDasharray="4 4" label={{ value: "목표가", position: "insideTopRight", fill: "#3DDC84", fontSize: 10 }} />
        )}
        {stopLoss != null && (
          <ReferenceLine y={stopLoss} stroke="#FF6B6B" strokeDasharray="4 4" label={{ value: "손절가", position: "insideBottomRight", fill: "#FF6B6B", fontSize: 10 }} />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
