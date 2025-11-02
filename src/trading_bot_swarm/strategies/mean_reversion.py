"""
Mean reversion strategy implementation.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, StrategySignal, SignalType


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy using Bollinger Bands and statistical measures.

    Strategy logic:
    - Buy when price touches lower Bollinger Band and shows reversal
    - Sell when price touches upper Bollinger Band
    - Use RSI and volume for confirmation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize mean reversion strategy.

        Config parameters:
            bb_period: Bollinger Band period (default: 20)
            bb_std: Bollinger Band standard deviations (default: 2)
            rsi_period: RSI period (default: 14)
            rsi_oversold: RSI oversold level (default: 30)
            rsi_overbought: RSI overbought level (default: 70)
            min_confidence: Minimum confidence threshold (default: 0.6)
            stop_loss_pct: Stop loss percentage (default: 0.03)
            take_profit_pct: Take profit percentage (default: 0.05)
        """
        super().__init__("MeanReversion", config)

        self.bb_period = self.config.get('bb_period', 20)
        self.bb_std = self.config.get('bb_std', 2)
        self.rsi_period = self.config.get('rsi_period', 14)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.03)
        self.take_profit_pct = self.config.get('take_profit_pct', 0.05)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        df = df.copy()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)

        # Bollinger Band width (volatility indicator)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        # Price position in Bollinger Bands (0 = lower, 1 = upper)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Z-score (distance from mean)
        df['zscore'] = (df['close'] - df['bb_middle']) / bb_std

        # Volume
        df['volume_ma'] = df['volume'].rolling(window=20).mean()

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
        Generate trading signal based on mean reversion logic.
        """
        if historical_data is None or len(historical_data) < self.bb_period + 1:
            return None

        # Calculate indicators
        df = self.calculate_indicators(historical_data)

        # Get recent data
        current = df.iloc[-1]
        previous = df.iloc[-2]

        # Check for NaN values
        if pd.isna(current['bb_upper']) or pd.isna(current['bb_lower']):
            return None

        current_price = market_data.get('price', current['close'])

        signal = None

        # Buy signal (oversold, near lower band)
        if self._is_oversold(current, previous):
            confidence = self._calculate_buy_confidence(current, df)

            if confidence >= self.min_confidence:
                # Stop loss below lower band
                stop_loss = current['bb_lower'] * 0.99

                # Take profit at middle or upper band
                take_profit = current['bb_middle']

                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    confidence=confidence,
                    entry_price=current_price,
                    quantity=0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'bb_position': current['bb_position'],
                        'rsi': current['rsi'],
                        'zscore': current['zscore'],
                        'bb_width': current['bb_width']
                    }
                )

        # Sell signal (overbought, near upper band)
        elif self._is_overbought(current, previous):
            confidence = self._calculate_sell_confidence(current, df)

            if confidence >= self.min_confidence:
                signal = StrategySignal(
                    signal_type=SignalType.CLOSE_LONG,
                    symbol=symbol,
                    confidence=confidence,
                    entry_price=current_price,
                    quantity=0,
                    metadata={
                        'bb_position': current['bb_position'],
                        'rsi': current['rsi'],
                        'zscore': current['zscore'],
                        'bb_width': current['bb_width']
                    }
                )

        self._record_signal(signal)
        return signal

    def _is_oversold(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if price is in oversold condition."""
        # Price near or below lower Bollinger Band
        near_lower_band = current['bb_position'] < 0.2

        # RSI is oversold
        rsi_oversold = current['rsi'] < self.rsi_oversold

        # Price bouncing up (reversal signal)
        price_bouncing = current['close'] > previous['close']

        return near_lower_band and (rsi_oversold or price_bouncing)

    def _is_overbought(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if price is in overbought condition."""
        # Price near or above upper Bollinger Band
        near_upper_band = current['bb_position'] > 0.8

        # RSI is overbought
        rsi_overbought = current['rsi'] > self.rsi_overbought

        # Price starting to fall (reversal signal)
        price_falling = current['close'] < previous['close']

        return near_upper_band and (rsi_overbought or price_falling)

    def _calculate_buy_confidence(self, current: pd.Series, df: pd.DataFrame) -> float:
        """Calculate confidence for buy signal."""
        confidence = 0.4

        # Strong oversold condition
        if current['rsi'] < 25:
            confidence += 0.25
        elif current['rsi'] < self.rsi_oversold:
            confidence += 0.15

        # Price well below mean (z-score)
        if current['zscore'] < -2:
            confidence += 0.2
        elif current['zscore'] < -1:
            confidence += 0.1

        # High volume (conviction)
        if current['volume'] > current['volume_ma'] * 1.5:
            confidence += 0.15

        # Low volatility (better for mean reversion)
        if current['bb_width'] < df['bb_width'].quantile(0.3):
            confidence += 0.1

        return min(confidence, 1.0)

    def _calculate_sell_confidence(self, current: pd.Series, df: pd.DataFrame) -> float:
        """Calculate confidence for sell signal."""
        confidence = 0.4

        # Strong overbought condition
        if current['rsi'] > 75:
            confidence += 0.25
        elif current['rsi'] > self.rsi_overbought:
            confidence += 0.15

        # Price well above mean (z-score)
        if current['zscore'] > 2:
            confidence += 0.2
        elif current['zscore'] > 1:
            confidence += 0.1

        # High volume
        if current['volume'] > current['volume_ma'] * 1.5:
            confidence += 0.15

        # Low volatility
        if current['bb_width'] < df['bb_width'].quantile(0.3):
            confidence += 0.1

        return min(confidence, 1.0)

    def validate_signal(self, signal: StrategySignal) -> bool:
        """Validate the generated signal."""
        if signal.confidence < self.min_confidence:
            return False

        if signal.entry_price <= 0:
            return False

        # For mean reversion, ensure we're not entering in extreme conditions
        zscore = signal.metadata.get('zscore', 0)
        if abs(zscore) > 3:  # Too extreme, might continue
            return False

        return True
