import asyncio
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_LOG_FILE_SIZE = 1_048_576
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_log_path(filename: str) -> Path:
    requested_path = Path(filename)
    if requested_path.is_absolute():
        logger.warning("Rejected absolute log file path: %s", filename)
        raise PermissionError("Absolute paths are not permitted for log access.")

    resolved_path = (LOGS_DIR / requested_path).resolve()
    if LOGS_DIR not in resolved_path.parents and resolved_path != LOGS_DIR:
        logger.warning("Rejected path traversal attempt: %s", filename)
        raise PermissionError("Path traversal is not permitted when reading logs.")

    return resolved_path


def _validate_log_file_size(log_path: Path) -> None:
    size = log_path.stat().st_size
    if size > MAX_LOG_FILE_SIZE:
        logger.warning("Rejected oversized log file: %s (%s bytes)", log_path, size)
        raise PermissionError(
            "Log files larger than 1 MB are not permitted for security reasons."
        )


async def read_log_file(filename: str) -> Any:
    """Read a log file from the server logs directory."""
    logger.info("Invoked read_log_file filename=%s", filename)
    try:
        log_path = _resolve_log_path(filename)
        if not log_path.exists():
            logger.error("Log file not found: %s", log_path)
            raise FileNotFoundError(f"Log file not found: {filename}")
        if not log_path.is_file():
            logger.error("Requested log path is not a file: %s", log_path)
            raise FileNotFoundError(f"Log file not found: {filename}")

        _validate_log_file_size(log_path)
        return await asyncio.to_thread(
            log_path.read_text, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError as exc:
        return {"error": str(exc)}
    except PermissionError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error reading log file")
        return {"error": f"Unexpected error reading log file: {exc}"}
