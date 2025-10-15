"""
Trading Engine - Main orchestrator for the trading bot.
Coordinates market data, strategy signals, and trade execution.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable

from .config_manager import ConfigManager
from .market_data import MarketDataHandler, OHLCVData, TickerData
from .strategy_interface import TradingSignal, SignalType
from .risk_manager import RiskManager, Position
from ..strategies.noice_strategy import NOICEStrategy


class TradingEngine:
    """
    Main trading engine that orchestrates all trading operations.

    Responsibilities:
    - Manage market data feeds
    - Execute trading strategies
    - Handle risk management
    - Coordinate trade execution
    - Provide real-time monitoring
    """

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.market_data: Optional[MarketDataHandler] = None
        self.strategy: Optional[NOICEStrategy] = None
        self.risk_manager: Optional[RiskManager] = None

        # State tracking
        self.is_running = False
        self.is_trading_enabled = True
        self.last_signal: Optional[TradingSignal] = None
        self.trade_callbacks: List[Callable] = []

        # Performance metrics
        self.signals_generated = 0
        self.trades_executed = 0
        self.start_time: Optional[datetime] = None

        self._setup_components()

    def _setup_components(self):
        """Initialize all trading components."""
        try:
            # Get trading configuration
            trading_config = self.config.get_trading_config()

            # Initialize market data handler
            self.market_data = MarketDataHandler(
                symbol=trading_config.symbol,
                primary_exchange="mexc",
                backup_exchange="binance",
            )

            # Initialize strategy
            self.strategy = NOICEStrategy(symbol=trading_config.symbol)

            # Initialize risk manager
            self.risk_manager = RiskManager(
                initial_capital=trading_config.capital,
                max_risk_per_trade=trading_config.max_position_pct,
                max_portfolio_risk=0.10,  # 10% max portfolio risk
                max_drawdown=0.15,  # 15% max drawdown
                max_positions=5,
            )

            # Set up market data callbacks
            self.market_data.add_ohlcv_callback(self._on_market_data)
            self.market_data.add_ticker_callback(self._on_ticker_data)

            self.logger.info("Trading engine components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to setup trading components: {e}")
            raise

    def _on_market_data(self, ohlcv: OHLCVData):
        """
        Handle incoming OHLCV data from market feed.

        Args:
            ohlcv: New OHLCV data point
        """
        try:
            if not self.is_trading_enabled:
                return

            # Update strategy with new data
            signal = self.strategy.update(ohlcv)

            if signal:
                self.signals_generated += 1
                self.last_signal = signal
                self.logger.info(
                    f"Signal generated: {signal.signal_type.value} at {signal.price:.6f}"
                )

                # Process the signal
                self._process_signal(signal)

            # Update existing positions with current price
            self._update_positions(ohlcv.close)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")

    def _on_ticker_data(self, ticker: TickerData):
        """
        Handle real-time ticker updates.

        Args:
            ticker: Ticker data with current price info
        """
        # Update positions with real-time price data
        if self.risk_manager:
            self._update_positions(ticker.price)

    def _process_signal(self, signal: TradingSignal):
        """
        Process trading signal and execute if conditions met.

        Args:
            signal: Trading signal to process
        """
        try:
            # Check if we can open a new position
            if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                if not self.risk_manager.can_open_position(signal):
                    self.logger.warning(f"Cannot open position: Risk limits exceeded")
                    return

                # Calculate position size
                quantity = self.risk_manager.calculate_position_size(signal)
                if quantity <= 0:
                    self.logger.warning(f"Invalid position size calculated: {quantity}")
                    return

                # Execute the trade
                self._execute_trade(signal, quantity)

            # Handle position closing signals
            elif signal.signal_type in [SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT]:
                self._close_position(signal.symbol, "manual_close")

        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")

    def _execute_trade(self, signal: TradingSignal, quantity: float):
        """
        Execute a trade based on signal and quantity.

        Args:
            signal: Trading signal
            quantity: Position size to trade
        """
        try:
            # In a real implementation, this would interface with an exchange
            # For now, we'll simulate the trade execution

            self.logger.info(
                f"Executing {signal.signal_type.value} order: "
                f"{quantity:.6f} {signal.symbol} at {signal.price:.6f}"
            )

            # Open position in risk manager
            position = self.risk_manager.open_position(signal, quantity)

            self.trades_executed += 1

            # Notify callbacks
            self._notify_trade_callbacks(
                {
                    "action": "open_position",
                    "signal": signal.to_dict(),
                    "position": position.to_dict(),
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            )

            self.logger.info(f"Position opened successfully: {position.symbol}")

        except Exception as e:
            self.logger.error(f"Failed to execute trade: {e}")

    def _update_positions(self, current_price: float):
        """
        Update all positions with current price and check exit conditions.

        Args:
            current_price: Current market price
        """
        if not self.risk_manager or not self.strategy:
            return

        symbols_to_process = list(self.risk_manager.positions.keys())

        for symbol in symbols_to_process:
            try:
                # Update position and check for exit signals
                exit_action = self.risk_manager.update_position(symbol, current_price)

                if exit_action:
                    self._handle_position_exit(symbol, exit_action)

            except Exception as e:
                self.logger.error(f"Error updating position {symbol}: {e}")

    def _handle_position_exit(self, symbol: str, exit_action: str):
        """
        Handle position exit based on risk management rules.

        Args:
            symbol: Symbol to exit
            exit_action: Type of exit ('stop_loss', 'take_profit_1', 'take_profit_2')
        """
        try:
            partial_close = 1.0  # Full close by default

            # For take_profit_1, only close 50% of position
            if exit_action == "take_profit_1":
                partial_close = 0.5

            # Close the position
            closed_position = self.risk_manager.close_position(
                symbol, exit_action, partial_close
            )

            if closed_position:
                self.logger.info(
                    f"Position {exit_action} triggered for {symbol}: "
                    f"PnL: {closed_position.get_total_pnl():.2f}"
                )

                # Notify callbacks
                self._notify_trade_callbacks(
                    {
                        "action": exit_action,
                        "symbol": symbol,
                        "position": closed_position.to_dict(),
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    }
                )

        except Exception as e:
            self.logger.error(f"Error handling position exit for {symbol}: {e}")

    def _close_position(self, symbol: str, reason: str):
        """
        Manually close a position.

        Args:
            symbol: Symbol to close
            reason: Reason for closing
        """
        if symbol in self.risk_manager.positions:
            closed_position = self.risk_manager.close_position(symbol, reason, 1.0)
            if closed_position:
                self.logger.info(f"Position manually closed: {symbol} - {reason}")

    def _notify_trade_callbacks(self, trade_data: Dict[str, Any]):
        """
        Notify all registered trade callbacks.

        Args:
            trade_data: Trade event data
        """
        for callback in self.trade_callbacks:
            try:
                callback(trade_data)
            except Exception as e:
                self.logger.error(f"Error in trade callback: {e}")

    def add_trade_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add callback for trade events.

        Args:
            callback: Function to call on trade events
        """
        self.trade_callbacks.append(callback)

    async def start(self):
        """Start the trading engine."""
        if self.is_running:
            self.logger.warning("Trading engine is already running")
            return

        try:
            self.is_running = True
            self.start_time = datetime.now(tz=timezone.utc)

            self.logger.info("Starting trading engine...")

            # Start market data feeds
            if self.market_data:
                await self.market_data.start()

            self.logger.info("Trading engine started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start trading engine: {e}")
            self.is_running = False
            raise

    def stop(self):
        """Stop the trading engine."""
        if not self.is_running:
            return

        try:
            self.logger.info("Stopping trading engine...")

            self.is_running = False

            # Stop market data feeds
            if self.market_data:
                self.market_data.stop()

            # Close all open positions (optional - for emergency stop)
            # if self.risk_manager:
            #     for symbol in list(self.risk_manager.positions.keys()):
            #         self._close_position(symbol, "engine_stop")

            self.logger.info("Trading engine stopped")

        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")

    def enable_trading(self):
        """Enable trade execution."""
        self.is_trading_enabled = True
        self.logger.info("Trading enabled")

    def disable_trading(self):
        """Disable trade execution (monitoring only)."""
        self.is_trading_enabled = False
        self.logger.info("Trading disabled - monitoring only")

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status and statistics."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now(tz=timezone.utc) - self.start_time).total_seconds()

        portfolio_summary = {}
        if self.risk_manager:
            portfolio_summary = self.risk_manager.get_portfolio_summary()

        strategy_stats = {}
        if self.strategy:
            strategy_stats = self.strategy.get_signal_stats()

        return {
            "engine": {
                "is_running": self.is_running,
                "is_trading_enabled": self.is_trading_enabled,
                "uptime_seconds": uptime,
                "signals_generated": self.signals_generated,
                "trades_executed": self.trades_executed,
            },
            "portfolio": portfolio_summary,
            "strategy": strategy_stats,
            "last_signal": self.last_signal.to_dict() if self.last_signal else None,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions."""
        if self.risk_manager:
            return self.risk_manager.get_active_positions()
        return []

    def force_close_position(self, symbol: str) -> bool:
        """
        Force close a specific position.

        Args:
            symbol: Symbol to close

        Returns:
            True if position was closed
        """
        try:
            if self.risk_manager and symbol in self.risk_manager.positions:
                self._close_position(symbol, "force_close")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error force closing position {symbol}: {e}")
            return False

    def force_close_all_positions(self) -> int:
        """
        Force close all open positions.

        Returns:
            Number of positions closed
        """
        closed_count = 0

        if self.risk_manager:
            symbols = list(self.risk_manager.positions.keys())
            for symbol in symbols:
                if self.force_close_position(symbol):
                    closed_count += 1

        return closed_count
