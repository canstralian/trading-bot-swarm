"""
Portfolio and position management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class PositionType(Enum):
    """Type of position."""
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """
    Represents a trading position.
    """
    symbol: str
    position_type: PositionType
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime = field(default_factory=datetime.now)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict = field(default_factory=dict)

    @property
    def cost_basis(self) -> float:
        """Calculate cost basis."""
        return self.quantity * self.entry_price

    @property
    def current_value(self) -> float:
        """Calculate current value."""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss."""
        if self.position_type == PositionType.LONG:
            return self.current_value - self.cost_basis
        else:  # SHORT
            return self.cost_basis - self.current_value

    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def update_price(self, new_price: float):
        """Update current price."""
        self.current_price = new_price

    def should_stop_loss(self) -> bool:
        """Check if stop loss should trigger."""
        if self.stop_loss is None:
            return False
        if self.position_type == PositionType.LONG:
            return self.current_price <= self.stop_loss
        else:  # SHORT
            return self.current_price >= self.stop_loss

    def should_take_profit(self) -> bool:
        """Check if take profit should trigger."""
        if self.take_profit is None:
            return False
        if self.position_type == PositionType.LONG:
            return self.current_price >= self.take_profit
        else:  # SHORT
            return self.current_price <= self.take_profit

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'type': self.position_type.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'cost_basis': self.cost_basis,
            'current_value': self.current_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent,
            'entry_time': self.entry_time.isoformat(),
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'metadata': self.metadata
        }


@dataclass
class Portfolio:
    """
    Manages a collection of positions and portfolio metrics.
    """
    cash_balance: float
    positions: Dict[str, Position] = field(default_factory=dict)
    trade_history: List[Dict] = field(default_factory=list)
    initial_balance: float = 0.0

    def __post_init__(self):
        if self.initial_balance == 0.0:
            self.initial_balance = self.cash_balance

    @property
    def total_position_value(self) -> float:
        """Calculate total value of all positions."""
        return sum(pos.current_value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """Calculate total portfolio value (cash + positions)."""
        return self.cash_balance + self.total_position_value

    @property
    def total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def total_return(self) -> float:
        """Calculate total return percentage."""
        if self.initial_balance == 0:
            return 0.0
        return ((self.total_value - self.initial_balance) / self.initial_balance) * 100

    def add_position(self, position: Position):
        """Add a new position to portfolio."""
        self.positions[position.symbol] = position
        self.cash_balance -= position.cost_basis

    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """
        Close a position and realize P&L.
        Returns the realized P&L or None if position doesn't exist.
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        position.update_price(exit_price)
        realized_pnl = position.unrealized_pnl

        # Add cash back
        self.cash_balance += position.current_value

        # Record trade
        self.trade_history.append({
            'symbol': symbol,
            'type': position.position_type.value,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'realized_pnl': realized_pnl,
            'entry_time': position.entry_time.isoformat(),
            'exit_time': datetime.now().isoformat()
        })

        # Remove position
        del self.positions[symbol]

        return realized_pnl

    def update_prices(self, price_updates: Dict[str, float]):
        """Update prices for multiple positions."""
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if portfolio has a position."""
        return symbol in self.positions

    def to_dict(self) -> Dict:
        """Convert portfolio to dictionary."""
        return {
            'cash_balance': self.cash_balance,
            'total_position_value': self.total_position_value,
            'total_value': self.total_value,
            'total_unrealized_pnl': self.total_unrealized_pnl,
            'total_return': self.total_return,
            'positions': {k: v.to_dict() for k, v in self.positions.items()},
            'num_positions': len(self.positions),
            'trade_count': len(self.trade_history)
        }
