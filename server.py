import asyncio
import logging
from pathlib import Path

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

from tools.log_tools import read_log_file
from tools.process_tools import (
    get_top_process_details,
    list_high_cpu_processes,
    list_high_memory_processes,
)
from tools.system_tools import (
    get_battery_status,
    get_disk_details,
    get_network_stats,
    get_system_status,
    get_system_temperature,
)

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "server.log"


def configure_logging() -> None:
    """Configure application logging for the MCP server."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", None) == str(LOG_FILE)
        for handler in root_logger.handlers
    ):
        return

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger.setLevel(logging.INFO)
    root_logger.propagate = False

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def register_tools(server: FastMCP) -> None:
    """Register the MCP tool functions with the FastMCP server."""
    server.tool(
        get_system_status,
        name="get_system_status",
        description="Return CPU, RAM, disk, uptime, and running process count.",
    )
    server.tool(
        list_high_cpu_processes,
        name="list_high_cpu_processes",
        description="Return the top processes by CPU usage.",
    )
    server.tool(
        list_high_memory_processes,
        name="list_high_memory_processes",
        description="Return the top processes by memory usage.",
    )
    server.tool(
        get_disk_details,
        name="get_disk_details",
        description="Return total, used, free disk space and usage percentage.",
    )
    server.tool(
        read_log_file,
        name="read_log_file",
        description="Read a log file from the local logs directory.",
    )
    server.tool(
        get_network_stats,
        name="get_network_stats",
        description="Return aggregated network transmit and receive statistics.",
    )
    server.tool(
        get_battery_status,
        name="get_battery_status",
        description="Return battery charge, plugged status, and remaining runtime.",
    )
    server.tool(
        get_top_process_details,
        name="get_top_process_details",
        description="Return detailed metrics for a process by PID.",
    )
    server.tool(
        get_system_temperature,
        name="get_system_temperature",
        description="Return available system temperature sensor readings.",
    )


async def main() -> None:
    """Start the System Metrics MCP server."""
    configure_logging()
    logging.info("Starting System Metrics MCP server")

    server = FastMCP(
        name="system-metrics",
        instructions=(
            "A lightweight MCP server exposing system metrics, process details, "
            "disk usage, network stats, battery information, and secure log reading."
        ),
        version="1.0.0",
        strict_input_validation=True,
        list_page_size=50,
    )

    register_tools(server)

    await server.run_stdio_async(log_level="info")


if __name__ == "__main__":
    asyncio.run(main())
