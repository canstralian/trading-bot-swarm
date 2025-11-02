"""
Trading strategies for the bot swarm.
"""

from .base_strategy import BaseStrategy, StrategySignal, SignalType
from .trend_following import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy

__all__ = [
    'BaseStrategy',
    'StrategySignal',
    'SignalType',
    'TrendFollowingStrategy',
    'MeanReversionStrategy',
    'MomentumStrategy'
]
