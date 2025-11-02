# Release Process

This document outlines the checklist for cutting a production release and publishing the package to PyPI.

## Pre-release Checklist

1. **Ensure quality gates are clean**
   - `make format lint` – code style and static analysis
   - `make security` – bandit and dependency audits
   - `make test-cov` – run unit tests with coverage report
2. **Review dependencies**
   - `pip list --outdated` or `make deps-check`
   - Update pinned versions if necessary and document changes
3. **Update documentation**
   - Confirm README, usage docs, and configuration references are current
   - Append a new entry to `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) semantics

## Versioning Strategy

- Semantic Versioning (`MAJOR.MINOR.PATCH`)
- Increment:
  - **MAJOR** when making incompatible API changes
  - **MINOR** for backwards-compatible functionality
  - **PATCH** for backwards-compatible bug fixes

## Tagging & Release

1. Bump the version in `pyproject.toml` and commit the change.
2. Create a signed tag: `git tag -s vX.Y.Z -m "Release vX.Y.Z"`
3. Push the branch and tag: `git push origin main --tags`
4. The `release.yml` GitHub Action will:
   - Install dependencies
   - Build source and wheel distributions
   - Publish to PyPI using `PYPI_API_TOKEN`
   - Create a GitHub release with the changelog excerpt

## Post-release Tasks

- Verify the package on PyPI: `pip install trading-bot-swarm==X.Y.Z`
- Monitor CI dashboards and error trackers for regressions
- Gather feedback and schedule follow-up fixes or enhancements
