import asyncio
import logging
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)

MAX_PROCESS_LIST_LIMIT = 50


def _validate_limit(limit: int) -> int:
    if limit is None:
        return 5
    if limit <= 0:
        logger.warning("Non-positive limit provided, falling back to default")
        return 5
    if limit > MAX_PROCESS_LIST_LIMIT:
        logger.warning("Clamping process list limit from %s to %s", limit, MAX_PROCESS_LIST_LIMIT)
        return MAX_PROCESS_LIST_LIMIT
    return limit


def _collect_process_metrics() -> list[dict[str, Any]]:
    processes: list[psutil.Process] = []
    result: list[dict[str, Any]] = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc.cpu_percent(None)
            processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    time.sleep(0.15)

    for proc in processes:
        try:
            result.append(
                {
                    "pid": proc.pid,
                    "name": proc.name() or "unknown",
                    "cpu_usage_percent": proc.cpu_percent(None),
                    "memory_usage_percent": proc.memory_percent(),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return result


async def list_high_cpu_processes(limit: int = 5) -> dict[str, Any]:
    """Return a sorted list of top CPU-consuming processes."""
    limit = _validate_limit(limit)
    logger.info("Invoked list_high_cpu_processes limit=%s", limit)
    try:
        processes = await asyncio.to_thread(_collect_process_metrics)
        top_processes = sorted(
            processes,
            key=lambda item: item["cpu_usage_percent"],
            reverse=True,
        )[:limit]
        return {"processes": top_processes}
    except Exception as exc:
        logger.exception("Unexpected error in list_high_cpu_processes")
        return {"error": f"Unexpected error listing CPU-heavy processes: {exc}"}


async def list_high_memory_processes(limit: int = 5) -> dict[str, Any]:
    """Return a sorted list of top memory-consuming processes."""
    limit = _validate_limit(limit)
    logger.info("Invoked list_high_memory_processes limit=%s", limit)
    try:
        processes = await asyncio.to_thread(_collect_process_metrics)
        top_processes = sorted(
            processes,
            key=lambda item: item["memory_usage_percent"],
            reverse=True,
        )[:limit]
        return {"processes": top_processes}
    except Exception as exc:
        logger.exception("Unexpected error in list_high_memory_processes")
        return {"error": f"Unexpected error listing memory-heavy processes: {exc}"}


def _fetch_process_details(pid: int) -> dict[str, Any]:
    proc = psutil.Process(pid)
    with proc.oneshot():
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "status": proc.status(),
            "cpu_usage_percent": proc.cpu_percent(interval=0.15),
            "memory_usage_percent": proc.memory_percent(),
            "create_time": proc.create_time(),
            "exe": proc.exe(),
            "cmdline": proc.cmdline(),
            "username": proc.username(),
        }


async def get_top_process_details(pid: int) -> dict[str, Any]:
    """Return detailed information for a single process."""
    logger.info("Invoked get_top_process_details pid=%s", pid)
    if not isinstance(pid, int) or pid <= 0:
        logger.warning("Invalid PID supplied to get_top_process_details: %s", pid)
        return {"error": "The PID must be a positive integer."}

    try:
        return await asyncio.to_thread(_fetch_process_details, pid)
    except psutil.NoSuchProcess:
        logger.exception("Requested process does not exist")
        return {"error": f"No process found with PID {pid}."}
    except psutil.AccessDenied:
        logger.exception("Access denied while reading process details")
        return {"error": f"Access denied reading details for PID {pid}."}
    except ValueError:
        logger.exception("Invalid PID supplied to get_top_process_details")
        return {"error": "The PID must be a positive integer."}
    except Exception as exc:
        logger.exception("Unexpected error in get_top_process_details")
        return {"error": f"Unexpected error reading process details: {exc}"}
