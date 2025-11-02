"""
Configuration Manager for the Trading Bot Swarm
Handles loading and managing configuration across different environments.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet


@dataclass
class TradingConfig:
    """Trading configuration parameters."""

    symbol: str
    capital: float
    max_position_pct: float
    min_volume_multiplier: float
    stop_loss_pct: float
    take_profit_pct: float


@dataclass
class ExchangeConfig:
    """Exchange API configuration."""

    name: str
    api_key: str
    api_secret: str
    testnet: bool
    enabled: bool


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str
    port: int
    user: str
    password: str
    database: str


class ConfigManager:
    """
    Centralized configuration management with encryption support.
    Loads from YAML files and environment variables.
    """

    def __init__(
        self, config_path: str = "config/config.yaml", env: str = "development"
    ):
        self.config_path = Path(config_path)
        self.env = env
        self.config: Dict[str, Any] = {}
        self._encryption_key: Optional[bytes] = None

        self._load_encryption_key()
        self._load_config()
        self._load_env_overrides()

    def _load_encryption_key(self):
        """Load encryption key for sensitive data."""
        key_path = Path(".secret.key")
        if key_path.exists():
            with open(key_path, "rb") as f:
                self._encryption_key = f.read().strip()

    def _load_config(self):
        """Load main configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Load environment-specific overrides
        env_config_path = self.config_path.parent / f"{self.env}.yaml"
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f)
                self._merge_config(self.config, env_config)

    def _load_env_overrides(self):
        """Load configuration from environment variables."""
        # Override sensitive values from environment
        env_mappings = {
            "BINANCE_API_KEY": ["trading", "exchanges", "binance", "api_key"],
            "BINANCE_API_SECRET": ["trading", "exchanges", "binance", "api_secret"],
            "MEXC_API_KEY": ["trading", "exchanges", "mexc", "api_key"],
            "MEXC_API_SECRET": ["trading", "exchanges", "mexc", "api_secret"],
            "DB_PASSWORD": ["database", "password"],
            "REDIS_PASSWORD": ["database", "redis", "password"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(self.config, config_path, value)

    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _set_nested_value(self, config: Dict, path: list, value: Any):
        """Set nested configuration value using path list."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        Example: get('trading.risk.max_position_size')
        """
        keys = path.split(".")
        current = self.config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def get_trading_config(self) -> TradingConfig:
        """Get trading configuration as dataclass."""
        trading = self.config.get("trading", {})
        return TradingConfig(
            symbol=trading.get("symbol", "NOICEUSDT"),
            capital=trading.get("capital", 10000.0),
            max_position_pct=trading.get("max_position_pct", 0.01),
            min_volume_multiplier=trading.get("min_volume_multiplier", 1.5),
            stop_loss_pct=trading.get("stop_loss_pct", 0.02),
            take_profit_pct=trading.get("take_profit_pct", 0.05),
        )

    def get_exchange_config(self, exchange_name: str) -> ExchangeConfig:
        """Get exchange configuration as dataclass."""
        exchanges = self.config.get("trading", {}).get("exchanges", {})
        exchange = exchanges.get(exchange_name, {})

        return ExchangeConfig(
            name=exchange_name,
            api_key=exchange.get("api_key", ""),
            api_secret=exchange.get("api_secret", ""),
            testnet=exchange.get("testnet", True),
            enabled=exchange.get("enabled", False),
        )

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration as dataclass."""
        db = self.config.get("database", {})
        return DatabaseConfig(
            host=db.get("host", "localhost"),
            port=db.get("port", 5432),
            user=db.get("user", "trading_bot"),
            password=db.get("password", ""),
            database=db.get("database", "trading_swarm"),
        )

    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration value."""
        if not self._encryption_key:
            raise ValueError("Encryption key not available")

        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value."""
        if not self._encryption_key:
            raise ValueError("Encryption key not available")

        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(encrypted_value.encode()).decode()

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    def is_testnet(self) -> bool:
        """Check if exchanges should use testnet."""
        return self.get("trading.testnet", True)
