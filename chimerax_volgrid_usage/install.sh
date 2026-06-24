#!/bin/bash

# ChimeraX Volgrid Usage Plugin Installer

set -e

echo "Installing ChimeraX Volgrid Usage Plugin..."

# Check if we're in the correct directory
if [ ! -f "bundle_info.xml" ]; then
    echo "Error: Must run from chimerax_volgrid_usage directory"
    exit 1
fi

# Ensure the bundled VolGrids copy is present
if [ ! -d "src/vendor/volgrids" ]; then
    echo "Error: src/vendor/volgrids directory not found. This directory is required for the plugin to work."
    exit 1
fi

# Build and install the plugin
echo "Building plugin..."
python setup.py bdist_wheel

echo "Plugin built successfully!"
echo ""
echo "In chimerax, use CD to go in the dist directory, and use the ChimeraX command line:"
echo "toolshed install ."
