"""Unit tests for Pydantic schemas."""

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).parent.parent.parent / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError

from app.schemas.auth import EmailUpdate, PasswordChange, RefreshTokenRequest, UserCreate, UserLogin


class TestUserCreate:
    """Tests for UserCreate schema validation."""

    def test_valid_user(self):
        user = UserCreate(username="testuser", email="test@example.com", password="password123")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "viewer"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", email="test@example.com", password="password123")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            UserCreate(username="a" * 51, email="test@example.com", password="password123")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(username="testuser", email="not-an-email", password="password123")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="testuser", email="test@example.com", password="short")

    def test_custom_role(self):
        user = UserCreate(username="testuser", email="test@example.com", password="password123", role="admin")
        assert user.role == "admin"


class TestUserLogin:
    """Tests for UserLogin schema."""

    def test_valid_login(self):
        login = UserLogin(username="admin", password="password")
        assert login.username == "admin"

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            UserLogin(username="admin")


class TestPasswordChange:
    """Tests for PasswordChange schema."""

    def test_valid_change(self):
        change = PasswordChange(current_password="old", new_password="newpassword123")
        assert change.new_password == "newpassword123"

    def test_new_password_too_short(self):
        with pytest.raises(ValidationError):
            PasswordChange(current_password="old", new_password="short")


class TestEmailUpdate:
    """Tests for EmailUpdate schema."""

    def test_valid_email(self):
        update = EmailUpdate(email="new@example.com")
        assert update.email == "new@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            EmailUpdate(email="not-valid")

    def test_empty_email(self):
        with pytest.raises(ValidationError):
            EmailUpdate(email="")


class TestRefreshTokenRequest:
    """Tests for RefreshTokenRequest schema."""

    def test_valid_request(self):
        req = RefreshTokenRequest(refresh_token="some.jwt.token")
        assert req.refresh_token == "some.jwt.token"

    def test_missing_token(self):
        with pytest.raises(ValidationError):
            RefreshTokenRequest()
