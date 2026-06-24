import os
from setuptools import setup

# The bundled VolGrids copy (src/vendor/volgrids) vendors its own freyacli/molutils
# dependencies, so the only extra runtime requirements are h5py and MDAnalysis
# (numpy/scipy/matplotlib are already provided by ChimeraX itself, see bundle_info.xml).
#
# install_bundled.sh instead vendors numpy/scipy/matplotlib/MDAnalysis/h5py directly into
# src/vendor_deps (a fully self-contained, offline-installable wheel) and sets
# VOLGRIDS_BUNDLE_DEPS=1 so pip doesn't also try to separately fetch them from PyPI.
install_requires = [] if os.environ.get("VOLGRIDS_BUNDLE_DEPS") == "1" else ["h5py", "MDAnalysis"]

setup(
    name="ChimeraX-Volgrids", 
    version="1.11",
    description="Volumetric grid analysis tool for ChimeraX with Smiffer and APBS integration",
    author="Louis Meuret",
    author_email="contact@example.com",
    url="https://github.com/DiegoBarMor/volgrids",
    packages=["chimerax.volgrids"],
    package_dir={"chimerax.volgrids": "src"},
    include_package_data=True,
    package_data={
        "chimerax.volgrids": ["*.xml", "*.ini", "*.chem", "*.md", "*.txt", "*.yml", "*.sh"],
    },
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Visualization",
        ### Required for ChimeraX's toolshed to recognize/list this as a bundle+tool;
        ### without these "ChimeraX ::" classifiers the wheel installs fine via pip
        ### but never shows up in "toolshed list" or the Tools menu.
        "ChimeraX :: Bundle :: Structure Analysis :: 1,1 :: chimerax.volgrids ::  :: ",
        "ChimeraX :: Tool :: Volgrids :: Structure Analysis :: Volumetric grid analysis with Smiffer and APBS integration",
    ],
    python_requires=">=3.6",
    entry_points={
        "chimerax.bundles": [
            "chimerax.volgrids = chimerax.volgrids:bundle_api",
        ],
    },
)
