# Configuration

The Trading Bot Swarm uses layered YAML configuration and environment variables to adapt to multiple deployment targets.

## File Layout

```
config/
├── config.yaml         # base defaults (development)
├── production.yaml     # production overrides
└── *.yaml              # additional environment-specific overrides
```

When `ConfigManager` loads `config/config.yaml`, it also looks for `<environment>.yaml` in the same directory and merges the overrides.

## Key Sections

### `trading`
- `symbol`: market symbol traded by the swarm.
- `capital`: starting portfolio value.
- `max_position_pct`: max exposure per position (e.g. 0.02 = 2%).
- `stop_loss_pct` / `take_profit_pct`: defaults used when strategy signals omit explicit levels.
- `exchanges`: API credentials per exchange.

### `database`
- Configure PostgreSQL (`host != localhost`) or SQLite (default) connections.
- Provide `path` when using SQLite to override the default database file.

### `logging`
- `directory`: output directory for log files.
- `level`: default logging level (INFO, DEBUG, etc.).

### `monitoring`
- `alerts`: thresholds for CPU, memory, disk, and temperature warnings used by `SystemMonitor`.

## Environment Variables

The following environment variables override sensitive credentials:

| Variable            | Target path                                  |
| ------------------- | -------------------------------------------- |
| `BINANCE_API_KEY`   | `trading.exchanges.binance.api_key`          |
| `BINANCE_API_SECRET`| `trading.exchanges.binance.api_secret`       |
| `MEXC_API_KEY`      | `trading.exchanges.mexc.api_key`             |
| `MEXC_API_SECRET`   | `trading.exchanges.mexc.api_secret`          |
| `DB_PASSWORD`       | `database.password`                          |
| `REDIS_PASSWORD`    | `database.redis.password`                    |

Set `PYTHONPATH` or install the package (`pip install -e .`) so that `main.py` discovers the modules correctly.

## Secrets Encryption

Create a `.secret.key` containing a Fernet key to enable encryption helpers:

```bash
python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

Store the printed key in `.secret.key` and secure it using your secrets management solution. Encrypt individual values with `ConfigManager.encrypt_value` and store them in the YAML file; decrypt at runtime with `decrypt_value`.
