from chimerax.ui import MainToolWindow
from chimerax.core.tools import ToolInstance
from Qt.QtWidgets import (QVBoxLayout, QPushButton, QLabel, QListWidget, QHBoxLayout,
                         QInputDialog, QMessageBox, QFileDialog, QLineEdit, QComboBox,
                         QCheckBox, QSpinBox, QDoubleSpinBox, QTextEdit, QProgressBar,
                         QGroupBox, QGridLayout, QFormLayout, QTabWidget, QWidget,
                         QScrollArea, QSplitter, QStackedWidget, QApplication)
from functools import partial
from Qt.QtCore import Qt, QThread
try:
    from Qt.QtCore import pyqtSignal
except ImportError:
    try:
        from Qt.QtCore import Signal as pyqtSignal
    except ImportError:
        from PyQt5.QtCore import pyqtSignal
import os
import json
import re
import shutil
import subprocess
import sys
import threading
import os.path

# //////////////////////////////////////////////////////////////////////////////
# Declarative specs for the 'vgtools' and 'smutils' subcommands, mirroring
# volgrids/_ui/fy_help.fyh and fy_rules.fyr. Each arg tuple is:
#   (key, flag_or_None, kind, label, required, default)
# 'flag' is the CLI flag (e.g. "-f"); None means the argument is positional.
# 'kind' selects the widget: file_in/file_out/dir_out/files_in/str/float/int/
# floats3/floats4/floats6/bool/choice. "floatsN" kinds hold space-separated
# values, split into separate argv tokens when building the command.

def _io_2_inputs_args():
    return [
        ("path_in_0", None, "file_in", "Input Grid A (defines target grid)", True, None),
        ("path_in_1", None, "file_in", "Input Grid B (interpolated if needed)", True, None),
        ("path_out", None, "file_out", "Output Grid", True, None),
        ("common_box", "-b", "bool", "Use common box (--common-box)", False, None),
    ]

VGTOOLS_OPERATIONS = {
    "convert": {
        "subcommand": ["convert"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
            ("folder_out", None, "dir_out", "Output Folder (optional)", False, None),
            ("format", "-f", "choice", "Format", False, "MRC"),
        ],
    },
    "pack": {
        "subcommand": ["pack"],
        "args": [
            ("paths_in", None, "files_in", "Input Grids", True, None),
            ("path_out", "-o", "file_out", "Output CMAP File", True, None),
        ],
    },
    "unpack": {
        "subcommand": ["unpack"],
        "args": [
            ("path_in", None, "file_in", "Input CMAP File", True, None),
            ("folder_out", None, "dir_out", "Output Folder (optional)", False, None),
            ("format", "-f", "choice", "Format", False, "MRC"),
        ],
    },
    "extract": {
        "subcommand": ["extract"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
        ],
    },
    "fix_cmap": {
        "subcommand": ["fix_cmap"],
        "args": [
            ("path_in", None, "file_in", "Input CMAP File", True, None),
            ("path_out", None, "file_out", "Output CMAP File", True, None),
        ],
    },
    "rotate": {
        "subcommand": ["rotate"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
            ("path_out", None, "file_out", "Output Grid", True, None),
            ("x", "-x", "float", "Rotation X (yz plane, deg)", False, "0.0"),
            ("y", "-y", "float", "Rotation Y (xz plane, deg)", False, "0.0"),
            ("z", "-z", "float", "Rotation Z (xy plane, deg)", False, "0.0"),
        ],
    },
    "segment": {
        "subcommand": ["segment"],
        "args": [
            ("path_in", None, "file_in", "Input Grid (BIN format)", True, None),
            ("path_out", None, "file_out", "Output Grid (cluster labels)", True, None),
            ("isovalue", "-i", "float", "Isovalue", False, "0.1"),
            ("volume_thr", "-v", "int", "Volume Threshold", False, "200"),
        ],
    },
    "average": {
        "subcommand": ["average"],
        "args": [
            ("path_in", None, "file_in", "Input CMAP Series File", True, None),
            ("path_out", None, "file_out", "Output Grid", True, None),
        ],
    },
    "std_dev": {
        "subcommand": ["std_dev"],
        "args": [
            ("path_in", None, "file_in", "Input CMAP Series File", True, None),
            ("path_out", None, "file_out", "Output Grid", True, None),
        ],
    },
    "op_abs": {
        "subcommand": ["op", "abs"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
            ("path_out", None, "file_out", "Output Grid", True, None),
        ],
    },
    "op_add": {"subcommand": ["op", "add"], "args": _io_2_inputs_args()},
    "op_sub": {"subcommand": ["op", "sub"], "args": _io_2_inputs_args()},
    "op_mul": {"subcommand": ["op", "mul"], "args": _io_2_inputs_args()},
    "op_div": {"subcommand": ["op", "div"], "args": _io_2_inputs_args()},
    "op_and": {"subcommand": ["op", "and"], "args": _io_2_inputs_args()},
    "op_or":  {"subcommand": ["op", "or"],  "args": _io_2_inputs_args()},
    "summary": {
        "subcommand": ["summary"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
        ],
    },
    "histogram": {
        "subcommand": ["histogram"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
            ("path_out", "-o", "file_out", "Output Plot Image (optional)", False, None),
            ("key", "-k", "str", "CMAP Key (optional)", False, None),
        ],
    },
    "compare": {
        "subcommand": ["compare"],
        "args": [
            ("path_0", None, "file_in", "Grid A", True, None),
            ("path_1", None, "file_in", "Grid B", True, None),
            ("threshold", "-t", "float", "Threshold", False, "1e-3"),
        ],
    },
    "points": {
        "subcommand": ["points"],
        "args": [
            ("path_in", None, "file_in", "Input Grid", True, None),
            ("points", None, "floats3", "Points (x y z [x y z ...])", True, None),
        ],
    },
}

