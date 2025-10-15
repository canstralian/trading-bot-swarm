"""
Base trading bot class that all bots inherit from.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from .bot_state import BotState, BotStatus
from .portfolio import Portfolio, Position, PositionType


class BaseBot(ABC):
    """
    Abstract base class for all trading bots.

    All concrete bot implementations should inherit from this class
    and implement the required abstract methods.
    """

    def __init__(
        self,
        bot_id: Optional[str] = None,
        initial_balance: float = 10000.0,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base bot.

        Args:
            bot_id: Unique identifier for the bot
            initial_balance: Starting capital
            name: Human-readable bot name
            config: Configuration dictionary
        """
        self.bot_id = bot_id or str(uuid.uuid4())
        self.name = name or f"Bot-{self.bot_id[:8]}"
        self.config = config or {}

        # Initialize state and portfolio
        self.state = BotState(bot_id=self.bot_id, balance=initial_balance)
        self.portfolio = Portfolio(cash_balance=initial_balance, initial_balance=initial_balance)

        # Runtime control
        self._running = False
        self._stop_requested = False

        logger.info(f"Initialized {self.name} (ID: {self.bot_id})")

    @abstractmethod
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signals.

        Args:
            market_data: Current market data

        Returns:
            Analysis results including signals
        """
        pass

    @abstractmethod
    async def execute_trade(self, signal: Dict[str, Any]) -> bool:
        """
        Execute a trade based on a signal.

        Args:
            signal: Trading signal to execute

        Returns:
            True if trade executed successfully
        """
        pass

    @abstractmethod
    async def get_market_data(self) -> Dict[str, Any]:
        """
        Fetch current market data.

        Returns:
            Market data dictionary
        """
        pass

    async def run(self):
        """Main bot execution loop."""
        if self._running:
            logger.warning(f"{self.name} is already running")
            return

        self._running = True
        self._stop_requested = False
        self.state.update_status(BotStatus.RUNNING)

        logger.info(f"Starting {self.name}")

        try:
            while not self._stop_requested:
                try:
                    # Get market data
                    market_data = await self.get_market_data()

                    # Update portfolio prices
                    await self._update_portfolio_prices(market_data)

                    # Check risk management
                    await self._check_risk_management()

                    # Analyze market
                    analysis = await self.analyze_market(market_data)

                    # Execute trades if signals present
                    if analysis.get('signal'):
                        success = await self.execute_trade(analysis['signal'])

                        # Record trade
                        profit_loss = analysis.get('expected_pnl', 0.0)
                        self.state.record_trade(success, profit_loss)

                    # Update state
                    self.state.balance = self.portfolio.total_value

                    # Wait before next iteration
                    await asyncio.sleep(self.config.get('interval', 1.0))

                except Exception as e:
                    logger.error(f"{self.name} error in main loop: {e}")
                    await asyncio.sleep(5)  # Wait before retry

        except Exception as e:
            logger.error(f"{self.name} critical error: {e}")
            self.state.update_status(BotStatus.ERROR, str(e))

        finally:
            self._running = False
            self.state.update_status(BotStatus.STOPPED)
            logger.info(f"Stopped {self.name}")

    async def stop(self):
        """Stop the bot gracefully."""
        logger.info(f"Stopping {self.name}")
        self._stop_requested = True

        # Close all positions
        await self._close_all_positions()

        # Wait for main loop to finish
        timeout = 10
        while self._running and timeout > 0:
            await asyncio.sleep(0.1)
            timeout -= 0.1

    async def pause(self):
        """Pause bot execution."""
        self.state.update_status(BotStatus.PAUSED)
        logger.info(f"Paused {self.name}")

    async def resume(self):
        """Resume bot execution."""
        self.state.update_status(BotStatus.RUNNING)
        logger.info(f"Resumed {self.name}")

    async def _update_portfolio_prices(self, market_data: Dict[str, Any]):
        """Update portfolio position prices."""
        price_updates = {}
        for symbol in self.portfolio.positions.keys():
            if symbol in market_data:
                price_updates[symbol] = market_data[symbol].get('price', 0.0)

        if price_updates:
            self.portfolio.update_prices(price_updates)

    async def _check_risk_management(self):
        """Check and enforce risk management rules."""
        for symbol, position in list(self.portfolio.positions.items()):
            # Check stop loss
            if position.should_stop_loss():
                logger.warning(f"{self.name} triggering stop loss for {symbol}")
                await self._close_position(symbol, position.current_price, "stop_loss")

            # Check take profit
            elif position.should_take_profit():
                logger.info(f"{self.name} triggering take profit for {symbol}")
                await self._close_position(symbol, position.current_price, "take_profit")

    async def _close_position(self, symbol: str, exit_price: float, reason: str = "manual"):
        """Close a position."""
        realized_pnl = self.portfolio.close_position(symbol, exit_price)
        if realized_pnl is not None:
            logger.info(
                f"{self.name} closed {symbol} at {exit_price}, "
                f"P&L: ${realized_pnl:.2f}, reason: {reason}"
            )
            return True
        return False

    async def _close_all_positions(self):
        """Close all open positions."""
        for symbol in list(self.portfolio.positions.keys()):
            position = self.portfolio.positions[symbol]
            await self._close_position(symbol, position.current_price, "shutdown")

    def open_position(
        self,
        symbol: str,
        position_type: PositionType,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Open a new trading position.

        Args:
            symbol: Trading symbol
            position_type: LONG or SHORT
            quantity: Amount to trade
            entry_price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            True if position opened successfully
        """
        # Check if we have enough cash
        cost = quantity * entry_price
        if cost > self.portfolio.cash_balance:
            logger.warning(f"{self.name} insufficient funds for {symbol}")
            return False

        # Create and add position
        position = Position(
            symbol=symbol,
            position_type=position_type,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.portfolio.add_position(position)
        logger.info(
            f"{self.name} opened {position_type.value} position: "
            f"{quantity} {symbol} at ${entry_price}"
        )
        return True

    def get_state(self) -> Dict[str, Any]:
        """Get current bot state."""
        return {
            'bot_id': self.bot_id,
            'name': self.name,
            'state': self.state.to_dict(),
            'portfolio': self.portfolio.to_dict(),
            'is_running': self._running
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.bot_id[:8]}, "
            f"name={self.name}, status={self.state.status.value})"
        )
