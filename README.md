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

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd trading-bot-swarm
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the configuration:**
    *   Copy the environment template: `cp config/.env.template config/.env`
    *   Edit `config/.env` to add your API keys and other secrets.
    *   Review and customize `config/config.yaml` for your trading strategies and bot configurations.

## Usage

To run the main application, execute the `main.py` script:

```bash
python main.py
```

Make sure to configure your bots and strategies in the `config/config.yaml` file before running the application.

### Working with Local LLM Assistants

Some traders enhance their research workflows with lightweight language models that run locally for idea generation or report summarization. If you would like to experiment with this approach, you can load a quantized [GGUF](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) model from Hugging Face using [`llama-cpp-python`](https://github.com/abetlen/llama-cpp-python):

```python
!pip install llama-cpp-python huggingface_hub

from llama_cpp import Llama
from huggingface_hub import hf_hub_download

# Download the GGUF model from Hugging Face
model_path = hf_hub_download(
    repo_id="GGUF-A-Lot/DeepHat-V1-7B-GGUF",
    filename="DeepHat-V1-7B-Q4_K_M.gguf"
)

# Load the model
llm = Llama(model_path=model_path, n_ctx=4096, n_threads=8)

# Run an inference
output = llm(
    "Write a concise summary of DeepHat’s intended architecture and training goals.",
    max_tokens=256,
    temperature=0.7,
)
print(output["choices"][0]["text"])
```

**Tips:**

* `hf_hub_download` retrieves the `.gguf` artifact directly into your environment so it can be reused across sessions.
* `Llama(model_path=...)` is the correct constructor signature for quantized models downloaded from the Hub.
* Tune `n_ctx` (context window) and `n_threads` to fit your hardware capabilities.
* On Windows or Replit you may need a BLAS backend (for example, OpenBLAS). On Apple Silicon, `llama-cpp-python` automatically uses Metal if available.

## Testing

To run the test suite, use `pytest`:

```bash
pytest
```

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
