// StockBot 백엔드(FastAPI) 연동. 인증이 필요 없는 공개 API라 별도 키/토큰은 없다.
const DEFAULT_API_BASE = "https://stockbot-api-ni3d.onrender.com";

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/+$/, "");

async function readErrorMessage(res) {
  try {
    const body = await res.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch {
    // 응답이 JSON 이 아닌 경우 무시하고 기본 메시지 사용
  }
  return `요청 실패 (HTTP ${res.status})`;
}

export async function fetchModes() {
  const res = await fetch(`${API_BASE}/api/modes`);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.json();
}

export async function fetchAnalysis(ticker, mode) {
  const url = new URL(`${API_BASE}/api/analyze/${encodeURIComponent(ticker)}`);
  if (mode) url.searchParams.set("mode", mode);
  const res = await fetch(url);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.json();
}

export function chartUrl(ticker, mode) {
  const url = new URL(`${API_BASE}/api/chart/${encodeURIComponent(ticker)}.png`);
  if (mode) url.searchParams.set("mode", mode);
  return url.toString();
}

export async function fetchCompare(tickers, mode) {
  const url = new URL(`${API_BASE}/api/compare`);
  url.searchParams.set("tickers", tickers.join(","));
  if (mode) url.searchParams.set("mode", mode);
  const res = await fetch(url);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.json();
}

export async function fetchMonteCarlo(ticker, mode, simulations) {
  const url = new URL(`${API_BASE}/api/montecarlo/${encodeURIComponent(ticker)}`);
  if (mode) url.searchParams.set("mode", mode);
  if (simulations) url.searchParams.set("simulations", String(simulations));
  const res = await fetch(url);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.json();
}
