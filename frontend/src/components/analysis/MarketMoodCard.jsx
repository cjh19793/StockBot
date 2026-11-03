import Card from "@/components/ui/Card";
import { fmt } from "@/lib/format";

export default function MarketMoodCard({ result }) {
  const r = result;
  const regime = r.market_regime;
  const hasSentimentRow = r.fear_greed_label || r.earnings || r.news_sentiment;

  if (!regime && !hasSentimentRow && r.news_titles.length === 0) return null;

  return (
    <Card>
      {regime && (
        <div className="mb-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-[15px] font-semibold">시장환경</h3>
            <span className="text-[13px] font-medium tabular-nums text-ink-label">{regime.label} ({regime.score}점)</span>
          </div>
          <div className="space-y-1.5 text-[14px]">
            <div className="flex justify-between"><span className="text-ink-label">S&amp;P 500</span><span>{regime.sp500_trend}</span></div>
            <div className="flex justify-between"><span className="text-ink-label">NASDAQ</span><span>{regime.nasdaq_trend}</span></div>
            <div className="flex justify-between"><span className="text-ink-label">VIX</span><span>{fmt(regime.vix, 1)} ({regime.vix_level})</span></div>
          </div>
        </div>
      )}

      {hasSentimentRow && (
        <div className={regime ? "border-t border-border pt-4" : ""}>
          <div className="space-y-1.5 text-[14px]">
            {r.fear_greed_label && (
              <div className="flex justify-between"><span className="text-ink-label">공포탐욕지수</span><span>{r.fear_greed_score} · {r.fear_greed_label}</span></div>
            )}
            {r.earnings && (
              <div className="flex justify-between"><span className="text-ink-label">실적</span><span>{r.earnings}</span></div>
            )}
            {r.news_sentiment && (
              <div className="flex justify-between"><span className="text-ink-label">뉴스 감성</span><span>{r.news_sentiment}</span></div>
            )}
          </div>
        </div>
      )}

      {r.news_titles.length > 0 && (
        <ul className="mt-3 space-y-1.5 border-t border-border pt-3 text-[13px] text-ink-label">
          {r.news_titles.map((t, i) => (
            <li key={i} className="line-clamp-2">· {t}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}
