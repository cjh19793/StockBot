"use client";

export default function ChartTooltip({ active, payload, label, rows = [] }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-bg-raised px-3 py-2 font-pretendard text-[12px] tabular-nums shadow-lg">
      <div className="mb-1 text-ink-label">{label}</div>
      {rows.map((row) => {
        const item = payload.find((p) => p.dataKey === row.key);
        if (!item || item.value == null) return null;
        return (
          <div key={row.key} className="flex items-center justify-between gap-4">
            <span className="text-ink-label">{row.label}</span>
            <span className="font-semibold" style={{ color: row.color }}>
              {typeof item.value === "number" ? item.value.toFixed(row.digits ?? 2) : item.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}
