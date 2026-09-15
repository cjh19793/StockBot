import ResultHeader from "./ResultHeader";
import CompositePanel from "./CompositePanel";
import PriceStatTiles from "./PriceStatTiles";
import ChartsPanel from "./ChartsPanel";
import IndicatorGrid from "./IndicatorGrid";
import SignalLists from "./SignalLists";
import MarketMoodCard from "./MarketMoodCard";
import FundamentalsCard from "./FundamentalsCard";
import Card from "@/components/ui/Card";

export default function AnalysisView({ result, series }) {
  return (
    <div className="space-y-5">
      <ResultHeader result={result} />
      <CompositePanel composite={result.composite} />
      <PriceStatTiles result={result} />

      <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
        <div className="space-y-5">
          <ChartsPanel series={series} result={result} />
          <Card>
            <h2 className="mb-3 text-[13px] font-semibold">기술 지표</h2>
            <IndicatorGrid result={result} />
          </Card>
        </div>
        <div className="space-y-5">
          <MarketMoodCard result={result} />
          <FundamentalsCard fundamentals={result.fundamentals} />
        </div>
      </div>

      <SignalLists result={result} />
    </div>
  );
}
