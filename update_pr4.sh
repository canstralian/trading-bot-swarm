#!/bin/bash
# Script to update PR #4 with the new title and body
# This script requires GitHub CLI (gh) to be installed and authenticated

set -e

PR_NUMBER=4
REPO="canstralian/trading-bot-swarm"

NEW_TITLE="Add production deployment runbook to docs directory"

NEW_BODY="This PR adds a comprehensive Production Deployment Runbook to the repository.

## Changes
- ✅ Created comprehensive Production Deployment Runbook document
- ✅ Added the runbook to the docs/ directory as PRODUCTION_DEPLOYMENT_RUNBOOK.md
- ✅ Formatted the document as Markdown with proper sections
- ✅ Included all required sections: pre-release preparations, testing, deployment steps, health checks, monitoring, rollback, and continuous improvement
- ✅ Verified the document is properly formatted and complete

## Document Overview
The runbook provides a comprehensive guide for deploying the Trading Bot Swarm system to production, covering:
- Pre-release preparations (code review, security audit, dependency updates, configuration management, backup)
- Testing (unit, integration, security, performance, staging deployment)
- Deployment steps (infrastructure preparation, application deployment, database deployment, validation)
- Health checks (automated and manual verification)
- Monitoring (application, infrastructure, logging, security)
- Rollback procedures
- Continuous improvement processes

This documentation ensures secure, reliable deployments of the Trading Bot Swarm system."

echo "Updating PR #$PR_NUMBER..."
echo "New title: $NEW_TITLE"
echo ""

# Update the PR title and body
gh pr edit $PR_NUMBER --repo $REPO --title "$NEW_TITLE" --body "$NEW_BODY"

echo "PR #$PR_NUMBER has been updated successfully!"
