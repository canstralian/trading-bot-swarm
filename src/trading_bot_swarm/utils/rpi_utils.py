"""Utility helpers for interacting with Raspberry Pi hardware safely."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RPiUtils:
    """Raspberry Pi specific utilities with graceful fallbacks."""

    CPU_TEMP_PATH = Path("/sys/class/thermal/thermal_zone0/temp")
    GPU_TEMP_COMMAND = ("/usr/bin/vcgencmd", "measure_temp")

    @classmethod
    def is_raspberry_pi(cls) -> bool:
        """Return True when running on Raspberry Pi hardware."""
        try:
            model_path = Path("/proc/device-tree/model")
            if model_path.exists():
                return "raspberry pi" in model_path.read_text().lower()
        except OSError:
            logger.debug("Unable to determine Raspberry Pi model", exc_info=True)
        return False

    @classmethod
    def get_cpu_temperature(cls) -> Optional[float]:
        """Read the CPU temperature in Celsius when available."""
        try:
            if cls.CPU_TEMP_PATH.exists():
                raw_value = cls.CPU_TEMP_PATH.read_text().strip()
                return float(raw_value) / 1000.0
        except (OSError, ValueError):
            logger.debug("Failed to read CPU temperature", exc_info=True)
        return None

    @classmethod
    def get_gpu_temperature(cls) -> Optional[float]:
        """Read the GPU temperature from vcgencmd when available."""
        try:
            from subprocess import check_output  # imported lazily for performance

            output = check_output(cls.GPU_TEMP_COMMAND, text=True)
            if "=" in output:
                temp_value = output.split("=")[1].split("'C")[0]
                return float(temp_value)
        except Exception:  # pragma: no cover - hardware specific
            logger.debug("Failed to read GPU temperature", exc_info=True)
        return None

    @classmethod
    def get_serial_number(cls) -> Optional[str]:
        """Fetch the Raspberry Pi serial number when it exists."""
        try:
            cpu_info = Path("/proc/cpuinfo").read_text().splitlines()
            for line in cpu_info:
                if line.lower().startswith("serial"):
                    return line.split(":")[-1].strip()
        except OSError:
            logger.debug("Failed to obtain Raspberry Pi serial", exc_info=True)
        return None


__all__ = ["RPiUtils"]
