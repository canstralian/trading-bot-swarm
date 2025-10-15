# Production Deployment Runbook

## Overview

This runbook provides comprehensive guidance for deploying the Trading Bot Swarm system to production environments. It covers all stages from pre-release preparations through post-deployment monitoring and continuous improvement.

**Target Audience:** DevOps Engineers, Site Reliability Engineers, Release Managers

**Last Updated:** 2025-10-15

---

## Table of Contents

1. [Pre-Release Preparations](#pre-release-preparations)
2. [Testing](#testing)
3. [Automated Validation](#automated-validation)
4. [Security and Secrets Management](#security-and-secrets-management)
5. [Deployment Steps](#deployment-steps)
6. [Health Checks](#health-checks)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Rollback Procedures](#rollback-procedures)
9. [Continuous Improvement](#continuous-improvement)
10. [Contributing to this Runbook](#contributing-to-this-runbook)

---

## Pre-Release Preparations

### 1.1 Code Review and Approval

- [ ] All pull requests have been reviewed and approved by at least two team members
- [ ] Code changes have passed security scanning (SAST/DAST)
- [ ] All merge conflicts have been resolved
- [ ] Release notes have been prepared and reviewed

### 1.2 Environment Verification

- [ ] Verify production environment credentials are valid and accessible
- [ ] Confirm database backup schedule is current
- [ ] Ensure adequate disk space and resources are available
- [ ] Verify SSL/TLS certificates are valid and not expiring within 30 days
- [ ] Check that all external API keys and secrets are properly configured

### 1.3 Dependency Management

- [ ] All dependencies are up-to-date and vulnerability-free
- [ ] Third-party API integrations are tested and operational
- [ ] Trading exchange API connections are stable
- [ ] Database migration scripts are prepared and tested

### 1.4 Communication

- [ ] Notify stakeholders of planned deployment window
- [ ] Create incident response channel (Slack/Teams/Discord)
- [ ] Prepare rollback communication templates
- [ ] Schedule post-deployment review meeting

### 1.5 Backup and Recovery

- [ ] Create full database backup
- [ ] Export current configuration files
- [ ] Document current system state (versions, configurations)
- [ ] Verify backup restoration process is working
- [ ] Tag current production release in version control

---

## Testing

### 2.1 Pre-Deployment Testing

#### Unit Tests
```bash
# Run unit tests
npm test
# or
pytest tests/unit/

# Verify all tests pass
# Coverage should be > 80%
```

#### Integration Tests
```bash
# Run integration tests
npm run test:integration
# or
pytest tests/integration/

# Verify bot-to-bot communication
# Verify exchange API integrations
# Verify database operations
```

#### End-to-End Tests
```bash
# Run E2E tests in staging
npm run test:e2e
# or
pytest tests/e2e/

# Test complete trading workflows
# Verify order placement and cancellation
# Test portfolio management
```

### 2.2 Staging Environment Testing

- [ ] Deploy to staging environment
- [ ] Run smoke tests on staging
- [ ] Perform load testing with production-like data
- [ ] Execute security penetration tests
- [ ] Validate monitoring and alerting systems
- [ ] Test rollback procedures in staging

### 2.3 Performance Testing

- [ ] Load test with expected production volume
- [ ] Stress test with 2x expected volume
- [ ] Monitor resource utilization under load
- [ ] Verify autoscaling triggers work correctly
- [ ] Test rate limiting and throttling mechanisms

### 2.4 Security Testing

- [ ] Run vulnerability scans
- [ ] Verify authentication and authorization
- [ ] Test API key rotation procedures
- [ ] Validate encrypted data storage
- [ ] Check audit logging functionality

---

## Automated Validation

### 3.1 CI/CD Pipeline Validation

Integrate automated validation checks into your CI/CD pipeline to ensure runbook steps and scripts are validated before deployment.

#### GitHub Actions Workflow Example

Create `.github/workflows/runbook-validation.yml`:

```yaml
name: Runbook Validation

on:
  pull_request:
    paths:
      - 'docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md'
      - 'scripts/**'
  push:
    branches:
      - main

jobs:
  validate-runbook:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Validate Markdown syntax
        uses: nosborn/github-action-markdown-cli@v3.3.0
        with:
          files: docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md
          config_file: .markdownlint.json

      - name: Check for broken links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          use-verbose-mode: 'yes'

      - name: Validate shell scripts syntax
        run: |
          find scripts -name "*.sh" -exec shellcheck {} +

      - name: Test script executability
        run: |
          find scripts -name "*.sh" -exec test -x {} \; || {
            echo "Error: Some scripts are not executable"
            exit 1
          }

      - name: Validate configuration files
        run: |
          # Check JSON syntax
          find . -name "*.json" -exec jq empty {} \;
          # Check YAML syntax
          find . -name "*.yml" -o -name "*.yaml" -exec yamllint {} \;
```

#### Pre-commit Hooks

Install pre-commit hooks to validate changes locally:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: https://github.com/markdownlint/markdownlint
    rev: v0.12.0
    hooks:
      - id: markdownlint

  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck
EOF

# Install the hooks
pre-commit install
```

### 3.2 Script Validation

#### Automated Script Testing

Create a test suite for deployment scripts:

```bash
# scripts/test-scripts.sh
#!/bin/bash
# Test all deployment scripts for syntax and basic functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Testing deployment scripts..."

# Test each script with --dry-run or --help
for script in "$SCRIPT_DIR"/*.sh; do
    if [[ "$script" != "$0" ]]; then
        echo "Testing: $script"
        
        # Check syntax
        bash -n "$script" || {
            echo "Syntax error in $script"
            exit 1
        }
        
        # Check if script has help/dry-run mode
        if "$script" --help &>/dev/null || "$script" --dry-run &>/dev/null; then
            echo "✓ $script passed validation"
        fi
    fi
done

echo "All scripts validated successfully!"
```

### 3.3 Configuration Validation

```bash
# scripts/verify-config.sh
#!/bin/bash
# Validate environment configuration before deployment

set -e

echo "Validating configuration..."

# Check required environment variables
REQUIRED_VARS=(
    "DATABASE_URL"
    "API_KEY"
    "REDIS_URL"
    "LOG_LEVEL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Validate configuration file syntax
if [[ -f ".env.production" ]]; then
    # Check for syntax errors
    set -a
    source .env.production
    set +a
    echo "✓ Configuration file is valid"
else
    echo "Error: .env.production not found"
    exit 1
fi

# Validate database connection
if command -v psql &> /dev/null; then
    psql "$DATABASE_URL" -c "SELECT 1;" &>/dev/null || {
        echo "Error: Cannot connect to database"
        exit 1
    }
    echo "✓ Database connection successful"
fi

# Validate external API connectivity
curl -f -s -o /dev/null "$HEALTH_CHECK_URL" || {
    echo "Warning: Health check endpoint not responding"
}

echo "Configuration validation completed successfully!"
```

### 3.4 Infrastructure as Code Validation

For Terraform deployments:

```bash
# Validate Terraform configuration
terraform init
terraform validate
terraform plan -out=tfplan

# Run security checks
tfsec .

# Check for cost implications
infracost breakdown --path .
```

For Kubernetes deployments:

```bash
# Validate Kubernetes manifests
kubectl apply --dry-run=client -f k8s/
kubectl apply --dry-run=server -f k8s/

# Lint Kubernetes files
kube-linter lint k8s/

# Validate with Helm
helm lint charts/trading-bot-swarm
helm template charts/trading-bot-swarm | kubectl apply --dry-run=client -f -
```

---

## Security and Secrets Management

### 4.1 Secrets Management Best Practices

#### HashiCorp Vault Integration

Set up HashiCorp Vault for centralized secrets management:

```bash
# Install Vault
wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
unzip vault_1.15.0_linux_amd64.zip
sudo mv vault /usr/local/bin/

# Initialize Vault (first time only)
vault operator init

# Unseal Vault
vault operator unseal <unseal-key-1>
vault operator unseal <unseal-key-2>
vault operator unseal <unseal-key-3>

# Login to Vault
vault login <root-token>

# Enable secrets engine
vault secrets enable -path=trading-bot-swarm kv-v2

# Store secrets
vault kv put trading-bot-swarm/production \
    database_url="postgresql://user:pass@host:5432/db" \
    api_key="your-api-key" \
    redis_url="redis://localhost:6379"

# Read secrets in deployment
vault kv get -format=json trading-bot-swarm/production | jq -r '.data.data'
```

#### Retrieving Secrets in Scripts

```bash
# scripts/load-secrets.sh
#!/bin/bash
# Load secrets from Vault into environment

set -e

if ! command -v vault &> /dev/null; then
    echo "Error: Vault CLI not found"
    exit 1
fi

# Authenticate with Vault
vault login -method=aws || \
vault login -method=kubernetes || \
vault login -token="$VAULT_TOKEN"

# Retrieve secrets
SECRETS=$(vault kv get -format=json trading-bot-swarm/production)

# Export as environment variables
export DATABASE_URL=$(echo "$SECRETS" | jq -r '.data.data.database_url')
export API_KEY=$(echo "$SECRETS" | jq -r '.data.data.api_key')
export REDIS_URL=$(echo "$SECRETS" | jq -r '.data.data.redis_url')

echo "Secrets loaded successfully"
```

### 4.2 API Key Rotation

Implement automated API key rotation:

```bash
# scripts/rotate-api-keys.sh
#!/bin/bash
# Rotate API keys for external services

set -e

echo "Starting API key rotation..."

# 1. Generate new API key
NEW_API_KEY=$(curl -X POST https://api.exchange.com/v1/keys \
    -H "Authorization: Bearer $CURRENT_API_KEY" \
    -d '{"name": "production-key-'$(date +%Y%m%d)'"}' | jq -r '.key')

# 2. Update Vault with new key
vault kv put trading-bot-swarm/production \
    api_key="$NEW_API_KEY" \
    api_key_previous="$CURRENT_API_KEY"

# 3. Deploy updated configuration (zero-downtime)
./scripts/deploy-config-update.sh

# 4. Verify new key works
sleep 30
./scripts/verify-api-connectivity.sh

# 5. Revoke old API key after grace period (24 hours)
# Schedule this with cron or CI/CD
at now + 24 hours <<EOF
curl -X DELETE https://api.exchange.com/v1/keys/$CURRENT_API_KEY \
    -H "Authorization: Bearer $NEW_API_KEY"
vault kv patch trading-bot-swarm/production api_key_previous=null
EOF

echo "API key rotation completed successfully"
```

### 4.3 Secrets Rotation Schedule

| Secret Type | Rotation Frequency | Automated | Priority |
|-------------|-------------------|-----------|----------|
| Database passwords | 90 days | Yes | High |
| API keys | 90 days | Yes | High |
| SSL/TLS certificates | Before expiry (30 days) | Yes | Critical |
| Service account tokens | 90 days | Yes | High |
| Encryption keys | 180 days | Manual | Critical |
| SSH keys | 180 days | Manual | Medium |

### 4.4 Encryption at Rest and in Transit

#### Database Encryption

```bash
# Enable database encryption (PostgreSQL example)
psql -U postgres -d trading_bot_swarm -c "
    ALTER DATABASE trading_bot_swarm SET encryption = 'on';
"

# Verify encryption status
psql -U postgres -d trading_bot_swarm -c "
    SHOW data_encryption;
"
```

#### Application-Level Encryption

```python
# Example: Encrypt sensitive data before storage
from cryptography.fernet import Fernet
import os

# Load encryption key from Vault
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data before storage."""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data after retrieval."""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()
```

### 4.5 Security Scanning and Compliance

```bash
# scripts/security-scan.sh
#!/bin/bash
# Comprehensive security scanning

set -e

echo "Running security scans..."

# 1. Dependency vulnerability scanning
if [[ -f "package.json" ]]; then
    npm audit --audit-level=moderate
    # or use Snyk
    snyk test
fi

if [[ -f "requirements.txt" ]]; then
    pip install safety
    safety check -r requirements.txt
fi

# 2. Secret scanning
if command -v gitleaks &> /dev/null; then
    gitleaks detect --source . --verbose
fi

# 3. Container image scanning
if command -v trivy &> /dev/null; then
    trivy image --severity HIGH,CRITICAL trading-bot-swarm:latest
fi

# 4. Infrastructure security
if command -v tfsec &> /dev/null; then
    tfsec .
fi

# 5. OWASP ZAP scanning (for web interfaces)
if [[ -n "$STAGING_URL" ]]; then
    docker run -t owasp/zap2docker-stable zap-baseline.py \
        -t "$STAGING_URL" -r zap-report.html
fi

echo "Security scans completed"
```

### 4.6 Access Control and Audit Logging

```bash
# Enable comprehensive audit logging
cat > /etc/audit/rules.d/trading-bot-swarm.rules <<EOF
# Monitor access to sensitive files
-w /etc/trading-bot-swarm/ -p wa -k trading_bot_config_changes
-w /var/log/trading-bot-swarm/ -p wa -k trading_bot_logs_access

# Monitor privileged commands
-a always,exit -F arch=b64 -S execve -F euid=0 -k root_commands

# Monitor network connections
-a always,exit -F arch=b64 -S socket -S connect -k network_connections
EOF

# Restart audit daemon
systemctl restart auditd

# View audit logs
ausearch -k trading_bot_config_changes
```

---

## Deployment Steps

### 5.1 Pre-Deployment Checklist

- [ ] Confirm maintenance window start time
- [ ] Set deployment status page to "maintenance mode"
- [ ] Disable automated trading bots
- [ ] Stop all background jobs and cron tasks
- [ ] Create snapshot of production environment

### 5.2 Deployment Process

#### Step 1: Enable Maintenance Mode
```bash
# Stop trading operations gracefully
./scripts/stop-trading.sh

# Enable maintenance mode
./scripts/enable-maintenance.sh
```

#### Step 2: Database Migration
```bash
# Backup database
./scripts/backup-db.sh

# Run migrations
./scripts/migrate-db.sh

# Verify migration success
./scripts/verify-migration.sh
```

#### Step 3: Application Deployment
```bash
# Pull latest code
git fetch origin
git checkout tags/v<version>

# Install dependencies
npm ci --production
# or
pip install -r requirements.txt

# Build application
npm run build
# or
python setup.py install
```

#### Step 4: Configuration Update
```bash
# Update environment variables
cp .env.production .env

# Verify configuration
./scripts/verify-config.sh

# Update feature flags
./scripts/update-feature-flags.sh
```

#### Step 5: Service Restart
```bash
# Restart application services
systemctl restart trading-bot-swarm

# or for containerized deployments
docker-compose down
docker-compose up -d

# or for Kubernetes
kubectl rollout restart deployment/trading-bot-swarm
kubectl rollout status deployment/trading-bot-swarm
```

#### Step 6: Smoke Tests
```bash
# Run post-deployment smoke tests
./scripts/smoke-tests.sh

# Verify critical paths
curl -f https://api.yourdomain.com/health || exit 1
```

### 5.3 Post-Deployment Verification

- [ ] Verify all services are running
- [ ] Check application logs for errors
- [ ] Test critical user journeys
- [ ] Verify database connectivity
- [ ] Test external API integrations
- [ ] Confirm monitoring dashboards are updating

### 5.4 Enable Production Traffic

```bash
# Disable maintenance mode
./scripts/disable-maintenance.sh

# Enable trading bots gradually
./scripts/enable-trading.sh --gradual

# Monitor for 15 minutes before full enablement
```

---

## Health Checks

### 6.1 Application Health

#### Basic Health Check
```bash
# Check application endpoint
curl https://api.yourdomain.com/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-10-15T17:37:53Z"}
```

#### Detailed Health Check
```bash
# Check component health
curl https://api.yourdomain.com/health/detailed

# Verify:
# - Database connection: OK
# - Cache connection: OK
# - Message queue: OK
# - External APIs: OK
```

### 6.2 Infrastructure Health

- [ ] CPU utilization < 70%
- [ ] Memory utilization < 80%
- [ ] Disk usage < 85%
- [ ] Network latency < 100ms
- [ ] Database response time < 50ms

### 6.3 Trading System Health

- [ ] Bot coordination working
- [ ] Order execution functioning
- [ ] Portfolio sync operational
- [ ] Risk management active
- [ ] Market data feeds connected

### 6.4 Monitoring Dashboards

Access the following dashboards to verify system health:

- **Application Dashboard**: Monitor application metrics, request rates, error rates
- **Infrastructure Dashboard**: Monitor server resources, network, storage
- **Trading Dashboard**: Monitor trading activity, positions, PnL
- **Security Dashboard**: Monitor authentication, authorization, suspicious activity

---

## Monitoring and Observability

### 7.1 Grafana Dashboard Setup

#### Installing Grafana

```bash
# Install Grafana
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

#### Grafana Dashboard Templates

**Application Performance Dashboard** (`dashboards/app-performance.json`):

```json
{
  "dashboard": {
    "title": "Trading Bot Swarm - Application Performance",
    "tags": ["trading", "production"],
    "timezone": "utc",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      },
      {
        "title": "Response Time (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      },
      {
        "title": "Active Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(active_connections)"
          }
        ]
      }
    ]
  }
}
```

**Trading Operations Dashboard** (`dashboards/trading-operations.json`):

```json
{
  "dashboard": {
    "title": "Trading Bot Swarm - Operations",
    "tags": ["trading", "operations"],
    "panels": [
      {
        "title": "Order Success Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(orders_successful[5m])) / sum(rate(orders_total[5m])) * 100"
          }
        ],
        "thresholds": [
          {"value": 95, "color": "green"},
          {"value": 90, "color": "yellow"},
          {"value": 0, "color": "red"}
        ]
      },
      {
        "title": "Order Latency (ms)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(order_latency_seconds_bucket[5m])) * 1000",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(order_latency_seconds_bucket[5m])) * 1000",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Active Positions",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(active_positions)"
          }
        ]
      },
      {
        "title": "P&L (Last 24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(profit_loss[24h]))"
          }
        ]
      }
    ]
  }
}
```

**Infrastructure Monitoring Dashboard** (`dashboards/infrastructure.json`):

```json
{
  "dashboard": {
    "title": "Trading Bot Swarm - Infrastructure",
    "tags": ["infrastructure", "monitoring"],
    "panels": [
      {
        "title": "CPU Usage %",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
          }
        ]
      },
      {
        "title": "Memory Usage %",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"
          }
        ]
      },
      {
        "title": "Disk Usage %",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100"
          }
        ]
      },
      {
        "title": "Network Traffic (Mbps)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m]) * 8 / 1000000",
            "legendFormat": "RX"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total[5m]) * 8 / 1000000",
            "legendFormat": "TX"
          }
        ]
      }
    ]
  }
}
```

#### Importing Dashboards

```bash
# Import dashboards via API
for dashboard in dashboards/*.json; do
    curl -X POST http://localhost:3000/api/dashboards/db \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $GRAFANA_API_KEY" \
        -d @"$dashboard"
done

# Or use Grafana provisioning
sudo mkdir -p /etc/grafana/provisioning/dashboards
sudo cp dashboards/*.json /etc/grafana/provisioning/dashboards/
sudo systemctl restart grafana-server
```

#### Dashboard Links

Once deployed, access your dashboards at:

- **Main Dashboard**: `https://grafana.yourdomain.com/d/trading-overview`
- **Application Performance**: `https://grafana.yourdomain.com/d/app-performance`
- **Trading Operations**: `https://grafana.yourdomain.com/d/trading-ops`
- **Infrastructure**: `https://grafana.yourdomain.com/d/infrastructure`

### 7.2 Log Aggregation and Analysis

#### ELK Stack Setup

**Elasticsearch, Logstash, Kibana (ELK) Stack**:

```bash
# Install Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update && sudo apt-get install elasticsearch

# Configure Elasticsearch
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch

# Install Logstash
sudo apt-get install logstash

# Configure Logstash for Trading Bot logs
cat > /etc/logstash/conf.d/trading-bot.conf <<EOF
input {
  file {
    path => "/var/log/trading-bot-swarm/*.log"
    start_position => "beginning"
    codec => json
  }
}

filter {
  if [level] == "ERROR" or [level] == "FATAL" {
    mutate {
      add_tag => ["critical"]
    }
  }
  
  # Parse trading-specific fields
  if [order_id] {
    mutate {
      add_field => { "[@metadata][index_type]" => "trading_orders" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "trading-bot-%{+YYYY.MM.dd}"
  }
}
EOF

# Start Logstash
sudo systemctl start logstash
sudo systemctl enable logstash

# Install Kibana
sudo apt-get install kibana
sudo systemctl start kibana
sudo systemctl enable kibana
```

#### Alternative: Loki + Promtail

For a lightweight alternative:

```bash
# Install Loki
wget https://github.com/grafana/loki/releases/download/v2.9.0/loki-linux-amd64.zip
unzip loki-linux-amd64.zip
sudo mv loki-linux-amd64 /usr/local/bin/loki

# Configure Loki
cat > /etc/loki/config.yml <<EOF
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2023-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h
EOF

# Install Promtail
wget https://github.com/grafana/loki/releases/download/v2.9.0/promtail-linux-amd64.zip
unzip promtail-linux-amd64.zip
sudo mv promtail-linux-amd64 /usr/local/bin/promtail

# Configure Promtail
cat > /etc/promtail/config.yml <<EOF
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: trading-bot-swarm
    static_configs:
      - targets:
          - localhost
        labels:
          job: trading-bot-swarm
          __path__: /var/log/trading-bot-swarm/*.log
EOF

# Start services
sudo systemctl start loki
sudo systemctl start promtail
```

### 7.3 Key Performance Indicators (KPIs)

#### Application Metrics
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Active connections
- Queue depth

#### Trading Metrics
- Order success rate
- Order latency
- Slippage
- Position count
- Profit/Loss (PnL)

#### Infrastructure Metrics
- CPU utilization (%)
- Memory usage (GB)
- Disk I/O (IOPS)
- Network throughput (Mbps)
- Database connections

### 7.4 Alert Thresholds

#### Critical Alerts (Page immediately)
- Application down (no response to health checks)
- Database connection failure
- Security breach detected
- Trading losses exceed threshold
- Exchange API connectivity lost

#### High Priority Alerts (Notify within 5 minutes)
- Error rate > 5%
- Response time > 1000ms (p95)
- CPU utilization > 85%
- Memory utilization > 90%
- Disk space < 10%

#### Medium Priority Alerts (Notify within 15 minutes)
- Error rate > 2%
- Response time > 500ms (p95)
- Increased order latency
- Cache miss rate high
- Unusual trading patterns

### 7.5 Log Monitoring

#### Application Logs
```bash
# View real-time logs
tail -f /var/log/trading-bot-swarm/app.log

# Search for errors
grep ERROR /var/log/trading-bot-swarm/app.log

# For containerized deployments
docker logs -f trading-bot-swarm
# or
kubectl logs -f deployment/trading-bot-swarm
```

#### Key Log Patterns to Monitor
- ERROR: Critical application errors
- WARN: Warning conditions that may need attention
- FATAL: System failures requiring immediate action
- Exception stack traces
- Trading order failures
- API rate limit warnings

### 7.6 Third-Party Integrations

- [ ] Configure Datadog/New Relic/Prometheus for metrics
- [ ] Set up PagerDuty/Opsgenie for on-call rotation
- [ ] Enable Sentry/Rollbar for error tracking
- [ ] Configure log aggregation (ELK/Splunk/Loki)
- [ ] Set up APM (Application Performance Monitoring)

### 7.7 Distributed Tracing

Implement distributed tracing for better troubleshooting:

```bash
# Install Jaeger for distributed tracing
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest

# Access Jaeger UI
# http://localhost:16686
```

**Instrumenting your application**:

```python
# Python example with OpenTelemetry
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Trace critical operations
@tracer.start_as_current_span("process_order")
def process_order(order_id):
    span = trace.get_current_span()
    span.set_attribute("order_id", order_id)
    # Process order logic
    return result
```

### 7.8 Real-time Alerting Configuration

#### PagerDuty Integration

```bash
# scripts/setup-pagerduty.sh
#!/bin/bash
# Configure PagerDuty integration

PAGERDUTY_TOKEN="your-api-token"
PAGERDUTY_SERVICE_ID="your-service-id"

# Create alert rule
curl -X POST https://api.pagerduty.com/incidents \
  -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident": {
      "type": "incident",
      "title": "Trading Bot Swarm Alert",
      "service": {
        "id": "'$PAGERDUTY_SERVICE_ID'",
        "type": "service_reference"
      },
      "urgency": "high",
      "body": {
        "type": "incident_body",
        "details": "Critical alert from monitoring system"
      }
    }
  }'
```

#### Slack Alerting

```bash
# scripts/notify-slack.sh
#!/bin/bash
# Send alerts to Slack

SLACK_WEBHOOK_URL="your-webhook-url"
MESSAGE="$1"
SEVERITY="${2:-info}"

case $SEVERITY in
  critical)
    COLOR="danger"
    ;;
  warning)
    COLOR="warning"
    ;;
  *)
    COLOR="good"
    ;;
esac

curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "attachments": [
      {
        "color": "'$COLOR'",
        "title": "Trading Bot Swarm Alert",
        "text": "'$MESSAGE'",
        "footer": "Production Monitoring",
        "ts": '$(date +%s)'
      }
    ]
  }'
```

---

## Rollback Procedures

### 8.1 When to Rollback

Initiate rollback if:
- Critical functionality is broken
- Data corruption is detected
- Security vulnerability is exploited
- System performance degrades significantly
- Trading losses exceed acceptable threshold
- More than 5% error rate persists for > 5 minutes

### 8.2 Rollback Process

#### Step 1: Immediate Actions
```bash
# Stop all trading activity
./scripts/emergency-stop.sh

# Enable maintenance mode
./scripts/enable-maintenance.sh

# Notify stakeholders
./scripts/notify-incident.sh "ROLLBACK_INITIATED"
```

#### Step 2: Rollback Application
```bash
# Revert to previous version
git checkout tags/v<previous-version>

# Rollback containerized deployment
docker-compose down
docker-compose -f docker-compose.previous.yml up -d

# or for Kubernetes
kubectl rollout undo deployment/trading-bot-swarm
kubectl rollout status deployment/trading-bot-swarm
```

#### Step 3: Rollback Database
```bash
# Only if database changes are incompatible
./scripts/rollback-db.sh

# Restore from backup if needed
./scripts/restore-db.sh <backup-timestamp>
```

#### Step 4: Verification
```bash
# Run health checks
./scripts/health-check.sh

# Verify critical functionality
./scripts/smoke-tests.sh

# Check logs for errors
./scripts/check-logs.sh
```

#### Step 5: Resume Operations
```bash
# Disable maintenance mode
./scripts/disable-maintenance.sh

# Re-enable trading gradually
./scripts/enable-trading.sh --gradual

# Monitor closely for 30 minutes
```

### 8.3 Post-Rollback Actions

- [ ] Document rollback reason and timeline
- [ ] Conduct incident retrospective
- [ ] Update rollback procedures based on learnings
- [ ] Create bug tickets for issues found
- [ ] Communicate status to stakeholders

### 8.4 Automated Rollback Testing

#### Staging Environment Rollback Tests

Create automated rollback testing procedures:

```bash
# scripts/test-rollback.sh
#!/bin/bash
# Automated rollback testing in staging environment

set -e

echo "Starting automated rollback test in staging..."

# 1. Record current state
CURRENT_VERSION=$(kubectl get deployment trading-bot-swarm -n staging -o jsonpath='{.spec.template.spec.containers[0].image}')
echo "Current version: $CURRENT_VERSION"

# 2. Deploy new version
echo "Deploying new version to staging..."
kubectl set image deployment/trading-bot-swarm \
  trading-bot-swarm=trading-bot-swarm:test-version \
  -n staging

# Wait for rollout
kubectl rollout status deployment/trading-bot-swarm -n staging --timeout=5m

# 3. Run smoke tests
echo "Running smoke tests..."
./scripts/smoke-tests.sh --env staging || {
    echo "Smoke tests failed - triggering rollback"
    ROLLBACK_NEEDED=true
}

# 4. Simulate failure scenario (optional)
if [[ "${SIMULATE_FAILURE}" == "true" ]]; then
    echo "Simulating failure scenario..."
    ROLLBACK_NEEDED=true
fi

# 5. Perform rollback
if [[ "${ROLLBACK_NEEDED}" == "true" ]]; then
    echo "Initiating rollback..."
    
    # Measure rollback start time
    ROLLBACK_START=$(date +%s)
    
    # Rollback
    kubectl rollout undo deployment/trading-bot-swarm -n staging
    kubectl rollout status deployment/trading-bot-swarm -n staging --timeout=5m
    
    # Measure rollback completion time
    ROLLBACK_END=$(date +%s)
    ROLLBACK_DURATION=$((ROLLBACK_END - ROLLBACK_START))
    
    echo "Rollback completed in ${ROLLBACK_DURATION} seconds"
    
    # Verify rollback
    ./scripts/smoke-tests.sh --env staging || {
        echo "ERROR: Post-rollback smoke tests failed!"
        exit 1
    }
    
    # Log rollback metrics
    echo "Rollback test metrics:"
    echo "  Duration: ${ROLLBACK_DURATION}s"
    echo "  Target: <900s (15 minutes)"
    echo "  Status: $([ $ROLLBACK_DURATION -lt 900 ] && echo 'PASS' || echo 'FAIL')"
    
    # Report to monitoring
    curl -X POST http://monitoring.yourdomain.com/api/metrics \
        -d "rollback_test_duration=$ROLLBACK_DURATION"
else
    echo "No rollback needed - cleaning up test deployment"
    kubectl set image deployment/trading-bot-swarm \
        trading-bot-swarm="$CURRENT_VERSION" \
        -n staging
fi

echo "Rollback test completed successfully!"
```

#### Automated Rollback Scheduling

Schedule regular rollback tests:

```yaml
# .github/workflows/rollback-test.yml
name: Automated Rollback Test

on:
  schedule:
    # Run every Monday at 2 AM UTC
    - cron: '0 2 * * 1'
  workflow_dispatch: # Allow manual trigger

jobs:
  rollback-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/setup-kubectl@v3

      - name: Run rollback test
        env:
          KUBECONFIG: ${{ secrets.STAGING_KUBECONFIG }}
        run: |
          ./scripts/test-rollback.sh

      - name: Report results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: rollback-test-results
          path: test-results/
```

#### Database Rollback Testing

```bash
# scripts/test-db-rollback.sh
#!/bin/bash
# Test database migration rollback

set -e

echo "Testing database rollback..."

# 1. Create test database snapshot
./scripts/backup-db.sh --env staging --tag "rollback-test-$(date +%s)"

# 2. Apply migration
./scripts/migrate-db.sh --env staging --version latest

# 3. Verify migration
./scripts/verify-migration.sh --env staging

# 4. Rollback migration
./scripts/rollback-db.sh --env staging --version previous

# 5. Verify rollback
./scripts/verify-migration.sh --env staging

# 6. Check data integrity
psql "$STAGING_DATABASE_URL" -c "
    SELECT COUNT(*) FROM information_schema.tables;
    SELECT COUNT(*) FROM users;
    SELECT COUNT(*) FROM orders;
" > /tmp/post-rollback-counts.txt

echo "Database rollback test completed successfully!"
```

### 8.5 Blue-Green Deployment for Zero-Downtime Rollback

Implement blue-green deployment strategy:

```bash
# scripts/blue-green-deploy.sh
#!/bin/bash
# Blue-green deployment with instant rollback capability

set -e

CURRENT_ENV="${1:-blue}"  # Current active environment
NEW_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

echo "Current active: $CURRENT_ENV"
echo "Deploying to: $NEW_ENV"

# 1. Deploy to inactive environment
kubectl apply -f k8s/deployment-$NEW_ENV.yaml

# 2. Wait for deployment to be ready
kubectl rollout status deployment/trading-bot-swarm-$NEW_ENV

# 3. Run health checks on new environment
./scripts/health-check.sh --env $NEW_ENV --timeout 120 || {
    echo "Health check failed on $NEW_ENV - keeping $CURRENT_ENV active"
    exit 1
}

# 4. Run smoke tests
./scripts/smoke-tests.sh --env $NEW_ENV || {
    echo "Smoke tests failed on $NEW_ENV - keeping $CURRENT_ENV active"
    exit 1
}

# 5. Switch traffic to new environment
echo "Switching traffic to $NEW_ENV..."
kubectl patch service trading-bot-swarm \
    -p '{"spec":{"selector":{"version":"'$NEW_ENV'"}}}'

# 6. Monitor for 5 minutes
echo "Monitoring new environment for 5 minutes..."
for i in {1..30}; do
    sleep 10
    ERROR_RATE=$(curl -s http://metrics.yourdomain.com/api/error_rate)
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "High error rate detected ($ERROR_RATE%) - rolling back!"
        # Instant rollback
        kubectl patch service trading-bot-swarm \
            -p '{"spec":{"selector":{"version":"'$CURRENT_ENV'"}}}'
        echo "Rollback completed - traffic restored to $CURRENT_ENV"
        exit 1
    fi
done

echo "Deployment successful! $NEW_ENV is now active"
echo "Old environment $CURRENT_ENV is still running and can be used for instant rollback"
```

### 8.6 Canary Deployment for Gradual Rollback

```bash
# scripts/canary-deploy.sh
#!/bin/bash
# Canary deployment with gradual traffic shifting

set -e

# Deploy canary version
kubectl apply -f k8s/canary-deployment.yaml

# Gradually increase canary traffic
for percentage in 10 25 50 75 100; do
    echo "Shifting ${percentage}% of traffic to canary..."
    
    kubectl patch virtualservice trading-bot-swarm -p "
    spec:
      http:
      - match:
        - headers:
            version:
              exact: canary
        route:
        - destination:
            host: trading-bot-swarm
            subset: canary
          weight: $percentage
        - destination:
            host: trading-bot-swarm
            subset: stable
          weight: $((100 - percentage))
    " --type merge
    
    # Monitor for 10 minutes at each stage
    sleep 600
    
    # Check metrics
    ERROR_RATE=$(curl -s http://metrics.yourdomain.com/api/canary_error_rate)
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "High error rate in canary - rolling back to 0%"
        kubectl patch virtualservice trading-bot-swarm -p "
        spec:
          http:
          - route:
            - destination:
                host: trading-bot-swarm
                subset: stable
              weight: 100
        " --type merge
        exit 1
    fi
done

echo "Canary deployment completed successfully!"
```

---

## Continuous Improvement

### 9.1 Post-Deployment Review

Schedule a review meeting within 24 hours of deployment to discuss:

- What went well?
- What could be improved?
- Were there any unexpected issues?
- Did we meet our deployment time targets?
- Were all team members properly informed?

### 9.2 Actionable Metrics and KPIs

Track and improve the following deployment metrics systematically:

#### DORA Metrics (DevOps Research and Assessment)

| Metric | Description | Target | Current | Trend |
|--------|-------------|--------|---------|-------|
| **Deployment Frequency** | How often we deploy to production | Daily | - | - |
| **Lead Time for Changes** | Time from commit to production | < 1 hour | - | - |
| **Mean Time to Recovery (MTTR)** | Time to recover from failures | < 15 minutes | - | - |
| **Change Failure Rate** | % of deployments causing issues | < 5% | - | - |

#### Additional Deployment Metrics

```bash
# scripts/collect-deployment-metrics.sh
#!/bin/bash
# Collect deployment metrics for continuous improvement

DEPLOYMENT_ID="$1"
START_TIME="$2"
END_TIME=$(date +%s)
DEPLOYMENT_DURATION=$((END_TIME - START_TIME))

# Calculate deployment success
SUCCESS=0
ERROR_COUNT=$(grep -c ERROR /var/log/trading-bot-swarm/deployment.log || echo 0)
if [[ $ERROR_COUNT -eq 0 ]]; then
    SUCCESS=1
fi

# Record metrics
cat > /tmp/deployment-metrics-$DEPLOYMENT_ID.json <<EOF
{
  "deployment_id": "$DEPLOYMENT_ID",
  "timestamp": $(date +%s),
  "duration_seconds": $DEPLOYMENT_DURATION,
  "success": $SUCCESS,
  "error_count": $ERROR_COUNT,
  "rollback_required": $([ -f /tmp/rollback-triggered ] && echo "true" || echo "false")
}
EOF

# Send to metrics system
curl -X POST http://metrics.yourdomain.com/api/deployments \
    -H "Content-Type: application/json" \
    -d @/tmp/deployment-metrics-$DEPLOYMENT_ID.json

echo "Deployment metrics recorded:"
echo "  Duration: ${DEPLOYMENT_DURATION}s"
echo "  Success: $SUCCESS"
echo "  Errors: $ERROR_COUNT"
```

#### Trading-Specific Metrics

| Metric | Description | Target | Monitoring |
|--------|-------------|--------|------------|
| **Order Success Rate** | % of orders executed successfully | > 99% | Real-time |
| **Order Latency (p95)** | 95th percentile order execution time | < 100ms | Real-time |
| **Slippage** | Average price slippage on orders | < 0.1% | Daily |
| **Position Accuracy** | Accuracy of position tracking | 100% | Real-time |
| **API Uptime** | Exchange API availability | > 99.9% | Real-time |

#### Recovery Metrics

Track recovery performance:

```python
# scripts/calculate_recovery_metrics.py
"""
Calculate and report recovery metrics for incident analysis.
"""

import json
from datetime import datetime
from typing import Dict, List

def calculate_mttr(incidents: List[Dict]) -> float:
    """
    Calculate Mean Time To Recovery (MTTR) from incident data.
    
    Args:
        incidents: List of incident dictionaries with 'start' and 'end' timestamps
        
    Returns:
        Average recovery time in minutes
    """
    if not incidents:
        return 0.0
    
    total_recovery_time = 0
    for incident in incidents:
        start = datetime.fromisoformat(incident['start'])
        end = datetime.fromisoformat(incident['end'])
        recovery_time = (end - start).total_seconds() / 60  # Convert to minutes
        total_recovery_time += recovery_time
    
    return total_recovery_time / len(incidents)

def calculate_mtbf(incidents: List[Dict], period_days: int = 30) -> float:
    """
    Calculate Mean Time Between Failures (MTBF).
    
    Args:
        incidents: List of incidents
        period_days: Period to calculate over
        
    Returns:
        Average time between failures in hours
    """
    if len(incidents) <= 1:
        return float('inf')
    
    total_hours = period_days * 24
    return total_hours / (len(incidents) - 1)

if __name__ == "__main__":
    # Load incident data
    with open('/var/log/trading-bot-swarm/incidents.json', 'r') as f:
        incidents = json.load(f)
    
    # Calculate metrics
    mttr = calculate_mttr(incidents)
    mtbf = calculate_mtbf(incidents)
    
    print(f"Recovery Metrics:")
    print(f"  MTTR: {mttr:.2f} minutes")
    print(f"  MTBF: {mtbf:.2f} hours")
    print(f"  Total Incidents: {len(incidents)}")
```

### 9.3 Metrics Dashboard

Create a deployment metrics dashboard:

```bash
# scripts/generate-metrics-report.sh
#!/bin/bash
# Generate deployment metrics report

cat > /tmp/deployment-report.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Deployment Metrics Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { border: 1px solid #ccc; padding: 15px; margin: 10px 0; }
        .metric h3 { margin-top: 0; }
        .success { color: green; }
        .warning { color: orange; }
        .danger { color: red; }
    </style>
</head>
<body>
    <h1>Trading Bot Swarm - Deployment Metrics</h1>
    <div class="metric">
        <h3>Deployment Success Rate</h3>
        <p class="success">95.5% (Target: >95%)</p>
    </div>
    <div class="metric">
        <h3>Mean Time to Recovery (MTTR)</h3>
        <p class="success">12 minutes (Target: <15 minutes)</p>
    </div>
    <div class="metric">
        <h3>Deployment Frequency</h3>
        <p class="success">4.2 deployments/week (Target: Daily)</p>
    </div>
    <div class="metric">
        <h3>Change Failure Rate</h3>
        <p class="warning">6.5% (Target: <5%)</p>
        <p><em>Action Item: Review failed deployments and improve testing</em></p>
    </div>
</body>
</html>
EOF

echo "Metrics report generated at /tmp/deployment-report.html"
```

### 9.4 Automation Opportunities

Identify areas for automation:

- [ ] Automated deployment pipeline (CI/CD)
- [ ] Automated rollback triggers
- [ ] Automated health checks and alerts
- [ ] Automated performance testing
- [ ] Automated security scanning
- [ ] Infrastructure as Code (IaC)

### 9.5 Documentation Updates

- [ ] Update this runbook based on lessons learned
- [ ] Document any new troubleshooting steps
- [ ] Add new monitoring dashboards or alerts
- [ ] Update architecture diagrams if changed
- [ ] Review and update disaster recovery procedures

### 9.6 Training and Knowledge Sharing

- [ ] Share deployment experience with team
- [ ] Update training materials
- [ ] Conduct knowledge transfer sessions
- [ ] Document tribal knowledge
- [ ] Cross-train team members on deployment

### 9.7 Security Improvements

- [ ] Review access controls and permissions
- [ ] Rotate API keys and credentials
- [ ] Update security scanning tools
- [ ] Review audit logs for anomalies
- [ ] Conduct security training

### 9.8 Process Improvements

Regular review and improvement of:

- Deployment checklist completeness
- Communication effectiveness
- Rollback procedure efficiency
- Monitoring coverage and alert quality
- Testing strategy comprehensiveness

---

## Contributing to this Runbook

### 10.1 Why Contribute?

This runbook is a living document that improves with team collaboration. Your contributions help:
- Share knowledge and best practices across the team
- Document lessons learned from real deployments
- Improve deployment reliability and reduce incidents
- Make onboarding easier for new team members

### 10.2 How to Contribute

#### Suggesting Improvements

1. **Open an Issue**: Create a GitHub issue describing the improvement
   ```
   Title: [Runbook] Improve database rollback procedure
   
   Description:
   - Current section: Rollback Procedures -> Database Rollback
   - Suggested improvement: Add more detailed steps for schema rollback
   - Rationale: Recent incident showed we need clearer guidance
   - References: Incident #123, Post-mortem doc
   ```

2. **Discuss with Team**: Bring up suggestions in deployment retrospectives

3. **Propose Changes**: Submit a pull request with your improvements

#### Making Direct Updates

```bash
# 1. Clone the repository
git clone https://github.com/canstralian/trading-bot-swarm.git
cd trading-bot-swarm

# 2. Create a feature branch
git checkout -b docs/improve-runbook-rollback

# 3. Make your changes to docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md
# Follow the contribution guidelines below

# 4. Commit your changes
git add docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md
git commit -m "docs: improve database rollback procedure"

# 5. Push and create a pull request
git push origin docs/improve-runbook-rollback
```

### 10.3 Contribution Guidelines

#### Content Guidelines

- **Be Specific**: Include exact commands, scripts, and configurations
- **Be Clear**: Write for someone who hasn't done this before
- **Be Accurate**: Test all commands and procedures before adding them
- **Be Current**: Ensure information reflects current practices and tools

#### Formatting Standards

Follow these Markdown best practices:

```markdown
# Use consistent heading levels (don't skip levels)
## Section Title
### Subsection Title

# Format code blocks with language specification
```bash
# This is a bash script
echo "Hello, World!"
```

# Use tables for structured data
| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

# Use checklists for step-by-step procedures
- [ ] Step 1: Do this
- [ ] Step 2: Do that
- [ ] Step 3: Verify result

# Use blockquotes for important notes
> **Note**: This is an important consideration

# Use inline code for commands and variables
Run `kubectl get pods` to check status
Set the `DATABASE_URL` environment variable
```

#### Code Examples

When adding scripts or code examples:

1. **Test First**: Always test code before adding it to the runbook
2. **Add Comments**: Include inline comments explaining complex sections
3. **Error Handling**: Include proper error handling (`set -e`, error checks)
4. **Documentation**: Add a header comment explaining what the script does

Example:

```bash
#!/bin/bash
# scripts/example-script.sh
# Description: Brief description of what this script does
# Usage: ./example-script.sh [options]
# 
# This script demonstrates proper formatting for runbook code examples

set -e  # Exit on error
set -u  # Exit on undefined variable

# Function with clear purpose and documentation
function validate_environment() {
    if [[ -z "${DATABASE_URL:-}" ]]; then
        echo "Error: DATABASE_URL is not set"
        return 1
    fi
    echo "Environment validated successfully"
}

# Main execution
validate_environment
echo "Script completed successfully"
```

#### Documentation Structure

When adding new sections:

1. **Place Appropriately**: Add to the most logical section
2. **Update Table of Contents**: Keep the TOC in sync
3. **Cross-Reference**: Link to related sections when helpful
4. **Update Version History**: Document your changes

### 10.4 Review Process

All runbook changes go through peer review:

1. **Automatic Checks**: CI validates Markdown syntax and links
2. **Peer Review**: At least one team member reviews the changes
3. **Testing**: Changes involving scripts/commands are tested in staging
4. **Approval**: DevOps lead or Release Manager approves the changes

#### Review Checklist

Reviewers should verify:

- [ ] Content is accurate and tested
- [ ] Formatting follows guidelines
- [ ] Links work correctly
- [ ] Code examples are complete and functional
- [ ] No sensitive information (passwords, keys) is included
- [ ] Changes are clear and improve the runbook
- [ ] Version history is updated

### 10.5 Maintenance Responsibilities

#### Regular Reviews

- **Quarterly Review**: Full runbook review every 3 months
- **Post-Incident**: Update after every significant incident
- **Tool Changes**: Update when adopting new tools or processes
- **Team Feedback**: Incorporate feedback from retrospectives

#### Version Control

Update the version history table with each change:

```markdown
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.1 | 2025-10-20 | John Doe | Added automated rollback testing |
| 2.0 | 2025-10-15 | DevOps Team | Major update with observability improvements |
```

### 10.6 Communication

#### Announcing Changes

When making significant updates:

1. **Notify the Team**: Post in the #devops Slack channel
2. **Training Session**: Consider holding a walkthrough for major changes
3. **Update Training Materials**: Sync with onboarding documentation

#### Getting Help

If you need help contributing:

- **Slack**: #devops channel for quick questions
- **Office Hours**: DevOps office hours every Tuesday at 2 PM
- **Documentation**: See [Contributing Guide](../CONTRIBUTING.md) for general guidelines

### 10.7 Recognition

We value contributions to our operational excellence:

- **Contributors List**: Maintained in the repository
- **Shoutouts**: Recognition in team meetings
- **Documentation Champion**: Monthly recognition for significant contributions

### 10.8 Templates

#### Issue Template for Runbook Improvements

```markdown
## Runbook Improvement Suggestion

**Section Affected**: [e.g., Rollback Procedures]

**Current Issue**: 
[Describe what's unclear, missing, or incorrect]

**Suggested Improvement**:
[Describe the proposed change]

**Rationale**:
[Explain why this improvement is needed]

**Priority**: [Low/Medium/High/Critical]

**References**:
- Incident: #XXX
- Related docs: [links]
- Discussion: [link to Slack thread]
```

#### Pull Request Template

```markdown
## Runbook Update

**Type of Change**:
- [ ] Bug fix (correcting inaccurate information)
- [ ] Enhancement (adding new content)
- [ ] Update (refreshing existing content)
- [ ] Formatting (improving structure/readability)

**Changes Made**:
- [List specific changes]

**Testing**:
- [ ] All code examples have been tested
- [ ] All links have been verified
- [ ] Changes reviewed by at least one team member

**Related Issues**: Closes #XXX

**Additional Notes**:
[Any additional context or considerations]
```

---

## Appendix

### A. Contact Information

| Role | Name | Contact |
|------|------|---------|
| Release Manager | TBD | release@example.com |
| DevOps Lead | TBD | devops@example.com |
| On-Call Engineer | TBD | oncall@example.com |
| Security Team | TBD | security@example.com |

### B. External Dependencies

| Service | Purpose | Status Page |
|---------|---------|-------------|
| Trading Exchange APIs | Order execution | https://status.exchange.com |
| Market Data Provider | Real-time data | https://status.marketdata.com |
| Cloud Provider | Infrastructure | https://status.aws.amazon.com |

### C. Useful Commands

```bash
# Check service status
systemctl status trading-bot-swarm

# View recent logs
journalctl -u trading-bot-swarm -n 100

# Check disk space
df -h

# Monitor system resources
htop

# Check database status
systemctl status postgresql

# Test network connectivity
curl -v https://api.exchange.com/ping
```

### D. Emergency Contacts

- **Production Incident**: Escalate to on-call rotation
- **Security Incident**: security@example.com (24/7)
- **Exchange Support**: support@exchange.com
- **Cloud Support**: AWS Support Portal

### E. Related Documents

- Architecture Overview
- API Documentation
- Database Schema
- Security Policy
- Disaster Recovery Plan
- Incident Response Plan

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | 2025-10-15 | DevOps Team | Enhanced with automated validation, security improvements, expanded rollback procedures, observability tools, metrics framework, and contributing guide |
| 1.0 | 2025-10-15 | DevOps Team | Initial version |

---

**Note**: This runbook is a living document and should be updated regularly based on deployment experiences and system changes. Review and update at least quarterly or after significant system changes.
