"""Unit tests for the risk management subsystem."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.core.risk_manager import PositionStatus, RiskManager
from src.core.strategy_interface import SignalType, TradingSignal


@pytest.fixture()
def sample_signal() -> TradingSignal:
    """Create a deterministic long signal for testing."""
    return TradingSignal(
        signal_type=SignalType.BUY,
        symbol="BTCUSDT",
        price=100.0,
        quantity=0.0,
        stop_loss=95.0,
        take_profit_1=110.0,
        take_profit_2=115.0,
        confidence=0.85,
        reason="unit-test",
        timestamp=datetime.now(tz=UTC),
        metadata={"strategy": "unit"},
    )


def test_can_open_position_within_limits(sample_signal: TradingSignal) -> None:
    manager = RiskManager(initial_capital=10_000, max_positions=2)
    assert manager.can_open_position(sample_signal) is True


def test_calculate_position_size(sample_signal: TradingSignal) -> None:
    manager = RiskManager(initial_capital=10_000, max_risk_per_trade=0.02)
    size = manager.calculate_position_size(sample_signal)
    assert pytest.approx(size, rel=1e-3) == 40.0


def test_open_and_close_position_flow(sample_signal: TradingSignal) -> None:
    manager = RiskManager(initial_capital=10_000, max_risk_per_trade=0.02)
    quantity = manager.calculate_position_size(sample_signal)
    position = manager.open_position(sample_signal, quantity)
    assert position.status == PositionStatus.OPEN
    manager.update_position(sample_signal.symbol, current_price=110.0)
    exit_reason = manager.update_position(sample_signal.symbol, current_price=112.0)
    assert exit_reason == "take_profit_1"

    closed = manager.close_position(sample_signal.symbol, reason=exit_reason, partial_close=0.5)
    assert closed is not None
    assert closed.tp1_hit is True
    assert closed.status == PositionStatus.PARTIAL

    manager.update_position(sample_signal.symbol, current_price=115.0)
    exit_reason = manager.update_position(sample_signal.symbol, current_price=118.0)
    assert exit_reason == "take_profit_2"
    fully_closed = manager.close_position(sample_signal.symbol, reason=exit_reason)
    assert fully_closed is not None
    assert fully_closed.status == PositionStatus.CLOSED
    assert manager.positions == {}


def test_portfolio_summary_updates(sample_signal: TradingSignal) -> None:
    manager = RiskManager(initial_capital=10_000, max_risk_per_trade=0.02)
    quantity = manager.calculate_position_size(sample_signal)
    manager.open_position(sample_signal, quantity)
    manager.update_position(sample_signal.symbol, current_price=102.0)

    summary = manager.get_portfolio_summary()
    assert summary["active_positions"] == 1
    assert summary["portfolio_risk"] > 0
