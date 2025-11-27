"""API dependencies."""

from typing import Annotated

from app.database import get_session
from app.models import User
from app.services.auth import AuthService
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    token_data = AuthService.decode_token(token)

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(token_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    return current_user


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user if they are an admin."""
    if current_user.role != "admin" and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_operator_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user if they are an operator or admin."""
    if current_user.role not in ("operator", "admin") and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator privileges required",
        )
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
OperatorUser = Annotated[User, Depends(get_operator_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
