# Trading Bot Swarm

[![CI](https://github.com/canstralian/trading-bot-swarm/actions/workflows/ci.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/ci.yml)
[![CodeQL Analysis](https://github.com/canstralian/trading-bot-swarm/actions/workflows/codeql.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/codeql.yml)
[![Docker Build](https://github.com/canstralian/trading-bot-swarm/actions/workflows/docker.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/docker.yml)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000?logo=python&logoColor=white)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/github/actions/workflow/status/canstralian/trading-bot-swarm/tests.yml?label=Tests&logo=pytest&logoColor=white)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/codecov/c/github/canstralian/trading-bot-swarm?label=Coverage&logo=codecov&logoColor=white)](https://codecov.io/gh/canstralian/trading-bot-swarm)
[![Docs](https://img.shields.io/badge/Docs-Available-green?logo=readthedocs&logoColor=white)](https://canstralian.github.io/trading-bot-swarm)
[![Security Scans](https://img.shields.io/badge/Security-Passed-success?logo=dependabot&logoColor=white)](https://github.com/canstralian/trading-bot-swarm/security)
[![Container Size](https://img.shields.io/docker/image-size/canstralian/trading-bot-swarm/latest?logo=docker&logoColor=white)](https://hub.docker.com/r/canstralian/trading-bot-swarm)

A sophisticated, multi-bot platform for orchestrating automated trading strategies across various cryptocurrency exchanges. This system is designed for scalability, allowing a "swarm" of bots to operate independently while being managed and monitored from a central point.

## Features

*   **Multi-Bot Architecture:** Run multiple trading bots simultaneously, each with its own strategy and configuration.
*   **Strategy Engine:** Supports a variety of trading strategies, including:
    *   Trend Following
    *   Mean Reversion
    *   Momentum
    *   (and easily extensible for more)
*   **Centralized Orchestration:** A core engine to manage, monitor, and control the entire swarm of bots.
*   **Market Data Analysis:** Integrates with various data sources and technical analysis libraries to inform trading decisions.
*   **Portfolio Management:** Tracks capital, positions, and performance across all bots.
*   **Risk Management:** Implements risk controls such as stop-loss and take-profit orders.
*   **Extensible and Modular:** The project is structured to be easily extended with new bots, strategies, and exchange integrations.
*   **Ready for Monitoring:** Includes support for Prometheus and Grafana for monitoring bot performance and system health.

## Tech Stack

This project is built with a modern Python stack, including:

*   **Core:** Python 3.12+
*   **Trading & Data:** `ccxt`, `yfinance`, `ta-lib`, `python-binance`, `alpaca-trade-api`
*   **Web & API:** `fastapi`, `uvicorn`, `websockets`
*   **Data Analysis & ML:** `numpy`, `pandas`, `scikit-learn`, `tensorflow`, `torch`
*   **Database:** `redis`, `sqlalchemy` (for PostgreSQL, etc.), `sqlite3`
*   **Async & Concurrency:** `asyncio`, `celery`, `zmq`
*   **Testing:** `pytest`, `pytest-asyncio`
*   **Code Quality:** `black`, `flake8`, `mypy`

## Getting Started

### Prerequisites

*   Python 3.12 or higher
*   Git
*   Docker and Docker Compose (optional, for containerized deployment)

## Development Environment Setup

The development environment is designed for local testing and debugging with minimal setup.

### Quick Start (Development)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/canstralian/trading-bot-swarm.git
    cd trading-bot-swarm
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt  # Development tools
    ```

4.  **Set up development configuration:**
    ```bash
    # Use the pre-configured development environment
    cp config/.env.development config/.env
    # Edit config/.env with your testnet API keys (optional)
    ```

5.  **Run the application in development mode:**
    ```bash
    python main.py --env development
    ```

### Development Features

*   **Database:** Uses SQLite (`data/trading_bot_dev.db`) - no external database required
*   **Debug Mode:** Enabled with verbose logging (`LOG_LEVEL=DEBUG`)
*   **Test Mode:** Safe trading with testnet/paper trading APIs
*   **Hot Reload:** Code changes are reflected immediately
*   **Testing:** Integrated with pytest and coverage reporting

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_environment.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=src --cov-report=html
```

### Code Quality Tools

```bash
# Format code with Black
black .

# Check code style
flake8 .

# Type checking
mypy src/

# Run all quality checks
black --check . && flake8 . && mypy src/
```

## Staging Environment Setup

The staging environment mimics production for final testing before deployment.

### Prerequisites for Staging

*   Linux server (Ubuntu 20.04+ recommended)
*   Docker and Docker Compose installed
*   PostgreSQL 15+
*   Redis 7+
*   Nginx (for reverse proxy)
*   Access to staging server via SSH

### Staging Deployment

#### Manual Deployment

1.  **Prepare the server:**
    ```bash
    # On your staging server
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose nginx
    sudo systemctl enable docker
    sudo systemctl start docker
    ```

2.  **Clone and configure:**
    ```bash
    cd /opt
    sudo git clone https://github.com/canstralian/trading-bot-swarm.git
    cd trading-bot-swarm
    
    # Set up staging environment variables
    sudo cp config/.env.staging config/.env
    # Edit config/.env with your staging credentials
    sudo nano config/.env
    ```

3.  **Deploy with Docker Compose:**
    ```bash
    sudo docker-compose -f docker-compose.staging.yml up -d
    ```

4.  **Verify deployment:**
    ```bash
    sudo docker-compose -f docker-compose.staging.yml ps
    curl http://localhost:8080/health
    ```

#### Automated Deployment via GitHub Actions

The project includes automated staging deployment via GitHub Actions.

**Setup Required Secrets:**

In your GitHub repository settings, add these secrets:

*   `STAGING_HOST` - Staging server hostname/IP
*   `STAGING_USER` - SSH username
*   `STAGING_SSH_KEY` - SSH private key for deployment
*   `STAGING_PORT` - SSH port (default: 22)
*   `STAGING_POSTGRES_HOST` - PostgreSQL host
*   `STAGING_POSTGRES_USER` - PostgreSQL username
*   `STAGING_POSTGRES_PASSWORD` - PostgreSQL password
*   `STAGING_REDIS_HOST` - Redis host
*   `STAGING_REDIS_PASSWORD` - Redis password
*   `STAGING_SENTRY_DSN` - Sentry DSN for error tracking
*   `DOCKER_USERNAME` - Docker Hub username
*   `DOCKER_PASSWORD` - Docker Hub password

**Deployment Trigger:**

Push to `develop` or `staging` branches triggers automatic deployment:

```bash
git push origin develop
```

### Staging Features

*   **Database:** PostgreSQL with connection pooling
*   **Caching:** Redis for session and data caching
*   **Web Server:** Gunicorn with multiple workers
*   **Reverse Proxy:** Nginx for load balancing and SSL
*   **Monitoring:** Prometheus + Grafana dashboards
*   **Error Tracking:** Sentry integration for real-time error monitoring
*   **Logging:** Centralized logging with rotation
*   **CI/CD:** Automated testing and deployment

### Monitoring Staging Environment

Access monitoring tools:

*   **Application:** `http://your-staging-server:8080`
*   **Prometheus:** `http://your-staging-server:9090`
*   **Grafana:** `http://your-staging-server:3000` (default: admin/admin)
*   **Logs:** `docker-compose -f docker-compose.staging.yml logs -f`

### Staging Configuration

Key staging settings in `config/.env.staging`:

*   Uses PostgreSQL for database (production-like)
*   Gunicorn with 4 workers and 2 threads
*   Sentry error tracking enabled
*   Prometheus metrics collection enabled
*   Debug mode disabled
*   Paper trading mode (safe for testing)

## Usage

### Running in Different Environments

```bash
# Development (default)
python main.py --env development

# Staging
python main.py --env staging

# Production
python main.py --env production

# Monitoring mode only (no trading)
python main.py --env development --no-trading
```

### Configuration

Environment-specific configurations are managed through:

*   `config/.env.development` - Development environment variables
*   `config/.env.staging` - Staging environment variables
*   `config/config.yaml` - Shared application configuration

Make sure to review and customize these files for your trading strategies and bot configurations.

## Project Structure

```
├── config/             # Configuration files
├── data/               # Data files (e.g., historical data)
├── logs/               # Log files
├── src/                # Source code
│   ├── bots/           # Individual trading bot implementations
│   ├── core/           # Core components (trading engine, portfolio, etc.)
│   ├── strategies/     # Trading strategy implementations
│   ├── utils/          # Utility functions (database, logger)
│   └── swarm/          # (Likely for swarm management and communication)
├── tests/              # Test files
├── main.py             # Main application entry point
├── requirements.txt    # Project dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
