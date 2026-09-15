"""Supabase 발급 JWT 검증.

이 Supabase 프로젝트는 비대칭 서명(ES256, "JWT Signing Keys")을 쓰므로 공유 시크릿을
저장할 필요가 없다 — JWKS 엔드포인트의 공개키로 서명만 검증한다(PyJWKClient가 JWKS
응답을 캐싱해 매 요청마다 네트워크를 타지 않는다). 로그인/가입 자체는 프론트(supabase-js)가
Supabase와 직접 처리하고, FastAPI는 그 결과로 발급된 access_token만 검증한다.
"""
import logging

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import SUPABASE_JWKS_URL, SUPABASE_URL

log = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)
_jwks_client = jwt.PyJWKClient(SUPABASE_JWKS_URL) if SUPABASE_JWKS_URL else None


class CurrentUser:
    """검증된 토큰에서 뽑아낸 사용자 식별 정보."""

    def __init__(self, user_id: str, email: str | None):
        self.user_id = user_id
        self.email = email


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    if _jwks_client is None:
        raise HTTPException(status_code=503, detail="인증이 설정되지 않았습니다 (관리자 문의).")

    token = credentials.credentials
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],
            audience="authenticated",
            issuer=f"{SUPABASE_URL}/auth/v1",
        )
    except jwt.PyJWTError as exc:
        log.info("JWT 검증 실패: %s", exc)
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰입니다.") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return CurrentUser(user_id=user_id, email=payload.get("email"))
