import Card from "@/components/ui/Card";

function ArrowUp() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 19V5" />
      <path d="M5 12l7-7 7 7" />
    </svg>
  );
}
function ArrowDown() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 5v14" />
      <path d="M19 12l-7 7-7-7" />
    </svg>
  );
}

export default function SignalLists({ result }) {
  const r = result;
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Card className="border-up/20">
        <h3 className="mb-3 flex items-center gap-2 text-[13px] font-semibold text-up">
          <ArrowUp /> 매수 신호 ({r.buy_score}점)
        </h3>
        {r.buy_signals.length > 0 ? (
          <ul className="space-y-2 text-[13px] text-ink-dim">
            {r.buy_signals.map((s, i) => (
              <li key={i} className="border-l-2 border-up/40 pl-2.5">{s}</li>
            ))}
          </ul>
        ) : (
          <p className="text-[13px] text-ink-faint">없음</p>
        )}
      </Card>
      <Card className="border-down/20">
        <h3 className="mb-3 flex items-center gap-2 text-[13px] font-semibold text-down">
          <ArrowDown /> 매도 신호 ({r.sell_score}점)
        </h3>
        {r.sell_signals.length > 0 ? (
          <ul className="space-y-2 text-[13px] text-ink-dim">
            {r.sell_signals.map((s, i) => (
              <li key={i} className="border-l-2 border-down/40 pl-2.5">{s}</li>
            ))}
          </ul>
        ) : (
          <p className="text-[13px] text-ink-faint">없음</p>
        )}
      </Card>
    </div>
  );
}
