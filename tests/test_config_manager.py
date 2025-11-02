"""Tests for configuration manager to ensure secure overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pytest
from cryptography.fernet import Fernet

from src.core.config_manager import ConfigManager


@pytest.fixture()
def config_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary configuration directory with encryption key."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    base_config: Dict[str, object] = {
        "trading": {
            "symbol": "TESTUSDT",
            "capital": 5000.0,
            "max_position_pct": 0.02,
            "testnet": True,
            "exchanges": {"binance": {"api_key": "placeholder", "api_secret": "placeholder"}},
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "user": "bot",
            "password": "local",
            "database": "trading",
        },
    }

    prod_override = {"trading": {"capital": 10_000.0, "testnet": False}}

    (config_dir / "config.yaml").write_text(yaml_dump(base_config))
    (config_dir / "production.yaml").write_text(yaml_dump(prod_override))

    key_path = tmp_path / ".secret.key"
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    monkeypatch.chdir(tmp_path)

    return config_dir


def yaml_dump(data: Dict[str, object]) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=False)


def test_environment_overrides_and_dataclasses(
    config_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BINANCE_API_KEY", "override-key")

    manager = ConfigManager(config_path=str(config_directory / "config.yaml"), env="production")

    trading_config = manager.get_trading_config()
    assert trading_config.capital == 10_000.0
    assert manager.is_production() is True
    assert manager.is_testnet() is False

    exchange_config = manager.get_exchange_config("binance")
    assert exchange_config.api_key == "override-key"

    encrypted = manager.encrypt_value("secret")
    assert manager.decrypt_value(encrypted) == "secret"


def test_get_method_with_default(config_directory: Path) -> None:
    manager = ConfigManager(config_path=str(config_directory / "config.yaml"))
    assert manager.get("nonexistent.value", default="fallback") == "fallback"
