#!/usr/bin/env bash
# Launch the What's New Orchestrator — starts all 3 servers
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create liverun directories
LIVERUN_DIR="$PROJECT_DIR/liverun"
mkdir -p "$LIVERUN_DIR/media"

# Load GitHub token with SSO authorization for elastic org
GITHUB_TOKEN_FILE="$PROJECT_DIR/.git-token/github.token"
if [ -f "$GITHUB_TOKEN_FILE" ]; then
    export GITHUB_TOKEN
    GITHUB_TOKEN=$(tr -d '[:space:]' < "$GITHUB_TOKEN_FILE")
    echo "  GitHub token loaded from .git-token/github.token"
else
    echo "  WARNING: No GitHub token found at .git-token/github.token"
    echo "  Media extraction from GitHub PRs will be skipped."
    echo "  See README.md for setup instructions."
fi

echo ""
echo "====================================="
echo "  What's New Orchestrator"
echo "  Starting all services..."
echo "====================================="
echo ""

# --- PM Highlighted Features UI (port 5003) ---
echo "Starting PM Features UI on port 5003..."
cd "$PROJECT_DIR/PMhighlightedfeatures"
[ ! -d .venv ] && python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
OUTPUT_DIR="$LIVERUN_DIR" .venv/bin/python3 app.py &
PM_PID=$!

# --- Feature Selection UI (port 5002) ---
echo "Starting Feature Selection UI on port 5002..."
cd "$PROJECT_DIR/FeatureSelection"
[ ! -d .venv ] && python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
OUTPUT_DIR="$LIVERUN_DIR" .venv/bin/python3 app.py &
FS_PID=$!

# --- Orchestrator (port 5000) ---
echo "Setting up Orchestrator on port 5001..."
cd "$SCRIPT_DIR"
[ ! -d .venv ] && python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

echo ""
echo "====================================="
echo "  All services running:"
echo "  Orchestrator:      http://localhost:5001"
echo "  Feature Selection: http://localhost:5002"
echo "  PM Features:       http://localhost:5003"
echo "====================================="
echo ""

# Clean up background processes on exit
cleanup() {
    echo ""
    echo "Shutting down all services..."
    kill "$PM_PID" "$FS_PID" 2>/dev/null || true
    wait "$PM_PID" "$FS_PID" 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

.venv/bin/python3 app.py
