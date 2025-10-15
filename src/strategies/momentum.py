"""
Momentum strategy implementation.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, StrategySignal, SignalType


class MomentumStrategy(BaseStrategy):
    """
    Momentum strategy based on price momentum and rate of change.

    Strategy logic:
    - Buy when momentum is strong and accelerating
    - Sell when momentum is weakening
    - Use multiple timeframes for confirmation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize momentum strategy.

        Config parameters:
            roc_period: Rate of Change period (default: 10)
            momentum_period: Momentum period (default: 14)
            rsi_period: RSI period (default: 14)
            min_momentum: Minimum momentum threshold (default: 0.02)
            min_confidence: Minimum confidence threshold (default: 0.65)
            stop_loss_pct: Stop loss percentage (default: 0.025)
            take_profit_pct: Take profit percentage (default: 0.06)
        """
        super().__init__("Momentum", config)

        self.roc_period = self.config.get('roc_period', 10)
        self.momentum_period = self.config.get('momentum_period', 14)
        self.rsi_period = self.config.get('rsi_period', 14)
        self.min_momentum = self.config.get('min_momentum', 0.02)
        self.min_confidence = self.config.get('min_confidence', 0.65)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.025)
        self.take_profit_pct = self.config.get('take_profit_pct', 0.06)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators."""
        df = df.copy()

        # Rate of Change (ROC)
        df['roc'] = df['close'].pct_change(periods=self.roc_period)

        # Momentum (absolute price change)
        df['momentum'] = df['close'] - df['close'].shift(self.momentum_period)

        # Normalized momentum
        df['momentum_norm'] = df['momentum'] / df['close']

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Moving average of momentum
        df['momentum_ma'] = df['momentum_norm'].rolling(window=5).mean()

        # Momentum acceleration (change in momentum)
        df['momentum_accel'] = df['momentum_norm'].diff()

        # Volume momentum
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_momentum'] = (df['volume'] - df['volume_ma']) / df['volume_ma']

        # MACD-like momentum indicator
        ema_fast = df['close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

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
        Generate trading signal based on momentum logic.
        """
        if historical_data is None or len(historical_data) < self.momentum_period + 1:
            return None

        # Calculate indicators
        df = self.calculate_indicators(historical_data)

        # Get recent data
        current = df.iloc[-1]
        previous = df.iloc[-2]

        # Check for NaN values
        if pd.isna(current['momentum_norm']) or pd.isna(current['roc']):
            return None

        current_price = market_data.get('price', current['close'])

        signal = None

        # Buy signal (strong positive momentum)
        if self._has_buy_momentum(current, previous):
            confidence = self._calculate_buy_confidence(current, df)

            if confidence >= self.min_confidence:
                stop_loss = current_price * (1 - self.stop_loss_pct)
                take_profit = current_price * (1 + self.take_profit_pct)

                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    confidence=confidence,
                    entry_price=current_price,
                    quantity=0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'momentum': current['momentum_norm'],
                        'roc': current['roc'],
                        'rsi': current['rsi'],
                        'momentum_accel': current['momentum_accel'],
                        'macd_hist': current['macd_hist']
                    }
                )

        # Sell signal (momentum weakening or reversing)
        elif self._has_sell_momentum(current, previous):
            confidence = self._calculate_sell_confidence(current, df)

            if confidence >= self.min_confidence:
                signal = StrategySignal(
                    signal_type=SignalType.CLOSE_LONG,
                    symbol=symbol,
                    confidence=confidence,
                    entry_price=current_price,
                    quantity=0,
                    metadata={
                        'momentum': current['momentum_norm'],
                        'roc': current['roc'],
                        'rsi': current['rsi'],
                        'momentum_accel': current['momentum_accel'],
                        'macd_hist': current['macd_hist']
                    }
                )

        self._record_signal(signal)
        return signal

    def _has_buy_momentum(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check for strong buying momentum."""
        # Strong positive momentum
        strong_momentum = current['momentum_norm'] > self.min_momentum

        # Momentum accelerating
        accelerating = current['momentum_accel'] > 0

        # MACD bullish
        macd_bullish = current['macd_hist'] > 0

        # RSI showing strength but not overbought
        rsi_ok = 50 < current['rsi'] < 75

        # At least 3 of 4 conditions must be true
        conditions = [strong_momentum, accelerating, macd_bullish, rsi_ok]
        return sum(conditions) >= 3

    def _has_sell_momentum(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check for momentum reversal or weakness."""
        # Momentum turning negative or very weak
        weak_momentum = current['momentum_norm'] < 0.005

        # Momentum decelerating
        decelerating = current['momentum_accel'] < 0

        # MACD bearish
        macd_bearish = current['macd_hist'] < 0

        # RSI showing weakness
        rsi_weak = current['rsi'] < previous['rsi']

        # At least 3 of 4 conditions must be true
        conditions = [weak_momentum, decelerating, macd_bearish, rsi_weak]
        return sum(conditions) >= 3

    def _calculate_buy_confidence(self, current: pd.Series, df: pd.DataFrame) -> float:
        """Calculate confidence for buy signal."""
        confidence = 0.5

        # Very strong momentum
        if current['momentum_norm'] > self.min_momentum * 2:
            confidence += 0.15
        elif current['momentum_norm'] > self.min_momentum:
            confidence += 0.1

        # Strong acceleration
        if current['momentum_accel'] > 0.01:
            confidence += 0.1

        # RSI in sweet spot (50-70)
        if 55 < current['rsi'] < 70:
            confidence += 0.1

        # MACD histogram increasing
        if current['macd_hist'] > df['macd_hist'].iloc[-2]:
            confidence += 0.1

        # Strong volume
        if current['volume_momentum'] > 0.2:
            confidence += 0.05

        return min(confidence, 1.0)

    def _calculate_sell_confidence(self, current: pd.Series, df: pd.DataFrame) -> float:
        """Calculate confidence for sell signal."""
        confidence = 0.5

        # Momentum turned negative
        if current['momentum_norm'] < 0:
            confidence += 0.2
        elif current['momentum_norm'] < self.min_momentum * 0.5:
            confidence += 0.1

        # Strong deceleration
        if current['momentum_accel'] < -0.01:
            confidence += 0.15

        # RSI declining
        rsi_decline = current['rsi'] - df['rsi'].iloc[-2]
        if rsi_decline < -5:
            confidence += 0.1

        # MACD histogram declining
        if current['macd_hist'] < df['macd_hist'].iloc[-2]:
            confidence += 0.1

        return min(confidence, 1.0)

    def validate_signal(self, signal: StrategySignal) -> bool:
        """Validate the generated signal."""
        if signal.confidence < self.min_confidence:
            return False

        if signal.entry_price <= 0:
            return False

        # Check momentum is reasonable
        momentum = signal.metadata.get('momentum', 0)
        if signal.signal_type == SignalType.BUY:
            if momentum < 0:  # Don't buy on negative momentum
                return False

        return True
