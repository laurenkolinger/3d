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
    """Get the path to the YAML file."""
    # First try to get from command line
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # Then look in current directory
    if os.path.exists("analysis_params.yaml"):
        return "analysis_params.yaml"
    
    # Then look in parent directory
    if os.path.exists("../analysis_params.yaml"):
        return "../analysis_params.yaml"
    
    # Then look in repository root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_yaml = os.path.join(repo_root, "analysis_params.yaml")
    if os.path.exists(repo_yaml):
        return repo_yaml
    
    raise FileNotFoundError("Could not find analysis_params.yaml. Please specify the path.")

# Load YAML configuration
YAML_PATH = get_yaml_path()
PARAMS = load_yaml(YAML_PATH)

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

# Frame extraction rate
EXTRACTION_RATE = PARAMS['processing']['extraction_rate']

# Project metadata
PROJECT_NAME = PARAMS['project']['name']
PROJECT_NOTES = PARAMS['project']['notes']

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
    """Create all required directories."""
    for dir_path in DIRECTORIES.values():
        if isinstance(dir_path, str) and not dir_path.startswith(('http://', 'https://')):  # Skip URLs and non-strings
            os.makedirs(dir_path, exist_ok=True)

def get_tracking_files():
    """Get list of all tracking files for this project."""
    tracking_files = []
    transects_dir = DIRECTORIES["frames"]
    if os.path.exists(transects_dir):
        for transect_dir in os.listdir(transects_dir):
            if os.path.isdir(os.path.join(transects_dir, transect_dir)):
                tracking_file = os.path.join(DIRECTORIES["data_root"], f"{transect_dir}_tracking.csv")
                if os.path.exists(tracking_file):
                    tracking_files.append(tracking_file)
    return tracking_files

def get_tracking_file(model_id):
    """Get tracking file path for a specific model."""
    return os.path.join(DIRECTORIES["data_root"], f"{model_id}_tracking.csv")

def initialize_tracking(model_id):
    """Initialize tracking CSV file for a model."""
    tracking_file = get_tracking_file(model_id)
    
    if not os.path.exists(tracking_file):
        with open(tracking_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Model ID", "Status", "Step 0 complete", "Step 1 complete", 
                           "Step 1 start time", "Step 1 end time", "Step 1 processing time (s)", 
                           "Aligned cameras", "Total cameras", "PSX file", "Report file",
                           "Step 1 error time", "Notes"])
            writer.writerow([model_id, "Initialized", "False", "False", "", "", "", 
                           "", "", "", "", "", "Tracking initialized"])
    
    return tracking_file

def update_tracking(model_id, data):
    """Update tracking file with new data."""
    tracking_file = get_tracking_file(model_id)
    
    if not os.path.exists(tracking_file):
        tracking_file = initialize_tracking(model_id)
    
    # Read existing data
    rows = []
    with open(tracking_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    
    if len(rows) < 2:
        # Initialize with header and empty row if file is empty
        rows = [
            ["Model ID", "Status", "Step 0 complete", "Step 1 complete", 
             "Step 1 start time", "Step 1 end time", "Step 1 processing time (s)", 
             "Aligned cameras", "Total cameras", "PSX file", "Report file",
             "Step 1 error time", "Notes"],
            [model_id, "Initialized", "False", "False", "", "", "", 
             "", "", "", "", "", ""]
        ]
    
    # Update data in the second row (assuming header + one data row)
    header = rows[0]
    row = rows[1] if len(rows) > 1 else [""] * len(header)
    
    # Update values
    for key, value in data.items():
        try:
            index = header.index(key)
            row[index] = value
        except ValueError:
            # If key not in header, add it
            header.append(key)
            row.append(value)
    
    # Ensure model ID is set
    try:
        id_index = header.index("Model ID")
        row[id_index] = model_id
    except ValueError:
        header.insert(0, "Model ID")
        row.insert(0, model_id)
    
    # Write updated data
    rows = [header, row]
    with open(tracking_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    
    return tracking_file

def get_transect_status(model_id):
    """Get the current status for a model."""
    tracking_file = get_tracking_file(model_id)
    
    if not os.path.exists(tracking_file):
        return {}
    
    with open(tracking_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    
    if len(rows) < 2:
        return {}
    
    header = rows[0]
    row = rows[1]
    
    status = {}
    for i in range(len(header)):
        if i < len(row):
            status[header[i]] = row[i]
    
    return status

# Create all directories on import
create_directories() 