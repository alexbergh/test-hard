"""User management endpoints (admin only)."""

from app.api.deps import AdminUser, DbSession
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.services.auth import AuthService
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(session: DbSession, current_user: AdminUser) -> list[UserResponse]:
    """List all users (admin only)."""
    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: DbSession,
    current_user: AdminUser,
) -> UserResponse:
    """Create a new user (admin only)."""
    auth_service = AuthService(session)

    existing = await auth_service.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing = await auth_service.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    user = await auth_service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: DbSession,
    current_user: AdminUser,
) -> None:
    """Delete a user (admin only). Cannot delete yourself."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.delete(user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: dict,
    session: DbSession,
    current_user: AdminUser,
) -> UserResponse:
    """Update user role (admin only)."""
    allowed_roles = {"admin", "user", "auditor"}
    new_role = role_data.get("role", "")
    if new_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed: {', '.join(sorted(allowed_roles))}",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.role = new_role
    await session.flush()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    session: DbSession,
    current_user: AdminUser,
) -> UserResponse:
    """Toggle user active status (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = not user.is_active
    await session.flush()
    await session.refresh(user)
    return UserResponse.model_validate(user)
