"""
TCRMP 3D Processing Configuration

This file loads configuration parameters from a YAML file and provides
access to them throughout the processing workflow.
"""

import os
import yaml
import datetime
import sys
import csv
import glob
from pathlib import Path


def load_yaml(yaml_path):
    """Load and validate YAML file."""
    try:
        with open(yaml_path, 'r') as f:
            params = yaml.safe_load(f)
    except Exception as e:
        # If yaml module is not available, provide a helpful error message
        if 'yaml' in str(e) and 'No module named' in str(e):
            print("Error: The PyYAML module is not installed.")
            print("Please install it using: pip install pyyaml")
            print("Or for Metashape's Python environment:")
            print("/Applications/MetashapePro.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/pip3 install pyyaml")
            print("Alternatively, modify src/config.py to work without yaml dependency.")
            raise ImportError("PyYAML module required")
        else:
            raise e
    
    # Validate required sections
    required_sections = ['project', 'directories', 'processing']
    for section in required_sections:
        if section not in params:
            raise ValueError(f"Missing required section '{section}' in YAML file")
    
    # Validate required processing parameters for all steps
    required_processing = [
        'frames_per_transect', 'extraction_rate',         # Step 0
        'chunk_size', 'use_gpu', 'metashape',             # Step 1
        'chunk_management',                               # Step 2
        'model_processing',                               # Step 3
        'final_exports'                                   # Step 4
    ]
    
    for param in required_processing:
        if param not in params['processing']:
            print(f"Warning: Missing recommended parameter '{param}' under 'processing' in YAML file")
    
    return params

def get_yaml_path():
    """Get the path to the YAML file by asking user for project directory."""
    # First try to get from command line
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # Prompt user for project directory
    print("Please enter the absolute path to your project directory containing analysis_params.yaml")
    print("Example: /Users/yourname/examples/sample_project/ or '/Users/yourname/examples/sample_project'")
    project_dir = input("Project directory: ").strip()
    
    # Remove potential surrounding single or double quotes
    project_dir = project_dir.strip('\'"')
    
    # Remove any trailing slashes
    project_dir = project_dir.rstrip('/')
    
    # Construct path to yaml file
    yaml_path = os.path.join(project_dir, "analysis_params.yaml")
    
    # Verify file exists
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Could not find analysis_params.yaml in {project_dir}")
    
    return yaml_path

# Get the directory name from a path (last component)
def get_dir_name(path):
    """Extract the directory name (last component) from a path."""
    # Handle trailing slashes
    path = path.rstrip('/')
    # Get the last component of the path
    return os.path.basename(path)

# Load YAML configuration
YAML_PATH = get_yaml_path()
PARAMS = load_yaml(YAML_PATH)

# Get project directory (parent dir of the YAML file)
PROJECT_DIR = os.path.dirname(YAML_PATH)

# Directory containing your MP4/MOV video files
VIDEO_SOURCE_DIRECTORY = PARAMS['directories']['video_source']

# Base directory for all inputs and outputs
BASE_DIRECTORY = PARAMS['directories'].get('base', '.')

# Input data directory (where frames will be stored)
DATA_DIRECTORY = PARAMS['directories'].get('data', 'data')

# Output directory (where logs will be stored)
OUTPUT_DIRECTORY = PARAMS['directories'].get('output', 'output')

# Number of frames to extract per transect
FRAMES_PER_TRANSECT = PARAMS['processing']['frames_per_transect']

# Project metadata - derive name from directory if not specified
PROJECT_NAME = PARAMS['project'].get('name')
if not PROJECT_NAME:
    # Derive from project directory name
    PROJECT_NAME = get_dir_name(PROJECT_DIR)

PROJECT_NOTES = PARAMS['project'].get('notes', '')

# Get a unique project identifier that's filesystem-safe
def get_project_id():
    """Get a filesystem-safe identifier for this project."""
    # Use the directory name as the project ID
    return get_dir_name(PROJECT_DIR)

