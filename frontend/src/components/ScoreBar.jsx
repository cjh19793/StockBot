// value 는 백엔드가 계산해 내려준 0~100 값을 그대로 막대 길이로만 사용한다.
export default function ScoreBar({ label, value }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="bar-row">
      <div className="bar-head">
        <span>{label}</span>
        <b>{value}</b>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