SMUTILS_OPERATIONS = {
    "res_nobp": {
        "subcommand": ["res_nobp"],
        "args": [("path_in", None, "file_in", "Input Structure", True, None)],
    },
    "res_nostk": {
        "subcommand": ["res_nostk"],
        "args": [("path_in", None, "file_in", "Input Structure", True, None)],
    },
    "chemgen": {
        "subcommand": ["chemgen"],
        "args": [
            ("path_in", None, "file_in", "Input Ligand Structure", True, None),
            ("path_out", None, "file_out", "Output .chem File (optional)", False, None),
        ],
    },
    "sphere_find": {
        "subcommand": ["sphere", "find"],
        "args": [
            ("path_in", None, "file_in", "Input Structure", True, None),
            ("query", None, "str", "Selection Query (MDAnalysis syntax)", True, None),
            ("path_traj", "-t", "file_in", "Trajectory File (optional)", False, None),
            ("radius_extra", "-r", "float", "Extra Radius", False, "0.0"),
        ],
    },
    "sphere_grid": {
        "subcommand": ["sphere", "grid"],
        "args": [
            ("path_in", None, "file_in", "Input Structure", True, None),
            ("sphere", "-s", "floats4", "Sphere (x y z radius)", True, None),
            ("folder_out", "-o", "dir_out", "Output Folder (optional)", False, None),
            ("path_traj", "-t", "file_in", "Trajectory File (optional)", False, None),
        ],
    },
    "occupancy": {
        "subcommand": ["occupancy"],
        "args": [
            ("path_in", None, "file_in", "Input Structure", True, None),
            ("folder_out", "-o", "dir_out", "Output Folder (optional)", False, None),
            ("path_traj", "-t", "file_in", "Trajectory File (optional)", False, None),
            ("path_apbs", "-a", "file_in", "Cached APBS File (optional)", False, None),
            ("path_chem", "-e", "file_in", "Chem Table Override (optional)", False, None),
            ("configs", "-c", "str", "Config Overrides (file path or KEY=value pairs, optional)", False, None),
            ("box", "-b", "floats6", "Box (x_min x_max y_min y_max z_min z_max, optional)", False, None),
            ("sphere", "-s", "floats4", "Sphere (x y z radius, optional)", False, None),
            ("residues", "-r", "str", "Residues (chain.resid ..., optional)", False, None),
            ("nproc", "-n", "int", "Worker Processes", False, "1"),
            ("pack", "--pack", "bool", "Pack outputs into single CMAP", False, None),
        ],
    },
    "pwoverlap": {
        "subcommand": ["pwoverlap"],
        "args": [
            ("path_source", None, "file_in", "Source Structure", True, None),
            ("path_target", None, "file_in", "Target Structure", True, None),
            ("path_out", None, "file_out", "Output CSV File", True, None),
        ],
    },
    "box_dim": {
        "subcommand": ["box_dim"],
        "args": [("path_in", None, "file_in", "Input Structure", True, None)],
    },
    "log_apbs": {
        "subcommand": ["log_apbs"],
        "args": [
            ("path_in", None, "file_in", "Input APBS Grid", True, None),
            ("path_out", None, "file_out", "Output Grid", True, None),
        ],
    },
}

# Dependencies VolGrids needs. "pip" deps are installed into this application's own
# Python interpreter (the same one VolGrids subprocesses run under via sys.executable);
# "binary" deps (pdb2pqr, apbs) are external command-line tools resolved via PATH (they
# may live in a totally different environment, e.g. a conda install), so they're checked
# by actually running them rather than via Python package metadata.
DEPENDENCY_SPECS = [
    {"name": "numpy", "kind": "pip", "min_version": (2, 3), "pip_spec": "numpy~=2.3"},
    {"name": "scipy", "kind": "pip", "min_version": (1, 15), "pip_spec": "scipy~=1.15"},
    {"name": "matplotlib", "kind": "pip", "min_version": (3, 10), "pip_spec": "matplotlib~=3.10"},
    {"name": "MDAnalysis", "kind": "pip", "min_version": (2, 9), "pip_spec": "MDAnalysis~=2.9"},
    {"name": "h5py", "kind": "pip", "min_version": (3, 14), "pip_spec": "h5py~=3.14"},
    {"name": "pdb2pqr", "kind": "binary", "min_version": (3, 0), "pip_spec": None},
    {"name": "apbs", "kind": "binary", "min_version": None, "pip_spec": None},
]


