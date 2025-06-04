#!/bin/bash

# Set the working directory to the script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting MCP server setup..." >&2
echo "Working directory: $SCRIPT_DIR" >&2
echo "Current Python: $(which python3)" >&2

# Source the Oracle environment variables
if [ -f "$SCRIPT_DIR/setup_oracle_env.sh" ]; then
    echo "Sourcing Oracle environment..." >&2
    source "$SCRIPT_DIR/setup_oracle_env.sh"
else
    echo "Error: setup_oracle_env.sh not found in $SCRIPT_DIR" >&2
    exit 1
fi

# Activate the virtual environment
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    echo "Activating virtual environment..." >&2
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "Using Python: $(which python3)" >&2
else
    echo "Error: Virtual environment not found in $SCRIPT_DIR/.venv" >&2
    exit 1
fi

# Check if MCP server exists
if [ -f "$SCRIPT_DIR/mcp_server.py" ]; then
    echo "Starting MCP server..." >&2
    python3 "$SCRIPT_DIR/mcp_server.py"
else
    echo "Error: mcp_server.py not found in $SCRIPT_DIR" >&2
    exit 1
fi 