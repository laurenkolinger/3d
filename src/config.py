"""
TCRMP 3D Processing Configuration

This file contains all configuration parameters for the 3D processing workflow.
"""

import os
import pandas as pd
import datetime
import glob

#############################################
#          USER CONFIGURATION AREA          #
#############################################

# ===== REQUIRED: SET THESE PATHS =====

# Directory containing your MP4/MOV video files
VIDEO_SOURCE_DIRECTORY = ""  # Use absolute path to video files

# Base directory for all inputs and outputs (leave empty to use same directory as scripts)
BASE_DIRECTORY = ""  # Use absolute path or leave empty

# Input data directory (where frames, processed frames, etc. will be stored)
DATA_DIRECTORY = ""  # Use absolute path or leave empty to use BASE_DIRECTORY/data

# Output directory (where models, PSX files, etc. will be stored)
OUTPUT_DIRECTORY = ""  # Use absolute path or leave empty to use BASE_DIRECTORY/output

# ===== OPTIONAL: PROCESSING PARAMETERS =====

# Number of frames to extract per transect
FRAMES_PER_TRANSECT = 1200

# Metashape processing quality (1=highest, 8=lowest quality but faster)
METASHAPE_QUALITY = 2  

# Number of vertices for decimated models for web upload
DECIMATED_VERTICES = 3000000

# Sketchfab API token for model uploads
SKETCHFAB_API_TOKEN = "your_sketchfab_api_token_here"  # Replace with your token

# ===== OPTIONAL: PROJECT METADATA =====

# Project name (used in tracking file name)
PROJECT_NAME = "TCRMP_3D"  # Will be used in tracking file name

# Project notes (will be included in tracking file)
PROJECT_NOTES = """
Project started: {timestamp}
Video source: {video_dir}
Processing quality: {quality}
"""

#############################################
#       END OF USER CONFIGURATION AREA      #
#############################################

# Project root directory - the parent directory of this script
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

# Directory structure - defaults that can be overridden
# These can be absolute paths or relative to BASE_DIR
DEFAULT_PATHS = {
    "video_source": VIDEO_SOURCE_DIRECTORY,
    "data_root": DATA_DIRECTORY,
    "extracted_frames": os.path.join(DATA_DIRECTORY, "frames"),
    "edited_images": os.path.join(DATA_DIRECTORY, "processed_frames"),
    "psx_input": os.path.join(DATA_DIRECTORY, "psx_input"),
    "output_root": OUTPUT_DIRECTORY,
    "psx_output": os.path.join(OUTPUT_DIRECTORY, "psx"),
    "reports": os.path.join(OUTPUT_DIRECTORY, "reports"),
    "models": os.path.join(OUTPUT_DIRECTORY, "models"),
    "orthomosaics": os.path.join(OUTPUT_DIRECTORY, "orthomosaics"),
    "initial_reports": os.path.join(OUTPUT_DIRECTORY, "reports_initial"),
}

# Current paths - will be set by set_paths()
PATHS = {}

# Processing parameters
PROCESSING_PARAMS = {
    "extract_frames": {
        "frames_per_transect": FRAMES_PER_TRANSECT,
    },
    "step1": {
        "reconstruction_uncertainty": 50,
        "reprojection_error": 1,
        "projection_accuracy": 10,
        "downscale_factor": METASHAPE_QUALITY,
    },
    "step4": {
        "vertices_count": DECIMATED_VERTICES,
        "sketchfab_api_token": SKETCHFAB_API_TOKEN,
    }
}

def set_paths(custom_paths=None):
    """
    Set up paths using defaults and any custom paths provided.
    
    Args:
        custom_paths (dict): Dictionary of custom paths to override defaults
    """
    global PATHS
    
    # Start with default paths
    PATHS = DEFAULT_PATHS.copy()
    
    # Override with any custom paths
    if custom_paths:
        for key, value in custom_paths.items():
            if key in PATHS:
                PATHS[key] = value
    
    # Convert any relative paths to absolute
    for key, path in PATHS.items():
        if path and not os.path.isabs(path):
            PATHS[key] = os.path.join(BASE_DIRECTORY, path)
    
    # Ensure all output directories exist
    create_output_directories()
    
    return PATHS

def create_output_directories():
    """Create all output directories if they don't exist."""
    # Create data directories
    os.makedirs(PATHS["data_root"], exist_ok=True)
    
    data_dirs = ["extracted_frames", "edited_images", "psx_input"]
    for dir_name in data_dirs:
        if dir_name in PATHS and PATHS[dir_name]:
            os.makedirs(PATHS[dir_name], exist_ok=True)
    
    # Create output directories
    os.makedirs(PATHS["output_root"], exist_ok=True)
    
    output_dirs = ["psx_output", "reports", "models", "orthomosaics", "initial_reports"]
    for dir_name in output_dirs:
        if dir_name in PATHS and PATHS[dir_name]:
            os.makedirs(PATHS[dir_name], exist_ok=True)

def get_tracking_filename():
    """Generate a unique tracking filename based on project name and timestamp."""
    return f"{PROJECT_NAME}_{TIMESTAMP}_processing_status.txt"

def initialize_tracking():
    """
    Initialize a new tracking file with project metadata and empty transect list.
    Returns the path to the tracking file.
    """
    # Create the directory for the tracking file if it doesn't exist
    os.makedirs(PATHS["data_root"], exist_ok=True)
    
    # Generate unique filename
    tracking_file = get_tracking_filename()
    tracking_path = os.path.join(PATHS["data_root"], tracking_file)
    
    # Create initial tracking file with project metadata
    with open(tracking_path, 'w') as f:
        f.write(f"TCRMP 3D Processing Status Report\n")
        f.write(f"================================\n\n")
        f.write(f"Project: {PROJECT_NAME}\n")
        f.write(f"Started: {TIMESTAMP}\n")
        f.write(f"Video Source: {PATHS['video_source']}\n")
        f.write(f"Data Directory: {PATHS['data_root']}\n")
        f.write(f"Output Directory: {PATHS['output_root']}\n")
        f.write(f"Processing Quality: {METASHAPE_QUALITY}\n\n")
        f.write("Project Notes:\n")
        f.write(PROJECT_NOTES.format(
            timestamp=TIMESTAMP,
            video_dir=PATHS['video_source'],
            quality=METASHAPE_QUALITY
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
    tracking_path = os.path.join(PATHS["data_root"], get_tracking_filename())
    
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
    tracking_path = os.path.join(PATHS["data_root"], get_tracking_filename())
    
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

# Initialize paths with defaults
set_paths()

# Initialize tracking file
TRACKING_FILE = initialize_tracking() 