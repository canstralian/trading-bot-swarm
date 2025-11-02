# Trading Bot Swarm

[![Quality Gate](https://github.com/canstralian/trading-bot-swarm/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/quality-gate.yml)
[![Release](https://github.com/canstralian/trading-bot-swarm/actions/workflows/release.yml/badge.svg)](https://github.com/canstralian/trading-bot-swarm/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Trading Bot Swarm is a modular Python platform for orchestrating multiple automated trading agents with shared market data, risk management, and monitoring utilities. The project is structured as a production-ready package that can be installed with `pip`, tested automatically, and published to PyPI.

## Key Capabilities

- **Multi-strategy orchestration** – run a swarm of specialised bots with shared market data and risk controls.
- **Robust risk management** – portfolio-aware sizing, drawdown protections, and automated take-profit / stop-loss handling.
- **Structured monitoring** – async system monitoring with Raspberry Pi fallbacks for edge deployments.
- **Configurable deployments** – YAML driven configuration with encrypted secrets and environment overrides.
- **Package-first design** – installable from PyPI, fully typed, and validated by CI quality gates.

## Repository Layout

```text
├── config/                 # Default configuration bundles
├── docs/                   # Operations, CI/CD, and usage guides
├── src/                    # Installable package source code
│   ├── bots/               # High-level bot orchestrators
│   ├── core/               # Trading engine, risk, portfolio, config
│   ├── strategies/         # Strategy implementations
│   └── utils/              # Logging, monitoring, and persistence helpers
├── tests/                  # Pytest suite and fixtures
├── pyproject.toml          # Build metadata and dependency management
└── Makefile                # Common development tasks
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

Configure secrets and environment specific overrides in `config/` (see [docs/CONFIGURATION.md](docs/CONFIGURATION.md)). You can then start the reference orchestrator:

```bash
python main.py --env development
```

## Quality Gates

The repository uses reproducible automation via the `Makefile`:

| Purpose          | Command                      |
| ---------------- | ---------------------------- |
| Format code      | `make format`                |
| Static analysis  | `make lint` (flake8 + mypy)  |
| Security checks  | `make security` (bandit etc) |
| Tests + coverage | `make test-cov`              |

Continuous integration (see `.github/workflows/quality-gate.yml`) runs linting, type checking, unit tests, and security audits for every code change.

## Documentation

- [Usage Guide](docs/USAGE_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Operations Runbook](docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md)
- [CI/CD Overview](docs/CI_CD.md)
- [Release Process](docs/RELEASE_PROCESS.md)
- [Changelog](CHANGELOG.md)

## Releasing & Publishing

1. Ensure `make check` and tests are green locally.
2. Update `CHANGELOG.md` with user-facing notes.
3. Bump the version in `pyproject.toml` (semantic versioning).
4. Create a signed tag (`git tag -s vX.Y.Z`) and push.
5. GitHub Actions will build wheels and publish to PyPI once the `PYPI_API_TOKEN` secret is configured.

See [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) for the detailed checklist, including verification, signing, and rollout monitoring.

## Contributing

We welcome issues and pull requests! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and ensure that all CI checks pass before requesting a review.