PROJECT_ID = get_project_id()

# Metashape processing parameters
METASHAPE_DEFAULTS = PARAMS['processing']['metashape']['defaults']
CHUNK_SIZE = PARAMS['processing']['chunk_size']
USE_GPU = PARAMS['processing']['use_gpu']
MAX_CHUNKS_PER_PSX = PARAMS['processing'].get('max_chunks_per_psx', 5)

# Generate unique timestamp for this processing run
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Directory structure
DIRECTORIES = {
    "base": BASE_DIRECTORY,
    "data_root": DATA_DIRECTORY,
    "output_root": OUTPUT_DIRECTORY,
    "frames": os.path.join(DATA_DIRECTORY, "frames"),
    "reports": os.path.join(OUTPUT_DIRECTORY, "reports"),
    "psx_input": os.path.join(DATA_DIRECTORY, "psx_input"),
    "orthomosaics": os.path.join(OUTPUT_DIRECTORY, "orthomosaics"),
    "models": os.path.join(OUTPUT_DIRECTORY, "models"),
    "psx_output": PARAMS['directories'].get('psx_output', os.path.join(OUTPUT_DIRECTORY, "05_outputs/psx")),
    "adobe_presets": PARAMS['directories'].get('adobe_presets', ''),
    "metashape_presets": PARAMS['directories'].get('metashape_presets', ''),
    "scripts": PARAMS['directories'].get('scripts', ''),
    "final_outputs": PARAMS['directories'].get('final_outputs', os.path.join(OUTPUT_DIRECTORY, "final"))
}

# Configure logging
LOG_FILE = os.path.join(DIRECTORIES["reports"], f"processing_{PROJECT_NAME}.log")

def create_directories():
    """Create only required directories that should exist within data/ and output/ folders."""
    # Only create directories that the user expects to be created
    # (Skip creating any files directly in the project root)
    for dir_name, dir_path in DIRECTORIES.items():
        # Skip if not a string or is a URL
        if not isinstance(dir_path, str) or dir_path.startswith(('http://', 'https://')):
            continue
            
        # Skip empty paths
        if not dir_path:
            continue
            
        # Only create directories within data and output folders
        # or if they are the data and output folders themselves
        # Exclude specific directories like psx_output and final_outputs early on
        if dir_name in ["psx_output", "final_outputs"]:
            continue
            
        if (dir_name in ["data_root", "output_root"] or
            dir_path.startswith(DIRECTORIES["data_root"]) or
            dir_path.startswith(DIRECTORIES["output_root"])):
            os.makedirs(dir_path, exist_ok=True)
            
def ensure_parent_directory(filepath):
    """Ensure the parent directory of a file exists."""
    parent_dir = os.path.dirname(filepath)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
        
def get_tracking_file(model_id=None):
    """Get tracking file path for the project."""
    # Use project ID in the filename to create a unique tracking file per project
    return os.path.join(DIRECTORIES["base"], f"status_{PROJECT_ID}.csv")

def get_tracking_files():
    """Get list of all tracking files for this project."""
    # This is kept for backward compatibility but will now return a single file
    tracking_file = get_tracking_file()
    return [tracking_file] if os.path.exists(tracking_file) else []

