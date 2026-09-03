#!/usr/bin/env bash
# Launcher for macOS and Linux. Make executable with: chmod +x run.sh
cd "$(dirname "$0")" || exit 1
PYTHONPATH="$PWD/src" python3 -m numeracycheck
