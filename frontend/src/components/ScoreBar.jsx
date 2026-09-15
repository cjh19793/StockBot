// value 는 백엔드가 계산해 내려준 0~100 값을 그대로 막대 길이로만 사용한다.
export default function ScoreBar({ label, value }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-[13px]">
        <span className="text-ink-dim">{label}</span>
        <b className="font-mono">{value}</b>
      </div>
      <div className="h-1.5 rounded-full bg-bg-raised">
        <div className="h-1.5 rounded-full bg-amber" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
