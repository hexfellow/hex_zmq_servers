#!/usr/bin/env bash
set -Eeuo pipefail
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-05-26
################################################################

# Parse command line arguments
MINIMAL=false
EXAMPLES=true
while [[ $# -gt 0 ]]; do
  case $1 in
  --min)
    MINIMAL=true
    shift
    ;;
  --pkg-only)
    EXAMPLES=false
    shift
    ;;
  *)
    echo "Unknown option: $1"
    echo "Usage: $0 [--min|--pkg-only]"
    echo "  --min : Install with minimal package"
    echo "  --pkg-only : Install without examples"
    exit 1
    ;;
  esac
done

CUR_DIR="$(pwd)"
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "CUR_DIR: $CUR_DIR"
echo "SCRIPT_DIR: $SCRIPT_DIR"

cd $SCRIPT_DIR

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv not found. Please install uv first." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  uv venv --python 3.11
fi
source .venv/bin/activate

# Install hex_zmq_servers
rm -rf dist build *.egg-info
uv pip uninstall hex_zmq_servers || true

if [ "$MINIMAL" = true ]; then
  echo "Installing minimal package..."
  uv pip install -e .
else
  echo "Installing with [all] extras..."
  uv pip install -e .[all]
fi

if [ "$EXAMPLES" = true ]; then
  echo "Installing requirements for advanced examples..."
  uv pip install -r examples/adv/requirements.txt
fi

cd $CUR_DIR
