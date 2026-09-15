import Card from "@/components/ui/Card";
import ScoreBadge from "@/components/ScoreBadge";
import ScoreBar from "@/components/ScoreBar";

export default function CompositePanel({ composite }) {
  const c = composite;
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-wide text-ink-faint">종합점수</span>
        <ScoreBadge total={c.total} label={c.label} size="lg" />
      </div>
      <div className="space-y-3.5">
        <ScoreBar label="기술적 분석" value={c.technical} />
        <ScoreBar label="시장환경" value={c.market} />
        <ScoreBar label="리스크 (높을수록 안전)" value={c.risk} />
        <ScoreBar label="펀더멘털" value={c.fundamentals} />
      </div>
      {(!c.market_available || !c.fundamentals_available) && (
        <p className="mt-4 text-[12px] leading-relaxed text-ink-faint">
          {!c.market_available && "시장환경 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다. "}
          {!c.fundamentals_available && "펀더멘털 데이터를 가져오지 못해 중립값(50)으로 계산되었습니다."}
        </p>
      )}
    </Card>
  );
}
