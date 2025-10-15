"""
Market Data Handler for Real-time Price Feeds
Supports WebSocket connections to multiple exchanges.
"""

import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging


@dataclass
class OHLCVData:
    """OHLCV (Open, High, Low, Close, Volume) data structure."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol,
        }


@dataclass
class TickerData:
    """Real-time ticker data."""

    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    timestamp: datetime


class WebSocketClient(ABC):
    """Abstract base class for exchange WebSocket clients."""

    @abstractmethod
    async def connect(self):
        """Establish WebSocket connection."""
        pass

    @abstractmethod
    async def subscribe_ohlcv(self, symbol: str, timeframe: str):
        """Subscribe to OHLCV data."""
        pass

    @abstractmethod
    async def subscribe_ticker(self, symbol: str):
        """Subscribe to ticker data."""
        pass


class MEXCWebSocketClient(WebSocketClient):
    """
    MEXC Exchange WebSocket client for real-time market data.
    Handles reconnection, heartbeat, and data normalization.
    """

    def __init__(
        self,
        symbol: str = "NOICEUSDT",
        on_ohlcv: Optional[Callable[[OHLCVData], None]] = None,
        on_ticker: Optional[Callable[[TickerData], None]] = None,
    ):
        self.symbol = symbol.upper()
        self.ws_url = "wss://wbs.mexc.com/ws"
        self.on_ohlcv = on_ohlcv
        self.on_ticker = on_ticker
        self.running = False
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60

    async def connect(self):
        """Establish WebSocket connection with auto-reconnect."""
        self.running = True
        reconnect_delay = self.reconnect_delay

        while self.running:
            try:
                self.logger.info(f"Connecting to MEXC WebSocket: {self.ws_url}")

                async with websockets.connect(
                    self.ws_url, ping_interval=20, ping_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.logger.info("Connected to MEXC WebSocket")

                    # Subscribe to data streams
                    await self.subscribe_ohlcv(self.symbol, "Min1")
                    await self.subscribe_ticker(self.symbol)

                    # Reset reconnect delay on successful connection
                    reconnect_delay = self.reconnect_delay

                    # Listen for messages
                    async for message in websocket:
                        try:
                            await self._handle_message(message)
                        except Exception as e:
                            self.logger.error(f"Error handling message: {e}")

            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                if self.running:
                    self.logger.info(f"Reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, self.max_reconnect_delay)

    async def subscribe_ohlcv(self, symbol: str, timeframe: str):
        """Subscribe to OHLCV (kline) data."""
        if not self.websocket:
            return

        subscribe_msg = {
            "method": "SUBSCRIPTION",
            "params": [f"spot@public.kline.v3.api@{symbol}@{timeframe}"],
        }

        await self.websocket.send(json.dumps(subscribe_msg))
        self.logger.info(f"Subscribed to {symbol} {timeframe} klines")

    async def subscribe_ticker(self, symbol: str):
        """Subscribe to ticker data."""
        if not self.websocket:
            return

        subscribe_msg = {
            "method": "SUBSCRIPTION",
            "params": [f"spot@public.miniTicker.v3.api@{symbol}"],
        }

        await self.websocket.send(json.dumps(subscribe_msg))
        self.logger.info(f"Subscribed to {symbol} ticker")

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)

            # Handle kline data
            if data.get("c") == "spot@public.kline.v3.api":
                ohlcv = self._parse_kline(data)
                if self.on_ohlcv:
                    self.on_ohlcv(ohlcv)

            # Handle ticker data
            elif data.get("c") == "spot@public.miniTicker.v3.api":
                ticker = self._parse_ticker(data)
                if self.on_ticker:
                    self.on_ticker(ticker)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _parse_kline(self, data: Dict) -> OHLCVData:
        """Parse MEXC kline data into OHLCV format."""
        kline = data["d"]["k"]

        return OHLCVData(
            timestamp=datetime.fromtimestamp(kline["t"] / 1000, tz=timezone.utc),
            open=float(kline["o"]),
            high=float(kline["h"]),
            low=float(kline["l"]),
            close=float(kline["c"]),
            volume=float(kline["v"]),
            symbol=self.symbol,
        )

    def _parse_ticker(self, data: Dict) -> TickerData:
        """Parse MEXC ticker data."""
        ticker = data["d"]

        return TickerData(
            symbol=self.symbol,
            price=float(ticker["c"]),
            bid=float(ticker.get("b", 0)),
            ask=float(ticker.get("a", 0)),
            volume_24h=float(ticker.get("v", 0)),
            change_24h=float(ticker.get("P", 0)),
            timestamp=datetime.now(tz=timezone.utc),
        )

    def stop(self):
        """Stop WebSocket client."""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())


class BinanceWebSocketClient(WebSocketClient):
    """Binance WebSocket client for backup data feed."""

    def __init__(
        self,
        symbol: str = "NOICEUSDT",
        on_ohlcv: Optional[Callable[[OHLCVData], None]] = None,
        on_ticker: Optional[Callable[[TickerData], None]] = None,
    ):
        self.symbol = symbol.lower()
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.on_ohlcv = on_ohlcv
        self.on_ticker = on_ticker
        self.running = False
        self.websocket = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Connect to Binance WebSocket."""
        self.running = True

        stream_name = f"{self.symbol}@kline_1m/{self.symbol}@ticker"
        ws_url = f"{self.ws_url}/{stream_name}"

        try:
            async with websockets.connect(ws_url) as websocket:
                self.websocket = websocket
                self.logger.info("Connected to Binance WebSocket")

                async for message in websocket:
                    if not self.running:
                        break
                    await self._handle_message(message)

        except Exception as e:
            self.logger.error(f"Binance WebSocket error: {e}")

    async def subscribe_ohlcv(self, symbol: str, timeframe: str):
        """Binance auto-subscribes via URL."""
        pass

    async def subscribe_ticker(self, symbol: str):
        """Binance auto-subscribes via URL."""
        pass

    async def _handle_message(self, message: str):
        """Handle Binance WebSocket messages."""
        try:
            data = json.loads(message)

            if data.get("e") == "kline":
                ohlcv = self._parse_kline(data)
                if self.on_ohlcv:
                    self.on_ohlcv(ohlcv)

            elif data.get("e") == "24hrTicker":
                ticker = self._parse_ticker(data)
                if self.on_ticker:
                    self.on_ticker(ticker)

        except Exception as e:
            self.logger.error(f"Error parsing Binance message: {e}")

    def _parse_kline(self, data: Dict) -> OHLCVData:
        """Parse Binance kline data."""
        kline = data["k"]

        return OHLCVData(
            timestamp=datetime.fromtimestamp(kline["t"] / 1000, tz=timezone.utc),
            open=float(kline["o"]),
            high=float(kline["h"]),
            low=float(kline["l"]),
            close=float(kline["c"]),
            volume=float(kline["v"]),
            symbol=self.symbol.upper(),
        )

    def _parse_ticker(self, data: Dict) -> TickerData:
        """Parse Binance ticker data."""
        return TickerData(
            symbol=self.symbol.upper(),
            price=float(data["c"]),
            bid=float(data["b"]),
            ask=float(data["a"]),
            volume_24h=float(data["v"]),
            change_24h=float(data["P"]),
            timestamp=datetime.now(tz=timezone.utc),
        )

    def stop(self):
        """Stop WebSocket client."""
        self.running = False


