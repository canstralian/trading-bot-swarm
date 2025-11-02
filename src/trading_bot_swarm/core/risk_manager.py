"""
Risk Management System
Handles position sizing, stop-loss enforcement, and portfolio risk.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

from .strategy_interface import TradingSignal, SignalType


class PositionStatus(Enum):
    """Position status types."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"


@dataclass
class Position:
    """
    Represents an open trading position.
    """

    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    current_price: float

    # Position state
    status: PositionStatus = PositionStatus.OPEN
    tp1_hit: bool = False
    tp2_hit: bool = False
    remaining_quantity: float = 0.0

    # Timing
    opened_at: datetime = None
    updated_at: datetime = None

    # PnL tracking
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    # Metadata
    strategy: str = ""
    signal_confidence: float = 0.0

    def __post_init__(self):
        """Initialize computed fields."""
        if self.opened_at is None:
            self.opened_at = datetime.now(tz=timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.opened_at
        if self.remaining_quantity == 0.0:
            self.remaining_quantity = self.quantity

    def update_price(self, new_price: float):
        """Update current price and calculate unrealized PnL."""
        self.current_price = new_price
        self.updated_at = datetime.now(tz=timezone.utc)

        # Calculate unrealized PnL
        if self.side == "LONG":
            price_diff = new_price - self.entry_price
        else:  # SHORT
            price_diff = self.entry_price - new_price

        self.unrealized_pnl = price_diff * self.remaining_quantity

    def get_total_pnl(self) -> float:
        """Get total PnL (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    def get_pnl_percentage(self) -> float:
        """Get PnL as percentage of initial investment."""
        initial_value = self.entry_price * self.quantity
        if initial_value == 0:
            return 0.0
        return (self.get_total_pnl() / initial_value) * 100

    def is_profitable(self) -> bool:
        """Check if position is currently profitable."""
        return self.get_total_pnl() > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary for storage."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "current_price": self.current_price,
            "status": self.status.value,
            "tp1_hit": self.tp1_hit,
            "tp2_hit": self.tp2_hit,
            "remaining_quantity": self.remaining_quantity,
            "opened_at": self.opened_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "strategy": self.strategy,
            "signal_confidence": self.signal_confidence,
        }


class RiskManager:
    """
    Comprehensive risk management system for trading operations.

    Features:
    - Position sizing based on capital and risk limits
    - Stop-loss and take-profit monitoring
    - Portfolio-level risk controls
    - Drawdown protection
    - Dynamic position management
    """

    def __init__(
        self,
        initial_capital: float,
        max_risk_per_trade: float = 0.02,  # 2% max risk per trade
        max_portfolio_risk: float = 0.10,  # 10% max portfolio risk
        max_drawdown: float = 0.15,  # 15% max drawdown
        max_positions: int = 5,  # Max concurrent positions
        min_risk_reward: float = 1.5,  # Minimum risk-reward ratio
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown = max_drawdown
        self.max_positions = max_positions
        self.min_risk_reward = min_risk_reward

        # Position tracking
        self.positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []

        # Risk metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.total_fees = 0.0
        self.max_historical_capital = initial_capital

    def can_open_position(self, signal: TradingSignal) -> bool:
        """
        Check if new position can be opened based on risk limits.

        Args:
            signal: Trading signal to evaluate

        Returns:
            True if position can be opened safely
        """
        # Check maximum number of positions
        if len(self.positions) >= self.max_positions:
            return False

        # Check if already have position in this symbol
        if signal.symbol in self.positions:
            return False

        # Check portfolio risk
        current_portfolio_risk = self.get_portfolio_risk()
        if current_portfolio_risk >= self.max_portfolio_risk:
            return False

        # Check drawdown
        if self.get_current_drawdown() >= self.max_drawdown:
            return False

        # Check risk-reward ratio
        risk_reward = self.calculate_risk_reward_ratio(signal)
        if risk_reward < self.min_risk_reward:
            return False

        return True

    def calculate_position_size(self, signal: TradingSignal) -> float:
        """
        Calculate appropriate position size based on risk management rules.

        Args:
            signal: Trading signal with price and stop loss

        Returns:
            Position size (quantity)
        """
        # Calculate maximum risk amount
        max_risk_amount = self.current_capital * self.max_risk_per_trade

        # Calculate risk per share/unit
        price_diff = abs(signal.price - signal.stop_loss)
        if price_diff == 0:
            return 0.0

        # Calculate position size based on risk
        position_size = max_risk_amount / price_diff

        # Ensure we don't exceed available capital
        max_affordable = (
            self.current_capital * 0.95
        ) / signal.price  # 95% to leave buffer
        position_size = min(position_size, max_affordable)

        return round(position_size, 8)  # Round to 8 decimal places

    def calculate_risk_reward_ratio(self, signal: TradingSignal) -> float:
        """
        Calculate risk-reward ratio for a signal.

        Args:
            signal: Trading signal

        Returns:
            Risk-reward ratio
        """
        risk = abs(signal.price - signal.stop_loss)
        reward = abs(signal.take_profit_1 - signal.price)

        if risk == 0:
            return 0.0

        return reward / risk

    def open_position(self, signal: TradingSignal, quantity: float) -> Position:
        """
        Open a new position based on trading signal.

        Args:
            signal: Trading signal
            quantity: Position size

        Returns:
            Created position object
        """
        side = "LONG" if signal.signal_type == SignalType.BUY else "SHORT"

        position = Position(
            symbol=signal.symbol,
            side=side,
            entry_price=signal.price,
            quantity=quantity,
            stop_loss=signal.stop_loss,
            take_profit_1=signal.take_profit_1,
            take_profit_2=signal.take_profit_2,
            current_price=signal.price,
            strategy=signal.metadata.get("strategy", "") if signal.metadata else "",
            signal_confidence=signal.confidence,
        )

        self.positions[signal.symbol] = position
        self.total_trades += 1

        return position

    def update_position(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Update position with new price and check for exit conditions.

        Args:
            symbol: Symbol to update
            current_price: Current market price

        Returns:
            Exit action if any ('stop_loss', 'take_profit_1', 'take_profit_2')
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        position.update_price(current_price)

        # Check stop loss
        if self._should_stop_loss(position):
            return "stop_loss"

        # Check take profit levels
        if not position.tp1_hit and self._should_take_profit_1(position):
            return "take_profit_1"

        if (
            position.tp1_hit
            and not position.tp2_hit
            and self._should_take_profit_2(position)
        ):
            return "take_profit_2"

        return None

    def _should_stop_loss(self, position: Position) -> bool:
        """Check if stop loss should be triggered."""
        if position.side == "LONG":
            return position.current_price <= position.stop_loss
        else:  # SHORT
            return position.current_price >= position.stop_loss

    def _should_take_profit_1(self, position: Position) -> bool:
        """Check if first take profit should be triggered."""
        if position.side == "LONG":
            return position.current_price >= position.take_profit_1
        else:  # SHORT
            return position.current_price <= position.take_profit_1

    def _should_take_profit_2(self, position: Position) -> bool:
        """Check if second take profit should be triggered."""
        if position.side == "LONG":
            return position.current_price >= position.take_profit_2
        else:  # SHORT
            return position.current_price <= position.take_profit_2

    def close_position(
        self, symbol: str, reason: str, partial_close: float = 1.0
    ) -> Optional[Position]:
        """
        Close position (fully or partially).

        Args:
            symbol: Symbol to close
            reason: Reason for closing
            partial_close: Fraction to close (1.0 = full close)

        Returns:
            Position object if closed
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        close_quantity = position.remaining_quantity * partial_close

        # Calculate realized PnL for closed portion
        if position.side == "LONG":
            price_diff = position.current_price - position.entry_price
        else:  # SHORT
            price_diff = position.entry_price - position.current_price

        realized_pnl = price_diff * close_quantity
        position.realized_pnl += realized_pnl
        position.remaining_quantity -= close_quantity

        # Update capital
        self.current_capital += realized_pnl

        # Track winning trades
        if realized_pnl > 0:
            self.winning_trades += 1

        # Mark take profit levels as hit
        if reason == "take_profit_1":
            position.tp1_hit = True
            position.status = PositionStatus.PARTIAL
            # Move stop loss to breakeven after TP1
            position.stop_loss = position.entry_price

        elif reason == "take_profit_2":
            position.tp2_hit = True
            position.status = PositionStatus.CLOSED

        elif partial_close >= 1.0:
            position.status = PositionStatus.CLOSED

        # If fully closed, move to history and remove from active positions
        if position.remaining_quantity <= 0.001:  # Almost zero
            position.status = PositionStatus.CLOSED
            self.position_history.append(position)
            del self.positions[symbol]

        return position

    def get_portfolio_risk(self) -> float:
        """Calculate current portfolio risk exposure."""
        total_risk = 0.0

        for position in self.positions.values():
            position_risk = (
                abs(position.entry_price - position.stop_loss)
                * position.remaining_quantity
            )
            total_risk += position_risk

        if self.current_capital == 0:
            return 0.0

        return total_risk / self.current_capital

    def get_current_drawdown(self) -> float:
        """Calculate current drawdown from peak capital."""
        if self.max_historical_capital == 0:
            return 0.0

        # Update max historical capital
        self.max_historical_capital = max(
            self.max_historical_capital, self.current_capital
        )

        # Calculate drawdown
        drawdown = (
            self.max_historical_capital - self.current_capital
        ) / self.max_historical_capital
        return max(0.0, drawdown)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        total_realized_pnl = self.current_capital - self.initial_capital

        win_rate = (
            (self.winning_trades / self.total_trades * 100)
            if self.total_trades > 0
            else 0
        )

        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_pnl": total_realized_pnl,
            "unrealized_pnl": total_unrealized_pnl,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": round(win_rate, 2),
            "active_positions": len(self.positions),
            "portfolio_risk": round(self.get_portfolio_risk() * 100, 2),
            "current_drawdown": round(self.get_current_drawdown() * 100, 2),
            "max_historical_capital": self.max_historical_capital,
        }

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get list of active positions."""
        return [pos.to_dict() for pos in self.positions.values()]