class SmifferTool(ToolInstance):

    SESSION_ENDURING = True
    SESSION_SAVE = True
    help = "help:user/tools/smiffertool.html"

    def __init__(self, session, tool_name):
        ToolInstance.__init__(self, session, tool_name)
        self.display_name = "Smiffer Tool"

        self.current_process = None
        self.worker_thread = None
        self.dependency_rows = {}
        self.dependency_fix_workers = []

        from chimerax.ui import MainToolWindow
        self.tool_window = MainToolWindow(self)
        self.tool_window.fill_context_menu = self.fill_context_menu
        self._build_ui()

    def fill_context_menu(self, menu, x, y):

        from Qt.QtGui import QAction
        clear_action = QAction("Clear", menu)
        clear_action.triggered.connect(lambda *args: self.line_edit.clear())
        menu.addAction(clear_action)

    def _build_ui(self):
        # Create main splitter for layout
        main_splitter = QSplitter(Qt.Vertical)
        
        # Create tab widget for different sections
        tabs = QTabWidget()
        
        # Basic Settings Tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Input file section
        input_group = QGroupBox("Input Structure")
        input_layout = QFormLayout(input_group)
        
        self.input_file_edit = QLineEdit()
        self.first_files_folder = []
        input_browse_btn = QPushButton("Browse")
        input_load_current_structure = QPushButton("Load Currently displayed structure")
        input_browse_btn.clicked.connect(self.browse_input_file)
        input_load_current_structure.clicked.connect(self.load_current_structure)
        input_file_layout = QHBoxLayout()
        input_file_layout.addWidget(self.input_file_edit)
        input_file_layout.addWidget(input_browse_btn)
        input_file_layout.addWidget(input_load_current_structure)
        input_layout.addRow("Structure File:", input_file_layout)

        # Output directory
        self.output_dir_edit = QLineEdit()
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(output_browse_btn)
        input_layout.addRow("Output Directory:", output_dir_layout)

        basic_layout.addWidget(input_group)

        # Configuration overrides section: every tunable setting from VolGrids' own
        # config_volgrids.ini, each with a checkbox to opt into overriding it and an
        # editable field (pre-filled with the bundled default) for the value to use.
        config_group = QGroupBox("Configuration Overrides")
        config_outer_layout = QVBoxLayout(config_group)

        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setMaximumHeight(250)
        config_scroll_widget = QWidget()
        config_scroll_layout = QVBoxLayout(config_scroll_widget)

        self.config_setting_rows = {}
        for entry in self._parse_config_settings():
            if entry[0] == "section":
                _, title = entry
                section_label = QLabel(title)
                section_label.setStyleSheet("font-weight: bold;")
                config_scroll_layout.addWidget(section_label)
                continue

            _, key, value, comment = entry
            row_layout = QHBoxLayout()
            checkbox = QCheckBox(key)
            value_edit = QLineEdit(value)
            if comment:
                checkbox.setToolTip(comment)
                value_edit.setToolTip(comment)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(value_edit)
            config_scroll_layout.addLayout(row_layout)
            self.config_setting_rows[key] = (checkbox, value_edit)

        config_scroll_layout.addStretch()
        config_scroll.setWidget(config_scroll_widget)
        config_outer_layout.addWidget(config_scroll)

        basic_layout.addWidget(config_group)

        # Advanced Settings Tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Trajectory section
        traj_group = QGroupBox("Trajectory Options")
        traj_layout = QFormLayout(traj_group)
        
        self.trajectory_edit = QLineEdit()
        traj_browse_btn = QPushButton("Browse")
        traj_browse_btn.clicked.connect(self.browse_trajectory)
        traj_layout_h = QHBoxLayout()
        traj_layout_h.addWidget(self.trajectory_edit)
        traj_layout_h.addWidget(traj_browse_btn)
        traj_layout.addRow("Trajectory File:", traj_layout_h)

        self.nproc_spin = QSpinBox()
        self.nproc_spin.setRange(1, 256)
        self.nproc_spin.setValue(1)
        self.nproc_spin.setToolTip("Worker processes for trajectory mode (1 disables multiprocessing). No effect outside trajectory mode.")
        traj_layout.addRow("Worker Processes:", self.nproc_spin)

        advanced_layout.addWidget(traj_group)

        # APBS section
        apbs_group = QGroupBox("APBS Options")
        apbs_layout = QFormLayout(apbs_group)

        self.apbs_file_edit = QLineEdit()
        apbs_browse_btn = QPushButton("Browse")
        apbs_browse_btn.clicked.connect(self.browse_apbs_file)
        apbs_layout_h = QHBoxLayout()
        apbs_layout_h.addWidget(self.apbs_file_edit)
        apbs_layout_h.addWidget(apbs_browse_btn)
        apbs_layout.addRow("Cached APBS File:", apbs_layout_h)

        apbs_note = QLabel(
            "If left empty, Smiffer computes APBS automatically.\n"
            "Use the button below to pre-compute it with 'volgrids apbs' and reuse the result."
        )
        apbs_note.setStyleSheet("color: gray; font-style: italic;")
        apbs_layout.addRow("", apbs_note)

        self.apbs_mrc_checkbox = QCheckBox("Output as MRC (instead of DX)")
        apbs_layout.addRow("", self.apbs_mrc_checkbox)

        self.apbs_keep_pqr_checkbox = QCheckBox("Keep intermediary PQR file")
        apbs_layout.addRow("", self.apbs_keep_pqr_checkbox)

        self.apbs_verbose_checkbox = QCheckBox("Verbose APBS output")
        apbs_layout.addRow("", self.apbs_verbose_checkbox)

        self.run_apbs_now_button = QPushButton("Generate APBS Grid Now")
        self.run_apbs_now_button.clicked.connect(self.run_apbs_now)
        apbs_layout.addRow("", self.run_apbs_now_button)

        advanced_layout.addWidget(apbs_group)
        
        # Pocket sphere section
        pocket_group = QGroupBox("Pocket Sphere Mode")
        pocket_layout = QFormLayout(pocket_group)
        
        self.pocket_sphere_checkbox = QCheckBox("Enable Pocket Sphere Mode")
        self.pocket_sphere_checkbox.toggled.connect(self.toggle_pocket_sphere)
        pocket_layout.addRow("", self.pocket_sphere_checkbox)
        
        self.sphere_radius_spin = QDoubleSpinBox()
        self.sphere_radius_spin.setRange(0.1, 100.0)
        self.sphere_radius_spin.setValue(10.0)
        self.sphere_radius_spin.setEnabled(False)
        pocket_layout.addRow("Radius (Å):", self.sphere_radius_spin)
        
        sphere_coords_layout = QHBoxLayout()
        self.sphere_x_spin = QDoubleSpinBox()
        self.sphere_x_spin.setRange(-999.0, 999.0)
        self.sphere_x_spin.setEnabled(False)
        self.sphere_y_spin = QDoubleSpinBox()
        self.sphere_y_spin.setRange(-999.0, 999.0)
        self.sphere_y_spin.setEnabled(False)
        self.sphere_z_spin = QDoubleSpinBox()
        self.sphere_z_spin.setRange(-999.0, 999.0)
        self.sphere_z_spin.setEnabled(False)
        sphere_coords_layout.addWidget(QLabel("X:"))
        sphere_coords_layout.addWidget(self.sphere_x_spin)
        sphere_coords_layout.addWidget(QLabel("Y:"))
        sphere_coords_layout.addWidget(self.sphere_y_spin)
        sphere_coords_layout.addWidget(QLabel("Z:"))
        sphere_coords_layout.addWidget(self.sphere_z_spin)
        pocket_layout.addRow("Center:", sphere_coords_layout)
        
        advanced_layout.addWidget(pocket_group)
        
        # Chemical table section
        chem_group = QGroupBox("Chemical Table")
        chem_layout = QFormLayout(chem_group)
        
        self.chem_table_edit = QLineEdit()
        chem_browse_btn = QPushButton("Browse")
        chem_browse_btn.clicked.connect(self.browse_chem_table)
        chem_layout_h = QHBoxLayout()
        chem_layout_h.addWidget(self.chem_table_edit)
        chem_layout_h.addWidget(chem_browse_btn)
        chem_layout.addRow("Table File (.chem):", chem_layout_h)
        
        advanced_layout.addWidget(chem_group)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        
        self.config_file_edit = QLineEdit()
        config_browse_btn = QPushButton("Browse")
        config_browse_btn.clicked.connect(self.browse_config_file)
        config_layout_h = QHBoxLayout()
        config_layout_h.addWidget(self.config_file_edit)
        config_layout_h.addWidget(config_browse_btn)
        config_layout.addRow("Config File (.ini):", config_layout_h)
        
        advanced_layout.addWidget(config_group)

        # VGTools / SMUtils tabs: generic operation selector + auto-generated form,
        # built from the VGTOOLS_OPERATIONS / SMUTILS_OPERATIONS specs above.
        vgtools_tab, self.vgtools_op_combo, self.vgtools_field_widgets, vgtools_run_btn = \
            self._build_operation_tab(VGTOOLS_OPERATIONS)
        vgtools_run_btn.clicked.connect(lambda: self._run_operation(
            "vgtools", VGTOOLS_OPERATIONS, self.vgtools_op_combo, self.vgtools_field_widgets, vgtools_run_btn
        ))

        smutils_tab, self.smutils_op_combo, self.smutils_field_widgets, smutils_run_btn = \
            self._build_operation_tab(SMUTILS_OPERATIONS)
        smutils_run_btn.clicked.connect(lambda: self._run_operation(
            "smutils", SMUTILS_OPERATIONS, self.smutils_op_combo, self.smutils_field_widgets, smutils_run_btn
        ))

        # Dependencies tab: checks the Python packages and external tools VolGrids needs
        dependencies_tab = QWidget()
        dependencies_layout = QVBoxLayout(dependencies_tab)

        deps_info_label = QLabel(
            "Checks the Python packages and external tools VolGrids needs.\n"
            "Click 'Fix' to install/upgrade a missing or outdated dependency."
        )
        deps_info_label.setStyleSheet("color: gray; font-style: italic;")
        dependencies_layout.addWidget(deps_info_label)

        deps_group = QGroupBox("Dependencies")
        deps_grid = QGridLayout(deps_group)
        deps_grid.addWidget(QLabel("<b>Status</b>"), 0, 0)
        deps_grid.addWidget(QLabel("<b>Package</b>"), 0, 1)
        deps_grid.addWidget(QLabel("<b>Detail</b>"), 0, 2)
        deps_grid.addWidget(QLabel("<b>Action</b>"), 0, 3)

        for row_idx, spec in enumerate(DEPENDENCY_SPECS, start=1):
            status_label = QLabel("?")
            status_label.setMinimumWidth(20)
            detail_label = QLabel("Checking...")
            fix_btn = QPushButton("Fix")
            fix_btn.clicked.connect(partial(self._fix_dependency, spec, status_label, detail_label, fix_btn))

            deps_grid.addWidget(status_label, row_idx, 0)
            deps_grid.addWidget(QLabel(spec["name"]), row_idx, 1)
            deps_grid.addWidget(detail_label, row_idx, 2)
            deps_grid.addWidget(fix_btn, row_idx, 3)
            self.dependency_rows[spec["name"]] = (status_label, detail_label, fix_btn)

        dependencies_layout.addWidget(deps_group)

        deps_refresh_btn = QPushButton("Check All")
        deps_refresh_btn.clicked.connect(self._refresh_all_dependencies)
        dependencies_layout.addWidget(deps_refresh_btn)
        dependencies_layout.addStretch()

        # Citation / Help tabs
        citation_tab = self._build_citation_tab()
        help_tab = self._build_help_tab()

        # Add tabs
        tabs.addTab(basic_tab, "Basic Settings")
        tabs.addTab(advanced_tab, "Advanced Settings")
        tabs.addTab(vgtools_tab, "VGTools")
        tabs.addTab(smutils_tab, "SMUtils")
        tabs.addTab(dependencies_tab, "Dependencies")
        tabs.addTab(citation_tab, "Citation")
        tabs.addTab(help_tab, "Help")
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run Smiffer")
        self.run_button.clicked.connect(self.run_smiffer)
        self.run_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_smiffer)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
        
        self.load_results_button = QPushButton("Load Results")
        self.load_results_button.clicked.connect(self.load_results)
        self.load_results_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
        
        control_layout.addWidget(self.run_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.load_results_button)
        control_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Log area
        log_group = QGroupBox("Progress Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("QTextEdit { background-color: #f5f5f5; color: #000000; font-family: monospace; }")
        log_layout.addWidget(self.log_text)
        
        # Add everything to main splitter
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(tabs)
        top_layout.addLayout(control_layout)
        top_layout.addWidget(self.progress_bar)
        
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(log_group)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)
        
        self.tool_window.ui_area.setLayout(QVBoxLayout())
        self.tool_window.ui_area.layout().addWidget(main_splitter)
        self.tool_window.manage(None)

        self._refresh_all_dependencies()

    def log_message(self, message):
        """Add a message to the log"""
        self.log_text.append(f"[{self._get_timestamp()}] {message}")
        self.log_text.ensureCursorVisible()
        
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def browse_input_file(self):
        """Browse for input structure file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.tool_window.ui_area, 
            "Select Structure File", 
            "", 
            "Structure Files (*.pdb *.cif *.mmcif);;All Files (*)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            # Auto-set output directory to input file directory
            if not self.output_dir_edit.text():
                self.output_dir_edit.setText(os.path.dirname(file_path))

    def load_current_structure(self):
        """Load actual 3d structure displayed"""
        try:
            from chimerax.atomic import AtomicStructure
            structures = self.session.models.list(type=AtomicStructure)
            print(structures)
            if not structures:
                QMessageBox.information(None, "Info", "No structures loaded to save")
                return
            for structure in structures:
                print(dir(structure))
            if hasattr(structure, 'filename') and structure.filename:
                print(structure.filename)
                print(os.path.splitext(os.path.basename(structure.filename))[0])
                self.input_file_edit.setText(structure.filename)
                self.output_dir_edit.setText(os.path.dirname(structure.filename))
                    

        except Exception as e:
            self.session.logger.error(f"Error {e}")



    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self.tool_window.ui_area, 
            "Select Output Directory"
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def browse_trajectory(self):
        """Browse for trajectory file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.tool_window.ui_area, 
            "Select Trajectory File", 
            "", 
            "Trajectory Files (*.xtc *.trr *.dcd);;All Files (*)"
        )
        if file_path:
            self.trajectory_edit.setText(file_path)
    
    def browse_apbs_file(self):
        """Browse for APBS file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.tool_window.ui_area, 
            "Select APBS File", 
            "", 
            "APBS Files (*.dx);;All Files (*)"
        )
        if file_path:
            self.apbs_file_edit.setText(file_path)
    
    def browse_chem_table(self):
        """Browse for chemical table file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.tool_window.ui_area, 
            "Select Chemical Table File", 
            "", 
            "Chemical Table Files (*.chem);;All Files (*)"
        )
        if file_path:
            self.chem_table_edit.setText(file_path)
    
    def browse_config_file(self):
        """Browse for configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.tool_window.ui_area, 
            "Select Configuration File", 
            "", 
            "Configuration Files (*.ini);;All Files (*)"
        )
        if file_path:
            self.config_file_edit.setText(file_path)
    
    def toggle_pocket_sphere(self, enabled):
        """Toggle pocket sphere controls"""
        self.sphere_radius_spin.setEnabled(enabled)
        self.sphere_x_spin.setEnabled(enabled)
        self.sphere_y_spin.setEnabled(enabled)
        self.sphere_z_spin.setEnabled(enabled)

    def _vendor_dir(self):
        """Folder containing the VolGrids copy bundled with this plugin (holds the 'volgrids' package)"""
        return os.path.join(os.path.dirname(__file__), "vendor")

    def _vendor_deps_dir(self):
        """Folder containing bundled third-party dependencies (numpy/scipy/matplotlib/
        MDAnalysis/h5py), only present when built via install_bundled.sh. Kept separate
        from _vendor_dir() so the regular build never silently picks these up."""
        return os.path.join(os.path.dirname(__file__), "vendor_deps")

    def _default_config_path(self):
        """VolGrids' own config_volgrids.ini, bundled with this plugin and listing every
        tunable setting; GRID_FORMAT_OUTPUT is set to CMAP here instead of upstream's MRC"""
        return os.path.join(os.path.dirname(__file__), "config_volgrids.ini")

    def _parse_config_settings(self):
        """Parse the bundled config_volgrids.ini into an ordered list of entries:
        ("section", title) for section-header comments, or ("setting", key, value,
        comment) for every KEY = value line, preserving the file's own order."""
        entries = []
        with open(self._default_config_path(), encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue

                if line.startswith(';'):
                    title = line.strip(';').strip()
                    if title and title.isupper() and all(ch.isalpha() or ch.isspace() for ch in title):
                        entries.append(("section", title))
                    continue

                if '=' not in line:
                    continue
                body, _, comment = line.partition(';')
                key, _, value = body.partition('=')
                key, value, comment = key.strip(), value.strip(), comment.strip()
                if key:
                    entries.append(("setting", key, value, comment))
        return entries

    def _resolve_volgrids_invocation(self):
        """Resolve the (command_prefix, env) used to invoke the VolGrids copy bundled
        with this plugin (a pinned, known-working version shipped under src/vendor).

        ChimeraX's own Python launcher always runs as if '-I' (isolated mode) were
        passed, which makes it ignore PYTHONPATH entirely for '-m' invocations - so
        'python -m volgrids' silently fails to find the bundled copy. ChimeraX's '-c'
        handling is the one path that re-enables custom sys.path entries, so the
        vendor directory is injected there directly instead of relying on PYTHONPATH.
        """
        vendor_dir = self._vendor_dir()
        vendor_dirs = [vendor_dir]
        vendor_deps_dir = self._vendor_deps_dir()
        if os.path.isdir(vendor_deps_dir):
            vendor_dirs.append(vendor_deps_dir)

        code = (
            "import sys; "
            + "".join(f"sys.path.insert(0, {d!r}); " for d in reversed(vendor_dirs))
            + "sys.argv[0] = 'volgrids'; "
            "from volgrids.__main__ import main; "
            "sys.exit(main())"
        )
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(vendor_dirs) + (os.pathsep + existing if existing else "")
        self._augment_path_for_apbs_tools(env)
        return [sys.executable, "-c", code], env

    def _binary_search_dirs(self):
        """Common conda-style locations to look for external tools (pdb2pqr, apbs,
        conda/mamba itself) in, beyond whatever's already on PATH."""
        return [
            os.path.expanduser("~/miniconda3/bin"),
            os.path.expanduser("~/miniconda3/condabin"),
            os.path.expanduser("~/anaconda3/bin"),
            os.path.expanduser("~/miniforge3/bin"),
            os.path.expanduser("~/mambaforge/bin"),
            "/opt/conda/bin",
            "/usr/local/bin",
            "/opt/homebrew/bin",
        ]

    def _augment_path_for_apbs_tools(self, env):
        """Make sure a modern 'pdb2pqr'/'apbs' are used for the APBS SMIF, by prepending
        known conda-style locations ahead of whatever is already on PATH.

        This is needed because some hosts ship their own, much older 'pdb2pqr' with an
        incompatible CLI (e.g. PyMOL's own bundled distribution includes pdb2pqr 2.1.2,
        whose '--apbs-input' flag takes no argument, unlike the modern 3.x CLI VolGrids
        expects) - that older copy would otherwise shadow a correct installation that's
        also present on the system but later in PATH.
        """
        path = env.get("PATH", "")
        path_dirs = path.split(os.pathsep) if path else []
        extra = [
            d for d in self._binary_search_dirs()
            if d not in path_dirs
            and (os.path.isfile(os.path.join(d, "pdb2pqr")) or os.path.isfile(os.path.join(d, "apbs")))
        ]
        if extra:
            env["PATH"] = os.pathsep.join(extra + path_dirs) if path_dirs else os.pathsep.join(extra)

    def _find_binary(self, name):
        """Find an external binary by name, checking PATH first then known conda-style
        locations (since these tools may not be on PATH for the host application)."""
        found = shutil.which(name)
        if found:
            return found
        for d in self._binary_search_dirs():
            candidate = os.path.join(d, name)
            if os.path.isfile(candidate):
                return candidate
        return None

    def _check_dependency(self, spec):
        """Check whether a dependency is installed and meets the minimum version.
        Returns (ok, detail_str)."""
        if spec["kind"] == "pip":
            try:
                from importlib import metadata as importlib_metadata
            except ImportError:
                import importlib_metadata
            try:
                version_str = importlib_metadata.version(spec["name"])
            except importlib_metadata.PackageNotFoundError:
                return False, "Not installed"
            if spec["min_version"] and not self._version_at_least(version_str, spec["min_version"]):
                return False, f"v{version_str} installed (requires >= {'.'.join(map(str, spec['min_version']))})"
            return True, f"v{version_str}"

        # kind == "binary"
        path = self._find_binary(spec["name"])
        if not path:
            return False, "Not found on PATH"
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
            output = (result.stdout + result.stderr).strip()
            match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
            version_str = match.group(1) if match else (output.splitlines()[0] if output else "unknown")
        except Exception:
            match, version_str = None, "unknown"
        if spec["min_version"] and match and not self._version_at_least(version_str, spec["min_version"]):
            return False, f"{path} (v{version_str}, requires >= {'.'.join(map(str, spec['min_version']))})"
        return True, f"{path} (v{version_str})"

    @staticmethod
    def _version_at_least(version_str, min_version):
        parts = []
        for tok in version_str.split('.')[:len(min_version)]:
            digits = ''.join(ch for ch in tok if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        while len(parts) < len(min_version):
            parts.append(0)
        return tuple(parts) >= min_version

    def _refresh_dependency_row(self, spec, status_label, detail_label, fix_btn):
        ok, detail = self._check_dependency(spec)
        if ok:
            status_label.setText("✓")
            status_label.setStyleSheet("color: green; font-weight: bold;")
            fix_btn.setVisible(False)
        else:
            status_label.setText("✗")
            status_label.setStyleSheet("color: red; font-weight: bold;")
            fix_btn.setVisible(True)
        detail_label.setText(detail)

    def _refresh_all_dependencies(self):
        for spec in DEPENDENCY_SPECS:
            status_label, detail_label, fix_btn = self.dependency_rows[spec["name"]]
            self._refresh_dependency_row(spec, status_label, detail_label, fix_btn)

    def _fix_dependency(self, spec, status_label, detail_label, fix_btn):
        if spec["kind"] == "pip":
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", spec["pip_spec"]]
        else:
            conda_exe = self._find_binary("mamba") or self._find_binary("conda")
            if not conda_exe:
                self.log_message(
                    f"Cannot auto-install '{spec['name']}': no conda/mamba executable found. "
                    f"Install it manually (e.g. via conda-forge: conda install -c conda-forge {spec['name']})."
                )
                return
            cmd = [conda_exe, "install", "-y", "-c", "conda-forge", spec["name"]]

        self.log_message(f"Running command: {' '.join(cmd)}")
        fix_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        worker = SmifferWorker(cmd, None)
        worker.output.connect(self.log_message)
        worker.error.connect(self.on_smiffer_error)
        worker.finished.connect(partial(self._on_dependency_fix_finished, spec, status_label, detail_label, fix_btn, worker))
        self.dependency_fix_workers.append(worker)
        worker.start()

    def _on_dependency_fix_finished(self, spec, status_label, detail_label, fix_btn, worker):
        fix_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if worker in self.dependency_fix_workers:
            self.dependency_fix_workers.remove(worker)
        self._refresh_dependency_row(spec, status_label, detail_label, fix_btn)

    def build_smiffer_command(self):
        """Build the 'volgrids smiffer' command from UI inputs"""
        if not self.input_file_edit.text():
            raise ValueError("Please select an input structure file")

        cmd, env = self._resolve_volgrids_invocation()
        cmd = cmd + ["smiffer", self.input_file_edit.text()]

        # Output directory
        if self.output_dir_edit.text():
            cmd.extend(["-o", self.output_dir_edit.text()])

        # Trajectory
        if self.trajectory_edit.text():
            cmd.extend(["-t", self.trajectory_edit.text()])

        # Cached APBS file
        if self.apbs_file_edit.text():
            cmd.extend(["-a", self.apbs_file_edit.text()])

        # Pocket sphere: order is x, y, z, radius
        if self.pocket_sphere_checkbox.isChecked():
            cmd.extend(["-s",
                       str(self.sphere_x_spin.value()),
                       str(self.sphere_y_spin.value()),
                       str(self.sphere_z_spin.value()),
                       str(self.sphere_radius_spin.value())])

        # Chemical table override (e.g. for ligand mode)
        if self.chem_table_edit.text():
            cmd.extend(["-e", self.chem_table_edit.text()])

        # Config file / overrides (defaults to CMAP output unless the user supplies their own),
        # plus any setting explicitly checked in the "Configuration Overrides" list
        config_args = [self.config_file_edit.text() or self._default_config_path()]
        config_args += [
            f"{key}={value_edit.text()}"
            for key, (checkbox, value_edit) in self.config_setting_rows.items()
            if checkbox.isChecked()
        ]
        cmd.extend(["-c"] + config_args)

        # Worker processes (trajectory mode only)
        if self.nproc_spin.value() > 1:
            cmd.extend(["-n", str(self.nproc_spin.value())])

        return cmd, env

    def build_apbs_command(self):
        """Build the 'volgrids apbs' command from UI inputs"""
        if not self.input_file_edit.text():
            raise ValueError("Please select an input structure file")

        cmd, env = self._resolve_volgrids_invocation()
        cmd = cmd + ["apbs", self.input_file_edit.text()]
        if self.apbs_mrc_checkbox.isChecked():
            cmd.append("--mrc")
        if self.apbs_keep_pqr_checkbox.isChecked():
            cmd.append("--pqr")
        if self.apbs_verbose_checkbox.isChecked():
            cmd.append("--verbose")
        return cmd, env

    def run_apbs_now(self):
        """Pre-compute an APBS grid with 'volgrids apbs' and reuse it for Smiffer"""
        try:
            if not self.input_file_edit.text():
                QMessageBox.warning(None, "Error", "Please select an input structure file")
                return
            if not os.path.exists(self.input_file_edit.text()):
                QMessageBox.warning(None, "Error", "Input structure file does not exist")
                return

            cmd, env = self.build_apbs_command()
            self.log_message(f"Running command: {' '.join(cmd)}")

            self.run_apbs_now_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            structure_file = self.input_file_edit.text()
            suffix = "mrc" if self.apbs_mrc_checkbox.isChecked() else "dx"
            expected_output = f"{structure_file}.{suffix}"

            self.apbs_worker_thread = SmifferWorker(cmd, os.path.dirname(structure_file) or None, env=env)
            self.apbs_worker_thread.output.connect(self.log_message)
            self.apbs_worker_thread.error.connect(self.on_smiffer_error)
            self.apbs_worker_thread.finished.connect(
                lambda: self._on_apbs_now_finished(expected_output)
            )
            self.apbs_worker_thread.start()

        except Exception as e:
            self.log_message(f"Error starting APBS: {str(e)}")
            QMessageBox.warning(None, "Error", f"Failed to start APBS: {str(e)}")

    def _on_apbs_now_finished(self, expected_output):
        self.run_apbs_now_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        if os.path.exists(expected_output):
            self.apbs_file_edit.setText(expected_output)
            self.log_message(f"APBS grid ready: {expected_output}")
        else:
            self.log_message("APBS finished, but the expected output file was not found.")

    def run_smiffer(self):
        """Run the smiffer calculation"""
        try:
            # Validate inputs
            if not self.input_file_edit.text():
                QMessageBox.warning(None, "Error", "Please select an input structure file")
                return
            
            if not os.path.exists(self.input_file_edit.text()):
                QMessageBox.warning(None, "Error", "Input structure file does not exist")
                return
            
            # Build command
            cmd, env = self.build_smiffer_command()

            output_dir = self.output_dir_edit.text() or os.path.dirname(self.input_file_edit.text())
            self.first_files_folder = os.listdir(output_dir) if output_dir and os.path.exists(output_dir) else []

            # Set working directory
            working_dir = output_dir or None

            self.log_message(f"Running command: {' '.join(cmd)}")
            self.log_message(f"Working directory: {working_dir}")

            # Create and start worker thread
            self.worker_thread = SmifferWorker(cmd, working_dir, env=env)
            self.worker_thread.finished.connect(self.on_smiffer_finished)
            self.worker_thread.error.connect(self.on_smiffer_error)
            self.worker_thread.output.connect(self.log_message)
            self.worker_thread.progress.connect(self.on_progress_update)
            
            # Update UI
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            self.worker_thread.start()
            
        except Exception as e:
            self.log_message(f"Error starting Smiffer: {str(e)}")
            QMessageBox.warning(None, "Error", f"Failed to start Smiffer: {str(e)}")

    def stop_smiffer(self):
        """Stop the running Smiffer process"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.log_message("Stopping Smiffer process...")
            self.worker_thread.stop()
            self.worker_thread.wait()

    def on_smiffer_finished(self):
        """Handle Smiffer completion"""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.log_message("Smiffer process finished")

    def on_smiffer_error(self, error_msg):
        """Handle errors reported by any VolGrids subprocess (smiffer/apbs/pip install)"""
        self.log_message(f"Error: {error_msg}")
        QMessageBox.warning(None, "VolGrids Error", error_msg)

    def on_progress_update(self, progress_msg):
        """Handle progress updates"""
        # Could update progress bar here if needed
        pass

    def load_results(self):
        """Load Smiffer results into ChimeraX"""
        try:
            output_dir = self.output_dir_edit.text()
            if not output_dir:
                output_dir = os.path.dirname(self.input_file_edit.text()) if self.input_file_edit.text() else ""
            
            if not output_dir or not os.path.exists(output_dir):
                QMessageBox.warning(None, "Error", "Output directory not found")
                return
            
            # Find result files
            result_files = []
            files_in_folder_before = self.first_files_folder
            for ext in ['.cmap', '.dx', '.ccp4', '.mrc']:
                files = [f for f in os.listdir(output_dir) if f.endswith(ext)]
                new_files = [x for x in files if x not in files_in_folder_before]
                result_files.extend([os.path.join(output_dir, f) for f in new_files])
            
            if not result_files:
                QMessageBox.information(None, "Info", "No result files found in output directory")
                return
            
            # Load files into ChimeraX
            from chimerax.core.commands import run
            loaded_count = 0
            
            for file_path in result_files:
                try:
                    self.log_message(f"Loading {file_path}")
                    run(self.session, f"open \"{file_path}\"")
                    loaded_count += 1
                except Exception as e:
                    self.log_message(f"Failed to load {file_path}: {str(e)}")
            
            self.log_message(f"Loaded {loaded_count} result files")
            
            # Auto-color the loaded volumes
            self.color_loaded_volumes()
            
            QMessageBox.information(None, "Success", f"Loaded {loaded_count} result files")
            
        except Exception as e:
            self.log_message(f"Error loading results: {str(e)}")
            QMessageBox.warning(None, "Error", f"Failed to load results: {str(e)}")

    def color_loaded_volumes(self):
        """Auto-color loaded volumes based on their names"""
        try:
            from chimerax.map import Volume
            from chimerax.core.commands import run
            
            # Color mapping, keyed by the SMIF kind abbreviations used in volgrids' output filenames
            color_map = {
                'hphob': "#FFFF00",     # Yellow - hydrophobic
                'hphil': "#4DD9FF",     # Light Blue - hydrophilic
                'hba':   "#FF8000",     # Orange - hbond acceptors
                'hbd':   "#B300FF",     # Purple - hbond donors
                'stk':   "#00FF00",     # Green - stacking
                'apbs':  "#0000FF",     # Blue - APBS electrostatics
                'cav':   "#FF00FF",     # Magenta - cavities
                'trim':  "#888888",     # Gray - trimming mask
            }
            
            volumes = self.session.models.list(type=Volume)
            colored_count = 0
            
            for volume in volumes:
                if hasattr(volume, 'data') and hasattr(volume.data, 'path'):
                    filename = os.path.basename(volume.data.path)
                    base_name = os.path.splitext(filename)[0]
                    
                    # Check for field type in filename
                    for field_type, color in color_map.items():
                        if field_type in base_name.lower():
                            run(self.session, f"color #{volume.id_string} {color}")
                            self.log_message(f"Colored {filename} as {field_type}: {color}")
                            colored_count += 1
                            break
            
            if colored_count > 0:
                self.log_message(f"Auto-colored {colored_count} volumes")
                
        except Exception as e:
            self.log_message(f"Error auto-coloring volumes: {str(e)}")

    # ---- generic vgtools/smutils operation UI -------------------------------------

    def _browse_for_field(self, line_edit, mode):
        """Open the appropriate file dialog for a dynamic operation field and append
        the chosen path(s) (space-separated for 'open_multi') into the line edit."""
        if mode == "open":
            path, _ = QFileDialog.getOpenFileName(self.tool_window.ui_area, "Select File")
            if path:
                line_edit.setText(path)
        elif mode == "open_multi":
            paths, _ = QFileDialog.getOpenFileNames(self.tool_window.ui_area, "Select Files")
            if paths:
                line_edit.setText(" ".join(paths))
        elif mode == "save":
            path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area, "Select Output File")
            if path:
                line_edit.setText(path)
        elif mode == "dir":
            path = QFileDialog.getExistingDirectory(self.tool_window.ui_area, "Select Folder")
            if path:
                line_edit.setText(path)

    def _build_field_widget(self, kind, default):
        """Build the widget for a single dynamic operation argument.
        Returns (row_widget_or_layout, value_widget)."""
        if kind == "bool":
            checkbox = QCheckBox()
            return checkbox, checkbox

        if kind == "choice":
            combo = QComboBox()
            combo.addItems(["DX", "BIN", "MRC", "CCP4", "CMAP"])
            if default:
                idx = combo.findText(default)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            return combo, combo

        line_edit = QLineEdit()
        if default is not None:
            line_edit.setText(str(default))

        browse_mode = {
            "file_in": "open",
            "file_out": "save",
            "dir_out": "dir",
            "dir_in": "dir",
            "files_in": "open_multi",
        }.get(kind)

        if browse_mode is None:
            return line_edit, line_edit

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(partial(self._browse_for_field, line_edit, browse_mode))
        row_layout = QHBoxLayout()
        row_layout.addWidget(line_edit)
        row_layout.addWidget(browse_btn)
        return row_layout, line_edit

    def _read_field_value(self, widget):
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        return widget.text().strip()

    def _build_citation_tab(self):
        """Tab pointing to the paper describing the SMIF method this tool implements."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel("If you use this tool, please cite:")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        citation_text = QLabel(
            "Barquero Morera D, Mattiotti G, Kocev A, Rousselot A, Meuret L, Rouaud L, "
            "Santuz H, Baaden M, Taly A, Pasquali S.<br>"
            "<i>Statistical Molecular Interaction Fields: A Fast and Informative Tool for "
            "Characterizing RNA and Protein-Binding Pockets.</i><br>"
            "J Chem Theory Comput. 2025;21(18):9120-9135.<br>"
            "DOI: <a href=\"https://doi.org/10.1021/acs.jctc.5c00688\">10.1021/acs.jctc.5c00688</a><br>"
            "PubMed: <a href=\"https://pubmed.ncbi.nlm.nih.gov/40890087/\">"
            "https://pubmed.ncbi.nlm.nih.gov/40890087/</a>"
        )
        citation_text.setTextFormat(Qt.RichText)
        citation_text.setOpenExternalLinks(True)
        citation_text.setWordWrap(True)
        layout.addWidget(citation_text)

        copy_btn = QPushButton("Copy Citation")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(
            "Barquero Morera D, Mattiotti G, Kocev A, Rousselot A, Meuret L, Rouaud L, "
            "Santuz H, Baaden M, Taly A, Pasquali S. Statistical Molecular Interaction "
            "Fields: A Fast and Informative Tool for Characterizing RNA and Protein-Binding "
            "Pockets. J Chem Theory Comput. 2025;21(18):9120-9135. "
            "doi:10.1021/acs.jctc.5c00688"
        ))
        layout.addWidget(copy_btn)
        layout.addStretch()
        return tab

    def _build_help_tab(self):
        """Tab pointing to the VolGrids documentation/source code on GitHub."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel("VolGrids documentation and source code:")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        link_label = QLabel(
            "<a href=\"https://github.com/DiegoBarMor/volgrids\">"
            "https://github.com/DiegoBarMor/volgrids</a>"
        )
        link_label.setTextFormat(Qt.RichText)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)
        layout.addStretch()
        return tab

    def _build_operation_tab(self, operations):
        """Build a tab with an operation selector and one auto-generated form page per
        operation (a QStackedWidget so widgets persist when switching operations)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Operation:"))
        op_combo = QComboBox()
        op_combo.addItems(list(operations.keys()))
        selector_layout.addWidget(op_combo)
        layout.addLayout(selector_layout)

        stacked = QStackedWidget()
        field_widgets = {}

        for op_key, op_spec in operations.items():
            page = QWidget()
            form = QFormLayout(page)
            widgets = {}
            for key, flag, kind, label, required, default in op_spec["args"]:
                row, value_widget = self._build_field_widget(kind, default)
                form.addRow((label + " *") if required else label, row)
                widgets[key] = value_widget
            field_widgets[op_key] = widgets
            stacked.addWidget(page)

        op_combo.currentIndexChanged.connect(stacked.setCurrentIndex)
        layout.addWidget(stacked)
        layout.addStretch()

        run_btn = QPushButton("Run")
        layout.addWidget(run_btn)

        return tab, op_combo, field_widgets, run_btn

    def _build_operation_command(self, subcommand_root, operations, op_combo, field_widgets):
        op_key = op_combo.currentText()
        op_spec = operations[op_key]
        cmd, env = self._resolve_volgrids_invocation()
        cmd = cmd + [subcommand_root] + op_spec["subcommand"]

        multi_kinds = {"files_in", "floats3", "floats4", "floats6"}

        for key, flag, kind, label, required, default in op_spec["args"]:
            value = self._read_field_value(field_widgets[op_key][key])

            if kind == "bool":
                if value:
                    cmd.append(flag)
                continue

            if not value:
                if required:
                    raise ValueError(f"'{label}' is required for {subcommand_root} {' '.join(op_spec['subcommand'])}")
                continue

            if kind in multi_kinds:
                parts = value.split()
                cmd.extend(([flag] if flag else []) + parts)
            else:
                cmd.extend([flag, value] if flag else [value])

        return cmd, env

    def _run_operation(self, subcommand_root, operations, op_combo, field_widgets, run_btn):
        """Run a vgtools/smutils operation. Only computes/logs the result - it is not
        auto-loaded, since these operations produce a wide variety of output formats
        (grids, CSVs, plain text, plots) that can't be handled generically."""
        try:
            cmd, env = self._build_operation_command(subcommand_root, operations, op_combo, field_widgets)
        except ValueError as e:
            QMessageBox.warning(None, "Error", str(e))
            return

        self.log_message(f"Running command: {' '.join(cmd)}")

        run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.operation_worker_thread = SmifferWorker(cmd, None, env=env)
        self.operation_worker_thread.output.connect(self.log_message)
        self.operation_worker_thread.error.connect(self.on_smiffer_error)
        self.operation_worker_thread.finished.connect(partial(self._on_operation_finished, run_btn))
        self.operation_worker_thread.start()

    def _on_operation_finished(self, run_btn):
        run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)


class SmifferWorker(QThread):
    """Worker thread for running Smiffer process"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    output = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, command, working_dir, env=None):
        super().__init__()
        self.command = command
        self.working_dir = working_dir
        self.env = env
        self.process = None
        self.should_stop = False

    def run(self):
        """Run the smiffer command"""
        try:
            self.process = subprocess.Popen(
                self.command,
                cwd=self.working_dir,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if self.should_stop:
                    break
                if line.strip():
                    self.output.emit(line.strip())
                    if any(keyword in line.lower() for keyword in ['processing', 'frame', 'calculating', 'trimming', 'saving']):
                        self.progress.emit(line.strip())
            
            self.process.wait()
            
            if self.process.returncode == 0 and not self.should_stop:
                self.output.emit("Smiffer calculation completed successfully!")
            elif self.should_stop:
                self.output.emit("Smiffer calculation stopped by user.")
            else:
                self.error.emit(f"Smiffer failed with return code: {self.process.returncode}")
                
        except Exception as e:
            self.error.emit(f"Error running Smiffer: {str(e)}")
        finally:
            self.finished.emit()
    
    def stop(self):
        """Stop the running process"""
        self.should_stop = True
        if self.process:
            self.process.terminate()
            self.process.wait()
