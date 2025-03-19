"""
Example Configuration File for TCRMP 3D Processing

This configuration file demonstrates how to set up paths and parameters
for processing coral reef 3D models.
"""

import os
import datetime
import sys

# Add the main src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# =============================================================================
# USER CONFIGURATION AREA
# =============================================================================

# Directory containing your MP4/MOV video files
VIDEO_SOURCE_DIRECTORY = "../video_source"  # Relative path to video files

# Base directory for all inputs and outputs
BASE_DIRECTORY = ""  # Leave empty to use current directory

# Input data directory (where frames, processed frames, etc. will be stored)
DATA_DIRECTORY = ""  # Leave empty to use BASE_DIRECTORY/data

# Output directory (where models, PSX files, etc. will be stored)
OUTPUT_DIRECTORY = ""  # Leave empty to use BASE_DIRECTORY/output

# Directory containing Adobe presets (.xmp files)
ADOBE_PRESETS_DIRECTORY = "../../presets/lightroom"

# Directory containing Metashape presets (.epr files)
METASHAPE_PRESETS_DIRECTORY = "../../presets/premiere"

# =============================================================================
# PROCESSING PARAMETERS
# =============================================================================

# Number of frames to extract per transect
FRAMES_PER_TRANSECT = 1200

# Frame extraction rate - higher means taking more frames
# 1.0 = extract all frames, 0.5 = extract every other frame, etc.
EXTRACTION_RATE = 0.5

# Chunk size for breaking up Metashape processing
CHUNK_SIZE = 400

# If True, attempt to apply Adobe presets during processing
USE_ADOBE_PRESETS = True

# If True, use GPU acceleration in Metashape
USE_GPU = True

# Number of vertices for decimated models for web upload
DECIMATED_VERTICES = 3000000

# Sketchfab API token for model uploads
SKETCHFAB_API_TOKEN = "your_sketchfab_api_token_here"  # Replace with your token

# =============================================================================
# PROJECT METADATA
# =============================================================================

# Project name (used in tracking file name)
PROJECT_NAME = "TCRMP_3D_Example"

# Project notes (will be included in tracking file)
PROJECT_NOTES = """
This is an example project demonstrating the TCRMP 3D processing workflow.
The project includes two sample video files for processing:
- TCRMP20241014_3D_BWR_T1.mov
- TCRMP20241014_3D_BWR_T2.mov

Processing parameters:
- Frames per transect: {frames_per_transect}
- Extraction rate: {extraction_rate}
- Chunk size: {chunk_size}
- GPU acceleration: {use_gpu}
"""

# =============================================================================
# INTERNAL CONFIGURATION - DO NOT MODIFY UNLESS YOU'RE SURE
# =============================================================================

# Project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Handle directories based on user configuration
if not BASE_DIRECTORY:
    BASE_DIRECTORY = ROOT_DIR

if not DATA_DIRECTORY:
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")

if not OUTPUT_DIRECTORY:
    OUTPUT_DIRECTORY = os.path.join(BASE_DIRECTORY, "output")

# Generate unique timestamp for this processing run
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Directory structure
DIRECTORIES = {
    # Root directories
    "data_root": DATA_DIRECTORY,
    "output_root": OUTPUT_DIRECTORY,
    
    # Input directories
    "frames": os.path.join(DATA_DIRECTORY, "frames"),
    "edited_frames": os.path.join(DATA_DIRECTORY, "processed_frames"),
    "psx_input": os.path.join(DATA_DIRECTORY, "psx_input"),
    
    # Output directories
    "psx_output": os.path.join(OUTPUT_DIRECTORY, "psx"),
    "orthomosaics": os.path.join(OUTPUT_DIRECTORY, "orthomosaics"),
    "models": os.path.join(OUTPUT_DIRECTORY, "models"),
    "reports": os.path.join(OUTPUT_DIRECTORY, "reports"),
    "reports_initial": os.path.join(OUTPUT_DIRECTORY, "reports_initial")
}

