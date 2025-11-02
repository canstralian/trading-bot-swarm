"""
Trend following bot implementation.
"""

import asyncio
from typing import Dict, Any, Optional
import pandas as pd
from loguru import logger

from ..core.base_bot import BaseBot
from ..core.portfolio import PositionType
from ..strategies.trend_following import TrendFollowingStrategy


class TrendFollowingBot(BaseBot):
    """
    Trading bot that implements trend following strategy.
    """

    def __init__(
        self,
        bot_id: Optional[str] = None,
        initial_balance: float = 10000.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize trend following bot.

        Config parameters:
            symbols: List of symbols to trade
            data_source: Data source configuration
            strategy_params: Strategy-specific parameters
            risk_per_trade: Risk percentage per trade
        """
        super().__init__(bot_id, initial_balance, "TrendFollowingBot", config)

        # Initialize strategy
        strategy_params = self.config.get('strategy_params', {})
        self.strategy = TrendFollowingStrategy(strategy_params)

        # Bot configuration
        self.symbols = self.config.get('symbols', ['BTC/USDT'])
        self.risk_per_trade = self.config.get('risk_per_trade', 0.02)
        self.max_positions = self.config.get('max_positions', 3)

        # Historical data storage
        self.historical_data: Dict[str, pd.DataFrame] = {}
        self.data_window = self.config.get('data_window', 100)

        logger.info(f"Initialized {self.name} trading {self.symbols}")

    async def get_market_data(self) -> Dict[str, Any]:
        """
        Fetch current market data for all symbols.

        Returns:
            Dictionary with symbol -> market data
        """
        market_data = {}

        for symbol in self.symbols:
            try:
                # In a real implementation, fetch from exchange API
                # For now, simulate with dummy data
                price = await self._fetch_price(symbol)
                volume = await self._fetch_volume(symbol)

                market_data[symbol] = {
                    'price': price,
                    'volume': volume,
                    'timestamp': pd.Timestamp.now()
                }

                # Update historical data
                await self._update_historical_data(symbol, price, volume)

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")

        return market_data

    async def _fetch_price(self, symbol: str) -> float:
        """Fetch current price (placeholder for real implementation)."""
        # This would connect to real exchange API
        # For simulation, return a dummy value
        return 50000.0  # Placeholder

    async def _fetch_volume(self, symbol: str) -> float:
        """Fetch current volume (placeholder for real implementation)."""
        return 1000.0  # Placeholder

    async def _update_historical_data(self, symbol: str, price: float, volume: float):
        """Update historical data buffer."""
        if symbol not in self.historical_data:
            self.historical_data[symbol] = pd.DataFrame(
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

        new_row = pd.DataFrame([{
            'timestamp': pd.Timestamp.now(),
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': volume
        }])

        self.historical_data[symbol] = pd.concat(
            [self.historical_data[symbol], new_row],
            ignore_index=True
        )

        # Keep only recent data
        if len(self.historical_data[symbol]) > self.data_window:
            self.historical_data[symbol] = self.historical_data[symbol].iloc[-self.data_window:]

    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market and generate trading signals.

        Args:
            market_data: Current market data for all symbols

        Returns:
            Analysis results with signals
        """
        analysis_results = {
            'signals': [],
            'timestamp': pd.Timestamp.now()
        }

        for symbol in self.symbols:
            try:
                # Skip if we already have max positions
                if len(self.portfolio.positions) >= self.max_positions:
                    continue

                # Skip if we already have a position in this symbol
                if self.portfolio.has_position(symbol):
                    continue

                # Get historical data
                hist_data = self.historical_data.get(symbol)
                if hist_data is None or len(hist_data) < 50:
                    continue

                # Generate signal using strategy
                signal = self.strategy.generate_signal(
                    symbol=symbol,
                    market_data=market_data.get(symbol, {}),
                    historical_data=hist_data
                )

                if signal and self.strategy.validate_signal(signal):
                    # Calculate position size
                    signal.quantity = self.strategy.calculate_position_size(
                        signal=signal,
                        portfolio_value=self.portfolio.total_value,
                        risk_per_trade=self.risk_per_trade
                    )

                    analysis_results['signals'].append(signal)
                    logger.info(f"{self.name} generated signal for {symbol}: {signal.signal_type.value}")

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")

        # Return first signal if any
        if analysis_results['signals']:
            analysis_results['signal'] = analysis_results['signals'][0]

        return analysis_results

    async def execute_trade(self, signal: Dict[str, Any]) -> bool:
        """
        Execute a trade based on the signal.

        Args:
            signal: Trading signal (StrategySignal object or dict)

        Returns:
            True if trade executed successfully
        """
        try:
            # Handle both dict and StrategySignal object
            if hasattr(signal, 'to_dict'):
                signal_dict = signal.to_dict()
            else:
                signal_dict = signal

            symbol = signal_dict['symbol']
            signal_type = signal_dict['signal_type']
            entry_price = signal_dict['entry_price']
            quantity = signal_dict['quantity']
            stop_loss = signal_dict.get('stop_loss')
            take_profit = signal_dict.get('take_profit')

            logger.info(
                f"{self.name} executing {signal_type} for {symbol}: "
                f"qty={quantity:.4f} @ ${entry_price:.2f}"
            )

            # Execute based on signal type
            if signal_type in ['buy', 'BUY']:
                success = self.open_position(
                    symbol=symbol,
                    position_type=PositionType.LONG,
                    quantity=quantity,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )

                if success:
                    logger.info(f"{self.name} successfully opened position in {symbol}")
                    return True
                else:
                    logger.warning(f"{self.name} failed to open position in {symbol}")
                    return False

            elif signal_type in ['sell', 'SELL', 'close_long', 'CLOSE_LONG']:
                if self.portfolio.has_position(symbol):
                    await self._close_position(symbol, entry_price)
                    return True

            return False

        except Exception as e:
            logger.error(f"{self.name} error executing trade: {e}")
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get bot performance statistics."""
        return {
            **self.get_state(),
            'strategy_stats': self.strategy.get_stats(),
            'symbols_traded': self.symbols,
            'max_positions': self.max_positions,
            'risk_per_trade': self.risk_per_trade
        }
