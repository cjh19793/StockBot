// 랜딩 히어로 차트가 실데이터 로딩 중/실패 시 보여주는 장식용 시계열.
// SeriesResponse 와 동일한 필드 모양을 갖추되 실제 티커 데이터가 아니므로
// 숫자/티커/판정 등 "사실"로 보일 수 있는 텍스트에는 절대 쓰지 않는다 (차트 형태만 장식용).
function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

function rollingMean(arr, window) {
  return arr.map((_, i) => {
    if (i < window - 1) return null;
    let sum = 0;
    for (let j = i - window + 1; j <= i; j++) sum += arr[j];
    return sum / window;
  });
}

function rollingStd(arr, window) {
  return arr.map((_, i) => {
    if (i < window - 1) return null;
    const slice = arr.slice(i - window + 1, i + 1);
    const mean = slice.reduce((a, b) => a + b, 0) / window;
    const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / window;
    return Math.sqrt(variance);
  });
}

export function generateDemoSeries(n = 60, seed = 42) {
  const rand = seededRandom(seed);
  const close = [];
  let v = 100;
  for (let i = 0; i < n; i++) {
    v += (rand() - 0.46) * 2.2;
    close.push(v);
  }

  const ma5 = rollingMean(close, 5);
  const ma20 = rollingMean(close, 20);
  const std20 = rollingStd(close, 20);
  const bbUpper = ma20.map((m, i) => (m != null ? m + std20[i] * 2 : null));
  const bbLower = ma20.map((m, i) => (m != null ? m - std20[i] * 2 : null));

  // RSI(14) 근사
  const rsi = close.map((_, i) => {
    if (i < 14) return null;
    let gain = 0;
    let loss = 0;
    for (let j = i - 13; j <= i; j++) {
      const d = close[j] - close[j - 1];
      if (d >= 0) gain += d;
      else loss -= d;
    }
    if (loss === 0) return 100;
    const rs = gain / 14 / (loss / 14);
    return 100 - 100 / (1 + rs);
  });

  // EMA 기반 MACD 근사
  function ema(arr, span) {
    const k = 2 / (span + 1);
    const out = [];
    let prev;
    arr.forEach((val, i) => {
      prev = i === 0 ? val : val * k + prev * (1 - k);
      out.push(prev);
    });
    return out;
  }
  const ema12 = ema(close, 12);
  const ema26 = ema(close, 26);
  const macd = ema12.map((v12, i) => v12 - ema26[i]);
  const macdSignal = ema(macd, 9);
  const macdHist = macd.map((m, i) => m - macdSignal[i]);

  const dates = close.map((_, i) => `D${i}`);

  return {
    ticker: "",
    mode: "기본",
    interval: "1d",
    dates,
    open: close,
    high: close,
    low: close,
    close,
    volume: close.map(() => null),
    ma5,
    ma20,
    ma60: close.map(() => null),
    bb_upper: bbUpper,
    bb_lower: bbLower,
    rsi,
    macd,
    macd_signal: macdSignal,
    macd_hist: macdHist,
    stoch_k: close.map(() => null),
    stoch_d: close.map(() => null),
    atr: close.map(() => null),
    support: close.map(() => null),
    resistance: close.map(() => null),
  };
}
