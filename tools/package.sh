#!/bin/bash
# Simple script to package IfcLCA-blend addon

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the packaging script
python3 "$SCRIPT_DIR/package_addon.py" 