import Card from "@/components/ui/Card";
import ScoreBar from "@/components/ScoreBar";

// 종합점수 자체는 최상단 타일에 표시하고, 여기서는 축별 구성만 보여준다.
export default function CompositePanel({ composite }) {
  const c = composite;
  return (
    <Card>
      <h3 className="mb-4 text-[15px] font-semibold">점수 구성</h3>
      <div className="space-y-4">
        <ScoreBar label="기술적 분석" value={c.technical} />
        <ScoreBar label="시장환경" value={c.market} />
        <ScoreBar label="리스크 (높을수록 안전)" value={c.risk} />
        <ScoreBar label="펀더멘털" value={c.fundamentals} />
      </div>
      {(!c.market_available || !c.fundamentals_available) && (
        <p className="mt-4 text-[13px] leading-relaxed text-ink-label">
          {!c.market_available && "시장환경 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다. "}
          {!c.fundamentals_available && "펀더멘털 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다."}
        </p>
      )}
    </Card>
  );
}
