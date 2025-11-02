# Usage Guide

This guide describes how to operate the Trading Bot Swarm package in development, staging, and production environments.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install trading-bot-swarm  # once published to PyPI
# or install from source
pip install -e .[dev]
```

The `[dev]` extra installs formatting, linting, and testing dependencies.

## Environment Setup

1. **Configuration** – copy `config/config.yaml` and adjust symbols, risk tolerances, and exchange credentials.
2. **Secrets** – populate environment variables (see [Configuration](CONFIGURATION.md)) or provide an encrypted `.secret.key` and encrypted values via `ConfigManager`.
3. **Database** – configure PostgreSQL or SQLite via `database` settings. The default uses SQLite for local development.

## Running the Orchestrator

```bash
python main.py --env development
```

The orchestrator performs the following steps:

1. Loads configuration using `ConfigManager` with environment overrides.
2. Configures structured logging.
3. Initializes the database manager, system monitor, and trading engine.
4. Starts the trading loop with async health checks and graceful shutdown handlers.

Use `--env production` to load `config/production.yaml` overrides and disable testnet mode.

## Observability

- Logs are written to the directory defined in the configuration (`logging.directory`).
- `SystemMonitor` produces CPU, memory, disk, and temperature metrics which can be forwarded to Prometheus or other sinks.
- Trade events are emitted through `TradingEngine.add_trade_callback`; hook in alerting systems (Telegram/Slack/etc.) as required.

## Maintenance Tasks

| Task                        | Command              |
| --------------------------- | -------------------- |
| Run unit tests              | `pytest -q`          |
| Test with coverage          | `make test-cov`      |
| Format + lint               | `make format lint`   |
| Security & dependency audit | `make security`      |

For containerised deployments see `docker-compose.yml` and the [Production Runbook](PRODUCTION_DEPLOYMENT_RUNBOOK.md).
