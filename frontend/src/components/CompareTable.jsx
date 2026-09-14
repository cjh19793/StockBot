import ScoreBadge from "./ScoreBadge";
import { judgmentTone } from "../judgmentTone";

function fmt(n, digits = 2) {
  return typeof n === "number" ? n.toFixed(digits) : "-";
}

// results 는 백엔드 /api/compare 응답을 그대로 받는다. 여기서 하는 유일한 가공은
// 이미 내려온 composite.total 기준 정렬뿐 — 새 점수를 계산하지 않는다.
export default function CompareTable({ results }) {
  if (results.length === 0) return null;

  const sorted = [...results].sort((a, b) => b.composite.total - a.composite.total);

  return (
    <>
      {/* Desktop: 테이블 */}
      <div className="card table-card compare-desktop">
        <table className="compare">
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
              <tr key={r.ticker} className={i === 0 ? "top" : ""}>
                <td><span className={`rank ${i === 0 ? "gold" : ""}`}>{i + 1}</span></td>
                <td className="t-ticker">{r.ticker}</td>
                <td>${fmt(r.price)}</td>
                <td><ScoreBadge total={r.composite.total} label={r.composite.label} size="sm" /></td>
                <td>{r.composite.technical}</td>
                <td>{r.composite.market}</td>
                <td>{r.composite.risk}</td>
                <td>{r.composite.fundamentals}</td>
                <td>${fmt(r.target_price)}</td>
                <td>${fmt(r.stop_loss)}</td>
                <td><span className={`judgment-text ${judgmentTone(r.judgment)}`}>{r.judgment}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile: 카드 리스트 */}
      <div className="compare-mobile">
        {sorted.map((r, i) => (
          <div className={`card rank-card ${i === 0 ? "top" : ""}`} key={r.ticker}>
            <div className="rc-top">
              <div className="rc-left">
                <span className={`rank ${i === 0 ? "gold" : ""}`}>{i + 1}</span>
                <div>
                  <div className="rc-ticker">{r.ticker}</div>
                  <div className="rc-price">${fmt(r.price)}</div>
                </div>
              </div>
              <ScoreBadge total={r.composite.total} label={r.composite.label} size="sm" />
            </div>
            <div className="rc-subscores">
              <div className="rc-sub"><span className="k">기술</span><span className="v">{r.composite.technical}</span></div>
              <div className="rc-sub"><span className="k">시장</span><span className="v">{r.composite.market}</span></div>
              <div className="rc-sub"><span className="k">리스크</span><span className="v">{r.composite.risk}</span></div>
              <div className="rc-sub"><span className="k">펀더멘털</span><span className="v">{r.composite.fundamentals}</span></div>
            </div>
            <div className="rc-bottom">
              <span className="rc-targets">
                목표 <b>${fmt(r.target_price)}</b> · 손절 <b className="down">${fmt(r.stop_loss)}</b>
              </span>
              <span className={`judgment-text ${judgmentTone(r.judgment)}`}>{r.judgment}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
