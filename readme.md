# 3D Processing Pipeline

A comprehensive workflow for processing 3D models from video footage.

## Overview

This project provides a set of Python scripts to automate the workflow of processing underwater video footage into 3D models of coral reefs. The pipeline uses Agisoft Metashape for 3D reconstruction and is designed to work with the Territorial Coral Reef Monitoring Program (TCRMP) methodology.

## Requirements

- Agisoft Metashape Pro (v2.1.1 or later)
- Python 3.9 (for both local environment and Metashape compatibility)
- Required Python packages (specific versions in `requirements.txt`):
  - PyYAML
  - pandas
  - numpy
  - opencv-python
  - matplotlib
  - pillow
- **Note:** This pipeline has been developed and tested primarily on macOS. Compatibility and performance on Windows or Linux are not guaranteed.

## Project Structure

```
./
├── analysis_params.yaml       # Base analysis parameters (copy to project dir)
├── docs/                      # Documentation files
├── examples/                  # Example project directories
├── images/                    # Supporting images (e.g., for README)
├── presets/                   # Preset files for software (Lightroom, Premiere)
├── src/                       # Source code
│   ├── config.py             # Configuration loading utilities
│   ├── enumerate_gpus.py     # Utility to list available GPUs for Metashape
│   ├── reset.sh              # Utility script to reset project outputs
│   ├── step0.py              # Frame Extraction
│   ├── step1.py              # Initial 3D Processing (and step1_isolated.py)
│   ├── step2.py              # Chunk Management
│   ├── step3.py              # Model Processing and Exports
│   └── step4.py              # Final Exports and Web Publishing
├── .gitignore                 # Specifies intentionally untracked files that Git should ignore
├── README.md                  # This file
└── requirements.txt           # Python package requirements
```

## Initial Setup

### 1. Repository Setup

Clone this repository to your local machine:
```bash
git clone https://github.com/laurenkolinger/3d.git
cd 3d
```

### 2. Create Project Directory Structure

Create all necessary directories for your project:
```bash
# From the workspace root, create the required directories
mkdir -p {PROJECT_DIR}/{video_source,processing,output}
```

This will create the following directory structure:
```
{PROJECT_DIR}/
├── video_source/                    # Input video files
├── processing/                      # Intermediate processing data
│   ├── frames/                      # Extracted frames organized by model (Step 0)
│   └── psxraw/                      # Initial PSX files (Step 1)
└── output/                          # All final outputs
    ├── psx/                         # Consolidated PSX files by site (Step 2)
    ├── orthomosaics/                # Orthomosaic outputs (Step 3)
    │   └── {MODEL_ID}/              # Each model in its own subdirectory
    │       └── {MODEL_ID}.tif       # Clean model ID filename
    ├── models/                      # 3D model outputs (Step 3)
    │   └── {MODEL_ID}/              # Each model in its own subdirectory
    │       ├── {MODEL_ID}.obj       # Clean model ID filename
    │       └── [texture files]      # Associated texture files
    ├── reports/                     # Processing reports (Step 3)
    │   ├── {MODEL_ID}.pdf           # Clean model ID filename (flat structure)
    │   └── {MODEL_ID}.pdf           # All reports in same directory
    ├── logs/                        # Processing logs
    └── final/                       # Final high-resolution outputs (Step 4)
```

**Important:** Once this directory structure is created, do not rename or move the standard subdirectories (`video_source`, `processing`, `output`). The scripts rely on this specific structure. The only manual change expected within `{PROJECT_DIR}` after setup is adding your video files to the `{PROJECT_DIR}/video_source/` directory.

Copy and configure the analysis parameters file:
```bash
# Copy the base configuration file to your project
cp analysis_params.yaml {PROJECT_DIR}/
```

The configuration file (`analysis_params.yaml`) located within your `{PROJECT_DIR}` contains all the settings for your project.

Make sure to:

1. Review and update the project name and notes inside the `{PROJECT_DIR}/analysis_params.yaml` file.
2. Adjust any processing parameters within the `{PROJECT_DIR}/analysis_params.yaml` file as needed for your specific project.
3. Note that the primary input/output directory paths (`video_source`, `processing`, `output`, etc.) are typically derived automatically by the scripts based on the `{PROJECT_DIR}` you provide when running them. You usually do not need to define these explicitly in the YAML file unless you intend to override the default structure.

