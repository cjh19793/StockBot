import ResultHeader from "./ResultHeader";
import CompositePanel from "./CompositePanel";
import PriceStatTiles from "./PriceStatTiles";
import ChartsPanel from "./ChartsPanel";
import IndicatorTable from "./IndicatorTable";
import SignalLists from "./SignalLists";
import MarketMoodCard from "./MarketMoodCard";
import FundamentalsCard from "./FundamentalsCard";
import Card from "@/components/ui/Card";
import { toRows } from "@/lib/chartData";

export default function AnalysisView({ result, series }) {
  const rows = toRows(series);
  return (
    <div className="space-y-5">
      <ResultHeader result={result} />
      <PriceStatTiles result={result} />

      {/* minmax(0,1fr): 차트가 컨테이너 최소폭을 밀어 오른쪽 패널이 잘리는 것을 방지 */}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0 space-y-5">
          <ChartsPanel series={series} result={result} />
          <Card>
            <h2 className="mb-3 text-[15px] font-semibold">기술 지표</h2>
            <IndicatorTable result={result} rows={rows} />
          </Card>
        </div>
        <div className="min-w-0 space-y-5">
          <CompositePanel composite={result.composite} />
          <MarketMoodCard result={result} />
          <FundamentalsCard fundamentals={result.fundamentals} />
        </div>
      </div>

      <SignalLists result={result} />
    </div>
  );
}
