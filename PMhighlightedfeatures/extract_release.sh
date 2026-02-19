#!/bin/bash
#
# Extract release features from an Elastic Observability Release Input Document PDF.
# Creates a temporary venv in /tmp, runs the extraction, then cleans up.
#
# Usage:
#   ./extract_release.sh <input.pdf> [output.md]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/extract_release_features.py"
VENV_DIR="$(mktemp -d "${TMPDIR:-/tmp}/release-extract.XXXXXX")"

if [ $# -lt 1 ]; then
    echo "Usage: ./extract_release.sh <input.pdf> [output.md]"
    echo ""
    echo "Extracts features from an Elastic Observability Release Input"
    echo "Document PDF and outputs a structured markdown file."
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: File not found: $1"
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: extract_release_features.py not found in $SCRIPT_DIR"
    exit 1
fi

# Cleanup function — runs on exit regardless of success or failure
cleanup() {
    if [ -d "$VENV_DIR" ]; then
        echo "Cleaning up temporary environment..."
        rm -rf "$VENV_DIR"
    fi
}
trap cleanup EXIT

# Create temporary venv in /tmp (avoids filesystem permission issues)
echo "Setting up temporary environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --quiet pdfplumber

# Run extraction
echo ""
python3 "$PYTHON_SCRIPT" "$@"

# Deactivate (cleanup trap handles deletion)
deactivate
echo ""
echo "Environment cleaned up."
