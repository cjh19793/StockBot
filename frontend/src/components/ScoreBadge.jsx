const TONE_BY_LABEL = {
  "Strong Buy": "tone-strong-buy",
  "Buy": "tone-buy",
  "Neutral": "tone-neutral",
  "Sell": "tone-sell",
  "Strong Sell": "tone-strong-sell",
};

// 백엔드가 계산한 total/label 을 그대로 표시만 한다 (프론트에서 점수 재계산 없음).
export default function ScoreBadge({ total, label, size = "md" }) {
  const tone = TONE_BY_LABEL[label] || "tone-neutral";
  return (
    <span className={`score-badge ${tone} size-${size}`}>
      <strong>{total}</strong>
      <span className="score-badge-label">{label}</span>
    </span>
  );
}
