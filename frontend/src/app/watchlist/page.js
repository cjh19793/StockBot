"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import Card from "@/components/ui/Card";
import TickerInput from "@/components/TickerInput";
import ModeSegmented from "@/components/ModeSegmented";
import ScoreBadge from "@/components/ScoreBadge";
import { ErrorMessage, Hint } from "@/components/ui/StatusMessage";
import { useAuth } from "@/lib/authContext";
import { FALLBACK_ANALYSIS_MODES } from "@/lib/modes";
import {
  fetchWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
  fetchAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
  fetchAlertEvents,
  markAlertEventRead,
  fetchAnalysis,
} from "@/lib/api";

const CONDITION_LABELS = {
  price_above: "현재가가 이 값 이상일 때",
  price_below: "현재가가 이 값 이하일 때",
  buy_score_above: "매수 신호 점수가 이 값 이상일 때",
  sell_score_above: "매도 신호 점수가 이 값 이상일 때",
};

export default function WatchlistPage() {
  const { user, loading: authLoading } = useAuth();

  if (authLoading) return null;
  if (!user) {
    return (
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">관심종목</h1>
        <Hint>
          관심종목과 알림을 사용하려면 로그인이 필요합니다.{" "}
          <Link href="/login" className="text-amber underline">로그인 / 회원가입</Link>
        </Hint>
      </div>
    );
  }
  return <WatchlistContent />;
}

