# analysegnss Task Runner
# A control center for GNSS data processing and EBH operations.
# Usage: just <command> [arguments]

# Default: List all available tasks and descriptions
default:
    @just --list

# --- System & Setup ---

# Initial setup: Syncs python environment and ensures system geoids are installed
setup:
    uv sync
    @echo "Installing/Updating GeographicLib geoids..."
    sudo geographiclib-get-geoids best

# The 'Nuclear' Clean: Removes virtual environment and all Python bytecode cache
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -rf .venv
    @echo "Environment and cache cleared. Run 'just setup' to rebuild."

# --- EBH (Experimental Buoy) Operations ---

# Launch the main EBH processing pipeline (usually requires a config file)
ebh-process *args:
    uv run launch_ebh_process {{ if args == "" { "--help" } else { args } }}

# Analyze EBH trajectory lines and deviations
ebh-lines *args:
    uv run ebh_lines {{ if args == "" { "--help" } else { args } }}

# Generate timing and synchronization statistics for EBH missions
ebh-timings *args:
    uv run get_ebh_timings {{ if args == "" { "--help" } else { args } }}

# Calculate spatial gradients for EBH mission data
ebh-gradients *args:
    uv run gradient_ebhlines {{ if args == "" { "--help" } else { args } }}

# --- RINEX Tools ---

# Download or fetch RINEX files from remote/local sources
get-rnx *args:
    uv run get_rnx_files {{ if args == "" { "--help" } else { args } }}

# Run Post-Processed Kinematic (PPK) analysis using rnx2rtkp
ppk-process *args:
    uv run ppk_rnx2rtkp {{ if args == "" { "--help" } else { args } }}

# Generic RINEX to CSV conversion utility
rnx-csv *args:
    uv run rnx_csv {{ if args == "" { "--help" } else { args } }}

# Convert RINEX Navigation files to CSV format
rnx-nav-csv *args:
    uv run rnxnav_csv {{ if args == "" { "--help" } else { args } }}

# Convert RINEX Observation files to CSV format
rnx-obs-csv *args:
    uv run rnxobs_csv {{ if args == "" { "--help" } else { args } }}

# --- SBF (Septentrio Binary Format) Tools ---

# Extract precise base station coordinates from SBF files
sbf-base *args:
    uv run get_base_coord_from_sbf {{ if args == "" { "--help" } else { args } }}

# Convert SBF measurement blocks to CSV
sbf-meas-csv *args:
    uv run sbfmeas_csv {{ if args == "" { "--help" } else { args } }}

# Convert SBF navigation blocks to CSV
sbf-nav-csv *args:
    uv run sbfnav_csv {{ if args == "" { "--help" } else { args } }}

# Process SBF PVT (Position, Velocity, Time) Geodetic blocks
sbf-pvt *args:
    uv run rtk_pvtgeod {{ if args == "" { "--help" } else { args } }}

# --- Device Parsers & NMEA ---

# Parse u-blox UBX binary logs into human-readable formats
ubx-parser *args:
    uv run ubx_parser {{ if args == "" { "--help" } else { args } }}

# Parse gLAB output files for error analysis
glab-parser *args:
    uv run glab_parser {{ if args == "" { "--help" } else { args } }}

# Read and process standard NMEA 0183 messages
nmea-reader *args:
    uv run nmea_reader {{ if args == "" { "--help" } else { args } }}

# --- Analysis & Utilities ---

# Generate coordinate plots (Time series or Map views)
plot-coords *args:
    uv run plot_coords {{ if args == "" { "--help" } else { args } }}

# Calculate the error between a processed position and a known reference
pos-error *args:
    uv run compute_position_error {{ if args == "" { "--help" } else { args } }}

# Prepare SBF/RINEX data for submission to NGS OPUS
opus-reformat *args:
    uv run reformat_sbf_rnx_for_opus {{ if args == "" { "--help" } else { args } }}

# Automated launcher for RTKLIB rnx2rtkp processing
rtk-launch *args:
    uv run launch_rnx2rtkp {{ if args == "" { "--help" } else { args } }}
