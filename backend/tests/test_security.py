"""Unit tests for security primitives (no DB)."""

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_password_handles_bad_hash() -> None:
    assert verify_password("x", "not-a-bcrypt-hash") is False


def test_access_token_roundtrip() -> None:
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_decode_rejects_garbage() -> None:
    assert decode_access_token("not.a.jwt") is None
