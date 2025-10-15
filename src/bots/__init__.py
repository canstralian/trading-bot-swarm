"""
Trading bot implementations.
"""

from .trend_bot import TrendFollowingBot
from .mean_reversion_bot import MeanReversionBot
from .momentum_bot import MomentumBot

__all__ = ['TrendFollowingBot', 'MeanReversionBot', 'MomentumBot']
