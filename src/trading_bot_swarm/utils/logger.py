"""
Logging utilities for the trading bot.
Provides structured logging with file rotation and multiple output formats.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.RESET}"


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "trading_bot",
    max_file_size: str = "10MB",
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup comprehensive logging system.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        app_name: Application name for log files
        max_file_size: Maximum size per log file
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Convert max_file_size to bytes
    size_units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    if max_file_size.endswith(("B", "KB", "MB", "GB")):
        for unit, multiplier in size_units.items():
            if max_file_size.endswith(unit):
                max_bytes = int(max_file_size[: -len(unit)]) * multiplier
                break
    else:
        max_bytes = int(max_file_size)

    # Configure root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = ColoredFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Main log file with rotation
    main_log_file = log_path / f"{app_name}.log"
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    main_handler.setLevel(logging.DEBUG)
    main_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    main_handler.setFormatter(main_format)
    logger.addHandler(main_handler)

    # Trading-specific log file
    trading_log_file = log_path / f"{app_name}_trading.log"
    trading_handler = logging.handlers.RotatingFileHandler(
        trading_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    trading_handler.setLevel(logging.INFO)
    trading_handler.addFilter(TradingLogFilter())
    trading_handler.setFormatter(main_format)
    logger.addHandler(trading_handler)

    # Error log file
    error_log_file = log_path / f"{app_name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(main_format)
    logger.addHandler(error_handler)

    return logger


class TradingLogFilter(logging.Filter):
    """Filter to capture only trading-related log messages."""

    TRADING_KEYWORDS = [
        "signal",
        "trade",
        "position",
        "order",
        "buy",
        "sell",
        "profit",
        "loss",
        "stop",
        "entry",
        "exit",
        "portfolio",
    ]

    def filter(self, record):
        """Check if log record contains trading-related keywords."""
        message = record.getMessage().lower()
        return any(keyword in message for keyword in self.TRADING_KEYWORDS)


class PerformanceLogger:
    """Logger for performance metrics and timing."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}

    def start_timer(self, name: str):
        """Start a performance timer."""
        self.timers[name] = datetime.now()

    def end_timer(self, name: str, message: Optional[str] = None):
        """End a performance timer and log the duration."""
        if name not in self.timers:
            self.logger.warning(f"Timer '{name}' was not started")
            return

        duration = (datetime.now() - self.timers[name]).total_seconds()
        log_message = message or f"Timer '{name}' completed"
        self.logger.debug(f"{log_message} - Duration: {duration:.3f}s")

        del self.timers[name]
        return duration


class StructuredLogger:
    """Logger with structured data support."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_trade_signal(self, signal_data: dict):
        """Log trading signal with structured data."""
        self.logger.info(
            f"SIGNAL | {signal_data.get('type')} | "
            f"{signal_data.get('symbol')} | "
            f"Price: {signal_data.get('price', 0):.6f} | "
            f"Confidence: {signal_data.get('confidence', 0):.2f}"
        )

    def log_trade_execution(self, trade_data: dict):
        """Log trade execution with structured data."""
        self.logger.info(
            f"TRADE | {trade_data.get('action')} | "
            f"{trade_data.get('symbol')} | "
            f"Qty: {trade_data.get('quantity', 0):.6f} | "
            f"Price: {trade_data.get('price', 0):.6f}"
        )

    def log_position_update(self, position_data: dict):
        """Log position update with structured data."""
        self.logger.info(
            f"POSITION | {position_data.get('symbol')} | "
            f"PnL: {position_data.get('pnl', 0):.2f} | "
            f"Status: {position_data.get('status')}"
        )

    def log_system_metrics(self, metrics: dict):
        """Log system performance metrics."""
        self.logger.debug(
            f"SYSTEM | CPU: {metrics.get('cpu_usage', 0):.1f}% | "
            f"Memory: {metrics.get('memory_usage', 0):.1f}% | "
            f"Temp: {metrics.get('cpu_temp', 0):.1f}°C"
        )


# Create module-level performance logger instance
_performance_logger = None


def get_performance_logger() -> PerformanceLogger:
    """Get or create performance logger instance."""
    global _performance_logger
    if _performance_logger is None:
        base_logger = logging.getLogger("performance")
        _performance_logger = PerformanceLogger(base_logger)
    return _performance_logger
