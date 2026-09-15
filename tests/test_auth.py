"""webapi/auth.py (Supabase JWT 검증) 단위 테스트.

실제 Supabase 프로젝트/네트워크 없이 검증한다 — 로컬에서 만든 ES256 키쌍으로 토큰을
서명하고, PyJWKClient(네트워크로 JWKS 조회하는 부분)만 목킹해서 그 공개키를 돌려준다.
"""
import datetime
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import jwt  # noqa: E402
import pytest  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials  # noqa: E402

from webapi import auth as auth_module  # noqa: E402

_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
_PUBLIC_KEY = _PRIVATE_KEY.public_key()
_OTHER_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())  # 서명자가 다른 토큰용


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


@pytest.fixture(autouse=True)
def _patch_jwks_client(monkeypatch):
    fake_client = mock.Mock()
    fake_client.get_signing_key_from_jwt.return_value = _FakeSigningKey(_PUBLIC_KEY)
    monkeypatch.setattr(auth_module, "_jwks_client", fake_client)
    yield


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_token(
    sub="user-123",
    email="user@example.com",
    exp_delta=datetime.timedelta(hours=1),
    audience="authenticated",
    issuer=None,
    key=_PRIVATE_KEY,
    algorithm="ES256",
    include_sub=True,
):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "email": email,
        "aud": audience,
        "iss": issuer or f"{auth_module.SUPABASE_URL}/auth/v1",
        "iat": now,
        "exp": now + exp_delta,
    }
    if include_sub:
        payload["sub"] = sub
    return jwt.encode(payload, key, algorithm=algorithm)


def test_valid_token_returns_current_user():
    token = _make_token(sub="user-123", email="a@b.com")
    user = auth_module.get_current_user(_credentials(token))
    assert user.user_id == "user-123"
    assert user.email == "a@b.com"


def test_missing_credentials_raises_401():
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(None)
    assert exc.value.status_code == 401


def test_expired_token_raises_401():
    token = _make_token(exp_delta=datetime.timedelta(seconds=-10))
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(_credentials(token))
    assert exc.value.status_code == 401


def test_wrong_audience_raises_401():
    token = _make_token(audience="not-authenticated")
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(_credentials(token))
    assert exc.value.status_code == 401


def test_wrong_issuer_raises_401():
    token = _make_token(issuer="https://not-our-project.supabase.co/auth/v1")
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(_credentials(token))
    assert exc.value.status_code == 401


def test_missing_sub_raises_401():
    token = _make_token(include_sub=False)
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(_credentials(token))
    assert exc.value.status_code == 401


def test_signature_from_wrong_key_raises_401():
    # JWKS가 돌려주는 공개키(_PUBLIC_KEY)와 실제 서명 키가 다른 경우 — 탈취/위조 토큰 시나리오.
    token = _make_token(key=_OTHER_PRIVATE_KEY)
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(_credentials(token))
    assert exc.value.status_code == 401


def test_jwks_not_configured_raises_503(monkeypatch):
    monkeypatch.setattr(auth_module, "_jwks_client", None)
    token = _make_token()
    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user(_credentials(token))
    assert exc.value.status_code == 503


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