# Add timestamp to generated files
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Ensure all directories exist
def create_directories():
    """Create all necessary directories for processing."""
    # Create data directories
    os.makedirs(DIRECTORIES["data_root"], exist_ok=True)
    
    data_dirs = ["frames", "edited_frames", "psx_input"]
    for dir_name in data_dirs:
        if dir_name in DIRECTORIES:
            os.makedirs(DIRECTORIES[dir_name], exist_ok=True)
    
    # Create output directories
    os.makedirs(DIRECTORIES["output_root"], exist_ok=True)
    
    output_dirs = ["psx_output", "orthomosaics", "models", "reports", "reports_initial"]
    for dir_name in output_dirs:
        if dir_name in DIRECTORIES:
            os.makedirs(DIRECTORIES[dir_name], exist_ok=True)

def get_tracking_filename():
    """Generate a unique tracking filename based on project name and timestamp."""
    return f"{PROJECT_NAME}_{TIMESTAMP}_processing_status.txt"

def initialize_tracking():
    """
    Initialize a new tracking file with project metadata and empty transect list.
    Returns the path to the tracking file.
    """
    # Create the directory for the tracking file if it doesn't exist
    os.makedirs(DIRECTORIES["data_root"], exist_ok=True)
    
    # Generate unique filename
    tracking_file = get_tracking_filename()
    tracking_path = os.path.join(DIRECTORIES["data_root"], tracking_file)
    
    # Create initial tracking file with project metadata
    with open(tracking_path, 'w') as f:
        f.write(f"TCRMP 3D Processing Status Report\n")
        f.write(f"================================\n\n")
        f.write(f"Project: {PROJECT_NAME}\n")
        f.write(f"Started: {TIMESTAMP}\n")
        f.write(f"Video Source: {VIDEO_SOURCE_DIRECTORY}\n")
        f.write(f"Data Directory: {DATA_DIRECTORY}\n")
        f.write(f"Output Directory: {OUTPUT_DIRECTORY}\n")
        f.write(f"Processing Quality: {METASHAPE_QUALITY}\n\n")
        f.write("Project Notes:\n")
        f.write(PROJECT_NOTES.format(
            frames_per_transect=FRAMES_PER_TRANSECT,
            extraction_rate=EXTRACTION_RATE,
            chunk_size=CHUNK_SIZE,
            use_gpu=USE_GPU
        ))
        f.write("\nTransect Processing Status:\n")
        f.write("-------------------------\n\n")
    
    return tracking_path

def update_tracking(transect_id, updates):
    """
    Update the tracking file for a specific transect.
    
    Args:
        transect_id (str): The transect identifier
        updates (dict): Dictionary of updates to make
    """
    tracking_path = os.path.join(DIRECTORIES["data_root"], get_tracking_filename())
    
    # Read current content
    with open(tracking_path, 'r') as f:
        lines = f.readlines()
    
    # Find or create transect section
    transect_section = f"\nTransect: {transect_id}\n"
    transect_found = False
    
    for i, line in enumerate(lines):
        if line.startswith(f"Transect: {transect_id}"):
            transect_found = True
            # Update existing transect section
            for key, value in updates.items():
                update_line = f"{key}: {value}\n"
                # Look for existing line to update
                for j in range(i+1, len(lines)):
                    if lines[j].startswith(f"{key}:"):
                        lines[j] = update_line
                        break
                else:
                    # Add new line if not found
                    lines.insert(i+1, update_line)
            break
    
    if not transect_found:
        # Add new transect section
        lines.append(transect_section)
        for key, value in updates.items():
            lines.append(f"{key}: {value}\n")
        lines.append("\n")
    
    # Write updated content
    with open(tracking_path, 'w') as f:
        f.writelines(lines)

def get_transect_status(transect_id):
    """
    Get the current status of a transect from the tracking file.
    
    Args:
        transect_id (str): The transect identifier
    
    Returns:
        dict: Dictionary of current status values
    """
    tracking_path = os.path.join(DIRECTORIES["data_root"], get_tracking_filename())
    
    if not os.path.exists(tracking_path):
        return {}
    
    status = {}
    current_transect = None
    
    with open(tracking_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"Transect: {transect_id}"):
                current_transect = transect_id
            elif current_transect == transect_id and line and not line.startswith("Transect:"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    status[key.strip()] = value.strip()
    
    return status

# Configure logging
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(DIRECTORIES["reports"], f"processing_log_{TIMESTAMP}.txt")

# Default Metashape processing settings
METASHAPE_DEFAULTS = {
    "accuracy": "high",
    "quality": "high",
    "depth_filtering": "moderate",
    "max_neighbors": 100
}

# Create all directories on import
create_directories()

# Initialize tracking file
TRACKING_FILE = initialize_tracking() 