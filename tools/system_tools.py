import asyncio
import logging
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


def _format_bytes(value: int) -> str:
    """Return a human-readable byte string."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{value} B"


def _format_uptime(seconds: float) -> str:
    """Return uptime as a human-readable string."""
    return str(timedelta(seconds=int(seconds)))


def _get_disk_root() -> str:
    """Return a normalized disk root for the current working directory."""
    anchor = Path.cwd().anchor
    return anchor or "/"


async def get_system_status() -> dict[str, Any]:
    """Get the current system health metrics."""
    logger.info("Invoked get_system_status")
    try:
        disk_root = _get_disk_root()
        cpu_task = asyncio.to_thread(psutil.cpu_percent, 0.25)
        memory_task = asyncio.to_thread(psutil.virtual_memory)
        disk_task = asyncio.to_thread(psutil.disk_usage, disk_root)
        process_task = asyncio.to_thread(lambda: len(psutil.pids()))

        cpu_usage, virtual_memory, disk_usage, process_count = await asyncio.gather(
            cpu_task,
            memory_task,
            disk_task,
            process_task,
        )

        uptime_seconds = time.time() - psutil.boot_time()
        return {
            "cpu_usage_percent": cpu_usage,
            "ram_usage_percent": virtual_memory.percent,
            "disk_usage_percent": disk_usage.percent,
            "system_uptime": _format_uptime(uptime_seconds),
            "running_processes": process_count,
        }
    except psutil.AccessDenied as exc:
        logger.exception("Access denied while reading system status")
        return {"error": "Access denied reading system status."}
    except Exception as exc:
        logger.exception("Unexpected error in get_system_status")
        return {"error": f"Unexpected error reading system status: {exc}"}


async def get_disk_details() -> dict[str, Any]:
    """Get details for the primary disk partition."""
    logger.info("Invoked get_disk_details")
    try:
        disk_root = _get_disk_root()
        disk_usage = await asyncio.to_thread(psutil.disk_usage, disk_root)
        return {
            "total_space": _format_bytes(disk_usage.total),
            "used_space": _format_bytes(disk_usage.used),
            "free_space": _format_bytes(disk_usage.free),
            "usage_percent": disk_usage.percent,
        }
    except psutil.AccessDenied:
        logger.exception("Access denied while reading disk details")
        return {"error": "Access denied reading disk details."}
    except Exception as exc:
        logger.exception("Unexpected error in get_disk_details")
        return {"error": f"Unexpected error reading disk details: {exc}"}


async def get_network_stats() -> dict[str, Any]:
    """Get network I/O totals for the system."""
    logger.info("Invoked get_network_stats")
    try:
        counters = await asyncio.to_thread(psutil.net_io_counters)
        return {
            "bytes_sent": counters.bytes_sent,
            "bytes_received": counters.bytes_recv,
            "packets_sent": counters.packets_sent,
            "packets_received": counters.packets_recv,
            "error_in": counters.errin,
            "error_out": counters.errout,
            "drop_in": counters.dropin,
            "drop_out": counters.dropout,
        }
    except psutil.AccessDenied:
        logger.exception("Access denied while reading network stats")
        return {"error": "Access denied reading network statistics."}
    except Exception as exc:
        logger.exception("Unexpected error in get_network_stats")
        return {"error": f"Unexpected error reading network stats: {exc}"}


async def get_battery_status() -> dict[str, Any]:
    """Get battery status when available."""
    logger.info("Invoked get_battery_status")
    try:
        battery = await asyncio.to_thread(psutil.sensors_battery)
        if battery is None:
            return {"message": "Battery information is not available on this system."}

        secsleft = battery.secsleft
        if battery.power_plugged:
            remaining = "Charging"
        elif secsleft >= 0:
            remaining = _format_uptime(secsleft)
        else:
            remaining = "Unknown"

        return {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
            "time_remaining": remaining,
        }
    except Exception as exc:
        logger.exception("Unexpected error in get_battery_status")
        return {"error": f"Unexpected error reading battery status: {exc}"}


async def get_system_temperature() -> dict[str, Any]:
    """Get available temperature sensor readings."""
    logger.info("Invoked get_system_temperature")
    try:
        temperature_sensors = await asyncio.to_thread(psutil.sensors_temperatures)
        if not temperature_sensors:
            return {"message": "Temperature sensors are not available on this system."}

        formatted = {
            name: [
                {
                    "label": sensor.label or "unknown",
                    "current": sensor.current,
                    "high": sensor.high,
                    "critical": sensor.critical,
                }
                for sensor in sensors
            ]
            for name, sensors in temperature_sensors.items()
        }
        return {"temperatures": formatted}
    except AttributeError:
        logger.exception("Temperature sensor support is unavailable")
        return {"message": "Temperature sensor support is unavailable on this platform."}
    except Exception as exc:
        logger.exception("Unexpected error in get_system_temperature")
        return {"error": f"Unexpected error reading temperature sensors: {exc}"}