## Standardized File Naming

The pipeline uses a clean, standardized naming system for all outputs:

- **Model ID Format:** All file names use the exact Model ID (e.g., `TCRMP20241014_3D_BWR_T2`)
- **No Suffixes:** Files are named simply as `{MODEL_ID}.ext` (no `_textured_model` or `_manualScale` suffixes)
- **Organized Structure:** 
  - Orthomosaics and models get their own subdirectories: `output/orthomosaics/{MODEL_ID}/` and `output/models/{MODEL_ID}/`
  - Reports are flat in `output/reports/{MODEL_ID}.pdf`
- **Consistent Across Scripts:** Both `step3.py` and `step3_manualScale.py` produce identical file names and structure

**Example Output:**
```
output/
├── orthomosaics/
│   └── TCRMP20241014_3D_BWR_T2/
│       └── TCRMP20241014_3D_BWR_T2.tif
├── models/
│   └── TCRMP20241014_3D_BWR_T2/
│       ├── TCRMP20241014_3D_BWR_T2.obj
│       └── TCRMP20241014_3D_BWR_T2.jpg  # texture file
└── reports/
    └── TCRMP20241014_3D_BWR_T2.pdf
```

### 3. Installing Dependencies

The pipeline requires dependencies in two Python environments:

1. Your local environment (for frame extraction - step0.py)
2. Metashape's Python environment (for 3D processing - step1.py and beyond)

#### Local Environment Setup

Create a Python virtual environment in your project:
```bash
# Create virtual environment in project directory using Python 3.9
python3.9 -m venv {PROJECT_DIR}/.venv

# Activate the virtual environment
source {PROJECT_DIR}/.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Running Metashape Scripts

To run Metashape scripts with the correct Python environment, you'll need to set the PYTHONPATH to point to your virtual environment's site-packages. This ensures Metashape uses the packages from your virtual environment while maintaining compatibility with Metashape's Python 3.9.

The general format for running Metashape scripts is:
```bash
PYTHONPATH={PROJECT_DIR}/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/stepX.py {PROJECT_DIR}
```

Where `stepX.py` is the specific step you want to run (step1.py, step2.py, etc.) and `{PROJECT_DIR}` is the path to your project directory containing `analysis_params.yaml`.

## Workflow Overview

The complete processing workflow consists of the following steps:

1. **Frame Extraction** (step0.py): Extract frames from video footage
2. **Initial 3D Processing** (step1.py): Process extracted frames to create initial 3D models
3. **Manual Quality Check & Alignment**: Check and align models (manual step)
4. **Chunk Management** (step2.py): Organize chunks by site
5. **Manual Straightening & Scaling**: Straighten and scale models (manual step)
6. **Model Processing and Exports** (step3.py): Add scale bars, remove small components, export assets
7. **Manual Touchups**: Review and touch up models (manual step)
8. **Final Exports & Web Publishing** (step4.py): Create final exports and upload to Sketchfab

**Note:** Each script will prompt for the project directory containing the `analysis_params.yaml` file if not provided as a command-line argument. This allows processing different projects without code modifications, as source files will be linked to individual project directories dynamically for each run.

## Detailed Workflow

### Step 0: Frame Extraction

This step extracts frames from video footage at a specified rate.

```bash
python src/step0.py            
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file
2. Scan the `video_source` directory for video files
3. Create a subdirectory for each video in the `frames` directory
4. Extract frames according to the settings in `analysis_params.yaml`
5. Create a tracking CSV file for each model
6. Generate a summary of extracted frames

### Step 1: Initial 3D Processing

This step performs the initial 3D reconstruction using the extracted frames. It creates batched PSX files with multiple models grouped together for efficiency.

Note this is the most time consuming step

