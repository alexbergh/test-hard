"""Authentication endpoints."""

from app.api.deps import CurrentUser, DbSession
from app.schemas import PasswordChange, Token, UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, session: DbSession) -> UserResponse:
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
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, session: DbSession) -> Token:
    """Authenticate user and return JWT token."""
    auth_service = AuthService(session)

    user = await auth_service.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
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
    return {"message": "Password changed successfully"}


@router.patch("/me/email")
async def update_email(
    data: dict,
    session: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Update current user's email."""
    from app.models import User
    from sqlalchemy import select

    new_email = data.get("email", "").strip()
    if not new_email or "@" not in new_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address",
        )

    # Check if email is already taken by another user
    result = await session.execute(
        select(User).where(User.email == new_email, User.id != current_user.id)
    )
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
