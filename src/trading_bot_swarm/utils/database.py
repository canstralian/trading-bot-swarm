"""
Database manager for storing trading data and analytics.
Supports SQLite and PostgreSQL with async operations.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import json

try:
    import asyncpg
except ImportError:
    asyncpg = None

from ..core.config_manager import DatabaseConfig


class DatabaseManager:
    """
    Async database manager for trading bot data storage.

    Handles:
    - Trade history logging
    - Market data storage
    - Signal tracking
    - Performance analytics
    - System metrics
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Any] = None
        self.sqlite_path: Optional[Path] = None

        # Determine database type
        if config.host == "localhost" and hasattr(config, "path"):
            self.use_sqlite = True
            self.sqlite_path = Path(config.database)
        else:
            self.use_sqlite = False

    async def initialize(self):
        """Initialize database connections and create tables."""
        if self.use_sqlite:
            self._init_sqlite()
        else:
            await self._init_postgresql()

        await self._create_tables()

    def _init_sqlite(self):
        """Initialize SQLite database."""
        if self.sqlite_path:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    async def _init_postgresql(self):
        """Initialize PostgreSQL connection pool."""
        if not asyncpg:
            raise ImportError("asyncpg is required for PostgreSQL support")

        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    async def _create_tables(self):
        """Create necessary database tables."""
        schema_sql = """
        -- Trading signals table
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            signal_type VARCHAR(10) NOT NULL,
            price DECIMAL(20, 10) NOT NULL,
            stop_loss DECIMAL(20, 10),
            take_profit_1 DECIMAL(20, 10),
            take_profit_2 DECIMAL(20, 10),
            confidence DECIMAL(3, 2),
            reason TEXT,
            metadata JSONB,
            timestamp TIMESTAMP NOT NULL,
            executed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Trades table
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            entry_price DECIMAL(20, 10) NOT NULL,
            exit_price DECIMAL(20, 10),
            quantity DECIMAL(20, 8) NOT NULL,
            stop_loss DECIMAL(20, 10) NOT NULL,
            take_profit_1 DECIMAL(20, 10) NOT NULL,
            take_profit_2 DECIMAL(20, 10) NOT NULL,
            tp1_hit BOOLEAN DEFAULT FALSE,
            tp2_hit BOOLEAN DEFAULT FALSE,
            opened_at TIMESTAMP NOT NULL,
            closed_at TIMESTAMP,
            pnl DECIMAL(20, 10),
            pnl_pct DECIMAL(10, 4),
            exit_reason VARCHAR(50),
            signal_reason TEXT,
            confidence DECIMAL(3, 2),
            strategy VARCHAR(50),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- OHLCV market data table
        CREATE TABLE IF NOT EXISTS ohlcv_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open_price DECIMAL(20, 10) NOT NULL,
            high_price DECIMAL(20, 10) NOT NULL,
            low_price DECIMAL(20, 10) NOT NULL,
            close_price DECIMAL(20, 10) NOT NULL,
            volume DECIMAL(20, 8) NOT NULL,
            source VARCHAR(20) DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp, source)
        );
        
        -- System metrics table
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            cpu_usage DECIMAL(5, 2),
            memory_usage DECIMAL(5, 2),
            cpu_temp DECIMAL(5, 2),
            disk_usage DECIMAL(5, 2),
            network_sent BIGINT,
            network_recv BIGINT,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Create indexes
        indexes_sql = [
            (
                "CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp "
                "ON signals(symbol, timestamp DESC);"
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_trades_symbol_opened "
                "ON trades(symbol, opened_at DESC);"
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timestamp "
                "ON ohlcv_data(symbol, timestamp DESC);"
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp "
                "ON system_metrics(timestamp DESC);"
            ),
        ]

        await self._execute_schema(schema_sql)

        for index_sql in indexes_sql:
            await self._execute_schema(index_sql)

    async def _execute_schema(self, schema_sql: str):
        """Execute schema SQL for table creation."""
        if self.use_sqlite:
            # For SQLite, modify SQL syntax
            sqlite_sql = schema_sql.replace("SERIAL", "INTEGER")
            sqlite_sql = sqlite_sql.replace("JSONB", "TEXT")
            sqlite_sql = sqlite_sql.replace("DECIMAL(20, 10)", "REAL")
            sqlite_sql = sqlite_sql.replace("DECIMAL(20, 8)", "REAL")
            sqlite_sql = sqlite_sql.replace("DECIMAL(5, 2)", "REAL")
            sqlite_sql = sqlite_sql.replace("DECIMAL(3, 2)", "REAL")
            sqlite_sql = sqlite_sql.replace("DECIMAL(10, 4)", "REAL")
            sqlite_sql = sqlite_sql.replace("BIGINT", "INTEGER")
            sqlite_sql = sqlite_sql.replace("CURRENT_TIMESTAMP", "datetime('now')")

            if self.sqlite_path:
                with sqlite3.connect(str(self.sqlite_path)) as conn:
                    conn.executescript(sqlite_sql)
        else:
            if self.pool:
                async with self.pool.acquire() as conn:
                    await conn.execute(schema_sql)

    async def log_signal(self, signal_data: Dict[str, Any]) -> int:
        """Log trading signal to database."""
        sql = """
        INSERT INTO signals (
            symbol, signal_type, price, stop_loss, take_profit_1,
            take_profit_2, confidence, reason, metadata, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
        """

        values = (
            signal_data.get("symbol"),
            signal_data.get("signal_type"),
            signal_data.get("price"),
            signal_data.get("stop_loss"),
            signal_data.get("take_profit_1"),
            signal_data.get("take_profit_2"),
            signal_data.get("confidence"),
            signal_data.get("reason"),
            json.dumps(signal_data.get("metadata", {})),
            signal_data.get("timestamp"),
        )

        result = await self._execute_returning(sql, values)
        return result if result is not None else 0

    async def log_trade_event(self, trade_data: Dict[str, Any]):
        """Log trade event (open/close position)."""
        action = trade_data.get("action")

        if action == "open_position":
            await self._log_trade_open(trade_data)
        elif action in ["stop_loss", "take_profit_1", "take_profit_2", "manual_close"]:
            await self._log_trade_close(trade_data)

    async def _log_trade_open(self, trade_data: Dict[str, Any]):
        """Log opening of new trade position."""
        position = trade_data.get("position", {})
        signal = trade_data.get("signal", {})

        sql = """
        INSERT INTO trades (
            symbol, side, entry_price, quantity, stop_loss,
            take_profit_1, take_profit_2, opened_at, signal_reason,
            confidence, strategy, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """

        values = (
            position.get("symbol"),
            position.get("side"),
            position.get("entry_price"),
            position.get("quantity"),
            position.get("stop_loss"),
            position.get("take_profit_1"),
            position.get("take_profit_2"),
            position.get("opened_at"),
            signal.get("reason"),
            signal.get("confidence"),
            position.get("strategy"),
            json.dumps(trade_data),
        )

        await self._execute(sql, values)

    async def _log_trade_close(self, trade_data: Dict[str, Any]):
        """Log closing of trade position."""
        position = trade_data.get("position", {})
        action = trade_data.get("action")

        if action == "take_profit_1":
            sql = """
            UPDATE trades SET tp1_hit = TRUE, metadata = $2
            WHERE symbol = $1 AND closed_at IS NULL
            """
            values = (position.get("symbol"), json.dumps(trade_data))
        else:
            sql = """
            UPDATE trades SET
                exit_price = $2, closed_at = $3, pnl = $4, pnl_pct = $5,
                exit_reason = $6, tp2_hit = $7, metadata = $8
            WHERE symbol = $1 AND closed_at IS NULL
            """
            values = (
                position.get("symbol"),
                position.get("current_price"),
                datetime.now(tz=timezone.utc),
                position.get("realized_pnl"),
                position.get("pnl_percentage", 0),
                action,
                action == "take_profit_2",
                json.dumps(trade_data),
            )

        await self._execute(sql, values)

    async def log_ohlcv_data(self, ohlcv_data: Dict[str, Any]):
        """Log OHLCV market data."""
        sql = """
        INSERT INTO ohlcv_data (
            symbol, timestamp, open_price, high_price, low_price,
            close_price, volume, source
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (symbol, timestamp, source) DO NOTHING
        """

        values = (
            ohlcv_data.get("symbol"),
            ohlcv_data.get("timestamp"),
            ohlcv_data.get("open"),
            ohlcv_data.get("high"),
            ohlcv_data.get("low"),
            ohlcv_data.get("close"),
            ohlcv_data.get("volume"),
            ohlcv_data.get("source", "websocket"),
        )

        await self._execute(sql, values)

    async def log_system_metrics(self, metrics: Dict[str, Any]):
        """Log system performance metrics."""
        sql = """
        INSERT INTO system_metrics (
            cpu_usage, memory_usage, cpu_temp, disk_usage,
            network_sent, network_recv, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """

        values = (
            metrics.get("cpu_usage"),
            metrics.get("memory_usage"),
            metrics.get("cpu_temp"),
            metrics.get("disk_usage"),
            metrics.get("network_sent"),
            metrics.get("network_recv"),
            metrics.get("timestamp", datetime.now(tz=timezone.utc)),
        )

        await self._execute(sql, values)

    async def get_trade_history(
        self, limit: int = 50, symbol: Optional[str] = None
    ) -> List[Dict]:
        """Get recent trade history."""
        sql = """
        SELECT * FROM trades
        WHERE ($2 IS NULL OR symbol = $2)
        ORDER BY opened_at DESC
        LIMIT $1
        """

        return await self._fetch_all(sql, (limit, symbol))

    async def get_trading_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get trading performance statistics."""
        if self.use_sqlite:
            sql = (
                """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                AVG(pnl) as avg_pnl,
                SUM(pnl) as total_pnl,
                MAX(pnl) as max_win,
                MIN(pnl) as max_loss,
                AVG(confidence) as avg_confidence
            FROM trades 
            WHERE opened_at >= datetime('now', '-%d days')
            """
                % days
            )
        else:
            sql = (
                """
            SELECT 
                COUNT(*) as total_trades,
                COUNT(*) FILTER (WHERE pnl > 0) as winning_trades,
                AVG(pnl) as avg_pnl,
                SUM(pnl) as total_pnl,
                MAX(pnl) as max_win,
                MIN(pnl) as max_loss,
                AVG(confidence) as avg_confidence
            FROM trades 
            WHERE opened_at >= NOW() - INTERVAL '%d days'
            """
                % days
            )

        result = await self._fetch_one(sql)

        if result:
            win_rate = 0
            if result["total_trades"] > 0:
                win_rate = (result["winning_trades"] / result["total_trades"]) * 100

            return {
                "total_trades": result["total_trades"],
                "winning_trades": result["winning_trades"],
                "win_rate": round(win_rate, 2),
                "avg_pnl": (float(result["avg_pnl"]) if result["avg_pnl"] else 0),
                "total_pnl": (float(result["total_pnl"]) if result["total_pnl"] else 0),
                "max_win": (float(result["max_win"]) if result["max_win"] else 0),
                "max_loss": (float(result["max_loss"]) if result["max_loss"] else 0),
                "avg_confidence": (
                    float(result["avg_confidence"]) if result["avg_confidence"] else 0
                ),
            }

        return {}

    async def _execute(self, sql: str, values: Optional[tuple] = None):
        """Execute SQL command."""
        if self.use_sqlite:
            if self.sqlite_path:
                with sqlite3.connect(str(self.sqlite_path)) as conn:
                    conn.execute(sql, values or ())
        else:
            if self.pool and values:
                async with self.pool.acquire() as conn:
                    await conn.execute(sql, *values)

    async def _execute_returning(self, sql: str, values: tuple) -> Optional[int]:
        """Execute SQL command and return ID."""
        if self.use_sqlite:
            if self.sqlite_path:
                with sqlite3.connect(str(self.sqlite_path)) as conn:
                    cursor = conn.execute(sql, values)
                    return cursor.lastrowid
        else:
            if self.pool:
                async with self.pool.acquire() as conn:
                    return await conn.fetchval(sql, *values)
        return None

    async def _fetch_one(
        self, sql: str, values: Optional[tuple] = None
    ) -> Optional[Dict]:
        """Fetch single row."""
        if self.use_sqlite:
            if self.sqlite_path:
                with sqlite3.connect(str(self.sqlite_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(sql, values or ())
                    row = cursor.fetchone()
                    return dict(row) if row else None
        else:
            if self.pool:
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(sql, *(values or ()))
                    return dict(row) if row else None
        return None

    async def _fetch_all(self, sql: str, values: Optional[tuple] = None) -> List[Dict]:
        """Fetch all rows."""
        if self.use_sqlite:
            if self.sqlite_path:
                with sqlite3.connect(str(self.sqlite_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(sql, values or ())
                    return [dict(row) for row in cursor.fetchall()]
        else:
            if self.pool:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(sql, *(values or ()))
                    return [dict(row) for row in rows]
        return []

    async def close(self):
        """Close database connections."""
        if self.pool:
            await self.pool.close()
