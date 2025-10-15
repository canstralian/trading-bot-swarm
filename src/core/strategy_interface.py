"""
Strategy Interface and Base Classes
Defines the contract for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .market_data import OHLCVData


class SignalType(Enum):
    """Trading signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


class PositionSide(Enum):
    """Position side types."""

    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class TradingSignal:
    """
    Trading signal with all necessary information for execution.
    """

    signal_type: SignalType
    symbol: str
    price: float
    quantity: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    confidence: float  # 0.0 to 1.0
    reason: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary for storage/transmission."""
        return {
            "signal_type": self.signal_type.value,
            "symbol": self.symbol,
            "price": self.price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "confidence": self.confidence,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


@dataclass
class StrategyParameters:
    """Base parameters for trading strategies."""

    min_confidence: float = 0.7
    max_signals_per_hour: int = 5
    enable_short_selling: bool = False
    risk_reward_ratio: float = 2.0


class StrategyInterface(ABC):
    """
    Abstract base class for all trading strategies.
    Defines the contract that all strategies must implement.
    """

    def __init__(self, symbol: str, parameters: StrategyParameters):
        self.symbol = symbol
        self.parameters = parameters
        self.data_buffer: List[OHLCVData] = []
        self.signal_history: List[TradingSignal] = []
        self.name = self.__class__.__name__

    @abstractmethod
    def update(self, ohlcv: OHLCVData) -> Optional[TradingSignal]:
        """
        Process new market data and generate trading signal if conditions met.

        Args:
            ohlcv: Latest OHLCV data point

        Returns:
            TradingSignal if conditions met, None otherwise
        """
        pass

    @abstractmethod
    def get_required_history(self) -> int:
        """
        Return minimum number of historical candles required.

        Returns:
            Number of candles needed for strategy calculations
        """
        pass

    def can_generate_signal(self) -> bool:
        """
        Check if strategy has enough data to generate signals.

        Returns:
            True if enough historical data available
        """
        return len(self.data_buffer) >= self.get_required_history()

    def add_data(self, ohlcv: OHLCVData):
        """
        Add new OHLCV data to buffer and maintain size limits.

        Args:
            ohlcv: New OHLCV data point
        """
        self.data_buffer.append(ohlcv)

        # Keep only last 500 candles to manage memory
        max_buffer_size = max(500, self.get_required_history() * 2)
        if len(self.data_buffer) > max_buffer_size:
            self.data_buffer = self.data_buffer[-max_buffer_size:]

    def log_signal(self, signal: TradingSignal):
        """
        Log generated signal to history.

        Args:
            signal: Trading signal to log
        """
        self.signal_history.append(signal)

        # Keep only last 100 signals
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]

    def get_recent_signals(self, hours: int = 24) -> List[TradingSignal]:
        """
        Get signals generated in the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent signals
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        return [
            signal
            for signal in self.signal_history
            if signal.timestamp.timestamp() > cutoff_time
        ]

    def get_signal_stats(self) -> Dict[str, Any]:
        """
        Get statistics about generated signals.

        Returns:
            Dictionary with signal statistics
        """
        if not self.signal_history:
            return {
                "total_signals": 0,
                "buy_signals": 0,
                "sell_signals": 0,
                "avg_confidence": 0.0,
            }

        buy_signals = sum(
            1 for s in self.signal_history if s.signal_type == SignalType.BUY
        )
        sell_signals = sum(
            1 for s in self.signal_history if s.signal_type == SignalType.SELL
        )
        avg_confidence = sum(s.confidence for s in self.signal_history) / len(
            self.signal_history
        )

        return {
            "total_signals": len(self.signal_history),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "avg_confidence": round(avg_confidence, 3),
            "strategy_name": self.name,
        }

    def reset(self):
        """Reset strategy state and clear buffers."""
        self.data_buffer.clear()
        self.signal_history.clear()


class BaseStrategy(StrategyInterface):
    """
    Base implementation with common functionality.
    Provides template methods for concrete strategies.
    """

    def __init__(self, symbol: str, parameters: StrategyParameters):
        super().__init__(symbol, parameters)
        self.last_signal_time = None

    def update(self, ohlcv: OHLCVData) -> Optional[TradingSignal]:
        """
        Template method for processing new data.
        """
        # Add data to buffer
        self.add_data(ohlcv)

        # Check if we have enough data
        if not self.can_generate_signal():
            return None

        # Check signal rate limiting
        if self._is_rate_limited():
            return None

        # Generate signal using strategy-specific logic
        signal = self._generate_signal()

        if signal and signal.confidence >= self.parameters.min_confidence:
            self.last_signal_time = datetime.now()
            self.log_signal(signal)
            return signal

        return None

    def _is_rate_limited(self) -> bool:
        """
        Check if signal generation is rate limited.

        Returns:
            True if rate limited
        """
        if not self.last_signal_time:
            return False

        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        min_interval = 3600 / self.parameters.max_signals_per_hour

        return time_since_last < min_interval

    @abstractmethod
    def _generate_signal(self) -> Optional[TradingSignal]:
        """
        Strategy-specific signal generation logic.
        Must be implemented by concrete strategies.

        Returns:
            TradingSignal if conditions met, None otherwise
        """
        pass

    def _calculate_stop_loss(
        self, entry_price: float, side: PositionSide, atr: float = None
    ) -> float:
        """
        Calculate stop loss based on ATR or percentage.

        Args:
            entry_price: Entry price for position
            side: Position side (LONG/SHORT)
            atr: Average True Range value

        Returns:
            Stop loss price
        """
        if atr:
            # Use 2x ATR for stop loss
            multiplier = 2.0
            if side == PositionSide.LONG:
                return entry_price - (atr * multiplier)
            else:
                return entry_price + (atr * multiplier)
        else:
            # Use 2% stop loss as fallback
            stop_pct = 0.02
            if side == PositionSide.LONG:
                return entry_price * (1 - stop_pct)
            else:
                return entry_price * (1 + stop_pct)

    def _calculate_take_profits(
        self, entry_price: float, side: PositionSide, stop_loss: float
    ) -> tuple[float, float]:
        """
        Calculate take profit levels based on risk-reward ratio.

        Args:
            entry_price: Entry price for position
            side: Position side (LONG/SHORT)
            stop_loss: Stop loss price

        Returns:
            Tuple of (take_profit_1, take_profit_2)
        """
        risk = abs(entry_price - stop_loss)

        if side == PositionSide.LONG:
            tp1 = entry_price + (risk * self.parameters.risk_reward_ratio)
            tp2 = entry_price + (risk * self.parameters.risk_reward_ratio * 2)
        else:
            tp1 = entry_price - (risk * self.parameters.risk_reward_ratio)
            tp2 = entry_price - (risk * self.parameters.risk_reward_ratio * 2)

        return tp1, tp2
