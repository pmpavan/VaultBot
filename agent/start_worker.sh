#!/bin/bash
# VaultBot Classifier Worker Startup Script
# This script activates the virtual environment and starts the worker

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load environment variables
export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)

# Activate virtual environment and run worker
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/src/worker.py"
