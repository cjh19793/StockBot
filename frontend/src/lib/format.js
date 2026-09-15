export function fmt(n, digits = 2) {
  return typeof n === "number" && !Number.isNaN(n) ? n.toFixed(digits) : "-";
}

export function fmtPrice(n) {
  return typeof n === "number" && !Number.isNaN(n) ? `$${n.toFixed(2)}` : "-";
}

export function fmtPct(n, digits = 1) {
  return typeof n === "number" && !Number.isNaN(n)
    ? `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`
    : "-";
}

export function fmtInt(n) {
  return typeof n === "number" && !Number.isNaN(n) ? Math.round(n).toLocaleString() : "-";
}

// judgment 문자열(예: "[Buy] Strong Buy")에서 배지 색상 톤만 뽑는다.
// 텍스트 자체는 백엔드 값을 그대로 표시한다.
export function judgmentTone(judgment) {
  if (!judgment) return "neutral";
  if (judgment.includes("Strong Buy")) return "strongbuy";
  if (judgment.includes("Buy")) return "buy";
  if (judgment.includes("Strong Sell")) return "strongsell";
  if (judgment.includes("Sell")) return "sell";
  return "neutral";
}

const SCORE_TONE_BY_LABEL = {
  "Strong Buy": "strongbuy",
  Buy: "buy",
  Neutral: "neutral",
  Sell: "sell",
  "Strong Sell": "strongsell",
};

export function scoreTone(label) {
  return SCORE_TONE_BY_LABEL[label] || "neutral";
}

export const TONE_CLASSES = {
  strongbuy: "text-up bg-up/10 border-up/30",
  buy: "text-up bg-up/10 border-up/20",
  neutral: "text-ink-dim bg-white/5 border-border",
  sell: "text-down bg-down/10 border-down/20",
  strongsell: "text-down bg-down/10 border-down/30",
};
