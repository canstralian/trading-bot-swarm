# Environment Setup Guide

This document provides detailed instructions for setting up and configuring development and staging environments for the Trading Bot Swarm project.

## Table of Contents

1. [Overview](#overview)
2. [Development Environment](#development-environment)
3. [Staging Environment](#staging-environment)
4. [Environment Variables](#environment-variables)
5. [Database Configuration](#database-configuration)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Overview

The Trading Bot Swarm project supports multiple environments, each optimized for different stages of the development lifecycle:

- **Development**: Local development with SQLite, debug logging, and hot reload
- **Staging**: Production-like environment with PostgreSQL, Gunicorn, and monitoring
- **Production**: Full production deployment (see separate production documentation)

## Development Environment

### Purpose

The development environment is designed for:
- Local code development and testing
- Quick iteration and debugging
- Safe experimentation without affecting production data
- Minimal setup requirements

### Configuration

#### Database
- **Type**: SQLite
- **Location**: `data/trading_bot_dev.db`
- **Rationale**: No external database server required, easy to reset and test

#### Python Environment
- **Setup**: Virtual environment with `venv`
- **Dependencies**: Installed via `requirements.txt` and `requirements-dev.txt`
- **Hot Reload**: Automatic code reload on changes (when using development server)

#### Trading APIs
- **Binance**: Testnet mode enabled (`BINANCE_TESTNET=true`)
- **Alpaca**: Paper trading mode (`ALPACA_BASE_URL=https://paper-api.alpaca.markets`)
- **Safety**: Real trading disabled (`ENABLE_REAL_TRADING=false`)

#### Logging
- **Level**: DEBUG
- **Output**: Console and file (`logs/`)
- **Format**: Detailed with timestamps and module names

### Quick Start

```bash
# 1. Clone and navigate to repository
git clone https://github.com/canstralian/trading-bot-swarm.git
cd trading-bot-swarm

# 2. Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure environment
cp config/.env.development config/.env
# Edit config/.env with your testnet API keys (optional)

# 5. Run the application
python main.py --env development
```

### Development Tools

#### Testing Framework
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_environment.py -v

# Run tests in watch mode (with pytest-watch)
ptw
```

#### Code Quality
```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy src/

# Run all checks
make lint  # if Makefile exists
```

#### Debugging
```bash
# Run with Python debugger
python -m pdb main.py --env development

# Run with IPython enhanced debugger (ipdb)
python -m ipdb main.py --env development
```

### Directory Structure

```
trading-bot-swarm/
├── config/
│   ├── .env.development      # Development environment variables
│   ├── .env.staging          # Staging environment variables
│   └── config.yaml           # Shared configuration
├── data/                     # SQLite database (gitignored)
├── logs/                     # Log files (gitignored)
├── src/                      # Source code
├── tests/                    # Test files
├── requirements.txt          # Production dependencies
└── requirements-dev.txt      # Development dependencies
```

## Staging Environment

### Purpose

The staging environment is designed for:
- Final testing before production deployment
- Performance testing under production-like conditions
- Integration testing with external services
- QA and acceptance testing

### Configuration

#### Database
- **Type**: PostgreSQL 15+
- **Schema**: `trading_swarm_staging`
- **Connection Pooling**: Enabled (10 connections, max 20)
- **Rationale**: Production-compatible database with better performance

#### Web Server
- **Server**: Gunicorn
- **Workers**: 4 (configurable via `GUNICORN_WORKERS`)
- **Threads**: 2 per worker
- **Bind**: 0.0.0.0:8080
- **Timeout**: 120 seconds

#### Reverse Proxy
- **Server**: Nginx
- **Features**: 
  - Load balancing
  - SSL/TLS termination
  - Rate limiting (10 req/s for API, 30 req/s general)
  - Static file serving
  - WebSocket support

#### Monitoring
- **Prometheus**: Metrics collection on port 9090
- **Grafana**: Dashboards on port 3000
- **Sentry**: Error tracking and performance monitoring
- **Logging**: Centralized with rotation (10MB max, 3 files)

### Deployment Methods

#### Method 1: Docker Compose (Recommended)

```bash
# On staging server
cd /opt/trading-bot-swarm

# Pull latest changes
git pull origin develop

# Start all services
docker-compose -f docker-compose.staging.yml up -d

# View logs
docker-compose -f docker-compose.staging.yml logs -f

# Check status
docker-compose -f docker-compose.staging.yml ps
```

#### Method 2: GitHub Actions (Automated)

Automatic deployment triggers on push to `develop` or `staging` branches.

**Required GitHub Secrets:**
```
STAGING_HOST              # Server IP/hostname
STAGING_USER              # SSH username
STAGING_SSH_KEY           # SSH private key
STAGING_POSTGRES_HOST     # PostgreSQL host
STAGING_POSTGRES_USER     # PostgreSQL username
STAGING_POSTGRES_PASSWORD # PostgreSQL password
STAGING_REDIS_HOST        # Redis host
STAGING_REDIS_PASSWORD    # Redis password
STAGING_SENTRY_DSN        # Sentry DSN
DOCKER_USERNAME           # Docker Hub username
DOCKER_PASSWORD           # Docker Hub password
```

**Deployment Process:**
1. Push to `develop` branch
2. GitHub Actions runs tests
3. Builds Docker image
4. Pushes to Docker Hub
5. Deploys to staging server via SSH
6. Runs health checks
7. Notifies team (optional)

#### Method 3: Manual Deployment

```bash
# On staging server
cd /opt/trading-bot-swarm

# Set up environment
cp config/.env.staging config/.env
nano config/.env  # Edit with your credentials

# Build and run with Docker
docker build -t trading-bot-swarm:staging .
docker run -d \
  --name trading-bot-staging \
  --env-file config/.env \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  trading-bot-swarm:staging
```

### Monitoring and Maintenance

#### Access Monitoring Tools

```bash
# Application
http://staging-server:8080

# Prometheus metrics
http://staging-server:9090

# Grafana dashboards
http://staging-server:3000
# Default credentials: admin / admin (change immediately)

# View logs
docker-compose -f docker-compose.staging.yml logs -f trading-bot-staging
```

#### Health Checks

```bash
# Application health
curl http://staging-server:8080/health

# Database connection
docker-compose -f docker-compose.staging.yml exec postgres-staging pg_isready

# Redis connection
docker-compose -f docker-compose.staging.yml exec redis-staging redis-cli ping
```

#### Common Operations

```bash
# Restart services
docker-compose -f docker-compose.staging.yml restart

# Scale workers (if using multiple instances)
docker-compose -f docker-compose.staging.yml up -d --scale trading-bot-staging=3

# View resource usage
docker stats

# Clean up old containers and images
docker system prune -f
```

## Environment Variables

### Development Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment name |
| `DATABASE_TYPE` | `sqlite` | Database type |
| `SQLITE_PATH` | `data/trading_bot_dev.db` | SQLite database path |
| `DEBUG` | `true` | Enable debug mode |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `ENABLE_REAL_TRADING` | `false` | Enable real trading |
| `BINANCE_TESTNET` | `true` | Use Binance testnet |

### Staging Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `staging` | Environment name |
| `DATABASE_TYPE` | `postgresql` | Database type |
| `POSTGRES_HOST` | - | PostgreSQL host (required) |
| `POSTGRES_DB` | `trading_swarm_staging` | Database name |
| `DEBUG` | `false` | Disable debug mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `GUNICORN_WORKERS` | `4` | Number of Gunicorn workers |
| `SENTRY_DSN` | - | Sentry error tracking DSN |
| `PROMETHEUS_ENABLED` | `true` | Enable Prometheus metrics |

## Database Configuration

### SQLite (Development)

SQLite is used in development for simplicity:

```python
# Automatic configuration from .env.development
DATABASE_TYPE=sqlite
SQLITE_PATH=data/trading_bot_dev.db
```

Reset database:
```bash
rm data/trading_bot_dev.db
python main.py --env development  # Recreates database
```

### PostgreSQL (Staging)

PostgreSQL setup for staging:

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE trading_swarm_staging;
CREATE USER staging_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE trading_swarm_staging TO staging_user;
\q

# Update .env.staging
POSTGRES_HOST=localhost
POSTGRES_DB=trading_swarm_staging
POSTGRES_USER=staging_user
POSTGRES_PASSWORD=secure_password
```

## Testing

### Unit Tests

```bash
# Run all unit tests
pytest tests/ -m unit

# Run with coverage
pytest tests/ -m unit --cov=src --cov-report=html
```

### Integration Tests

```bash
# Run integration tests
pytest tests/ -m integration

# Run against staging database
pytest tests/ -m integration --env=staging
```

### End-to-End Tests

```bash
# Run E2E tests
pytest tests/e2e/ -v

# Run against staging environment
pytest tests/e2e/ --base-url=http://staging-server:8080
```

## Monitoring

### Sentry Integration

Configure Sentry for error tracking:

```bash
# In .env.staging
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
```

### Prometheus Metrics

Custom metrics exposed by the application:

- `trading_bot_trades_total` - Total number of trades
- `trading_bot_pnl_total` - Total profit/loss
- `trading_bot_positions_open` - Number of open positions
- `trading_bot_api_calls_total` - Total API calls
- `trading_bot_errors_total` - Total errors

Access metrics: `http://staging-server:8000/metrics`

### Grafana Dashboards

Pre-configured dashboards include:

- Trading Overview - Key metrics and performance
- System Resources - CPU, memory, disk usage
- API Performance - Request rates and response times
- Error Tracking - Error rates and types

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.staging.yml ps postgres-staging

# Check connection
docker-compose -f docker-compose.staging.yml exec postgres-staging pg_isready

# View PostgreSQL logs
docker-compose -f docker-compose.staging.yml logs postgres-staging
```

#### High Memory Usage

```bash
# Check container memory usage
docker stats

# Reduce Gunicorn workers
# In .env.staging: GUNICORN_WORKERS=2

# Restart with new configuration
docker-compose -f docker-compose.staging.yml restart
```

#### Application Crashes

```bash
# View recent logs
docker-compose -f docker-compose.staging.yml logs --tail=100 trading-bot-staging

# Check Sentry for error details
# Visit your Sentry dashboard

# Check system resources
docker exec trading-bot-staging df -h
docker exec trading-bot-staging free -m
```

#### Port Conflicts

```bash
# Find processes using port 8080
sudo lsof -i :8080

# Change port in docker-compose.staging.yml
ports:
  - "8081:8080"  # Change external port
```

### Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Review Sentry dashboard for errors
3. Check GitHub Issues: https://github.com/canstralian/trading-bot-swarm/issues
4. Contact team on Slack/Discord

## Best Practices

### Development
- Always use testnet/paper trading APIs
- Run tests before committing code
- Use `.env.development` for local configuration
- Keep sensitive data out of version control
- Format code with Black before committing

### Staging
- Test all changes in staging before production
- Monitor error rates and performance metrics
- Review Sentry alerts regularly
- Keep staging environment similar to production
- Document any staging-specific configurations

### Security
- Never commit `.env` files with real credentials
- Use strong passwords for staging databases
- Restrict access to monitoring dashboards
- Rotate API keys regularly
- Enable SSL/TLS in production

## Additional Resources

- [Main README](../README.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Production Deployment Runbook](../docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md)
- [CI/CD Documentation](../docs/CI_CD.md)
