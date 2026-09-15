"""Supabase Postgres 연결 (SQLAlchemy).

SUPABASE_DB_* 환경변수가 없으면(로컬 최초 설정 전 등) engine을 만들지 않고 get_db() 가
503을 던진다 — 기존 분석 API(/api/analyze 등)와 텔레그램 봇은 DB 없이도 그대로 동작해야
하므로 여기서 앱 전체를 죽이지 않는다.
"""
import logging
from collections.abc import Generator

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import (
    SUPABASE_DB_HOST,
    SUPABASE_DB_NAME,
    SUPABASE_DB_PASSWORD,
    SUPABASE_DB_PORT,
    SUPABASE_DB_USER,
)

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _build_engine() -> Engine | None:
    if not (SUPABASE_DB_HOST and SUPABASE_DB_USER and SUPABASE_DB_PASSWORD):
        log.warning(
            "SUPABASE_DB_HOST/USER/PASSWORD 미설정 — watchlist/alerts DB 기능 비활성화 "
            "(기존 분석 API/텔레그램 봇 동작에는 영향 없음)"
        )
        return None
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=SUPABASE_DB_USER,
        password=SUPABASE_DB_PASSWORD,
        host=SUPABASE_DB_HOST,
        port=SUPABASE_DB_PORT,
        database=SUPABASE_DB_NAME,
    )
    # Supabase Free(Nano) + Render Free 조합을 고려해 커넥션 수를 작게 유지.
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=0)


engine = _build_engine()
SessionLocal = (
    sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine is not None else None
)


def is_db_configured() -> bool:
    return engine is not None


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="DB가 설정되지 않았습니다 (관리자 문의).")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