class MarketDataHandler:
    """
    Main market data handler that manages multiple WebSocket clients
    and provides unified data feed with failover support.
    """

    def __init__(
        self,
        symbol: str = "NOICEUSDT",
        primary_exchange: str = "mexc",
        backup_exchange: str = "binance",
    ):
        self.symbol = symbol
        self.primary_exchange = primary_exchange
        self.backup_exchange = backup_exchange
        self.logger = logging.getLogger(__name__)

        self.ohlcv_buffer: List[OHLCVData] = []
        self.latest_ticker: Optional[TickerData] = None

        self.primary_client = None
        self.backup_client = None
        self.data_callbacks: List[Callable[[OHLCVData], None]] = []
        self.ticker_callbacks: List[Callable[[TickerData], None]] = []

        self._setup_clients()

    def _setup_clients(self):
        """Setup primary and backup WebSocket clients."""
        if self.primary_exchange == "mexc":
            self.primary_client = MEXCWebSocketClient(
                symbol=self.symbol,
                on_ohlcv=self._on_ohlcv_data,
                on_ticker=self._on_ticker_data,
            )

        if self.backup_exchange == "binance":
            self.backup_client = BinanceWebSocketClient(
                symbol=self.symbol,
                on_ohlcv=self._on_backup_ohlcv,
                on_ticker=self._on_backup_ticker,
            )

    def _on_ohlcv_data(self, ohlcv: OHLCVData):
        """Handle OHLCV data from primary source."""
        self.ohlcv_buffer.append(ohlcv)

        # Keep only last 1000 candles in memory
        if len(self.ohlcv_buffer) > 1000:
            self.ohlcv_buffer = self.ohlcv_buffer[-1000:]

        # Notify all callbacks
        for callback in self.data_callbacks:
            try:
                callback(ohlcv)
            except Exception as e:
                self.logger.error(f"Error in data callback: {e}")

    def _on_ticker_data(self, ticker: TickerData):
        """Handle ticker data from primary source."""
        self.latest_ticker = ticker

        for callback in self.ticker_callbacks:
            try:
                callback(ticker)
            except Exception as e:
                self.logger.error(f"Error in ticker callback: {e}")

    def _on_backup_ohlcv(self, ohlcv: OHLCVData):
        """Handle backup OHLCV data (only if primary fails)."""
        # For now, just log - implement failover logic as needed
        self.logger.debug(f"Backup OHLCV received: {ohlcv.close}")

    def _on_backup_ticker(self, ticker: TickerData):
        """Handle backup ticker data (only if primary fails)."""
        self.logger.debug(f"Backup ticker received: {ticker.price}")

    def add_ohlcv_callback(self, callback: Callable[[OHLCVData], None]):
        """Add callback for OHLCV data updates."""
        self.data_callbacks.append(callback)

    def add_ticker_callback(self, callback: Callable[[TickerData], None]):
        """Add callback for ticker data updates."""
        self.ticker_callbacks.append(callback)

    def get_latest_ohlcv(self, count: int = 100) -> List[OHLCVData]:
        """Get latest OHLCV data from buffer."""
        return self.ohlcv_buffer[-count:] if self.ohlcv_buffer else []

    def get_dataframe(self, count: int = 100) -> pd.DataFrame:
        """Get OHLCV data as pandas DataFrame."""
        data = self.get_latest_ohlcv(count)
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame([asdict(ohlcv) for ohlcv in data])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df

    async def start(self):
        """Start market data feeds."""
        tasks = []

        if self.primary_client:
            tasks.append(self.primary_client.connect())

        if self.backup_client:
            tasks.append(self.backup_client.connect())

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def stop(self):
        """Stop all market data feeds."""
        if self.primary_client:
            self.primary_client.stop()

        if self.backup_client:
            self.backup_client.stop()
