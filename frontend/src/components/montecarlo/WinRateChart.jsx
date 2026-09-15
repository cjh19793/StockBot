"use client";

import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const GRADE_COLOR = {
  Excellent: "#3DDC84",
  Good: "#58A6FF",
  Neutral: "#8891A3",
  Caution: "#FF6B6B",
};

export default function WinRateChart({ holds, height = 220 }) {
  const data = holds.map((h) => ({ name: `${h.hold_days}일`, winRate: h.win_rate, grade: h.grade }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="#232937" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#8891A3", fontSize: 12, fontFamily: "var(--font-mono)" }} axisLine={{ stroke: "#232937" }} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: "#545E70", fontSize: 11, fontFamily: "var(--font-mono)" }} axisLine={false} tickLine={false} width={36} />
        <Tooltip
          cursor={{ fill: "#ffffff08" }}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const p = payload[0].payload;
            return (
              <div className="rounded-md border border-border bg-bg-raised px-3 py-2 font-mono text-[11px] shadow-lg">
                <div className="text-ink-faint">{label}</div>
                <div style={{ color: GRADE_COLOR[p.grade] }}>승률 {p.winRate.toFixed(1)}% · {p.grade}</div>
              </div>
            );
          }}
        />
        <Bar dataKey="winRate" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {data.map((d, i) => (
            <Cell key={i} fill={GRADE_COLOR[d.grade] || "#8891A3"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
