"""알림(관심종목 조건) CRUD + 인앱 알림함 + 내부 체크 엔드포인트.

MVP 알림 전달 방식은 인앱 알림함(alert_events, 프론트가 폴링)만 — 텔레그램/이메일 발송은
추후 확장(Profile.telegram_chat_id 는 그 확장을 위해 이미 마련해둔 컬럼).

/api/internal/alerts/check 는 사용자 JWT가 아니라 공유 시크릿(INTERNAL_ALERT_SECRET)으로
보호한다. Render 무료 티어엔 백그라운드 워커/크론이 없어서, GitHub Actions 크론
(.github/workflows/alert-check.yml, 15분 주기)이 이 엔드포인트를 호출해 조건을 검사한다.
조건 검사는 기존 engine.run_analysis() 를 그대로 재사용 — 분석 로직은 전혀 건드리지 않는다.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import INTERNAL_ALERT_SECRET, MODE_CONFIG
from engine import run_analysis
from errors import AnalysisError
from models import AnalysisResult
from validation import is_valid_ticker, resolve_mode
from webapi import schemas
from webapi.auth import CurrentUser, get_current_user
from webapi.db import get_db
from webapi.db_models import Alert, AlertEvent

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["alerts"])
internal_router = APIRouter(prefix="/api/internal/alerts", tags=["internal"])

_CONDITION_TYPES = {"price_above", "price_below", "buy_score_above", "sell_score_above"}


def _resolve_mode_param(raw: str | None) -> str:
    if not raw:
        return "기본"
    canon = resolve_mode(raw.strip().upper(), MODE_CONFIG)
    if canon is None:
        raise HTTPException(status_code=422, detail=f"지원하지 않는 모드: {raw!r}")
    return canon


@router.get("", response_model=list[schemas.AlertResponse])
def list_alerts(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Alert).where(Alert.user_id == user.user_id).order_by(Alert.created_at)
    return db.scalars(stmt).all()


@router.post("", response_model=schemas.AlertResponse, status_code=201)
def create_alert(
    body: schemas.AlertCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticker = body.ticker.strip().upper()
    if not is_valid_ticker(ticker):
        raise HTTPException(status_code=422, detail=f"올바르지 않은 티커 형식: {body.ticker!r}")
    if body.condition_type not in _CONDITION_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"지원하지 않는 조건: {body.condition_type!r} (가능: {sorted(_CONDITION_TYPES)})",
        )
    mode = _resolve_mode_param(body.mode)

    alert = Alert(
        user_id=user.user_id,
        ticker=ticker,
        mode=mode,
        condition_type=body.condition_type,
        condition_value=body.condition_value,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=schemas.AlertResponse)
def update_alert(
    alert_id: str,
    body: schemas.AlertUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.user_id))
    if alert is None:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    if body.is_active is not None:
        alert.is_active = body.is_active
    if body.condition_value is not None:
        alert.condition_value = body.condition_value
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.user_id))
    if alert is None:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    db.delete(alert)
    db.commit()


@router.get("/events", response_model=list[schemas.AlertEventResponse])
def list_alert_events(
    unread_only: bool = False,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(AlertEvent).where(AlertEvent.user_id == user.user_id)
    if unread_only:
        stmt = stmt.where(AlertEvent.is_read.is_(False))
    stmt = stmt.order_by(AlertEvent.created_at.desc())
    return db.scalars(stmt).all()


@router.post("/events/{event_id}/read", response_model=schemas.AlertEventResponse)
def mark_alert_event_read(
    event_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.scalar(
        select(AlertEvent).where(AlertEvent.id == event_id, AlertEvent.user_id == user.user_id)
    )
    if event is None:
        raise HTTPException(status_code=404, detail="알림 이벤트를 찾을 수 없습니다.")
    event.is_read = True
    db.commit()
    db.refresh(event)
    return event


def _condition_met(condition_type: str, condition_value: float, result: AnalysisResult) -> bool:
    if condition_type == "price_above":
        return result.price >= condition_value
    if condition_type == "price_below":
        return result.price <= condition_value
    if condition_type == "buy_score_above":
        return result.buy_score >= condition_value
    if condition_type == "sell_score_above":
        return result.sell_score >= condition_value
    return False


def _check_one(alert: Alert) -> AlertEvent | None:
    """알림 하나를 평가. 분석 실패는 알림 미발생으로 처리(체크 자체는 계속 진행)."""
    try:
        result = run_analysis(alert.ticker, alert.mode)
    except AnalysisError:
        log.exception("알림 체크 중 분석 실패 (%s)", alert.ticker)
        return None

    if not _condition_met(alert.condition_type, alert.condition_value, result):
        return None

    return AlertEvent(
        alert_id=alert.id,
        user_id=alert.user_id,
        message=(
            f"{alert.ticker} {alert.condition_type} {alert.condition_value} 조건 충족 "
            f"(현재가 {result.price}, 매수 {result.buy_score}/매도 {result.sell_score})"
        ),
    )


def _verify_internal_secret(x_internal_secret: str | None = Header(None)) -> None:
    if not INTERNAL_ALERT_SECRET or x_internal_secret != INTERNAL_ALERT_SECRET:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")


@internal_router.post("/check", response_model=schemas.AlertCheckResponse)
def check_alerts(
    _: None = Depends(_verify_internal_secret),
    db: Session = Depends(get_db),
):
    """활성 알림을 전부 평가해 조건 충족 시 alert_events 를 만든다.

    GitHub Actions 크론이 15분마다 호출한다 (Render 무료 티어는 백그라운드
    워커/크론이 없어 외부 트리거가 필요).
    """
    active_alerts = list(db.scalars(select(Alert).where(Alert.is_active.is_(True))).all())
    if not active_alerts:
        return schemas.AlertCheckResponse(checked=0, triggered=0)

    with ThreadPoolExecutor(max_workers=min(len(active_alerts), 10)) as ex:
        events = list(ex.map(_check_one, active_alerts))

    now = datetime.now(timezone.utc)
    triggered = 0
    for alert, event in zip(active_alerts, events):
        if event is None:
            continue
        db.add(event)
        alert.last_triggered_at = now
        triggered += 1
    db.commit()

    return schemas.AlertCheckResponse(checked=len(active_alerts), triggered=triggered)
