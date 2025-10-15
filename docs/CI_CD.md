# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) workflows implemented for the Trading Bot Swarm project.

## Overview

The project uses GitHub Actions for automated testing, security scanning, code quality checks, and deployment. Our CI/CD pipeline ensures that all code changes meet quality standards before being merged.

## Workflows

### 1. Main CI Pipeline (`ci.yml`)

**Trigger:** Push to `main`/`develop`, Pull Requests

**Jobs:**

#### Code Quality
- **Black**: Validates code formatting
- **Flake8**: Lints code for style and logical errors
- **MyPy**: Performs static type checking

#### Security Scanning
- **Bandit**: Scans for common security issues in Python code
- **Safety**: Checks for known vulnerabilities in dependencies
- Generates security reports uploaded as artifacts

#### Testing
- **Matrix Testing**: Tests across:
  - Python versions: 3.10, 3.11, 3.12
  - Operating systems: Ubuntu, macOS
- **Coverage**: Generates code coverage reports
- **Codecov**: Uploads coverage to Codecov for tracking

#### Dependency Audit
- **pip-audit**: Audits dependencies for security vulnerabilities

#### Build Validation
- Validates project structure
- Syntax checks all Python files
- Generates build artifacts

### 2. CodeQL Security Analysis (`codeql.yml`)

**Trigger:** Push to `main`/`develop`, Pull Requests, Weekly schedule

**Purpose:** Advanced security analysis using GitHub's CodeQL engine

**Features:**
- Scans for security vulnerabilities
- Identifies code quality issues
- Runs security and quality queries
- Results visible in Security tab

### 3. Docker Build & Push (`docker.yml`)

**Trigger:** Push to `main`, version tags, Pull Requests

**Purpose:** Builds and publishes Docker images

**Features:**
- Multi-platform builds (amd64, arm64)
- Automated tagging based on:
  - Branch names
  - Semantic version tags
  - Git SHA
- Pushes to GitHub Container Registry (ghcr.io)
- Uses Docker layer caching for faster builds

**Image Usage:**
```bash
docker pull ghcr.io/canstralian/trading-bot-swarm:main
docker run ghcr.io/canstralian/trading-bot-swarm:main
```

### 4. Dependency Updates (`dependency-updates.yml`)

**Trigger:** Weekly schedule (Monday 9 AM UTC), Manual

**Purpose:** Monitors and reports outdated dependencies

**Features:**
- Checks for outdated packages
- Automatically creates issues for updates
- Helps maintain security and compatibility

### 5. Documentation (`docs.yml`)

**Trigger:** Push/PR with changes to `*.md` or `docs/`

**Purpose:** Validates documentation quality

**Features:**
- **Markdownlint**: Lints markdown files for consistency
- **Link Checker**: Validates all links in documentation
- **Spell Check**: Checks spelling in documentation

## CI Status Badges

Current status of all workflows:

[![CI](https://github.com/canstralian/trading-bot-swarm/actions/workflows/ci.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/ci.yml)
[![CodeQL](https://github.com/canstralian/trading-bot-swarm/actions/workflows/codeql.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/codeql.yml)
[![Docker](https://github.com/canstralian/trading-bot-swarm/actions/workflows/docker.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/docker.yml)

## Running Checks Locally

### Prerequisites
```bash
pip install black flake8 mypy pytest pytest-asyncio pytest-cov bandit safety pip-audit
```

### Code Quality
```bash
# Format check
black --check --diff src/ main.py

# Lint
flake8 src/ main.py --max-line-length=127

# Type check
mypy src/ main.py --ignore-missing-imports
```

### Security
```bash
# Security linting
bandit -r src/ main.py

# Dependency vulnerabilities
safety check

# Dependency audit
pip-audit
```

### Testing
```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Deployment Process

### Automatic Deployment

1. **Development**: Push to `develop` branch
   - Triggers CI checks
   - No deployment

2. **Production**: Push to `main` branch or create version tag
   - Triggers CI checks
   - Builds Docker images
   - Publishes to GitHub Container Registry

### Manual Deployment

All workflows can be manually triggered via the GitHub Actions UI:

1. Go to the "Actions" tab
2. Select the workflow
3. Click "Run workflow"
4. Select branch and options

## Workflow Configuration

### Environment Variables

Workflows use these environment variables:

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- Custom secrets can be added in repository settings

### Artifacts

Workflows generate these artifacts:

- **Security Reports**: Bandit JSON reports (30-day retention)
- **Build Info**: Build metadata (90-day retention)
- **Coverage Reports**: Test coverage data (uploaded to Codecov)

### Caching

The CI pipeline uses caching to speed up builds:

- **pip cache**: Python packages cached per Python version
- **Docker layer cache**: Docker build layers cached
- Cache is automatically invalidated when dependencies change

## Troubleshooting CI Failures

### Code Quality Failures

**Black formatting errors:**
```bash
black src/ main.py
```

**Flake8 linting errors:**
- Fix reported issues
- Or add `# noqa: <error-code>` to ignore specific lines

**MyPy type errors:**
- Add type hints
- Or use `# type: ignore` for specific lines

### Test Failures

1. **Review test output** in the GitHub Actions log
2. **Reproduce locally:**
   ```bash
   pytest tests/test_specific.py -v
   ```
3. **Check dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Security Failures

**Bandit issues:**
- Review the security report artifact
- Fix high/medium severity issues
- Document false positives with `# nosec`

**Safety/pip-audit vulnerabilities:**
- Update vulnerable dependencies
- Check for patches or alternatives

### Build Failures

**Syntax errors:**
```bash
python -m py_compile <file.py>
```

**Import errors:**
- Ensure all dependencies are in `requirements.txt`
- Check Python version compatibility

## Best Practices

1. **Run checks locally** before pushing
2. **Keep dependencies updated** regularly
3. **Review security reports** promptly
4. **Maintain test coverage** above 80%
5. **Use semantic versioning** for releases
6. **Document changes** in commit messages
7. **Monitor CI dashboard** regularly

## Contributing to CI/CD

To improve or modify the CI/CD pipeline:

1. Test changes in a fork first
2. Use workflow dispatch for manual testing
3. Document changes in this file
4. Update CONTRIBUTING.md if needed
5. Ensure backward compatibility

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)

## Support

For CI/CD related issues:

1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Open an issue with the `ci` label
4. Contact maintainers

---

Last updated: 2025-10-15
