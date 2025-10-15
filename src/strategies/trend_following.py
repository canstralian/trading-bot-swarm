"""
Trend following strategy implementation.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, StrategySignal, SignalType


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend following strategy using moving averages and momentum.

    Strategy logic:
    - Buy when fast MA crosses above slow MA (golden cross)
    - Sell when fast MA crosses below slow MA (death cross)
    - Use RSI and volume for confirmation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trend following strategy.

        Config parameters:
            fast_period: Fast MA period (default: 20)
            slow_period: Slow MA period (default: 50)
            rsi_period: RSI period (default: 14)
            rsi_overbought: RSI overbought level (default: 70)
            rsi_oversold: RSI oversold level (default: 30)
            min_confidence: Minimum confidence threshold (default: 0.6)
            stop_loss_pct: Stop loss percentage (default: 0.02)
            take_profit_pct: Take profit percentage (default: 0.04)
        """
        super().__init__("TrendFollowing", config)

        # Set default parameters
        self.fast_period = self.config.get('fast_period', 20)
        self.slow_period = self.config.get('slow_period', 50)
        self.rsi_period = self.config.get('rsi_period', 14)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.02)
        self.take_profit_pct = self.config.get('take_profit_pct', 0.04)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        df = df.copy()

        # Moving averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Volume MA
        df['volume_ma'] = df['volume'].rolling(window=20).mean()

        # Trend strength (distance between MAs)
        df['trend_strength'] = (df['fast_ma'] - df['slow_ma']) / df['slow_ma']

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signal(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        historical_data: Optional[pd.DataFrame] = None
    ) -> Optional[StrategySignal]:
        """
        Generate trading signal based on trend following logic.
        """
        if historical_data is None or len(historical_data) < self.slow_period + 1:
            return None

        # Calculate indicators
        df = self.calculate_indicators(historical_data)

        # Get recent data
        current = df.iloc[-1]
        previous = df.iloc[-2]

        # Check for NaN values
        if pd.isna(current['fast_ma']) or pd.isna(current['slow_ma']):
            return None

        current_price = market_data.get('price', current['close'])

        # Detect crossovers
        golden_cross = (
            previous['fast_ma'] <= previous['slow_ma'] and
            current['fast_ma'] > current['slow_ma']
        )

        death_cross = (
            previous['fast_ma'] >= previous['slow_ma'] and
            current['fast_ma'] < current['slow_ma']
        )

        signal = None

        # Buy signal (golden cross)
        if golden_cross:
            confidence = self._calculate_buy_confidence(current, df)

            if confidence >= self.min_confidence:
                stop_loss = current_price * (1 - self.stop_loss_pct)
                take_profit = current_price * (1 + self.take_profit_pct)

                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    confidence=confidence,
                    entry_price=current_price,
                    quantity=0,  # Will be calculated by position sizing
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'fast_ma': current['fast_ma'],
                        'slow_ma': current['slow_ma'],
                        'rsi': current['rsi'],
                        'trend_strength': current['trend_strength']
                    }
                )

        # Sell signal (death cross)
        elif death_cross:
            confidence = self._calculate_sell_confidence(current, df)

            if confidence >= self.min_confidence:
                signal = StrategySignal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    confidence=confidence,
                    entry_price=current_price,
                    quantity=0,
                    metadata={
                        'fast_ma': current['fast_ma'],
                        'slow_ma': current['slow_ma'],
                        'rsi': current['rsi'],
                        'trend_strength': current['trend_strength']
                    }
                )

        self._record_signal(signal)
        return signal

    def _calculate_buy_confidence(self, current: pd.Series, df: pd.DataFrame) -> float:
        """Calculate confidence for buy signal."""
        confidence = 0.5  # Base confidence

        # RSI confirmation (not overbought)
        if current['rsi'] < self.rsi_overbought:
            confidence += 0.2

        # Volume confirmation (above average)
        if current['volume'] > current['volume_ma']:
            confidence += 0.15

        # Strong trend
        if current['trend_strength'] > 0.02:
            confidence += 0.15

        return min(confidence, 1.0)

    def _calculate_sell_confidence(self, current: pd.Series, df: pd.DataFrame) -> float:
        """Calculate confidence for sell signal."""
        confidence = 0.5  # Base confidence

        # RSI confirmation (not oversold)
        if current['rsi'] > self.rsi_oversold:
            confidence += 0.2

        # Volume confirmation
        if current['volume'] > current['volume_ma']:
            confidence += 0.15

        # Weak/negative trend
        if current['trend_strength'] < -0.02:
            confidence += 0.15

        return min(confidence, 1.0)

    def validate_signal(self, signal: StrategySignal) -> bool:
        """Validate the generated signal."""
        # Check confidence threshold
        if signal.confidence < self.min_confidence:
            return False

        # Check price is positive
        if signal.entry_price <= 0:
            return False

        # Check stop loss is reasonable
        if signal.stop_loss is not None:
            if signal.signal_type == SignalType.BUY:
                if signal.stop_loss >= signal.entry_price:
                    return False
            elif signal.signal_type == SignalType.SELL:
                if signal.stop_loss <= signal.entry_price:
                    return False

        return True
