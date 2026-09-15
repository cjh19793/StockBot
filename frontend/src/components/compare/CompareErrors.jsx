export default function CompareErrors({ errors }) {
  if (!errors || errors.length === 0) return null;
  return (
    <div className="rounded-md border border-down/20 bg-down/5 px-4 py-3 text-[12.5px] text-ink-dim">
      <p className="mb-1.5 font-semibold text-down">일부 종목 분석에 실패했습니다</p>
      <ul className="space-y-1">
        {errors.map((e) => (
          <li key={e.ticker}>
            <span className="font-mono font-semibold">{e.ticker}</span> — {e.error}
          </li>
        ))}
      </ul>
    </div>
  );
}
