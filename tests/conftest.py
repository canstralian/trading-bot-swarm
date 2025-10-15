"""
Test configuration and fixtures for pytest.
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def test_config():
    """Provide a test configuration."""
    return {
        "environment": "testing",
        "database": {
            "sqlite": {"path": ":memory:"},
            "type": "sqlite",
        },
        "trading": {
            "capital": 1000.0,
            "max_position_size": 0.1,
            "enable_real_trading": False,
        },
        "logging": {
            "level": "DEBUG",
            "directory": "logs",
        },
    }


@pytest.fixture
def mock_database_config():
    """Provide a mock database configuration."""
    from src.core.config_manager import DatabaseConfig

    return DatabaseConfig(
        host="localhost",
        port=5432,
        database=":memory:",
        user="test",
        password="test",
    )
