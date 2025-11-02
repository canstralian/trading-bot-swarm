"""
Core module initialization for the trading bot swarm.
"""

from .config_manager import ConfigManager
from .market_data import MarketDataHandler
from .trading_engine import TradingEngine
from .strategy_interface import StrategyInterface
from .risk_manager import RiskManager

__all__ = [
    "ConfigManager",
    "MarketDataHandler",
    "TradingEngine",
    "StrategyInterface",
    "RiskManager",
]

__version__ = "1.0.0"
