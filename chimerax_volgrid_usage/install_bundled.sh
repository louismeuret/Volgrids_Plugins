#!/bin/bash

# ChimeraX Volgrids Plugin Installer (self-contained / offline variant)
#
# Unlike install.sh (which relies on pip fetching h5py/MDAnalysis from PyPI at install
# time), this vendors numpy, scipy, matplotlib, MDAnalysis and h5py directly into
# src/vendor_deps and bakes them into the .whl. The resulting wheel needs no network
# access to install, at the cost of being much larger and tied to the exact platform/
# Python ABI of the ChimeraX it was built against.

set -e

echo "Building a self-contained ChimeraX-Volgrids wheel..."
echo "(bundles numpy, scipy, matplotlib, MDAnalysis, h5py directly into the .whl - no network access needed at install time)"
echo ""

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

# Find the ChimeraX executable, so dependencies are fetched matching the exact
# platform/Python ABI of the ChimeraX that will actually run this bundle.
CHIMERAX_BIN="${CHIMERAX_BIN:-$(command -v chimerax || command -v ChimeraX || true)}"
if [ -z "$CHIMERAX_BIN" ]; then
    echo "Error: could not find the 'chimerax' executable on PATH."
    echo "Set CHIMERAX_BIN=/path/to/chimerax and re-run if it's installed elsewhere."
    exit 1
fi
echo "Using ChimeraX at: $CHIMERAX_BIN"
echo ""

echo "Downloading dependencies into src/vendor_deps (requires network access; this can"
echo "take a few minutes and will make the wheel much larger than the regular build)..."
"$CHIMERAX_BIN" -m pip install --upgrade --target=src/vendor_deps \
    "numpy~=2.3" "scipy~=1.15" "matplotlib~=3.10" "MDAnalysis~=2.9" "h5py~=3.14"

echo "Cleaning up bytecode caches..."
find src/vendor_deps -iname "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find src/vendor_deps -iname "*.pyc" -delete 2>/dev/null || true

echo "Building self-contained wheel..."
VOLGRIDS_BUNDLE_DEPS=1 python3 setup.py bdist_wheel

echo ""
echo "Self-contained wheel built successfully in dist/"
echo ""
echo "In chimerax, use CD to go in the dist directory, and use the ChimeraX command line:"
echo "toolshed install . reinstall true"
echo ""
echo "To go back to the regular, smaller wheel (relying on pip/PyPI for h5py/MDAnalysis),"
echo "remove src/vendor_deps and use install.sh instead."
