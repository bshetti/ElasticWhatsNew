#!/usr/bin/env bash
# Launch the Feature Selection UI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create / reuse venv
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install deps (fast no-op when already installed)
pip install -q -r requirements.txt

echo ""
echo "====================================="
echo "  Feature Selection UI"
echo "  http://localhost:5002"
echo "====================================="
echo ""

python3 app.py
