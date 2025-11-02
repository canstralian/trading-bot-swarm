# API Reference

This document provides a high-level reference for the most commonly used classes and modules. See the source code for full details.

## `core` package

### `ConfigManager`
- Loads layered YAML configuration files and environment overrides.
- Provides typed dataclasses: `TradingConfig`, `ExchangeConfig`, and `DatabaseConfig`.
- Methods: `get(path, default)`, `encrypt_value`, `decrypt_value`, `is_production`, `is_testnet`.

### `TradingEngine`
- Main orchestrator coordinating market data, strategies, and risk controls.
- Call `TradingEngine.add_trade_callback(callback)` to subscribe to trade lifecycle events.
- Exposes metrics such as `signals_generated`, `trades_executed`, and `last_signal`.

### `RiskManager`
- Validates signals against drawdown, exposure, and risk/reward thresholds.
- `calculate_position_size(signal)` returns quantity sized by risk-per-trade.
- `open_position`, `update_position`, and `close_position` manage lifecycle and PnL.
- `get_portfolio_summary()` aggregates win-rate, capital, and exposure.

## `strategies` package

All strategies inherit from `StrategyInterface` and must implement:
- `update(OHLCVData) -> Optional[TradingSignal]`
- `get_required_history() -> int`

Provided implementations (`TrendFollowingStrategy`, `MeanReversionStrategy`, `MomentumStrategy`, `NOICEStrategy`) operate on pandas DataFrames and return `TradingSignal` dataclasses.

## `utils` package

### `logger.setup_logging`
- Configures rotating file handlers and stdout logging using standard `logging`.

### `database.DatabaseManager`
- Async interface for SQLite or PostgreSQL connections.
- Methods: `initialize()`, `log_signal`, `log_trade`, `log_market_data`, `log_system_metrics`.

### `monitoring.SystemMonitor`
- Async metrics collector returning CPU, memory, disk, network, and temperature data.
- `watch(callback, stop_event)` streams metrics to a coroutine-friendly consumer.

### `rpi_utils.RPiUtils`
- Raspberry Pi helpers: `is_raspberry_pi`, `get_cpu_temperature`, `get_gpu_temperature`, `get_serial_number`.

## Entry Point (`main.py`)

`NOICETradingBot` wires all components together. Instantiate with a configuration path and environment, then call `asyncio.run(bot.start())` (implicit via CLI entry point) to begin trading.
