"""
NOICE Trading Strategy Implementation
Advanced technical analysis strategy optimized for NOICE token trading.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from datetime import datetime

from ..core.strategy_interface import (
    BaseStrategy,
    StrategyParameters,
    TradingSignal,
    SignalType,
    PositionSide,
)
from ..core.market_data import OHLCVData


class TechnicalIndicators:
    """Technical analysis indicators for trading strategies."""

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return data.rolling(window=period).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # Neutral RSI for NaN values

    @staticmethod
    def macd(
        data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD indicator.
        Returns: (macd_line, signal_line, histogram)
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        data: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        Returns: (upper_band, middle_band, lower_band)
        """
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def atr(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr_data = pd.concat([tr1, tr2, tr3], axis=1)
        tr = tr_data.max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        Returns: (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()

        return k_percent, d_percent

    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Calculate volume simple moving average."""
        return volume.rolling(window=period).mean()


class NOICEStrategyParameters(StrategyParameters):
    """NOICE-specific strategy parameters."""

    def __init__(self):
        super().__init__()

        # Volume confirmation
        self.min_volume_multiplier = 1.5
        self.volume_period = 20

        # EMA settings
        self.ema_fast = 9
        self.ema_slow = 21

        # RSI settings
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70

        # MACD settings
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        # Bollinger Bands
        self.bb_period = 20
        self.bb_std = 2.0

        # ATR for stop loss
        self.atr_period = 14
        self.atr_multiplier = 2.0

        # Risk management
        self.max_risk_per_trade = 0.02  # 2%
        self.min_confidence = 0.75


class NOICEStrategy(BaseStrategy):
    """
    Advanced NOICE trading strategy combining multiple technical indicators:
    - EMA crossovers for trend direction
    - RSI for momentum confirmation
    - MACD for signal timing
    - Volume analysis for confirmation
    - Bollinger Bands for volatility
    - ATR for dynamic stop losses
    """

    def __init__(self, symbol: str = "NOICEUSDT"):
        parameters = NOICEStrategyParameters()
        super().__init__(symbol, parameters)
        self.indicators = TechnicalIndicators()

    def get_required_history(self) -> int:
        """Return minimum candles needed for calculations."""
        return (
            max(
                self.parameters.ema_slow,
                self.parameters.macd_slow,
                self.parameters.bb_period,
                self.parameters.atr_period,
                self.parameters.volume_period,
            )
            + 10
        )  # Extra buffer

    def _generate_signal(self) -> Optional[TradingSignal]:
        """Generate NOICE trading signal based on multi-indicator analysis."""
        try:
            # Convert buffer to DataFrame
            df = self._create_dataframe()

            if len(df) < self.get_required_history():
                return None

            # Calculate all indicators
            self._calculate_indicators(df)

            # Get current and previous values
            current = df.iloc[-1]
            previous = df.iloc[-2]

            # Check volume confirmation first
            if not self._check_volume_confirmation(current):
                return self._create_hold_signal(current, "Insufficient volume")

            # Analyze for bullish signals
            bullish_score = self._analyze_bullish_conditions(current, previous, df)

            # Analyze for bearish signals
            bearish_score = self._analyze_bearish_conditions(current, previous, df)

            # Generate signal based on scores
            if bullish_score >= 0.75:
                return self._create_buy_signal(current, bullish_score, df)
            elif bearish_score >= 0.75 and self.parameters.enable_short_selling:
                return self._create_sell_signal(current, bearish_score, df)
            else:
                return self._create_hold_signal(
                    current,
                    f"Bullish: {bullish_score:.2f}, Bearish: {bearish_score:.2f}",
                )

        except Exception as e:
            print(f"Error generating signal: {e}")
            return None

    def _create_dataframe(self) -> pd.DataFrame:
        """Convert OHLCV buffer to pandas DataFrame."""
        data = []
        for ohlcv in self.data_buffer:
            data.append(
                {
                    "timestamp": ohlcv.timestamp,
                    "open": ohlcv.open,
                    "high": ohlcv.high,
                    "low": ohlcv.low,
                    "close": ohlcv.close,
                    "volume": ohlcv.volume,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def _calculate_indicators(self, df: pd.DataFrame):
        """Calculate all technical indicators."""
        # EMAs
        df["ema_fast"] = self.indicators.ema(df["close"], self.parameters.ema_fast)
        df["ema_slow"] = self.indicators.ema(df["close"], self.parameters.ema_slow)

        # RSI
        df["rsi"] = self.indicators.rsi(df["close"], self.parameters.rsi_period)

        # MACD
        macd, signal, hist = self.indicators.macd(
            df["close"],
            self.parameters.macd_fast,
            self.parameters.macd_slow,
            self.parameters.macd_signal,
        )
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_hist"] = hist

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(
            df["close"], self.parameters.bb_period, self.parameters.bb_std
        )
        df["bb_upper"] = bb_upper
        df["bb_middle"] = bb_middle
        df["bb_lower"] = bb_lower

        # ATR
        df["atr"] = self.indicators.atr(
            df["high"], df["low"], df["close"], self.parameters.atr_period
        )

        # Volume indicators
        df["volume_sma"] = self.indicators.volume_sma(
            df["volume"], self.parameters.volume_period
        )

        # Stochastic
        stoch_k, stoch_d = self.indicators.stochastic(
            df["high"], df["low"], df["close"]
        )
        df["stoch_k"] = stoch_k
        df["stoch_d"] = stoch_d

    def _check_volume_confirmation(self, current: pd.Series) -> bool:
        """Check if current volume meets minimum requirements."""
        if pd.isna(current["volume_sma"]):
            return False

        volume_ratio = current["volume"] / current["volume_sma"]
        return volume_ratio >= self.parameters.min_volume_multiplier

    def _analyze_bullish_conditions(
        self, current: pd.Series, previous: pd.Series, df: pd.DataFrame
    ) -> float:
        """Analyze bullish market conditions and return confidence score."""
        score = 0.0
        max_score = 6.0  # Total possible points

        # 1. EMA Trend (1 point)
        if (
            current["close"] > current["ema_fast"]
            and current["ema_fast"] > current["ema_slow"]
        ):
            score += 1.0

        # 2. RSI Oversold (1 point)
        if current["rsi"] < self.parameters.rsi_oversold:
            score += 1.0
        elif current["rsi"] < 45:  # Partial points for moderate RSI
            score += 0.5

        # 3. MACD Bullish Crossover (1.5 points)
        if (
            current["macd"] > current["macd_signal"]
            and previous["macd"] <= previous["macd_signal"]
        ):
            score += 1.5
        elif current["macd"] > current["macd_signal"]:
            score += 0.5

        # 4. Bollinger Bands (1 point)
        if current["close"] <= current["bb_lower"]:
            score += 1.0  # Oversold condition
        elif current["close"] < current["bb_middle"]:
            score += 0.3

        # 5. Stochastic (1 point)
        if current["stoch_k"] < 20 and current["stoch_d"] < 20:
            score += 1.0
        elif current["stoch_k"] < 50:
            score += 0.3

        # 6. Price momentum (0.5 points)
        if current["close"] > previous["close"]:
            score += 0.5

        return min(score / max_score, 1.0)

    def _analyze_bearish_conditions(
        self, current: pd.Series, previous: pd.Series, df: pd.DataFrame
    ) -> float:
        """Analyze bearish market conditions and return confidence score."""
        score = 0.0
        max_score = 6.0

        # 1. EMA Trend (1 point)
        if (
            current["close"] < current["ema_fast"]
            and current["ema_fast"] < current["ema_slow"]
        ):
            score += 1.0

        # 2. RSI Overbought (1 point)
        if current["rsi"] > self.parameters.rsi_overbought:
            score += 1.0
        elif current["rsi"] > 55:
            score += 0.5

        # 3. MACD Bearish Crossover (1.5 points)
        if (
            current["macd"] < current["macd_signal"]
            and previous["macd"] >= previous["macd_signal"]
        ):
            score += 1.5
        elif current["macd"] < current["macd_signal"]:
            score += 0.5

        # 4. Bollinger Bands (1 point)
        if current["close"] >= current["bb_upper"]:
            score += 1.0  # Overbought condition
        elif current["close"] > current["bb_middle"]:
            score += 0.3

        # 5. Stochastic (1 point)
        if current["stoch_k"] > 80 and current["stoch_d"] > 80:
            score += 1.0
        elif current["stoch_k"] > 50:
            score += 0.3

        # 6. Price momentum (0.5 points)
        if current["close"] < previous["close"]:
            score += 0.5

        return min(score / max_score, 1.0)

    def _create_buy_signal(
        self, current: pd.Series, confidence: float, df: pd.DataFrame
    ) -> TradingSignal:
        """Create a buy signal with proper risk management."""
        entry_price = current["close"]

        # Calculate stop loss using ATR
        stop_loss = self._calculate_stop_loss(
            entry_price, PositionSide.LONG, current["atr"]
        )

        # Calculate take profits
        tp1, tp2 = self._calculate_take_profits(
            entry_price, PositionSide.LONG, stop_loss
        )

        # Build reason string
        reason_parts = [
            f"EMA bullish: {current['close']:.6f} > {current['ema_fast']:.6f}",
            f"RSI: {current['rsi']:.1f}",
            f"MACD: {current['macd']:.6f} > {current['macd_signal']:.6f}",
            f"Volume: {current['volume']:.0f}",
        ]

        return TradingSignal(
            signal_type=SignalType.BUY,
            symbol=self.symbol,
            price=entry_price,
            quantity=0.0,  # Will be calculated by risk manager
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            confidence=confidence,
            reason=" | ".join(reason_parts),
            timestamp=datetime.now(),
            metadata={
                "strategy": "NOICEStrategy",
                "indicators": {
                    "ema_fast": current["ema_fast"],
                    "ema_slow": current["ema_slow"],
                    "rsi": current["rsi"],
                    "macd": current["macd"],
                    "macd_signal": current["macd_signal"],
                    "atr": current["atr"],
                },
            },
        )

    def _create_sell_signal(
        self, current: pd.Series, confidence: float, df: pd.DataFrame
    ) -> TradingSignal:
        """Create a sell signal with proper risk management."""
        entry_price = current["close"]

        # Calculate stop loss using ATR
        stop_loss = self._calculate_stop_loss(
            entry_price, PositionSide.SHORT, current["atr"]
        )

        # Calculate take profits
        tp1, tp2 = self._calculate_take_profits(
            entry_price, PositionSide.SHORT, stop_loss
        )

        reason_parts = [
            f"EMA bearish: {current['close']:.6f} < {current['ema_fast']:.6f}",
            f"RSI: {current['rsi']:.1f}",
            f"MACD: {current['macd']:.6f} < {current['macd_signal']:.6f}",
            f"Volume: {current['volume']:.0f}",
        ]

        return TradingSignal(
            signal_type=SignalType.SELL,
            symbol=self.symbol,
            price=entry_price,
            quantity=0.0,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            confidence=confidence,
            reason=" | ".join(reason_parts),
            timestamp=datetime.now(),
            metadata={
                "strategy": "NOICEStrategy",
                "indicators": {
                    "ema_fast": current["ema_fast"],
                    "ema_slow": current["ema_slow"],
                    "rsi": current["rsi"],
                    "macd": current["macd"],
                    "macd_signal": current["macd_signal"],
                    "atr": current["atr"],
                },
            },
        )

    def _create_hold_signal(self, current: pd.Series, reason: str) -> TradingSignal:
        """Create a hold signal."""
        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=self.symbol,
            price=current["close"],
            quantity=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=0.0,
            confidence=0.0,
            reason=reason,
            timestamp=datetime.now(),
        )
