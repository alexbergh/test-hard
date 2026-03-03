"""Authentication endpoints."""

from app.api.deps import CurrentUser, DbSession
from app.schemas import EmailUpdate, PasswordChange, RefreshTokenRequest, Token, UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService
from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate, session: DbSession) -> UserResponse:
    """Register a new user."""
    auth_service = AuthService(session)

    # Check if username exists
    existing = await auth_service.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    existing = await auth_service.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await auth_service.create_user(user_data)

    from app.metrics import auth_register_total
    auth_register_total.labels(result="success").inc()

    from app.services.audit import _extract_request_info, log_action
    ri = _extract_request_info(request)
    await log_action(session, "user_registered", user_id=user.id, username=user.username,
                     resource_type="user", resource_id=str(user.id), **ri)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin, session: DbSession) -> Token:
    """Authenticate user and return JWT token."""
    auth_service = AuthService(session)

    from app.metrics import auth_login_total

    user = await auth_service.authenticate_user(credentials.username, credentials.password)
    if not user:
        auth_login_total.labels(result="failed").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        auth_login_total.labels(result="inactive").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    auth_login_total.labels(result="success").inc()

    from app.services.audit import _extract_request_info, log_action
    ri = _extract_request_info(request)
    await log_action(session, "user_login", user_id=user.id, username=user.username,
                     resource_type="user", resource_id=str(user.id), **ri)

    return auth_service.create_token_for_user(user)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh_token(request: Request, data: RefreshTokenRequest, session: DbSession) -> Token:
    """Get new access token using a refresh token."""
    auth_service = AuthService(session)
    token_data = auth_service.decode_token(data.refresh_token, expected_type="refresh")
    if not token_data or not token_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_username(token_data.username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return auth_service.create_token_for_user(user)


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    session: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Change current user's password."""
    auth_service = AuthService(session)
    success = await auth_service.change_password(current_user, data.current_password, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    from app.services.audit import log_action
    await log_action(session, "password_changed", user_id=current_user.id, username=current_user.username,
                     resource_type="user", resource_id=str(current_user.id))

    return {"message": "Password changed successfully"}


@router.patch("/me/email")
async def update_email(
    data: EmailUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Update current user's email."""
    from app.models import User
    from sqlalchemy import select

    new_email = data.email

    # Check if email is already taken by another user
    result = await session.execute(select(User).where(User.email == new_email, User.id != current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use",
        )

    current_user.email = new_email
    await session.flush()
    await session.refresh(current_user)
    return {"message": "Email updated successfully", "email": current_user.email}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)
