# Quick Start Guide

This guide helps you get up and running with Trading Bot Swarm in minutes.

## For Developers (Local Development)

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/canstralian/trading-bot-swarm.git
cd trading-bot-swarm

# Run the automated setup script
bash scripts/setup-dev.sh
```

The script will:
- Check Python version
- Create virtual environment
- Install dependencies
- Set up configuration files
- Create necessary directories
- Run tests to verify setup

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/canstralian/trading-bot-swarm.git
cd trading-bot-swarm

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up configuration
cp config/.env.development config/.env

# Run the application
python main.py --env development
```

### Using Make Commands

```bash
# Install and setup
make install-dev
make setup-dev

# Run tests
make test
make test-cov

# Format code
make format

# Run linting
make lint

# Run the application
make run-dev
```

## For QA/Testing (Staging Environment)

### Option 1: Automated Deployment

```bash
# Clone the repository on your staging server
git clone https://github.com/canstralian/trading-bot-swarm.git
cd trading-bot-swarm

# Run the automated staging deployment
bash scripts/deploy-staging.sh
```

### Option 2: Manual Docker Compose

```bash
# Set up environment
cp config/.env.staging config/.env
# Edit config/.env with your credentials
nano config/.env

# Start all services
docker-compose -f docker-compose.staging.yml up -d

# Check status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f
```

### Using Make Commands

```bash
# Deploy staging with Docker Compose
make docker-staging

# View logs
make docker-staging-logs

# Stop services
make docker-staging-stop
```

### Access Staging Services

After deployment, access:

- **Application**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (username: admin, password: admin)
- **Health Check**: http://localhost:8080/health

## Common Tasks

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_environment.py -v

# Or use Make
make test
make test-cov
```

### Code Quality

```bash
# Format code
black .

# Check code style
flake8 .

# Type checking
mypy src/

# Or use Make for all at once
make format
make lint
make check
```

### Working with Environments

```bash
# Development (SQLite, debug mode)
python main.py --env development

# Staging (PostgreSQL, production-like)
python main.py --env staging

# Production
python main.py --env production

# Monitoring mode only (no trading)
python main.py --env development --no-trading
```

### Database Management

#### Development (SQLite)

```bash
# Reset development database
rm data/trading_bot_dev.db
python main.py --env development  # Recreates automatically
```

#### Staging (PostgreSQL)

```bash
# Access PostgreSQL
docker-compose -f docker-compose.staging.yml exec postgres-staging psql -U staging_user -d trading_swarm_staging

# Backup database
docker-compose -f docker-compose.staging.yml exec postgres-staging pg_dump -U staging_user trading_swarm_staging > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.staging.yml exec -T postgres-staging psql -U staging_user -d trading_swarm_staging
```

## Troubleshooting

### Development Issues

**Virtual environment issues:**
```bash
# Remove and recreate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

**Import errors:**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"
```

**Test failures:**
```bash
# Run tests with verbose output
pytest -v --tb=long

# Check test configuration
pytest --collect-only
```

### Staging Issues

**Services not starting:**
```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs

# Check individual service
docker-compose -f docker-compose.staging.yml logs trading-bot-staging

# Restart services
docker-compose -f docker-compose.staging.yml restart
```

**Port conflicts:**
```bash
# Check what's using the port
sudo lsof -i :8080

# Change port in docker-compose.staging.yml
# Then restart services
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.staging.yml ps postgres-staging

# Check connection
docker-compose -f docker-compose.staging.yml exec postgres-staging pg_isready

# Check credentials in config/.env
```

## Next Steps

1. **Read the documentation**: Check out [ENVIRONMENTS.md](docs/ENVIRONMENTS.md) for detailed setup instructions
2. **Configure API keys**: Edit `config/.env` to add your trading API keys (use testnet keys!)
3. **Review strategies**: Explore `src/strategies/` to understand available trading strategies
4. **Run tests**: Ensure everything works with `make test`
5. **Start trading**: Run the bot with `python main.py --env development`

## Getting Help

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Check [GitHub Issues](https://github.com/canstralian/trading-bot-swarm/issues)
- **Contributing**: Read [CONTRIBUTING.md](CONTRIBUTING.md)

## Safety First! 🛡️

⚠️ **Important Reminders:**

- Always use **testnet/paper trading** APIs in development
- Never commit real API keys to version control
- Test thoroughly in staging before production
- Start with small capital amounts
- Monitor your bots regularly
- Set appropriate stop losses

Happy Trading! 🚀
