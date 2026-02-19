#!/bin/bash
#
# Generate the What's New HTML page for Elastic Observability.
#
# This script:
#   1. Creates a temporary venv (in case future dependencies are added)
#   2. Runs generate_whatsnew.py with the provided arguments
#   3. Copies the output to whats-new.html for Netlify deployment
#   4. Cleans up the venv
#
# Usage:
#   ./run_generate.sh --releases 9.2.0,9.2.2,9.2.3,9.3.0
#   ./run_generate.sh --releases 9.3.0 --pm-file PMhighlightedfeatures/observability-9.3-features.md
#
# Prerequisites:
#   - Python 3.10+
#   - GitHub CLI (gh) installed and authenticated, OR set GITHUB_TOKEN env var
#   - PM features markdown file (see PMhighlightedfeatures/README below)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATE_SCRIPT="$SCRIPT_DIR/generate_whatsnew.py"
VENV_DIR="$(mktemp -d "${TMPDIR:-/tmp}/whatsnew-generate.XXXXXX")"

if [ $# -lt 1 ]; then
    echo "Usage: ./run_generate.sh --releases <versions> [options]"
    echo ""
    echo "Generates the What's New HTML page from Elastic Observability release notes."
    echo ""
    echo "Options (passed through to generate_whatsnew.py):"
    echo "  --releases        Comma-separated versions (e.g. 9.2.0,9.3.0) [required]"
    echo "  --pm-file         PM highlighted features markdown file"
    echo "  --output          Output HTML path (default: whats-new.html)"
    echo "  --media-dir       Media download directory (default: media/)"
    echo "  --github-token    GitHub token (default: \$GITHUB_TOKEN or gh auth token)"
    echo ""
    echo "Example:"
    echo "  ./run_generate.sh --releases 9.2.0,9.2.2,9.2.3,9.3.0 \\"
    echo "    --pm-file PMhighlightedfeatures/observability-9.3-features.md"
    exit 1
fi

if [ ! -f "$GENERATE_SCRIPT" ]; then
    echo "Error: generate_whatsnew.py not found in $SCRIPT_DIR"
    exit 1
fi

# Cleanup function — runs on exit regardless of success or failure
cleanup() {
    if [ -d "$VENV_DIR" ]; then
        echo ""
        echo "Cleaning up temporary environment..."
        rm -rf "$VENV_DIR"
    fi
}
trap cleanup EXIT

# Resolve GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    if command -v gh &> /dev/null; then
        GITHUB_TOKEN="$(gh auth token 2>/dev/null || true)"
    fi
fi

# Build token flag
TOKEN_FLAG=""
if [ -n "$GITHUB_TOKEN" ]; then
    TOKEN_FLAG="--github-token $GITHUB_TOKEN"
fi

# Create temporary venv
echo "Setting up temporary environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# No pip dependencies needed currently (pure stdlib), but the venv
# ensures isolation. Add any future deps here:
# pip install --quiet <package>

# Run generation
echo ""
python3 "$GENERATE_SCRIPT" $TOKEN_FLAG "$@"

# Deactivate (cleanup trap handles deletion)
deactivate

echo ""
echo "Environment cleaned up."
echo "Done! Open the output HTML in a browser to verify."
