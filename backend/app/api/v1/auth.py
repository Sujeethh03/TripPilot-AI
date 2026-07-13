"""Authentication endpoints (PROJECT_PLAN §11)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.core.google_oauth import verify_google_token
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: SessionDep) -> UserResponse:
    repo = UserRepository(session)
    if await repo.get_by_email(body.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await repo.create(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
    )
    await session.commit()
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: SessionDep) -> TokenResponse:
    user = await UserRepository(session).get_by_email(body.email)
    if user is None or user.hashed_password is None:
        raise _invalid_credentials()
    if not verify_password(body.password, user.hashed_password):
        raise _invalid_credentials()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/auth/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest, session: SessionDep) -> TokenResponse:
    identity = verify_google_token(body.id_token)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token"
        )

    repo = UserRepository(session)
    user = await repo.get_by_google_id(identity.google_id)
    if user is None:
        # Link Google to an existing email account, or create a new one.
        user = await repo.get_by_email(identity.email)
        if user is not None:
            user.google_id = identity.google_id
        else:
            user = await repo.create_google(
                email=identity.email, google_id=identity.google_id, name=identity.name
            )
    await session.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name)


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
    )
