const TONE_BY_LABEL = {
  "Strong Buy": "strongbuy",
  "Buy": "buy",
  "Neutral": "neutral",
  "Sell": "sell",
  "Strong Sell": "strongsell",
};

// 백엔드가 계산한 total/label 을 그대로 표시만 한다 (프론트에서 점수 재계산 없음).
export default function ScoreBadge({ total, label, size = "lg" }) {
  const tone = TONE_BY_LABEL[label] || "neutral";
  return (
    <span className={`score-badge score-badge-${size} ${tone}`}>
      <strong>{total}</strong>
      <span>{label}</span>
    </span>
  );
}
