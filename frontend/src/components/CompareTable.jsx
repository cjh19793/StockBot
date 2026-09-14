import ScoreBadge from "./ScoreBadge";

function fmt(n, digits = 2) {
  return typeof n === "number" ? n.toFixed(digits) : "-";
}

// results 는 백엔드 /api/compare 응답을 그대로 받는다. 여기서 하는 유일한 가공은
// 이미 내려온 composite.total 기준 정렬뿐 — 새 점수를 계산하지 않는다.
export default function CompareTable({ results }) {
  if (results.length === 0) return null;

  const sorted = [...results].sort((a, b) => b.composite.total - a.composite.total);

  return (
    <div className="compare-table-wrap">
      <table className="compare-table">
        <thead>
          <tr>
            <th>순위</th>
            <th>티커</th>
            <th>현재가</th>
            <th>종합점수</th>
            <th>기술</th>
            <th>시장환경</th>
            <th>리스크</th>
            <th>펀더멘털</th>
            <th>목표가</th>
            <th>손절가</th>
            <th>판정</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={r.ticker}>
              <td>{i + 1}</td>
              <td className="compare-ticker">{r.ticker}</td>
              <td>${fmt(r.price)}</td>
              <td><ScoreBadge total={r.composite.total} label={r.composite.label} size="sm" /></td>
              <td>{r.composite.technical}</td>
              <td>{r.composite.market}</td>
              <td>{r.composite.risk}</td>
              <td>{r.composite.fundamentals}</td>
              <td>${fmt(r.target_price)}</td>
              <td>${fmt(r.stop_loss)}</td>
              <td>{r.judgment}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