function WatchlistContent() {
  const [items, setItems] = useState([]);
  const [snapshots, setSnapshots] = useState({}); // ticker|mode -> {loading, price, composite, error}
  const [itemsError, setItemsError] = useState(null);

  const [ticker, setTicker] = useState("");
  const [mode, setMode] = useState("기본");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState(null);

  const [alerts, setAlerts] = useState([]);
  const [alertsError, setAlertsError] = useState(null);
  const [alertTicker, setAlertTicker] = useState("");
  const [alertMode, setAlertMode] = useState("기본");
  const [conditionType, setConditionType] = useState("price_above");
  const [conditionValue, setConditionValue] = useState("");
  const [creatingAlert, setCreatingAlert] = useState(false);

  const [events, setEvents] = useState([]);
  const [eventsError, setEventsError] = useState(null);

  const loadWatchlist = useCallback(async () => {
    try {
      const rows = await fetchWatchlist();
      setItems(rows);
      setItemsError(null);
    } catch (err) {
      setItemsError(err.message || "관심종목을 불러오지 못했습니다.");
    }
  }, []);

  const loadAlerts = useCallback(async () => {
    try {
      setAlerts(await fetchAlerts());
      setAlertsError(null);
    } catch (err) {
      setAlertsError(err.message || "알림 목록을 불러오지 못했습니다.");
    }
  }, []);

  const loadEvents = useCallback(async () => {
    try {
      setEvents(await fetchAlertEvents());
      setEventsError(null);
    } catch (err) {
      setEventsError(err.message || "알림함을 불러오지 못했습니다.");
    }
  }, []);

  useEffect(() => {
    loadWatchlist();
    loadAlerts();
    loadEvents();
  }, [loadWatchlist, loadAlerts, loadEvents]);

  // 관심종목 각 행에 현재가/종합점수를 붙인다 — 기존 공개 /api/analyze 를 그대로 재사용.
  useEffect(() => {
    items.forEach((item) => {
      const key = `${item.ticker}|${item.mode}`;
      if (snapshots[key]) return;
      setSnapshots((prev) => ({ ...prev, [key]: { loading: true } }));
      fetchAnalysis(item.ticker, item.mode)
        .then((result) => {
          setSnapshots((prev) => ({ ...prev, [key]: { loading: false, result } }));
        })
        .catch((err) => {
          setSnapshots((prev) => ({ ...prev, [key]: { loading: false, error: err.message } }));
        });
    });
  }, [items, snapshots]);

  async function handleAdd(e) {
    e.preventDefault();
    const clean = ticker.trim().toUpperCase();
    if (!clean) return;
    setAdding(true);
    setAddError(null);
    try {
      await addWatchlistItem(clean, mode);
      setTicker("");
      await loadWatchlist();
    } catch (err) {
      setAddError(err.message || "추가에 실패했습니다.");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(id) {
    try {
      await removeWatchlistItem(id);
      await loadWatchlist();
    } catch (err) {
      setItemsError(err.message || "삭제에 실패했습니다.");
    }
  }

  async function handleCreateAlert(e) {
    e.preventDefault();
    const clean = alertTicker.trim().toUpperCase();
    const value = parseFloat(conditionValue);
    if (!clean || Number.isNaN(value)) return;
    setCreatingAlert(true);
    setAlertsError(null);
    try {
      await createAlert({ ticker: clean, mode: alertMode, conditionType, conditionValue: value });
      setAlertTicker("");
      setConditionValue("");
      await loadAlerts();
    } catch (err) {
      setAlertsError(err.message || "알림 생성에 실패했습니다.");
    } finally {
      setCreatingAlert(false);
    }
  }

  async function handleToggleAlert(alert) {
    try {
      await updateAlert(alert.id, { is_active: !alert.is_active });
      await loadAlerts();
    } catch (err) {
      setAlertsError(err.message || "알림 변경에 실패했습니다.");
    }
  }

  async function handleDeleteAlert(id) {
    try {
      await deleteAlert(id);
      await loadAlerts();
    } catch (err) {
      setAlertsError(err.message || "알림 삭제에 실패했습니다.");
    }
  }

  async function handleMarkRead(id) {
    try {
      await markAlertEventRead(id);
      await loadEvents();
    } catch (err) {
      setEventsError(err.message || "알림 읽음 처리에 실패했습니다.");
    }
  }

  const unreadCount = events.filter((e) => !e.is_read).length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">관심종목</h1>
        <p className="mt-1.5 text-[14px] text-ink-dim">관심종목을 등록하고, 조건을 만족하면 알림함에서 확인하세요.</p>
      </div>

      {/* 관심종목 */}
      <section className="space-y-4">
        <Card>
          <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-4">
            <div className="min-w-[200px] flex-1">
              <label htmlFor="wl-ticker" className="mb-1.5 block text-[12.5px] text-ink-faint">티커</label>
              <TickerInput id="wl-ticker" value={ticker} onChange={setTicker} maxLength={10} />
            </div>
            <div>
              <label className="mb-1.5 block text-[12.5px] text-ink-faint">모드</label>
              <ModeSegmented modes={FALLBACK_ANALYSIS_MODES} value={mode} onChange={setMode} ariaLabel="관심종목 모드" />
            </div>
            <button
              type="submit"
              disabled={adding || !ticker.trim()}
              className="rounded-md bg-amber px-5 py-2.5 font-semibold text-[#1A1000] transition-opacity disabled:opacity-40"
            >
              {adding ? "추가 중..." : "관심종목 추가"}
            </button>
          </form>
          {addError && <div className="mt-3"><ErrorMessage>{addError}</ErrorMessage></div>}
        </Card>

        {itemsError && <ErrorMessage>{itemsError}</ErrorMessage>}
        {items.length === 0 && !itemsError && <Hint>아직 등록한 관심종목이 없습니다.</Hint>}

        <div className="space-y-2">
          {items.map((item) => {
            const key = `${item.ticker}|${item.mode}`;
            const snap = snapshots[key];
            return (
              <Card key={item.id} className="flex flex-wrap items-center justify-between gap-3 !p-4">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-semibold">{item.ticker}</span>
                  <span className="rounded border border-border px-2 py-0.5 text-[11px] text-ink-faint">{item.mode}</span>
                </div>
                <div className="flex items-center gap-3">
                  {snap?.loading && <span className="text-[12px] text-ink-faint">조회 중...</span>}
                  {snap?.error && <span className="text-[12px] text-down">{snap.error}</span>}
                  {snap?.result && (
                    <>
                      <span className="font-mono text-sm text-ink-dim">${snap.result.price}</span>
                      <ScoreBadge total={snap.result.composite.total} label={snap.result.composite.label} size="sm" />
                    </>
                  )}
                  <button
                    type="button"
                    onClick={() => handleRemove(item.id)}
                    className="rounded-md border border-border px-3 py-1.5 text-[12.5px] text-ink-dim transition-colors hover:text-down"
                  >
                    삭제
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* 알림 조건 */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold tracking-tight">알림 조건</h2>
        <Card>
          <form onSubmit={handleCreateAlert} className="flex flex-wrap items-end gap-4">
            <div className="min-w-[160px]">
              <label htmlFor="alert-ticker" className="mb-1.5 block text-[12.5px] text-ink-faint">티커</label>
              <TickerInput id="alert-ticker" value={alertTicker} onChange={setAlertTicker} maxLength={10} />
            </div>
            <div>
              <label className="mb-1.5 block text-[12.5px] text-ink-faint">모드</label>
              <ModeSegmented modes={FALLBACK_ANALYSIS_MODES} value={alertMode} onChange={setAlertMode} ariaLabel="알림 모드" />
            </div>
            <div className="min-w-[220px]">
              <label htmlFor="condition-type" className="mb-1.5 block text-[12.5px] text-ink-faint">조건</label>
              <select
                id="condition-type"
                value={conditionType}
                onChange={(e) => setConditionType(e.target.value)}
                className="w-full rounded-md border border-border bg-bg-raised px-3 py-2.5 text-[13px] text-ink focus:border-amber-dim focus:outline-none"
              >
                {Object.entries(CONDITION_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="w-32">
              <label htmlFor="condition-value" className="mb-1.5 block text-[12.5px] text-ink-faint">값</label>
              <input
                id="condition-value"
                type="number"
                step="any"
                value={conditionValue}
                onChange={(e) => setConditionValue(e.target.value)}
                className="w-full rounded-md border border-border bg-bg-raised px-3 py-2.5 font-mono text-sm text-ink focus:border-amber-dim focus:outline-none"
                placeholder="예: 200"
              />
            </div>
            <button
              type="submit"
              disabled={creatingAlert || !alertTicker.trim() || conditionValue === ""}
              className="rounded-md bg-amber px-5 py-2.5 font-semibold text-[#1A1000] transition-opacity disabled:opacity-40"
            >
              {creatingAlert ? "생성 중..." : "알림 만들기"}
            </button>
          </form>
        </Card>

        {alertsError && <ErrorMessage>{alertsError}</ErrorMessage>}
        {alerts.length === 0 && !alertsError && <Hint>등록된 알림 조건이 없습니다.</Hint>}

        <div className="space-y-2">
          {alerts.map((alert) => (
            <Card key={alert.id} className="flex flex-wrap items-center justify-between gap-3 !p-4">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-semibold">{alert.ticker}</span>
                <span className="text-[12.5px] text-ink-dim">
                  {CONDITION_LABELS[alert.condition_type]} <strong>{alert.condition_value}</strong>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleToggleAlert(alert)}
                  className={`rounded-md border px-3 py-1.5 text-[12.5px] transition-colors ${
                    alert.is_active ? "border-up/40 text-up" : "border-border text-ink-faint"
                  }`}
                >
                  {alert.is_active ? "활성" : "비활성"}
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteAlert(alert.id)}
                  className="rounded-md border border-border px-3 py-1.5 text-[12.5px] text-ink-dim transition-colors hover:text-down"
                >
                  삭제
                </button>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* 알림함 */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold tracking-tight">
          알림함 {unreadCount > 0 && <span className="ml-1 rounded-full bg-amber px-2 py-0.5 text-[11px] font-mono text-[#1A1000]">{unreadCount}</span>}
        </h2>
        {eventsError && <ErrorMessage>{eventsError}</ErrorMessage>}
        {events.length === 0 && !eventsError && <Hint>아직 도착한 알림이 없습니다. 15분마다 조건을 확인합니다.</Hint>}
        <div className="space-y-2">
          {events.map((event) => (
            <Card
              key={event.id}
              className={`flex items-center justify-between gap-3 !p-4 ${event.is_read ? "opacity-60" : ""}`}
            >
              <span className="text-[13px]">{event.message}</span>
              {!event.is_read && (
                <button
                  type="button"
                  onClick={() => handleMarkRead(event.id)}
                  className="shrink-0 rounded-md border border-border px-3 py-1.5 text-[12.5px] text-ink-dim transition-colors hover:text-ink"
                >
                  읽음
                </button>
              )}
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
