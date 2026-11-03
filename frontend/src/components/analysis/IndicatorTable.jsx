import { fmt, fmtInt } from "@/lib/format";

// 해석 기준은 signals.py::detect_signal 의 임계값을 그대로 따른다.
//   RSI: <=30 과매도 / <=40 저점 근접 / >=70 과매수 / >=60 고점 근접
//   스토캐스틱: 20 / 80
//   볼린저: 종가 <= 하단(x1.02) / >= 상단(x0.98)
//   거래량: 20봉 평균 대비 2.0 / 1.5 / 0.5 배
//   MACD·MA: 교차(골든/데드) 및 종가 위치
// tone: up(매수 쪽) / down(매도 쪽) / neutral
const N = (text) => ({ text, tone: "neutral" });
const UP = (text) => ({ text, tone: "up" });
const DOWN = (text) => ({ text, tone: "down" });

const isNum = (v) => typeof v === "number" && Number.isFinite(v);

function readRsi(rsi) {
  if (!isNum(rsi)) return N("-");
  if (rsi <= 30) return UP("과매도 (반등 가능성)");
  if (rsi <= 40) return UP("저점 근접 (약한 매수 구간)");
  if (rsi >= 70) return DOWN("과매수 (조정 가능성)");
  if (rsi >= 60) return DOWN("고점 근접 (약한 매도 구간)");
  return N("중립");
}

function readStoch(k) {
  if (!isNum(k)) return N("-");
  if (k < 20) return UP("과매도권");
  if (k > 80) return DOWN("과매수권");
  return N("중립");
}

function readBbUpper(price, upper) {
  if (!isNum(price) || !isNum(upper)) return N("-");
  if (price >= upper) return DOWN("상단 이탈 (단기 조정 가능)");
  if (price >= upper * 0.98) return DOWN("상단 근접 (저항선 테스트)");
  return N("밴드 내");
}

function readBbLower(price, lower) {
  if (!isNum(price) || !isNum(lower)) return N("-");
  if (price <= lower) return UP("하단 이탈 (단기 반등 기대)");
  if (price <= lower * 1.02) return UP("하단 근접 (지지선 테스트)");
  return N("밴드 내");
}

// 마지막 두 봉으로 교차 여부를 판정한다 (signals.py 와 동일한 prev/curr 비교).
function readCross(rows, aKey, bKey, up, down, above, below) {
  const cur = rows[rows.length - 1];
  const prev = rows[rows.length - 2];
  if (!cur || !prev || ![cur[aKey], cur[bKey], prev[aKey], prev[bKey]].every(isNum)) return N("-");
  if (prev[aKey] < prev[bKey] && cur[aKey] > cur[bKey]) return UP(up);
  if (prev[aKey] > prev[bKey] && cur[aKey] < cur[bKey]) return DOWN(down);
  return N(cur[aKey] > cur[bKey] ? above : below);
}

function readMaPosition(price, ma5, ma20) {
  if (!isNum(price) || !isNum(ma5) || !isNum(ma20)) return N("-");
  if (price > ma5 && price > ma20) return UP("이동평균선 위 안착 (상승 추세)");
  if (price < ma5 && price < ma20) return DOWN("이동평균선 아래 (하락 추세)");
  return N("이동평균선 사이 (혼조)");
}

function readVolume(rows, volume) {
  const vols = rows.map((r) => r.volume).filter(isNum).slice(-20);
  if (vols.length < 20 || !isNum(volume)) return N("-");
  const avg = vols.reduce((a, b) => a + b, 0) / vols.length;
  if (!(avg > 0)) return N("-");
  const ratio = volume / avg;
  const t = `20봉 평균의 ${ratio.toFixed(1)}배`;
  if (ratio >= 2.0) return UP(`폭증 (${t})`);
  if (ratio >= 1.5) return UP(`급증 (${t})`);
  if (ratio < 0.5) return DOWN(`급감 (${t})`);
  return N(`보통 (${t})`);
}

function readDistance(price, level, label) {
  if (!isNum(price) || !isNum(level) || price === 0) return N("-");
  const pct = ((level - price) / price) * 100;
  return N(`현재가 대비 ${pct >= 0 ? "+" : ""}${pct.toFixed(1)}% (${label})`);
}

const TONE_TEXT = { up: "text-up", down: "text-down", neutral: "text-ink-label" };

export default function IndicatorTable({ result, rows }) {
  const r = result;
  const items = [
    ["RSI (14)", fmt(r.rsi, 1), readRsi(r.rsi)],
    ["MACD", fmt(r.macd), readCross(rows, "macd", "macdSignal", "골든크로스 (상승 전환)", "데드크로스 (하락 전환)", "시그널선 위", "시그널선 아래")],
    ["스토캐스틱 %K", fmt(r.stoch_k, 1), readStoch(r.stoch_k)],
    ["ATR", `${fmt(r.atr)} (${(r.atr_pct * 100).toFixed(1)}%)`, N("변동성 (현재가 대비 비율)")],
    ["MA5", fmt(r.ma5), readMaPosition(r.price, r.ma5, r.ma20)],
    ["MA20", fmt(r.ma20), readCross(rows, "ma5", "ma20", "MA 골든크로스 (중기 상승 전환)", "MA 데드크로스 (중기 하락 전환)", "MA5가 MA20 위", "MA5가 MA20 아래")],
    ["볼린저 상단", fmt(r.bb_upper), readBbUpper(r.price, r.bb_upper)],
    ["볼린저 하단", fmt(r.bb_lower), readBbLower(r.price, r.bb_lower)],
    ["지지선", fmt(r.support), readDistance(r.price, r.support, "하방")],
    ["저항선", fmt(r.resistance), readDistance(r.price, r.resistance, "상방")],
    ["거래량", fmtInt(r.volume), readVolume(rows, r.volume)],
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-border text-[13px] text-ink-label">
            <th className="py-2 pr-4 font-medium">지표</th>
            <th className="py-2 pr-4 text-right font-medium">값</th>
            <th className="py-2 font-medium">해석</th>
          </tr>
        </thead>
        <tbody>
          {items.map(([label, value, read]) => (
            <tr key={label} className="border-b border-border/60 last:border-0">
              <td className="whitespace-nowrap py-2.5 pr-4 text-[14px] font-medium text-ink-label">{label}</td>
              <td className="whitespace-nowrap py-2.5 pr-4 text-right text-[17px] font-semibold tabular-nums">{value}</td>
              <td className={`py-2.5 text-[14px] ${TONE_TEXT[read.tone]}`}>{read.text}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
