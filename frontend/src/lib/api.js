// StockBot 백엔드(FastAPI) 연동. 분석 계열(analyze/compare/chart/series/montecarlo)은
// 인증이 필요 없는 공개 API. watchlist/alerts 는 로그인 사용자 전용이라 Supabase 세션의
// access_token 을 Authorization 헤더로 붙인다(authedFetch, 아래).
import { supabase } from "@/lib/supabaseClient";

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

// --- 관심종목 / 알림 (로그인 필요) ---

async function authedFetch(url, options = {}) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("로그인이 필요합니다.");

  const headers = { ...(options.headers || {}), Authorization: `Bearer ${token}` };
  if (options.body) headers["Content-Type"] = "application/json";

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) throw new Error(await readErrorMessage(res));
  if (res.status === 204) return null;
  return res.json();
}

export function fetchWatchlist() {
  return authedFetch(`${API_BASE}/api/watchlist`);
}

export function addWatchlistItem(ticker, mode) {
  return authedFetch(`${API_BASE}/api/watchlist`, {
    method: "POST",
    body: JSON.stringify({ ticker, mode: mode || undefined }),
  });
}

export function removeWatchlistItem(id) {
  return authedFetch(`${API_BASE}/api/watchlist/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function fetchAlerts() {
  return authedFetch(`${API_BASE}/api/alerts`);
}

export function createAlert({ ticker, mode, conditionType, conditionValue }) {
  return authedFetch(`${API_BASE}/api/alerts`, {
    method: "POST",
    body: JSON.stringify({
      ticker,
      mode: mode || undefined,
      condition_type: conditionType,
      condition_value: conditionValue,
    }),
  });
}

export function updateAlert(id, patch) {
  return authedFetch(`${API_BASE}/api/alerts/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteAlert(id) {
  return authedFetch(`${API_BASE}/api/alerts/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function fetchAlertEvents(unreadOnly = false) {
  const url = new URL(`${API_BASE}/api/alerts/events`);
  if (unreadOnly) url.searchParams.set("unread_only", "true");
  return authedFetch(url);
}

export function markAlertEventRead(id) {
  return authedFetch(`${API_BASE}/api/alerts/events/${encodeURIComponent(id)}/read`, {
    method: "POST",
  });
}