```bash
PYTHONPATH={PROJECT_DIR}/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step1.py
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file
2. Find all model directories in the `frames` directory
3. Group models into batches (maximum 5 models per batch by default)
4. For each model:
   - Add photos and align cameras
   - Filter points and optimize cameras
   - Build depth maps and create 3D model
   - Apply textures and generate report
5. Save each batch as a separate PSX file in the `psxraw` directory
6. Create a batch summary CSV file mapping models to PSX files

### Manual Step: Quality Check & Alignment

After Step 1, manually check the quality of the generated models and make any necessary adjustments:

1. Open each PSX file in the `{PROJECT_DIR}/processing/psxraw` directory with Metashape
2. For each model (chunk) in the project:
   - Review camera alignment and model quality
   - Ensure point cloud is clean and representative of the model
   - Check for any alignment issues or artifacts
   - Identify any areas that might need adjustments in Step 2
   - Verify that model IDs are correctly labeled
3. Save the project

### Step 2: Chunk Management

This step consolidates chunks by site to prepare for final processing.

```bash
PYTHONPATH={PROJECT_DIR}/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step2.py
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file 
2. Read the tracking files to identify completed models
3. Group models by site
4. Create new PSX files organized by site in the `psx_output` directory
5. Update tracking information for each model

### Manual Step: Straightening & Scaling

After Step 2, manually straighten and scale each model:

1. Open each project in the `output/psx/` directory
2. For each chunk in the project:

   **Straightening:**
   - Load the textured model
   - Auto-adjust brightness and contrast in one of the images to improve texture
   - Switch to rotate model view
   - Rotate the model so it aligns horizontally at the top of the view
   - Use "Model > Region > Rotate Region to View" to set the alignment
   - Resize the region to "crop" to the model area (use top XY and side views)
   - Use the rectangular crop tool to crop to the model area bounded by the region

   **Scaling (if using manual scaling):**
   - Place markers on scale bars in the model
   - Set up at least 2 scale bars at different locations in the model
   - Set the known distance for each scale bar in the Reference pane
   - Press the Refresh button to update the scale
   - Verify that the error is less than 0.01
   
3. Save the project, and QUIT metashape before running Step 3

> **Note:** Make sure you are only working from ONE PSX file in the psxraw directory. The system should create just one processing status file and update that one file.

### Step 3: Model Processing and Exports

This step adds scale bars (if coded targets are present), removes small components, builds and exports orthomosaics, textured models, and reports using standardized file naming.

**On macOS**:
```bash
# Run with project directory as argument
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3.py {PROJECT_DIR}
# OR run without arguments to be prompted for the project directory
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3.py
```

**For manual scale workflow:**
```bash
# Use this version if you manually added scale bars in Metashape
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3_manualScale.py {PROJECT_DIR}
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file
2. Process each project in the `output/psx/` directory
3. For each model (chunk) in the project:
   - Add scale bars if coded targets are present (step3.py only)
   - Remove small disconnected components from the model
   - Build and export orthomosaic to `output/orthomosaics/{MODEL_ID}/{MODEL_ID}.tif`
   - Export textured model to `output/models/{MODEL_ID}/{MODEL_ID}.obj`
   - Generate report as `output/reports/{MODEL_ID}.pdf`
4. All outputs use clean Model ID naming (e.g., `TCRMP20241014_3D_BWR_T2`)

**Output Structure:** Both `step3.py` and `step3_manualScale.py` produce identical file names and directory structure - the only difference is the scaling method used internally.

### Manual Step: Model Review and Touchups

After Step 3, manually review and touch up the models:

1. Open each project in Metashape
2. For each chunk:
   - Review the orthomosaic for quality, artifacts, or holes
   - Check the textured model for issues with geometry or texture
   - Fill any small holes in the model if necessary
   - Adjust texture blending if needed
   - Check that small disconnected components were properly removed
   - Verify that scale bars are correctly set up (if applicable)
   - Review model colors and brightness, make adjustments if needed
3. Save the project

### Step 4: Final Exports and Web Publishing

This step creates final high-resolution outputs and uploads decimated models to Sketchfab for web viewing.

**On macOS**:
```bash
# Run with project directory as argument
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step4.py {PROJECT_DIR}
# OR run without arguments to be prompted for the project directory
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step4.py
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file
2. For each model (chunk) in the project:
   - Create a decimated copy for web viewing
   - Upload to Sketchfab (if API token is provided)
   - Export high-resolution orthomosaic
   - Export high-resolution textured model
   - Export point cloud
   - Generate comprehensive report
