# Example 3D Processing Project

This is an example project structure demonstrating how to set up and organize a 3D coral reef processing project using the TCRMP framework.

## Included Files

This example includes:
- Two real video files for processing:
  - `video_source/TCRMP20241014_3D_BWR_T1.mov` 
  - `video_source/TCRMP20241014_3D_BWR_T2.mov`
- A complete directory structure for organizing data
- A sample YAML configuration file (`analysis_params.yaml`)

## Project Structure

```
sample_project/
├── src/                     # Contains the configuration file
│   └── config.py            # Loads parameters from analysis_params.yaml
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

## Configuration

The project uses a YAML-based configuration system for easy parameter management:

1. Edit `analysis_params.yaml` to set your parameters:
   ```yaml
   # Project Information
   project:
     name: "TCRMP_3D_Example"
     notes: |
       This is an example project demonstrating the TCRMP 3D processing workflow.
       The project includes two sample video files for processing:
       - TCRMP20241014_3D_BWR_T1.mov
       - TCRMP20241014_3D_BWR_T2.mov

   # Directory Configuration
   directories:
     video_source: "../video_source"  # Directory containing MP4/MOV files
     base: ""  # Leave empty to use current directory
     data: ""  # Leave empty to use base/data
     output: ""  # Leave empty to use base/output
     adobe_presets: "../../presets/lightroom"
     metashape_presets: "../../presets/premiere"
     scripts: "../../src"  # Location of processing scripts
     config: "src/config.py"  # Location of config file

   # Processing Parameters
   processing:
     frames_per_transect: 1200
     extraction_rate: 0.5  # 1.0 = all frames, 0.5 = every other frame
     chunk_size: 400
     use_adobe_presets: true
     use_gpu: true
     decimated_vertices: 3000000
     sketchfab_token: "your_sketchfab_api_token_here"

   # Metashape Settings
   metashape:
     quality: 2  # 1=highest, 8=lowest quality but faster
     defaults:
       accuracy: "high"
       quality: "high"
       depth_filtering: "moderate"
       max_neighbors: 100
   ```

2. The `config.py` file automatically loads parameters from `analysis_params.yaml` when imported by the processing scripts.

3. The status file will be automatically generated and updated as processing proceeds.

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

Processing Parameters:
--------------------
Frames per transect: 1200
Extraction rate: 0.5
Chunk size: 400
GPU acceleration: True
Adobe presets: True

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
2. Edit `analysis_params.yaml` to set your own parameters
3. Follow the instructions in the main repository README to run the processing scripts

Note: This is only an example structure - no actual videos or outputs are included. 