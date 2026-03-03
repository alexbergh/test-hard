"""Unit tests for AuthService."""

import os
import sys
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set env vars BEFORE any app imports to satisfy module-level Settings/engine creation
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_auth.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")

# Add backend to path
BACKEND_ROOT = Path(__file__).parent.parent.parent / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

# Now safe to import - module-level engine creation will use sqlite URL
from app.services.auth import AuthService  # noqa: E402


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests."""
    settings = MagicMock()
    settings.secret_key = "test-secret-key-for-unit-tests-only"
    settings.algorithm = "HS256"
    settings.access_token_expire_minutes = 30
    settings.refresh_token_expire_days = 7
    settings.debug = False
    settings.environment = "development"
    with patch("app.services.auth.settings", settings):
        yield settings


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        from app.services.auth import AuthService

        hashed = AuthService.get_password_hash("testpassword123")
        assert hashed != "testpassword123"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        from app.services.auth import AuthService

        hashed = AuthService.get_password_hash("mypassword")
        assert AuthService.verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        from app.services.auth import AuthService

        hashed = AuthService.get_password_hash("mypassword")
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_hash_is_unique(self):
        from app.services.auth import AuthService

        hash1 = AuthService.get_password_hash("samepassword")
        hash2 = AuthService.get_password_hash("samepassword")
        assert hash1 != hash2  # bcrypt uses random salt


class TestAccessToken:
    """Tests for JWT access token creation and decoding."""

    def test_create_and_decode_access_token(self, mock_settings):
        from app.services.auth import AuthService

        data = {"sub": "testuser", "user_id": 1, "role": "admin"}
        token = AuthService.create_access_token(data)

        decoded = AuthService.decode_token(token, expected_type="access")
        assert decoded is not None
        assert decoded.username == "testuser"
        assert decoded.user_id == 1
        assert decoded.role == "admin"

    def test_decode_expired_token(self, mock_settings):
        from app.services.auth import AuthService

        data = {"sub": "testuser", "user_id": 1, "role": "viewer"}
        token = AuthService.create_access_token(data, expires_delta=timedelta(seconds=-1))

        decoded = AuthService.decode_token(token, expected_type="access")
        assert decoded is None

    def test_decode_invalid_token(self):
        from app.services.auth import AuthService

        decoded = AuthService.decode_token("invalid.token.string")
        assert decoded is None

    def test_decode_token_wrong_type(self, mock_settings):
        from app.services.auth import AuthService

        data = {"sub": "testuser", "user_id": 1, "role": "viewer"}
        token = AuthService.create_access_token(data)

        # Try to decode access token as refresh token
        decoded = AuthService.decode_token(token, expected_type="refresh")
        assert decoded is None

    def test_token_without_username_returns_none(self, mock_settings):
        from app.services.auth import AuthService

        data = {"user_id": 1, "role": "viewer"}  # no "sub"
        token = AuthService.create_access_token(data)

        decoded = AuthService.decode_token(token, expected_type="access")
        assert decoded is None


class TestRefreshToken:
    """Tests for refresh token creation and decoding."""

    def test_create_and_decode_refresh_token(self, mock_settings):
        from app.services.auth import AuthService

        data = {"sub": "testuser", "user_id": 1, "role": "admin"}
        token = AuthService.create_refresh_token(data)

        decoded = AuthService.decode_token(token, expected_type="refresh")
        assert decoded is not None
        assert decoded.username == "testuser"

    def test_refresh_token_not_valid_as_access(self, mock_settings):
        from app.services.auth import AuthService

        data = {"sub": "testuser", "user_id": 1, "role": "admin"}
        token = AuthService.create_refresh_token(data)

        decoded = AuthService.decode_token(token, expected_type="access")
        assert decoded is None


class TestTokenForUser:
    """Tests for create_token_for_user method."""

    def test_create_token_for_user(self, mock_settings):
        from app.services.auth import AuthService

        session = AsyncMock()
        service = AuthService(session)

        user = MagicMock()
        user.username = "admin"
        user.id = 1
        user.role = "admin"
        user.must_change_password = False

        token = service.create_token_for_user(user)
        assert token.access_token
        assert token.refresh_token
        assert token.token_type == "bearer"
        assert token.expires_in == 1800  # 30 min * 60
        assert token.must_change_password is False

    def test_must_change_password_flag(self, mock_settings):
        from app.services.auth import AuthService

        session = AsyncMock()
        service = AuthService(session)

        user = MagicMock()
        user.username = "newadmin"
        user.id = 2
        user.role = "admin"
        user.must_change_password = True

        token = service.create_token_for_user(user)
        assert token.must_change_password is True


class TestAuthenticateUser:
    """Tests for user authentication."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_authenticate_nonexistent_user(self, mock_settings):
        from app.services.auth import AuthService

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        service = AuthService(session)
        user = await service.authenticate_user("nonexistent", "password")
        assert user is None

    @pytest.mark.asyncio(loop_scope="function")
    async def test_authenticate_wrong_password(self, mock_settings):
        from app.services.auth import AuthService

        user_mock = MagicMock()
        user_mock.hashed_password = AuthService.get_password_hash("correctpassword")

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user_mock
        session.execute.return_value = result_mock

        service = AuthService(session)
        user = await service.authenticate_user("testuser", "wrongpassword")
        assert user is None

    @pytest.mark.asyncio(loop_scope="function")
    async def test_authenticate_success(self, mock_settings):
        from app.services.auth import AuthService

        user_mock = MagicMock()
        user_mock.hashed_password = AuthService.get_password_hash("correctpassword")

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user_mock
        session.execute.return_value = result_mock

        service = AuthService(session)
        user = await service.authenticate_user("testuser", "correctpassword")
        assert user is user_mock


class TestChangePassword:
    """Tests for password change."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_change_password_wrong_current(self, mock_settings):
        from app.services.auth import AuthService

        user_mock = MagicMock()
        user_mock.hashed_password = AuthService.get_password_hash("oldpassword")

        session = AsyncMock()
        service = AuthService(session)

        result = await service.change_password(user_mock, "wrongcurrent", "newpassword")
        assert result is False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_change_password_success(self, mock_settings):
        from app.services.auth import AuthService

        user_mock = MagicMock()
        user_mock.hashed_password = AuthService.get_password_hash("oldpassword")
        user_mock.must_change_password = True

        session = AsyncMock()
        service = AuthService(session)

        result = await service.change_password(user_mock, "oldpassword", "newpassword123")
        assert result is True
        assert user_mock.must_change_password is False
        assert user_mock.password_changed_at is not None
        # Verify new password is set and old one no longer works
        assert AuthService.verify_password("newpassword123", user_mock.hashed_password)
