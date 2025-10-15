# Contributing to Trading Bot Swarm

Thank you for your interest in contributing to Trading Bot Swarm! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please be respectful and constructive in your interactions with other contributors. We aim to foster an inclusive and welcoming community.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment tool (venv or virtualenv)

### Setup Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/trading-bot-swarm.git
   cd trading-bot-swarm
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies:**
   ```bash
   pip install black flake8 mypy pytest pytest-asyncio pytest-cov bandit safety
   ```

5. **Set up configuration:**
   ```bash
   cp config/.env.template config/.env
   # Edit config/.env with your settings
   ```

## Development Workflow

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Run code quality checks locally:**
   ```bash
   # Format code with Black
   black src/ main.py
   
   # Run linting
   flake8 src/ main.py
   
   # Type checking
   mypy src/ main.py --ignore-missing-imports
   
   # Security checks
   bandit -r src/ main.py
   ```

4. **Run tests:**
   ```bash
   pytest tests/ -v --cov=src
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guide
- Use Black for code formatting (line length: 100)
- Use type hints where appropriate
- Write docstrings for all public modules, functions, classes, and methods
- Keep functions focused and concise

### Code Formatting

We use [Black](https://github.com/psf/black) for consistent code formatting:

```bash
black --line-length 100 src/ main.py
```

### Linting

We use Flake8 for linting:

```bash
flake8 src/ main.py --max-line-length=127
```

### Type Checking

We use MyPy for static type checking:

```bash
mypy src/ main.py --ignore-missing-imports
```

### Security

We use Bandit for security linting:

```bash
bandit -r src/ main.py
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use pytest for testing
- Aim for high test coverage (>80%)
- Write both unit tests and integration tests

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py -v

# Run with markers
pytest tests/ -m "unit"
```

### Test Structure

```python
import pytest
from src.module import function_to_test


def test_function_basic_case():
    """Test basic functionality."""
    result = function_to_test(input_data)
    assert result == expected_output


def test_function_edge_case():
    """Test edge case handling."""
    with pytest.raises(ValueError):
        function_to_test(invalid_input)


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

## Continuous Integration

Our CI/CD pipeline automatically runs on every pull request and includes:

### 1. Code Quality Checks (`ci.yml`)
- **Black**: Code formatting validation
- **Flake8**: Linting for code quality
- **MyPy**: Static type checking

### 2. Security Scanning
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking
- **CodeQL**: Advanced security analysis

### 3. Testing
- Tests run on multiple Python versions (3.10, 3.11, 3.12)
- Tests run on multiple OS (Ubuntu, macOS)
- Code coverage reports generated

### 4. Build Validation
- Syntax checking
- Project structure validation
- Dependency installation verification

### 5. Documentation
- Markdown linting
- Link checking
- Spell checking

### 6. Docker
- Multi-platform Docker image builds (amd64, arm64)
- Automatic image publishing on releases

All checks must pass before a pull request can be merged.

## Pull Request Process

1. **Ensure all CI checks pass** - The automated CI pipeline will run on your PR

2. **Update documentation** - If you've added features, update README.md and relevant docs

3. **Add tests** - New features should include tests

4. **Follow commit conventions:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

5. **Request review** - Tag maintainers for review

6. **Address feedback** - Make requested changes and push updates

7. **Squash commits** - Clean up commit history if requested

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce the bug
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**:
  - OS and version
  - Python version
  - Relevant package versions
- **Logs**: Any relevant error messages or logs
- **Screenshots**: If applicable

### Feature Requests

When requesting features, please include:

- **Use Case**: Why you need this feature
- **Proposed Solution**: How you envision it working
- **Alternatives**: Alternative solutions you've considered
- **Additional Context**: Any other relevant information

## Development Tips

### Local Testing Before Pushing

Create a script to run all checks locally:

```bash
#!/bin/bash
# test.sh - Run all checks locally

echo "Running Black..."
black --check src/ main.py

echo "Running Flake8..."
flake8 src/ main.py

echo "Running MyPy..."
mypy src/ main.py --ignore-missing-imports

echo "Running Bandit..."
bandit -r src/ main.py

echo "Running tests..."
pytest tests/ -v --cov=src

echo "All checks passed!"
```

### Pre-commit Hooks

Consider setting up pre-commit hooks:

```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

Install hooks:
```bash
pre-commit install
```

## Questions?

If you have questions about contributing, please:

1. Check existing issues and documentation
2. Open a new issue with the "question" label
3. Reach out to maintainers

Thank you for contributing to Trading Bot Swarm! 🚀
