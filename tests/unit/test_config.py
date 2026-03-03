"""Unit tests for application configuration."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND_ROOT = Path(__file__).parent.parent.parent / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))


class TestSettings:
    """Tests for Settings validation."""

    def test_dev_auto_generates_secret_key(self):
        from app.config import Settings

        with patch.dict(os.environ, {"ENVIRONMENT": "development", "SECRET_KEY": ""}, clear=False):
            settings = Settings(environment="development", secret_key="")
            assert settings.secret_key != ""
            assert len(settings.secret_key) == 64  # hex(32) = 64 chars

    def test_production_requires_secret_key(self):
        from app.config import Settings

        with pytest.raises(ValueError, match="SECRET_KEY must be set in production"):
            Settings(environment="production", secret_key="")

    def test_production_accepts_explicit_secret_key(self):
        from app.config import Settings

        settings = Settings(environment="production", secret_key="my-production-key-here")
        assert settings.secret_key == "my-production-key-here"

    def test_default_cors_origins(self):
        from app.config import Settings

        settings = Settings(secret_key="test")
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:5173" in settings.cors_origins

    def test_default_refresh_token_days(self):
        from app.config import Settings

        settings = Settings(secret_key="test")
        assert settings.refresh_token_expire_days == 7

    def test_admin_default_password_empty_by_default(self):
        from app.config import Settings

        settings = Settings(secret_key="test")
        assert settings.admin_default_password == ""