3. Save all exports to the `final_outputs` directory

## Configuration

The processing pipeline is configured through YAML files:

- Base configuration: `config/analysis_params.yaml`
- Project-specific configuration: `{PROJECT_DIR}/analysis_params.yaml`

### Project Directory Approach

Each script in the pipeline requires a project directory containing an `analysis_params.yaml` file. This design allows:

1. Processing different projects without modifying code
2. Running multiple projects in parallel
3. Maintaining a clear separation between different datasets
4. Dynamically linking source files to project-specific directories for each run

You can specify the project directory:
- As a command-line argument when running scripts
- Or interactively when prompted by the script if no directory is provided

The system will load all configurations from the `analysis_params.yaml` file in that directory, ensuring all paths and settings are specific to the current project.

### Key Configuration Parameters

- **max_chunks_per_psx**: Maximum number of chunks/models per PSX file (default: 5)
- **reconstruction_uncertainty**: Maximum allowable reconstruction uncertainty (default: 50)
- **reprojection_error**: Maximum reprojection error in pixels (default: 1)
- **projection_accuracy**: Maximum projection accuracy value (default: 10)
- **depth_downscale**: Downscale factor for depth maps (default: 4)
- **texture_size**: Texture size in pixels (default: 16384)

See the configuration files for complete parameter descriptions.

## Utility Scripts

These scripts provide helpful utilities for managing the processing environment.

### `src/utility/reset_full.py`

**Complete Project Reset** - Resets project to **BEFORE Step 0** (frame extraction).

**What it does:**
- 🗑️ Empties `processing/` and `output/` directories completely
- 📁 **Keeps** empty folder structure (`processing/`, `output/` directories remain)
- 🗑️ Removes all tracking CSV files
- 🔒 **Preserves:** `video_source/`, `analysis_params.yaml`, `.venv/`

**Usage:**
```bash
python src/utility/reset_full.py /path/to/project
```

**When to use:** Starting completely over from the beginning (frame extraction).

### `src/utility/reset_step1.py`

**Reset After Step 1** - Preserves Steps 0 & 1, clears Steps 2+ outputs.

**What it PRESERVES (the time-consuming work):**
- 🔒 Step 0: Extracted frames (`processing/frames/`)
- 🔒 Step 1: PSX files (`processing/psxraw/`)  
- 🔒 Step 0 & Step 1 tracking status

**What it CLEARS:**
- 🗑️ Step 2+: All `output/` directory contents (consolidated PSX, orthomosaics, models, reports)
- 🗑️ Step 2+ tracking status (resets to "Step 1 complete")

**Usage:**
```bash
python src/utility/reset_step1.py /path/to/project
```

**When to use:** Re-running Step 2 (chunk management) and subsequent steps while preserving hours of Step 0 & Step 1 processing time.

### `src/utility/enumerate_gpus.py`

This Python script lists the available GPUs that Metashape can detect and use. This is useful for verifying GPU configuration and ensuring Metashape is utilizing the expected hardware acceleration.

**Usage:**
```bash
# Run using Metashape's Python environment
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/utility/enumerate_gpus.py
```

## Troubleshooting

### Common Issues

1. **Package Import Errors in Metashape**
   
   If you encounter import errors for packages like numpy, pandas, or PyYAML when running scripts through Metashape, you'll need to install these packages in Metashape's Python environment. Use the provided installation scripts:
   
   ```bash
   # On macOS/Linux
   ./src/legacy/install_metashape_deps.sh
   ```

2. **PSX files not generated**
   
   Ensure that the `psxraw` directory exists and is writable. Check the log file in the `reports` directory for error messages.

3. **"Module 'numpy' has no attribute 'bool'"**
   
   This error typically occurs with incompatible numpy versions. Use our installation scripts to install the compatible version in Metashape's Python environment.

4. **Metashape Python version mismatch**
   
   If your Metashape version uses a different Python version than 3.9, you may need to modify the installation scripts to point to the correct Python interpreter.

