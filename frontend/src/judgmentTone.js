// signals.final_judgment() 가 내려주는 문자열(예: "[Buy] Strong Buy")에서
// 배지 색상 톤만 뽑아낸다. 텍스트 자체는 백엔드 값을 그대로 표시한다.
export function judgmentTone(judgment) {
  if (!judgment) return "neutral";
  if (judgment.includes("Strong Buy")) return "strongbuy";
  if (judgment.includes("Buy")) return "buy";
  if (judgment.includes("Strong Sell")) return "strongsell";
  if (judgment.includes("Sell")) return "sell";
  return "neutral";
}
