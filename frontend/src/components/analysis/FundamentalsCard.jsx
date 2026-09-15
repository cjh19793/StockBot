import Card from "@/components/ui/Card";

function Row({ label, value }) {
  return (
    <div className="flex justify-between text-[12.5px]">
      <span className="text-ink-faint">{label}</span>
      <span>{typeof value === "number" ? `${value}점` : "데이터 없음"}</span>
    </div>
  );
}

export default function FundamentalsCard({ fundamentals }) {
  if (!fundamentals) return null;
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-[13px] font-semibold">펀더멘털</h3>
        <span className="font-mono text-[12px] text-ink-dim">{fundamentals.label} ({fundamentals.overall}점)</span>
      </div>
      <div className="space-y-1.5">
        <Row label="성장성" value={fundamentals.growth} />
        <Row label="수익성" value={fundamentals.profitability} />
        <Row label="밸류에이션" value={fundamentals.valuation} />
        <Row label="재무건전성" value={fundamentals.financial_health} />
      </div>
    </Card>
  );
}
