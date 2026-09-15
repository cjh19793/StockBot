// StockBot 백엔드(FastAPI) 연동. 인증이 필요 없는 공개 API라 별도 키/토큰은 없다.
const DEFAULT_API_BASE = "https://stockbot-api-ni3d.onrender.com";

export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE
).replace(/\/+$/, "");

async function readErrorMessage(res) {
  try {
    const body = await res.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch {
    // 응답이 JSON 이 아닌 경우 무시하고 기본 메시지 사용
  }
  return `요청 실패 (HTTP ${res.status})`;
}

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.json();
}

export function fetchModes() {
  return getJson(`${API_BASE}/api/modes`);
}

export function fetchAnalysis(ticker, mode) {
  const url = new URL(`${API_BASE}/api/analyze/${encodeURIComponent(ticker)}`);
  if (mode) url.searchParams.set("mode", mode);
  return getJson(url);
}

export function fetchSeries(ticker, mode) {
  const url = new URL(`${API_BASE}/api/series/${encodeURIComponent(ticker)}`);
  if (mode) url.searchParams.set("mode", mode);
  return getJson(url);
}

export function fetchCompare(tickers, mode) {
  const url = new URL(`${API_BASE}/api/compare`);
  url.searchParams.set("tickers", tickers.join(","));
  if (mode) url.searchParams.set("mode", mode);
  return getJson(url);
}

export function fetchMonteCarlo(ticker, mode, simulations) {
  const url = new URL(`${API_BASE}/api/montecarlo/${encodeURIComponent(ticker)}`);
  if (mode) url.searchParams.set("mode", mode);
  if (simulations) url.searchParams.set("simulations", String(simulations));
  return getJson(url);
}
