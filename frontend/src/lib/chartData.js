// SeriesResponse(webapi/schemas.py::SeriesResponse, 컬럼별 배열)를 recharts 가
// 바로 소비할 수 있는 행(row) 배열로 펼친다. null 은 그대로 유지해 recharts가
// 지표 계산에 필요한 초기 구간(rolling window 미충족)을 자연스럽게 끊어서 그리게 한다.
export function toRows(series) {
  if (!series) return [];
  const n = series.dates.length;
  const rows = new Array(n);
  for (let i = 0; i < n; i++) {
    const bbUpper = series.bb_upper[i];
    const bbLower = series.bb_lower[i];
    rows[i] = {
      date: series.dates[i],
      open: series.open[i],
      high: series.high[i],
      low: series.low[i],
      close: series.close[i],
      volume: series.volume[i],
      ma5: series.ma5[i],
      ma20: series.ma20[i],
      ma60: series.ma60[i],
      bbUpper,
      bbLower,
      bbBand: bbUpper != null && bbLower != null ? bbUpper - bbLower : null,
      rsi: series.rsi[i],
      macd: series.macd[i],
      macdSignal: series.macd_signal[i],
      macdHist: series.macd_hist[i],
      stochK: series.stoch_k[i],
      stochD: series.stoch_d[i],
      atr: series.atr[i],
      support: series.support[i],
      resistance: series.resistance[i],
    };
  }
  return rows;
}

// 짧은 날짜 표기 (X축 눈금용): 일봉 "01-15", 분/시간봉 "01-15 09:30" -> "09:30"
export function shortDate(date, interval) {
  if (!date) return "";
  if (interval === "1d") return date.slice(5); // MM-DD
  const [d, t] = date.split(" ");
  return t || d.slice(5);
}

// n개 데이터에서 대략 target개 정도만 눈금으로 남기기 위한 interval 값
export function tickInterval(n, target = 6) {
  return Math.max(0, Math.floor(n / target) - 1);
}
