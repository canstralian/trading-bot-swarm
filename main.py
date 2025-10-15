"""
NOICE Trading Bot - Main Application Entry Point
Orchestrates all components for autonomous trading on Raspberry Pi 5.
"""

import asyncio
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.config_manager import ConfigManager
from src.core.trading_engine import TradingEngine
from src.utils.logger import setup_logging
from src.utils.database import DatabaseManager
from src.utils.monitoring import SystemMonitor


class NOICETradingBot:
    """
    Main trading bot application for NOICE token.

    Features:
    - Real-time market data processing
    - Advanced technical analysis
    - Risk-managed trade execution
    - System monitoring and alerts
    - Database logging and analytics
    """

    def __init__(
        self, config_path: str = "config/config.yaml", environment: str = "development"
    ):
        """
        Initialize the NOICE trading bot.

        Args:
            config_path: Path to configuration file
            environment: Environment (development/production)
        """
        self.environment = environment
        self.logger: Optional[logging.Logger] = None
        self.config: Optional[ConfigManager] = None
        self.trading_engine: Optional[TradingEngine] = None
        self.database: Optional[DatabaseManager] = None
        self.monitor: Optional[SystemMonitor] = None
        self.shutdown_event = asyncio.Event()

        # Initialize components
        self._setup_config(config_path, environment)
        self._setup_logging()
        self._setup_signal_handlers()
        self._setup_components()

    def _setup_config(self, config_path: str, environment: str):
        """Setup configuration manager."""
        try:
            self.config = ConfigManager(config_path, environment)
            print(f"Configuration loaded for environment: {environment}")
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """Setup logging system."""
        try:
            log_config = self.config.get("logging", {})
            self.logger = setup_logging(
                level=log_config.get("level", "INFO"),
                log_dir=log_config.get("directory", "logs"),
                app_name="noice_trading_bot",
            )
            self.logger.info("Logging system initialized")
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            sys.exit(1)

    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self._shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _setup_components(self):
        """Initialize all trading bot components."""
        try:
            # Database manager
            self.database = DatabaseManager(self.config.get_database_config())

            # System monitor
            self.monitor = SystemMonitor(
                rpi_config=self.config.get("raspberry_pi", {}),
                alert_thresholds=self.config.get("monitoring.alerts", {}),
            )

            # Trading engine
            self.trading_engine = TradingEngine(self.config)

            # Add trade callback for database logging
            self.trading_engine.add_trade_callback(self._on_trade_event)

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise

    def _on_trade_event(self, trade_data: dict):
        """
        Handle trade events for logging and monitoring.

        Args:
            trade_data: Trade event data
        """
        try:
            # Log trade to database
            if self.database:
                asyncio.create_task(self.database.log_trade_event(trade_data))

            # Send alerts if configured
            if trade_data["action"] in ["open_position", "stop_loss"]:
                self._send_trade_alert(trade_data)

            self.logger.info(
                f"Trade event: {trade_data['action']} for {trade_data.get('symbol', 'unknown')}"
            )

        except Exception as e:
            self.logger.error(f"Error handling trade event: {e}")

    def _send_trade_alert(self, trade_data: dict):
        """Send trade alerts via configured channels."""
        # Implementation for Telegram/Discord/Email alerts
        # This would be implemented based on configuration
        pass

    async def _run_health_checks(self):
        """Run periodic health checks."""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Check every minute

                if self.monitor:
                    health_status = await self.monitor.get_system_health()

                    # Log system metrics
                    self.logger.debug(f"System health: {health_status}")

                    # Check for critical issues
                    if health_status.get("cpu_temp", 0) > 75:
                        self.logger.warning("High CPU temperature detected")

                    if health_status.get("memory_usage", 0) > 90:
                        self.logger.warning("High memory usage detected")

            except Exception as e:
                self.logger.error(f"Error in health check: {e}")

    async def start(self):
        """Start the trading bot."""
        try:
            self.logger.info("🚀 Starting NOICE Trading Bot...")
            self.logger.info(f"Environment: {self.environment}")
            self.logger.info(
                f"Symbol: {self.config.get('trading.symbol', 'NOICEUSDT')}"
            )
            self.logger.info(f"Capital: ${self.config.get('trading.capital', 0):,.2f}")

            # Initialize database
            if self.database:
                await self.database.initialize()
                self.logger.info("Database initialized")

            # Start system monitoring
            if self.monitor:
                await self.monitor.start()
                self.logger.info("System monitoring started")

            # Start trading engine
            if self.trading_engine:
                await self.trading_engine.start()
                self.logger.info("Trading engine started")

            # Start health check loop
            health_task = asyncio.create_task(self._run_health_checks())

            self.logger.info("✅ NOICE Trading Bot started successfully!")
            self.logger.info("Bot is now monitoring markets and ready to trade...")

            # Wait for shutdown signal
            await self.shutdown_event.wait()

            # Cancel health checks
            health_task.cancel()

            self.logger.info("Shutdown signal received, stopping bot...")

        except Exception as e:
            self.logger.error(f"Error starting trading bot: {e}")
            raise

    async def _shutdown(self):
        """Graceful shutdown of all components."""
        try:
            self.logger.info("Initiating graceful shutdown...")

            # Stop trading engine
            if self.trading_engine:
                self.trading_engine.stop()
                self.logger.info("Trading engine stopped")

            # Stop monitoring
            if self.monitor:
                await self.monitor.stop()
                self.logger.info("System monitoring stopped")

            # Close database connections
            if self.database:
                await self.database.close()
                self.logger.info("Database connections closed")

            # Signal shutdown complete
            self.shutdown_event.set()

            self.logger.info("Graceful shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.shutdown_event.set()

    def get_status(self) -> dict:
        """Get comprehensive bot status."""
        status = {
            "bot": {
                "environment": self.environment,
                "start_time": datetime.now().isoformat(),
                "status": "running" if not self.shutdown_event.is_set() else "stopped",
            }
        }

        if self.trading_engine:
            status["trading"] = self.trading_engine.get_status()

        if self.monitor:
            status["system"] = self.monitor.get_current_metrics()

        return status


async def main():
    """Main entry point for the trading bot."""
    import argparse

    parser = argparse.ArgumentParser(description="NOICE Trading Bot")
    parser.add_argument(
        "--env",
        choices=["development", "production", "testing"],
        default="development",
        help="Environment to run in",
    )
    parser.add_argument(
        "--config", default="config/config.yaml", help="Path to configuration file"
    )
    parser.add_argument(
        "--no-trading",
        action="store_true",
        help="Run in monitoring mode only (no trading)",
    )

    args = parser.parse_args()

    # Create and start the bot
    bot = NOICETradingBot(config_path=args.config, environment=args.env)

    if args.no_trading:
        bot.trading_engine.disable_trading()
        print("Trading disabled - running in monitoring mode only")

    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Failed to start bot: {e}")
        sys.exit(1)
