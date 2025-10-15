---

# **Copilot Instructions for Trading-Bot-Swarm**

## **Purpose**

This document provides guidance for developers and contributors on effectively using **GitHub Copilot** within the `trading-bot-swarm` project. Copilot can assist in generating code, suggesting improvements, and accelerating development workflows, particularly for writing trading strategies, bot orchestration logic, and integration scripts.

**Intended Audience:**

* Developers familiar with Python, asynchronous programming, and trading bot concepts.
* Contributors looking to enhance code productivity and maintain best practices while using Copilot.

---

## **1. Overview**

`trading-bot-swarm` is a multi-bot trading system designed to execute algorithmic trades across multiple exchanges and strategies. Copilot can help by:

* Suggesting bot behavior implementations.
* Generating API integration code for exchanges.
* Assisting with testing scripts and monitoring dashboards.

---

## **2. Setup Instructions**

### 2.1 Prerequisites

* GitHub account with **Copilot subscription**.
* Local development environment:

  * Python 3.11+
  * Node.js (for any dashboard scripts)
  * Docker (optional, for containerized bot nodes)

### 2.2 Installation

1. **Enable Copilot in VS Code**:

   * Install the **GitHub Copilot** extension from the VS Code marketplace.
   * Sign in using your GitHub credentials.

2. **Enable Copilot in the Repository**:

   * Navigate to the repository in VS Code.
   * Ensure Copilot is active (look for the Copilot icon in the bottom status bar).
   * Optionally configure suggestions via `File > Preferences > Settings > GitHub Copilot`.

3. **Configure Permissions**:

   * Grant Copilot access to the repository for inline suggestions.
   * Ensure network permissions allow VS Code to communicate with GitHub Copilot services.

---

## **3. Usage Guidelines**

### 3.1 Inline Suggestions

* Start typing function signatures, comments, or docstrings; Copilot will suggest code completions.
* Example:

```python
# Define a function to fetch the current BTC price from Binance
async def fetch_btc_price():
```

* Copilot may suggest the implementation automatically.

### 3.2 Code Generation

* Use Copilot for repetitive tasks like:

  * API request handling
  * Data transformations
  * Logging and error handling

### 3.3 Testing Support

* Generate unit tests for trading logic:

```python
# Test if strategy triggers correctly
def test_momentum_strategy_signal():
```

* Copilot can draft test cases based on existing logic.

### 3.4 Maximizing Copilot

* Write descriptive comments before functions to improve suggestion accuracy.
* Accept, modify, or reject suggestions thoughtfully — Copilot is a helper, not a replacement for code review.

---

## **4. Troubleshooting**

| Issue                                | Solution                                                                   |
| ------------------------------------ | -------------------------------------------------------------------------- |
| Copilot not suggesting code          | Ensure extension is installed, signed in, and repository access is enabled |
| Suggestions incorrect or irrelevant  | Provide more descriptive comments or function docstrings                   |
| Network errors                       | Verify internet connection and firewall settings for VS Code               |
| Conflicts with existing linter rules | Configure `.editorconfig` and `.pylintrc` to align with project style      |

**Additional Resources:**

* [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
* [VS Code Copilot Extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)

---

## **5. Best Practices**

* **Review Generated Code:** Always manually review suggestions before merging.
* **Maintain Security:** Do not allow Copilot to suggest secrets, keys, or credentials.
* **Collaborate with Comments:** Use clear function and module comments to improve Copilot accuracy.
* **Code Review Integration:** Pair Copilot usage with PR reviews to catch logic errors.
* **Incremental Adoption:** Use Copilot for scaffolding and boilerplate code rather than critical algorithm logic until verified.

---

## **6. Optional Enhancements**

* **Screenshots & Diagrams:** Include diagrams of bot architecture to guide Copilot in suggesting structured code.
* **Template Files:** Maintain templates for trading strategies or bot node scripts to help Copilot align with project patterns.

---

**Note:** This document should be periodically updated to reflect new Copilot features and updates in the `trading-bot-swarm` codebase.

---
