# Example 3D Processing Project

This is an example project structure demonstrating how to set up and organize a 3D coral reef processing project using the TCRMP framework.

## Included Files

This example includes:
- Two real video files for processing:
  - `video_source/TCRMP20241014_3D_BWR_T1.mov` 
  - `video_source/TCRMP20241014_3D_BWR_T2.mov`
- A complete directory structure for organizing data
- A sample configuration file pointing to the included videos

## Project Structure

```
sample_project/
├── src/                     # Contains the configuration file
│   └── config.py            # Example configuration with sample paths
│
├── data/                    # All input data
│   ├── frames/              # Where extracted frames would be stored
│   ├── processed_frames/    # Where edited frames would be stored
│   ├── psx_input/           # Where Metashape input projects would be stored
│   └── TCRMP_3D_Example_*_processing_status.txt  # Auto-generated status files
│
└── output/                  # All processing outputs
    ├── models/              # 3D model files (.obj, etc.)
    ├── orthomosaics/        # Orthomosaic images (.tif)
    ├── psx/                 # Final Metashape projects
    ├── reports/             # Processing reports
    └── reports_initial/     # Initial reports
```

## Example Configuration

The `src/config.py` file demonstrates how to set up the configuration for your project. It includes:

- Video source directory
- Base directory for all data and outputs
- Custom data directory (optional)
- Custom output directory (optional)
- Processing parameters
- Project metadata

Key settings in the configuration file:

```python
# Directory containing your MP4/MOV video files
VIDEO_SOURCE_DIRECTORY = "../video_source"  # Relative path to video files

# Base directory for all inputs and outputs
BASE_DIRECTORY = "/path/to/project"  # Replace with actual path or leave empty

# Optional: Custom data and output directories
DATA_DIRECTORY = ""  # Leave empty to use BASE_DIRECTORY/data
OUTPUT_DIRECTORY = ""  # Leave empty to use BASE_DIRECTORY/output

# Project metadata
PROJECT_NAME = "TCRMP_3D_Example"  # Used in status file name
PROJECT_NOTES = """..."""  # Project description and parameters

# Processing parameters
FRAMES_PER_TRANSECT = 1200
EXTRACTION_RATE = 0.5
CHUNK_SIZE = 400
```

## Status Tracking

The system automatically generates and maintains a status file for each processing run. The status file:

- Is named uniquely using the project name and timestamp
- Contains project metadata and configuration
- Tracks the progress of each transect
- Is updated automatically as processing proceeds
- Is stored in the data directory

Example status file format:
```
TCRMP 3D Processing Status Report
================================

Project: TCRMP_3D_Example
Started: 20240321_143022
Video Source: ../video_source
Data Directory: /path/to/project/data
Output Directory: /path/to/project/output
Processing Quality: 2

Project Notes:
This is an example project demonstrating the TCRMP 3D processing workflow.
...

Transect Processing Status:
-------------------------

Transect: TCRMP20241014_3D_BWR_T1
Status: Ready for processing
Frames extracted: 0
Step 1 complete: False
Step 2 complete: False
Step 3 complete: False
Step 4 complete: False
Notes: Initial setup complete
```

## Using This Example

To use this example as a template for your own project:

1. Copy the entire directory structure
2. Edit the `src/config.py` file to set your own paths and parameters
3. Follow the instructions in the main repository README to run the processing scripts

Note: This is only an example structure - no actual videos or outputs are included. 