def initialize_tracking(model_id):
    """Initialize tracking CSV file if not exists, and add a row for the model."""
    tracking_file = get_tracking_file()
    
    # If file doesn't exist, create it with comprehensive headers covering all processing steps
    if not os.path.exists(tracking_file):
        # Make sure the parent directory exists before writing the file
        ensure_parent_directory(tracking_file)
        
        with open(tracking_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "Model ID", "Status", 
                # Step 0 columns
                "Step 0 complete", "Video Length (s)", "Total Video Frames", "Frames Extracted", 
                "Video Source", "Extraction Timestamp", "Step 0 start time", "Step 0 end time",
                "Step 0 processing time (s)", "Frames directory",
                # Step 1 columns
                "Step 1 complete", "Step 1 start time", "Step 1 end time", 
                "Step 1 processing time (s)", "Aligned cameras", "Total cameras", 
                "PSX file", "Report file", "Step 1 error time",
                # Step 2 columns
                "Step 2 complete", "Step 2 site", "Step 2 consolidation time",
                # Step 3 columns
                "Step 3 complete", "Step 3 scale applied", "Step 3 ortho exported",
                "Step 3 model exported", "Step 3 processing time",
                # Step 4 columns
                "Step 4 complete", "Step 4 web published", "Sketchfab URL",
                "Step 4 high-res exported", "Step 4 processing time",
                # General
                "Notes"
            ])
    
    # Check if model_id already exists in the file
    model_exists = False
    rows = []
    
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            
            if len(rows) > 0:
                header = rows[0]
                # Find the index of the Model ID column
                try:
                    id_index = header.index("Model ID")
                    # Check if model_id exists in any row
                    for row in rows[1:]:
                        if row and id_index < len(row) and row[id_index] == model_id:
                            model_exists = True
                            break
                except ValueError:
                    # If Model ID column doesn't exist, something is wrong with the file
                    # We'll recreate the header with comprehensive columns
                    rows = [[
                        "Model ID", "Status", 
                        # Step 0 columns
                        "Step 0 complete", "Video Length (s)", "Total Video Frames", "Frames Extracted", 
                        "Video Source", "Extraction Timestamp", "Step 0 start time", "Step 0 end time",
                        "Step 0 processing time (s)", "Frames directory",
                        # Step 1 columns
                        "Step 1 complete", "Step 1 start time", "Step 1 end time", 
                        "Step 1 processing time (s)", "Aligned cameras", "Total cameras", 
                        "PSX file", "Report file", "Step 1 error time",
                        # Step 2 columns
                        "Step 2 complete", "Step 2 site", "Step 2 consolidation time",
                        # Step 3 columns
                        "Step 3 complete", "Step 3 scale applied", "Step 3 ortho exported",
                        "Step 3 model exported", "Step 3 processing time",
                        # Step 4 columns
                        "Step 4 complete", "Step 4 web published", "Sketchfab URL",
                        "Step 4 high-res exported", "Step 4 processing time",
                        # General
                        "Notes"
                    ]]
    
    # If model doesn't exist, add it
    if not model_exists:
        if len(rows) == 0:
            # File is empty, add comprehensive header
            rows = [[
                "Model ID", "Status", 
                # Step 0 columns
                "Step 0 complete", "Video Length (s)", "Total Video Frames", "Frames Extracted", 
                "Video Source", "Extraction Timestamp", "Step 0 start time", "Step 0 end time",
                "Step 0 processing time (s)", "Frames directory",
                # Step 1 columns
                "Step 1 complete", "Step 1 start time", "Step 1 end time", 
                "Step 1 processing time (s)", "Aligned cameras", "Total cameras", 
                "PSX file", "Report file", "Step 1 error time",
                # Step 2 columns
                "Step 2 complete", "Step 2 site", "Step 2 consolidation time",
                # Step 3 columns
                "Step 3 complete", "Step 3 scale applied", "Step 3 ortho exported",
                "Step 3 model exported", "Step 3 processing time",
                # Step 4 columns
                "Step 4 complete", "Step 4 web published", "Sketchfab URL",
                "Step 4 high-res exported", "Step 4 processing time",
                # General
                "Notes"
            ]]
        
        # Add new row for this model with empty values
        new_row = [""] * len(rows[0])
        
        # Set initial values
        try:
            id_index = rows[0].index("Model ID")
            new_row[id_index] = model_id
            
            status_index = rows[0].index("Status")
            new_row[status_index] = "Initialized"
            
            notes_index = rows[0].index("Notes")
            new_row[notes_index] = "Tracking initialized"
        except ValueError:
            # Fallback if columns not found
            new_row[0] = model_id
            new_row[1] = "Initialized"
            new_row[-1] = "Tracking initialized"
        
        rows.append(new_row)
        
        # Write the updated data
        with open(tracking_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
    
    return tracking_file

def update_tracking(model_id, data):
    """Update tracking file with new data for the specified model."""
    tracking_file = get_tracking_file()
    
    # Initialize tracking if file doesn't exist
    if not os.path.exists(tracking_file):
        initialize_tracking(model_id)
    
    # Read existing data
    rows = []
    with open(tracking_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    
    if len(rows) == 0:
        # Initialize with header if file is empty
        rows = [["Model ID", "Status", "Step 0 complete", "Step 1 complete", 
               "Step 1 start time", "Step 1 end time", "Step 1 processing time (s)", 
               "Aligned cameras", "Total cameras", "PSX file", "Report file",
               "Step 1 error time", "Notes"]]
    
    header = rows[0]
    model_row_index = -1
    
    # Find the row for this model_id
    try:
        id_index = header.index("Model ID")
        for i, row in enumerate(rows[1:], 1):
            if row and id_index < len(row) and row[id_index] == model_id:
                model_row_index = i
                break
    except ValueError:
        # If Model ID column doesn't exist, something is wrong with the file
        # Recreate the header
        header = ["Model ID", "Status", "Step 0 complete", "Step 1 complete", 
               "Step 1 start time", "Step 1 end time", "Step 1 processing time (s)", 
               "Aligned cameras", "Total cameras", "PSX file", "Report file",
               "Step 1 error time", "Notes"]
        rows[0] = header
    
    # If model doesn't exist in the file, add a new row
    if model_row_index == -1:
        new_row = [""] * len(header)
        try:
            id_index = header.index("Model ID")
            new_row[id_index] = model_id
        except ValueError:
            # If Model ID column doesn't exist, add it
            header.insert(0, "Model ID")
            new_row = [""] * len(header)
            new_row[0] = model_id
            rows[0] = header
        
        rows.append(new_row)
        model_row_index = len(rows) - 1
    
    # Update values in the model's row
    for key, value in data.items():
        try:
            index = header.index(key)
            if model_row_index < len(rows):
                while len(rows[model_row_index]) <= index:
                    rows[model_row_index].append("")
                rows[model_row_index][index] = value
        except ValueError:
            # If key not in header, add it
            header.append(key)
            rows[0] = header
            for i in range(1, len(rows)):
                rows[i].append("")
            if model_row_index < len(rows):
                rows[model_row_index][len(header) - 1] = value
    
    # Ensure model ID is set
    try:
        id_index = header.index("Model ID")
        if model_row_index < len(rows):
            rows[model_row_index][id_index] = model_id
    except ValueError:
        # If Model ID column doesn't exist, add it
        header.insert(0, "Model ID")
        rows[0] = header
        for i in range(1, len(rows)):
            rows[i].insert(0, "")
        if model_row_index < len(rows):
            rows[model_row_index][0] = model_id
    
    # Ensure parent directory exists
    ensure_parent_directory(tracking_file)
    
    # Write updated data
    with open(tracking_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    
    return tracking_file

def get_transect_status(model_id):
    """Get the current status for a model from the tracking file."""
    tracking_file = get_tracking_file()
    
    if not os.path.exists(tracking_file):
        return {}
    
    with open(tracking_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    
    if len(rows) < 2:
        return {}
    
    header = rows[0]
    
    # Find the row for this model_id
    try:
        id_index = header.index("Model ID")
        for row in rows[1:]:
            if row and id_index < len(row) and row[id_index] == model_id:
                # Create dictionary of column names to values
                status = {}
                for i in range(len(header)):
                    if i < len(row):
                        status[header[i]] = row[i]
                return status
    except ValueError:
        pass
    
    # If we get here, the model wasn't found
    return {}

# Create all directories on import
create_directories() 