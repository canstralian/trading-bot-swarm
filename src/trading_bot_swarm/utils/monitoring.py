"""Async system monitoring utilities for the trading bot."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

import psutil

from .rpi_utils import RPiUtils

logger = logging.getLogger(__name__)


@dataclass
class AlertThresholds:
    """Threshold configuration for health alerts."""

    cpu: float = 90.0
    memory: float = 90.0
    disk: float = 90.0
    cpu_temp: float = 80.0


class SystemMonitor:
    """Collects system metrics and evaluates alert thresholds."""

    def __init__(
        self,
        rpi_config: Optional[Dict[str, Any]] = None,
        alert_thresholds: Optional[Dict[str, Any]] = None,
        sample_interval: float = 5.0,
    ) -> None:
        self._rpi_config = rpi_config or {}
        self._thresholds = self._load_thresholds(alert_thresholds)
        self._sample_interval = sample_interval

    async def get_system_health(self) -> Dict[str, Any]:
        """Collect CPU, memory, disk and temperature metrics."""
        metrics = await asyncio.to_thread(self._collect_metrics)
        metrics["alerts"] = self._evaluate_alerts(metrics)
        return metrics

    async def watch(
        self,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        """Stream metrics to a callback until the stop event is set."""
        stop_event = stop_event or asyncio.Event()
        while not stop_event.is_set():
            metrics = await self.get_system_health()
            try:
                await callback(metrics)
            except Exception:  # pragma: no cover - consumer error
                logger.exception("System monitor callback failed")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self._sample_interval)
            except asyncio.TimeoutError:
                continue

    def _collect_metrics(self) -> Dict[str, Any]:
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_usage = psutil.virtual_memory().percent

        try:
            disk_usage = psutil.disk_usage(self._rpi_config.get("disk_path", "/")).percent
        except FileNotFoundError:
            disk_usage = psutil.disk_usage("/").percent

        net = psutil.net_io_counters()

        metrics: Dict[str, Any] = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_sent": net.bytes_sent,
            "network_recv": net.bytes_recv,
            "cpu_temp": self._safe_temperature(),
            "is_raspberry_pi": RPiUtils.is_raspberry_pi(),
        }
        return metrics

    def _safe_temperature(self) -> Optional[float]:
        temperature = RPiUtils.get_cpu_temperature()
        if temperature is not None:
            return temperature
        try:
            sensors = psutil.sensors_temperatures()
        except (AttributeError, NotImplementedError):  # pragma: no cover - platform specific
            return None

        if not sensors:
            return None
        core_readings = sensors.get("coretemp") or sensors.get("cpu-thermal")
        if not core_readings:
            return None
        primary = core_readings[0]
        return getattr(primary, "current", None)

    def _evaluate_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        alerts: List[str] = []
        if metrics["cpu_usage"] >= self._thresholds.cpu:
            alerts.append("cpu")
        if metrics["memory_usage"] >= self._thresholds.memory:
            alerts.append("memory")
        if metrics["disk_usage"] >= self._thresholds.disk:
            alerts.append("disk")
        cpu_temp = metrics.get("cpu_temp")
        if cpu_temp is not None and cpu_temp >= self._thresholds.cpu_temp:
            alerts.append("cpu_temp")
        return alerts

    def _load_thresholds(self, overrides: Optional[Dict[str, Any]]) -> AlertThresholds:
        if not overrides:
            return AlertThresholds()

        allowed_keys = {field.name for field in __import__("dataclasses").fields(AlertThresholds)}
        filtered = {k: v for k, v in overrides.items() if k in allowed_keys}
        return AlertThresholds(**filtered)


__all__ = ["SystemMonitor", "AlertThresholds"]
