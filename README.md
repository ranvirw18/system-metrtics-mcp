# System Metrics MCP

System Metrics MCP is a Python-based Model Context Protocol server that exposes system health, process information, disk details, network statistics, battery status, temperature sensors, and secure log file access.

## Installation

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Server

From the project root:

```bash
python server.py
```

This starts the MCP server using stdio transport, which is compatible with Claude Desktop and other MCP clients.

## Claude Desktop Configuration

Use the following `claude.json` or equivalent configuration block:

```json
{
  "mcpServers": {
    "system-metrics": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

## Available Tools

- `get_system_status()`
- `list_high_cpu_processes(limit=5)`
- `list_high_memory_processes(limit=5)`
- `get_disk_details()`
- `read_log_file(filename)`
- `get_network_stats()`
- `get_battery_status()`
- `get_top_process_details(pid)`
- `get_system_temperature()`

## Important Security Notes

- `read_log_file` only allows files inside the local `./logs/` directory.
- Absolute paths and path traversal attempts are rejected.
- Log files larger than 1 MB are refused to prevent denial-of-service or memory exhaustion.
- MCP tool inputs are validated using FastMCP strict input validation.

## Example Prompts

- "What is the current CPU and RAM usage on the system?"
- "List the top 5 processes by CPU usage."
- "Show the top 5 memory-hungry processes."
- "Return the current disk utilization details."
- "Read the contents of `app.log` from the logs directory."
- "Provide the system network statistics."
- "What is the battery charge percentage and is the system plugged in?"
- "Give me detailed metrics for PID 1234."
- "Do we have temperature sensors available and what are their readings?"

## Security Design

- Log files can only be read from the local `./logs/` directory.
- Absolute file paths are rejected.
- Path traversal attempts such as `../` or `../../` are blocked using `pathlib.Path.resolve()` and strict directory validation.
- Invalid file access attempts are logged and returned as human-readable errors.
- Each tool implements exception handling for `FileNotFoundError`, `PermissionError`, `psutil.AccessDenied`, `psutil.NoSuchProcess`, and unexpected exceptions.

## Logging

Application logging is written to `logs/server.log` and also streamed to the console. The server logs:

- tool invocations
- access errors
- unexpected failures

## Notes

- The server is designed for production-quality usage with async support and modular implementation.
- The `logs/` directory is intentionally included as an empty folder for secure log access and server logging.
