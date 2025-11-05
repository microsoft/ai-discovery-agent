#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# Script to generate NOTICE file for OSS compliance
# This is a wrapper around the Python script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
PYPROJECT_PATH="$PROJECT_ROOT/src/pyproject.toml"
OUTPUT_PATH="$PROJECT_ROOT/NOTICE"
INCLUDE_DEV=true
VERBOSE=false

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Generate NOTICE file for OSS compliance based on pyproject.toml dependencies.

OPTIONS:
    -p, --pyproject-path PATH   Path to pyproject.toml file (default: src/pyproject.toml)
    -o, --output PATH          Output path for NOTICE file (default: NOTICE)
    --no-dev                   Exclude development dependencies (dev deps included by default)
    -v, --verbose              Enable verbose output
    -h, --help                 Show this help message

EXAMPLES:
    $0                                    # Generate NOTICE file with default settings (includes dev deps)
    $0 --no-dev                          # Exclude development dependencies
    $0 --output NOTICE.txt --verbose     # Custom output path with verbose logging
    $0 --pyproject-path custom/pyproject.toml  # Custom pyproject.toml path

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--pyproject-path)
            PYPROJECT_PATH="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_PATH="$2"
            shift 2
            ;;
        --no-dev)
            INCLUDE_DEV=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1" >&2
            echo "Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Validate that pyproject.toml exists
if [[ ! -f "$PYPROJECT_PATH" ]]; then
    echo "Error: pyproject.toml not found at $PYPROJECT_PATH" >&2
    exit 1
fi

# Build arguments for Python script
PYTHON_ARGS=(
    "--pyproject-path" "$PYPROJECT_PATH"
    "--output" "$OUTPUT_PATH"
)

if [[ "$INCLUDE_DEV" == "false" ]]; then
    PYTHON_ARGS+=(--no-dev)
fi

if [[ "$VERBOSE" == "true" ]]; then
    PYTHON_ARGS+=(--verbose)
fi

# Check if we're in a virtual environment or if Python dependencies are available
if [[ "$VERBOSE" == "true" ]]; then
    echo "Checking Python environment..."
fi

# Try to use uv if available (project uses uv)
if command -v uv &> /dev/null && [[ -f "$PROJECT_ROOT/src/pyproject.toml" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Using uv to run the script..."
    fi
    cd "$PROJECT_ROOT/src"
    uv run python "$SCRIPT_DIR/generate-notice.py" "${PYTHON_ARGS[@]}"
else
    # Fallback to regular Python
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Using system Python to run the script..."
    fi
    python3 "$SCRIPT_DIR/generate-notice.py" "${PYTHON_ARGS[@]}"
fi

echo "NOTICE file generation completed!"
