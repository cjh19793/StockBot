"""관심종목 CRUD. Supabase Auth로 로그인한 사용자 소유 데이터만 다룬다.

기존 분석 로직(engine.run_analysis)은 건드리지 않는다 — 여기서는 티커 목록만 저장하고,
실제 분석 결과는 프론트가 기존 /api/analyze 를 그대로 호출해서 채운다(응답 중복/캐시
불일치를 피하기 위해 이 라우터에서 분석 결과를 함께 내려주지 않는다).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from config import MODE_CONFIG
from validation import is_valid_ticker, resolve_mode
from webapi import schemas
from webapi.auth import CurrentUser, get_current_user
from webapi.db import get_db
from webapi.db_models import WatchlistItem

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


def _resolve_mode_param(raw: str | None) -> str:
    if not raw:
        return "기본"
    canon = resolve_mode(raw.strip().upper(), MODE_CONFIG)
    if canon is None:
        raise HTTPException(status_code=422, detail=f"지원하지 않는 모드: {raw!r}")
    return canon


@router.get("", response_model=list[schemas.WatchlistItemResponse])
def list_watchlist(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user.user_id)
        .order_by(WatchlistItem.created_at)
    )
    return db.scalars(stmt).all()


@router.post("", response_model=schemas.WatchlistItemResponse, status_code=201)
def add_watchlist_item(
    body: schemas.WatchlistItemCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticker = body.ticker.strip().upper()
    if not is_valid_ticker(ticker):
        raise HTTPException(status_code=422, detail=f"올바르지 않은 티커 형식: {body.ticker!r}")
    mode = _resolve_mode_param(body.mode)

    existing = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.user_id,
            WatchlistItem.ticker == ticker,
            WatchlistItem.mode == mode,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="이미 관심종목에 있습니다.")

    item = WatchlistItem(user_id=user.user_id, ticker=ticker, mode=mode)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def remove_watchlist_item(
    item_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.id == item_id, WatchlistItem.user_id == user.user_id
        )
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="관심종목을 찾을 수 없습니다.")
