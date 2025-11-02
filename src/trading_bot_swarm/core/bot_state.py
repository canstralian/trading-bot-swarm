"""
Bot state management and status tracking.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


class BotStatus(Enum):
    """Bot operational status."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    IDLE = "idle"


@dataclass
class BotState:
    """
    Represents the current state of a trading bot.
    """
    bot_id: str
    status: BotStatus = BotStatus.INITIALIZED
    balance: float = 0.0
    positions: Dict[str, Any] = field(default_factory=dict)
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit_loss: float = 0.0
    last_trade_time: Optional[datetime] = None
    started_at: datetime = field(default_factory=datetime.now)
    stopped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_status(self, status: BotStatus, error_message: Optional[str] = None):
        """Update bot status."""
        self.status = status
        if error_message:
            self.error_message = error_message
        if status == BotStatus.STOPPED:
            self.stopped_at = datetime.now()

    def record_trade(self, success: bool, profit_loss: float):
        """Record trade execution."""
        self.total_trades += 1
        if success:
            self.successful_trades += 1
        else:
            self.failed_trades += 1
        self.total_profit_loss += profit_loss
        self.last_trade_time = datetime.now()

    def get_win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.successful_trades / self.total_trades) * 100

    def get_uptime(self) -> float:
        """Calculate uptime in seconds."""
        end_time = self.stopped_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'bot_id': self.bot_id,
            'status': self.status.value,
            'balance': self.balance,
            'positions': self.positions,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'win_rate': self.get_win_rate(),
            'total_profit_loss': self.total_profit_loss,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'started_at': self.started_at.isoformat(),
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'uptime_seconds': self.get_uptime(),
            'error_message': self.error_message,
            'metadata': self.metadata
        }
