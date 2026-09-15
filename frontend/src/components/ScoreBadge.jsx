import { scoreTone, TONE_CLASSES } from "@/lib/format";

const SIZE_CLASSES = {
  sm: "px-2 py-1 text-[11px] gap-1.5",
  lg: "px-3.5 py-2 text-sm gap-2.5",
};

// 백엔드가 계산한 total/label 을 그대로 표시만 한다 (프론트에서 점수 재계산 없음).
export default function ScoreBadge({ total, label, size = "lg" }) {
  const tone = scoreTone(label);
  return (
    <span className={`inline-flex items-center rounded-md border font-mono font-semibold ${SIZE_CLASSES[size]} ${TONE_CLASSES[tone]}`}>
      <strong className={size === "lg" ? "text-lg" : ""}>{total}</strong>
      <span className="font-sans font-medium opacity-90">{label}</span>
    </span>
  );
}
