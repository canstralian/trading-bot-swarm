"""
Basic environment configuration tests.
"""
import os
import pytest
from pathlib import Path


def test_environment_files_exist():
    """Test that environment configuration files exist."""
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"

    # Check for environment files
    assert (config_dir / ".env.template").exists(), ".env.template should exist"
    assert (config_dir / ".env.development").exists(), ".env.development should exist"
    assert (config_dir / ".env.staging").exists(), ".env.staging should exist"


def test_development_env_has_required_keys():
    """Test that development environment file has required configuration keys."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / ".env.development"

    with open(env_file, "r") as f:
        content = f.read()

    # Required keys for development environment
    required_keys = [
        "ENVIRONMENT",
        "DATABASE_TYPE",
        "DEBUG",
        "LOG_LEVEL",
        "ENABLE_REAL_TRADING",
    ]

    for key in required_keys:
        assert key in content, f"{key} should be in .env.development"


def test_staging_env_has_required_keys():
    """Test that staging environment file has required configuration keys."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / ".env.staging"

    with open(env_file, "r") as f:
        content = f.read()

    # Required keys for staging environment
    required_keys = [
        "ENVIRONMENT",
        "DATABASE_TYPE",
        "DEBUG",
        "LOG_LEVEL",
        "GUNICORN_WORKERS",
        "SENTRY_DSN",
    ]

    for key in required_keys:
        assert key in content, f"{key} should be in .env.staging"


def test_development_uses_sqlite():
    """Test that development environment is configured to use SQLite."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / ".env.development"

    with open(env_file, "r") as f:
        content = f.read()

    assert "DATABASE_TYPE=sqlite" in content, "Development should use SQLite"


def test_staging_uses_postgresql():
    """Test that staging environment is configured to use PostgreSQL."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / ".env.staging"

    with open(env_file, "r") as f:
        content = f.read()

    assert (
        "DATABASE_TYPE=postgresql" in content
    ), "Staging should use PostgreSQL"


def test_development_has_debug_enabled():
    """Test that development environment has debug mode enabled."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / ".env.development"

    with open(env_file, "r") as f:
        content = f.read()

    assert "DEBUG=true" in content, "Development should have DEBUG enabled"


def test_staging_has_debug_disabled():
    """Test that staging environment has debug mode disabled."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / "config" / ".env.staging"

    with open(env_file, "r") as f:
        content = f.read()

    assert "DEBUG=false" in content, "Staging should have DEBUG disabled"
