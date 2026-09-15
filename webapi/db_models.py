"""watchlist/alerts 테이블의 SQLAlchemy 모델.

실제 DDL(제약조건/RLS 정책)은 이 파일이 아니라 `db/schema.sql` 이 정본이다 — 이 클래스들은
그 테이블에 대한 SELECT/INSERT/UPDATE/DELETE 매핑용이라 `metadata.create_all()` 을 운영 DB에
호출하지 않는다(테스트에서 SQLite에 대해서만 사용). auth.users 는 Supabase Auth가 관리하므로
여기서는 참조하지 않고 user_id 를 평범한 문자열 컬럼으로만 둔다.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

from webapi.db import Base


class GUID(TypeDecorator):
    """schema.sql의 실제 uuid 컬럼과 SQLite(테스트) 양쪽에서 항상 str로 다루기 위한 타입.

    psycopg2는 Postgres `uuid` 컬럼을 읽을 때 자동으로 uuid.UUID 객체로 변환해버려서,
    String(36)으로만 선언하면 응답 스키마(Pydantic `str` 필드) 직렬화가 깨진다
    (실제 Supabase 연동 테스트에서 발견). 항상 str로 정규화해 그 문제를 원천 차단한다.
    """

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else str(value)


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    """auth.users 1:1 부가 정보. 텔레그램 알림 연동(향후) 을 위한 telegram_chat_id 포함."""

    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(GUID(), primary_key=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", "mode", name="uq_watchlist_user_ticker_mode"),
    )

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(GUID(), index=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(8), nullable=False, default="기본")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(GUID(), index=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(8), nullable=False, default="기본")
    condition_type: Mapped[str] = mapped_column(String(32), nullable=False)
    condition_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AlertEvent(Base):
    """트리거된 알림 — MVP 알림 방식은 인앱 알림함(이 테이블을 프론트가 폴링)."""

    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    alert_id: Mapped[str] = mapped_column(GUID(), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(GUID(), index=True, nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
