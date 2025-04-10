# TCRMP 3D Processing Pipeline

A comprehensive workflow for processing 3D coral reef models from video footage.

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

## Project Structure

```
TCRMP_3D/
├── presets/                 # Preset files for software
│   ├── lightroom/          # Adobe Lightroom presets
│   └── premiere/           # Adobe Premiere presets
├── src/                     # Source code
│   ├── config.py           # Configuration utilities
│   ├── step0.py            # Frame extraction
│   ├── step1.py            # Initial 3D processing
│   ├── step2.py            # Chunk management
│   ├── step3.py            # Model processing and exports
│   └── step4.py            # Final exports and web publishing
├── install_metashape_deps.sh    # Script to install dependencies for Metashape (macOS)
├── requirements.txt    # reqms
└── README.md                # This file
```

## Initial Setup

### 1. Repository Setup

Clone this repository to your local machine:
```bash
git clone https://github.com/yourusername/TCRMP_3D.git
cd TCRMP_3D
```

### 2. Create Project Directory Structure

Create all necessary directories for your project:
```bash
# From the workspace root, create the required directories
mkdir -p examples/sample_project/{video_source,data,output}
# final_outputs,psx_input,reports,frames,psx_output,models,orthomosaics}
```

This will create the following directory structure:
```
examples/sample_project/
├── video_source/   # Input video files
├── data/          # Data directory
├── output/        # Output directory
```

Copy and configure the analysis parameters file:
```bash
# Copy the base configuration file to your project
cp analysis_params.yaml examples/sample_project/

# Edit the configuration file to match your project settings
# The paths in the file should be relative to the workspace root
# For example:
#   video_source: "examples/sample_project/video_source"
#   base: "examples/sample_project"
#   data: "examples/sample_project/data"
#   etc.
```

The configuration file (`analysis_params.yaml`) contains all the settings for your project. Make sure to:
1. Keep all paths relative to the workspace root
2. Update the project name and notes
3. Verify that all directory paths match the structure you created
4. Adjust any processing parameters as needed for your specific project

### 3. Installing Dependencies

The pipeline requires dependencies in two Python environments:
1. Your local environment (for frame extraction - step0.py)
2. Metashape's Python environment (for 3D processing - step1.py and beyond)

#### Local Environment Setup

Create a Python virtual environment in your project:
```bash
# Create virtual environment in sample project directory using Python 3.9
python3.9 -m venv examples/test/.venv

# Activate the virtual environment
source examples/test/.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Running Metashape Scripts

To run Metashape scripts with the correct Python environment, you'll need to set the PYTHONPATH to point to your virtual environment's site-packages. This ensures Metashape uses the packages from your virtual environment while maintaining compatibility with Metashape's Python 3.9.

The general format for running Metashape scripts is:
```bash
# From the workspace root
PYTHONPATH=examples/test/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/stepX.py
```

Where `stepX.py` is the specific step you want to run (step1.py, step2.py, etc.).

### 4. Project Configuration

The sample project (`examples/sample_project`) is already configured with the necessary directory structure and settings. To use it:

1. **Verify Directory Structure**:
   ```bash
   # From the workspace root, check the sample project structure
   ls -la examples/sample_project
   ```
   You should see:
   - `.venv/` (Python virtual environment)
   - `video_source/` (for input videos)
   - `data/` 
   - `output/`
   - `analysis_params.yaml` (configuration file)

2. **Configure Your Project**:
   - Edit `examples/test/analysis_params.yaml` to match your project settings
   - Place your video files in `examples/test/video_source/`
   - All processing will happen within the project directory

3. **Verify Environment Setup**:
   - Local Python environment is set up in `examples/test/.venv`
   - All required directories exist in `examples/test`

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

# Run step0.py with project directory as argument
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

**Important**: Make sure you've installed the dependencies in Metashape's Python environment as explained in the setup section.

**On macOS**:
```bash
# From the workspace root
# Run with project directory as argument
# THIS IS BROKEN: PYTHONPATH=examples/sample_project/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step1.py 

# OR  this worked 5 april
PYTHONPATH=examples/test/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step1_isolated.py
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
5. Save each batch as a separate PSX file in the `psx_input` directory
6. Create a batch summary CSV file mapping models to PSX files

### Manual Step: Quality Check & Alignment

After Step 1, manually check the quality of the generated models and make any necessary adjustments:

1. Open each PSX file in the `psx_input` directory with Metashape
2. For each model (chunk) in the project:
   - Review camera alignment and model quality
   - Ensure point cloud is clean and representative of the model
   - Check for any alignment issues or artifacts
   - Identify any areas that might need adjustments in Step 2
   - Verify that model IDs are correctly labeled
3. Save the project

### Step 2: Chunk Management

This step consolidates chunks by site to prepare for final processing.

**On macOS**:
```bash
# Run with project directory as argument
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step2.py /path/to/your/project/directory
# OR run without arguments to be prompted for the project directory
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step2.py
```

**On Windows**:
```cmd
:: Run with project directory as argument
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r src\step2.py C:\path\to\your\project\directory
:: OR run without arguments to be prompted for the project directory
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r src\step2.py
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file 
2. Read the tracking files to identify completed models
3. Group models by site
4. Create new PSX files organized by site in the `psx_output` directory
5. Update tracking information for each model

### Manual Step: Straightening & Scaling

After Step 2, manually straighten and scale each model:

1. Open each project in the `05_outputs/psx` directory
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
   
3. Save the project

> **Note:** Make sure you are only working from ONE PSX file in the psx_input directory. The system should create just one processing status file and update that one file.

### Step 3: Model Processing and Exports

This step adds scale bars (if coded targets are present), removes small components, builds and exports orthomosaics, textured models, and reports.

**On macOS**:
```bash
# Run with project directory as argument
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3.py /path/to/your/project/directory
# OR run without arguments to be prompted for the project directory
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3.py
```

**On Windows**:
```cmd
:: Run with project directory as argument
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r src\step3.py C:\path\to\your\project\directory
:: OR run without arguments to be prompted for the project directory
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r src\step3.py
```

This will:
1. Load project configuration from the specified directory's `analysis_params.yaml` file
2. Process each project in the `psx_output` directory
3. For each model (chunk) in the project:
   - Add scale bars if coded targets are present
   - Remove small disconnected components from the model
   - Build and export orthomosaic
   - Export textured model
   - Generate report
4. Save exports to the appropriate directories

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
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step4.py /path/to/your/project/directory
# OR run without arguments to be prompted for the project directory
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step4.py
```

**On Windows**:
```cmd
:: Run with project directory as argument
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r src\step4.py C:\path\to\your\project\directory
:: OR run without arguments to be prompted for the project directory
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r src\step4.py
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
- Project-specific configuration: `examples/sample_project/analysis_params.yaml`

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

## Troubleshooting

### Common Issues

1. **Package Import Errors in Metashape**
   
   If you encounter import errors for packages like numpy, pandas, or PyYAML when running scripts through Metashape, you'll need to install these packages in Metashape's Python environment. Use the provided installation scripts:
   
   ```bash
   # On macOS/Linux
   ./install_metashape_deps.sh
   
   # On Windows
   install_metashape_deps.bat
   ```

2. **PSX files not generated**
   
   Ensure that the `psx_input` directory exists and is writable. Check the log file in the `reports` directory for error messages.

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