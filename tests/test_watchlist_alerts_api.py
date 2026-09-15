"""watchlist/alerts API 테스트.

실제 Supabase Postgres 대신 SQLite 인메모리 DB(webapi.db_models 의 테이블 정의를 그대로
create_all)를 쓰고, 인증(get_current_user)은 고정된 사용자로 오버라이드한다 — DB 비밀번호
없이도 라우팅/권한 분리(사용자별 행 격리)/검증 로직을 그대로 검증할 수 있다.

실행: python tests/test_watchlist_alerts_api.py   (pytest 도 가능)
"""
import os
import sys
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from webapi import alerts_routes  # noqa: E402
from webapi.auth import CurrentUser, get_current_user  # noqa: E402
from webapi.db import Base, get_db  # noqa: E402
from webapi.main import app  # noqa: E402

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"

_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
_TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


_current_user_id = USER_A


def _override_get_current_user():
    return CurrentUser(user_id=_current_user_id, email="test@example.com")


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_current_user] = _override_get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture(autouse=True)
def _default_user():
    global _current_user_id
    _current_user_id = USER_A
    yield
    _current_user_id = USER_A


def _as_user(user_id):
    global _current_user_id
    _current_user_id = user_id


# --- watchlist ---

def test_watchlist_empty_by_default():
    r = client.get("/api/watchlist")
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_watchlist_add_and_list():
    r = client.post("/api/watchlist", json={"ticker": "aapl"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ticker"] == "AAPL"
    assert body["mode"] == "기본"

    r = client.get("/api/watchlist")
    assert len(r.json()) == 1


def test_watchlist_add_invalid_ticker():
    r = client.post("/api/watchlist", json={"ticker": "not a ticker!!"})
    assert r.status_code == 422, r.text


def test_watchlist_add_invalid_mode():
    r = client.post("/api/watchlist", json={"ticker": "AAPL", "mode": "존재안함"})
    assert r.status_code == 422, r.text


def test_watchlist_duplicate_rejected():
    r1 = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert r1.status_code == 201, r1.text
    r2 = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert r2.status_code == 409, r2.text


def test_watchlist_delete():
    added = client.post("/api/watchlist", json={"ticker": "MSFT"}).json()
    r = client.delete(f"/api/watchlist/{added['id']}")
    assert r.status_code == 204, r.text
    assert client.get("/api/watchlist").json() == []


def test_watchlist_delete_not_found():
    r = client.delete("/api/watchlist/does-not-exist")
    assert r.status_code == 404, r.text


def test_watchlist_isolated_per_user():
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    _as_user(USER_B)
    assert client.get("/api/watchlist").json() == []
    client.post("/api/watchlist", json={"ticker": "GOOGL"})
    assert len(client.get("/api/watchlist").json()) == 1
    _as_user(USER_A)
    body = client.get("/api/watchlist").json()
    assert len(body) == 1 and body[0]["ticker"] == "AAPL"


def test_watchlist_requires_auth():
    del app.dependency_overrides[get_current_user]
    try:
        r = client.get("/api/watchlist")
        assert r.status_code == 401, r.text
    finally:
        app.dependency_overrides[get_current_user] = _override_get_current_user


def test_watchlist_user_a_cannot_delete_user_b_item():
    item = client.post("/api/watchlist", json={"ticker": "AAPL"}).json()
    _as_user(USER_B)
    r = client.delete(f"/api/watchlist/{item['id']}")
    assert r.status_code == 404, r.text  # 존재를 드러내지 않고 그냥 404


# --- alerts ---

def test_alert_create_and_list():
    r = client.post(
        "/api/alerts",
        json={"ticker": "aapl", "condition_type": "price_above", "condition_value": 200},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ticker"] == "AAPL"
    assert body["is_active"] is True
    assert body["last_triggered_at"] is None

    r = client.get("/api/alerts")
    assert len(r.json()) == 1


def test_alert_invalid_condition_type():
    r = client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "nonsense", "condition_value": 1},
    )
    assert r.status_code == 422, r.text


def test_alert_update_toggle_and_value():
    alert = client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "price_above", "condition_value": 200},
    ).json()
    r = client.patch(f"/api/alerts/{alert['id']}", json={"is_active": False, "condition_value": 250})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_active"] is False
    assert body["condition_value"] == 250