## Field Methods

### Required Materials

- Camera system:
  - Camera with lights
  - Memory card (CF Express)
  - Camera housing
  - External battery pack
  - Strobe light batteries
  - Camera lens
  - Cinema camera gear
  - Handle with clips and rope

- Field equipment:
  - Scale bars (2)
  - Field box containing:
    - Extra towels
    - O-ring grease
    - Cleaning materials
    - Dry towels
  - Slate
  - Vacuum device for housing seal check

### Camera Setup and Maintenance

#### Regular Maintenance
- Camera cinema gear maintenance
- Camera settings verification
- Programmable button configuration
- Housing maintenance (every few weeks or if leaks detected):
  - O-ring greasing

#### Pre-Dive Preparation
1. Day before:
   - Check housing and o-rings
   - Charge camera
   - Charge external battery pack
   - Charge strobe light batteries
   - Initialize media on memory card

2. Morning of:
   - Camera sealing procedure:
     1. Install battery and memory card
     2. Attach lens and verify autofocus is on
     3. Remove lens cap and check for smudges
     4. Prepare housing for camera insertion
     5. Seat camera in housing using cinema camera gear
     6. Connect external battery
     7. Final housing checks:
        - Turn on alarm
        - Check for smudges on housing lens
        - Verify o-ring condition
        - Close housing
        - Use vacuum device until light turns green

   - Equipment verification:
     - Camera and memory card
     - Housing
     - Field box with supplies
     - Slate
     - Scale bars (2)
     - Handle with clips and rope

   - Camera settings verification:
     - CP file: C2 (Canon log 3 / C.Gamut Color matrix neutral)
     - Sensor mode: full frame
     - Frequency: 59.94hz
     - Recording: RAW LT
     - Destination: CFexpress
     - Frame rate: 59.94 fps

### In-Water Procedures

#### Start of Dive
1. **B**uttons: Press all buttons to prime them
2. **P**ower: 
   - Turn on camera and lights (hold in/out buttons 1s, press middle button)
   - Put lights to sleep (hold center 2s)
3. **L**eaks: Monitor green light - if turns red, return to boat

#### Transect and Camera Setup
1. **S**cale bars: 
   - Place at each end of transect
   - One perpendicular, one parallel to transect
   - Ensure targets visible in footage
   - Verify scale bars remain stationary during filming

2. **T**ime code: Reset (Mode button)

3. **A**rms: Extend to position lights as far apart as possible

4. **L**ights: Turn on (hold Center Button 2 sec)

5. **W**hite balance: Press Button 13, hold camera over white part of scale bar

6. **E**xposure: 
   - Open WFM (Button 6) and false color (Button 9)
   - Use F-stop dial to slightly overexpose (just below 100% on WFM)

7. **A**ltitude: 
   - Position camera so viewfinder covers length of scale bar
   - Note height (should be ~70cm)
   - Maintain this altitude throughout filming

8. **R**ecord: 
   - Press Record button
   - Show transect number
   - Verify autofocus

#### Filming Protocol (4-Pass Method)
Each pass should be approximately 10 meters long and take about 1 minute, maintaining consistent altitude.

1. **Pass 1**: 
   - Start at one end
   - Camera facing straight down
   - Transect line visible in left quarter of viewfinder

2. **Pass 2**: 
   - Turn around
   - Camera facing straight down
   - Position slightly away from transect line
   - Viewfinder should see 1m distance from transect
   - Maintain ~0.5m overlap with Pass 1
   - Position approximately arm's length from transect

3. **Pass 3 & 4**: 
   - Move ~20cm from pass 1/2 position
   - Tilt camera 45°
   - Capture angled view of transect from either side

#### Post-Filming
- Press center button on each light for 2s to put lights to sleep

## Running a Sample Project

1. Clone this repository
2. Navigate to the sample project directory: `cd examples/sample_project`
3. Follow the setup instructions above
4. Run each step in sequence, performing the manual steps between automated ones
5. Check the output directories for results

## License

[MIT License](LICENSE)

## Acknowledgments

This project was developed for the Territorial Coral Reef Monitoring Program. 