def test_alert_delete():
    alert = client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "price_above", "condition_value": 200},
    ).json()
    r = client.delete(f"/api/alerts/{alert['id']}")
    assert r.status_code == 204, r.text
    assert client.get("/api/alerts").json() == []


def test_alert_isolated_per_user():
    client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "price_above", "condition_value": 200},
    )
    _as_user(USER_B)
    assert client.get("/api/alerts").json() == []


# --- alert events (인앱 알림함) ---

def test_alert_events_empty_by_default():
    r = client.get("/api/alerts/events")
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_alert_events_mark_read():
    alert = client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "price_above", "condition_value": 1},
    ).json()

    fake_result = SimpleNamespace(price=999.0, buy_score=9, sell_score=0)
    with mock.patch.object(alerts_routes, "INTERNAL_ALERT_SECRET", "test-secret"):
        with mock.patch.object(alerts_routes, "run_analysis", lambda t, m: fake_result):
            r = client.post(
                "/api/internal/alerts/check", headers={"X-Internal-Secret": "test-secret"}
            )
    assert r.status_code == 200, r.text
    assert r.json() == {"checked": 1, "triggered": 1}

    events = client.get("/api/alerts/events").json()
    assert len(events) == 1
    assert events[0]["is_read"] is False
    assert events[0]["alert_id"] == alert["id"]

    r = client.post(f"/api/alerts/events/{events[0]['id']}/read")
    assert r.status_code == 200, r.text
    assert r.json()["is_read"] is True

    unread = client.get("/api/alerts/events", params={"unread_only": True}).json()
    assert unread == []


# --- 내부 체크 엔드포인트 ---

def test_internal_check_requires_secret():
    r = client.post("/api/internal/alerts/check")
    assert r.status_code == 403, r.text

    with mock.patch.object(alerts_routes, "INTERNAL_ALERT_SECRET", "test-secret"):
        r = client.post("/api/internal/alerts/check", headers={"X-Internal-Secret": "wrong"})
        assert r.status_code == 403, r.text


def test_internal_check_no_active_alerts():
    with mock.patch.object(alerts_routes, "INTERNAL_ALERT_SECRET", "test-secret"):
        r = client.post("/api/internal/alerts/check", headers={"X-Internal-Secret": "test-secret"})
    assert r.status_code == 200, r.text
    assert r.json() == {"checked": 0, "triggered": 0}


def test_internal_check_condition_not_met_creates_no_event():
    client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "price_above", "condition_value": 500},
    )
    fake_result = SimpleNamespace(price=100.0, buy_score=1, sell_score=1)
    with mock.patch.object(alerts_routes, "INTERNAL_ALERT_SECRET", "test-secret"):
        with mock.patch.object(alerts_routes, "run_analysis", lambda t, m: fake_result):
            r = client.post(
                "/api/internal/alerts/check", headers={"X-Internal-Secret": "test-secret"}
            )
    assert r.json() == {"checked": 1, "triggered": 0}
    assert client.get("/api/alerts/events").json() == []


def test_internal_check_inactive_alert_skipped():
    alert = client.post(
        "/api/alerts",
        json={"ticker": "AAPL", "condition_type": "price_above", "condition_value": 1},
    ).json()
    client.patch(f"/api/alerts/{alert['id']}", json={"is_active": False})

    with mock.patch.object(alerts_routes, "INTERNAL_ALERT_SECRET", "test-secret"):
        r = client.post("/api/internal/alerts/check", headers={"X-Internal-Secret": "test-secret"})
    assert r.json() == {"checked": 0, "triggered": 0}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
