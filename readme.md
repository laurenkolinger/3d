# TCRMP 3D Processing Pipeline

A comprehensive workflow for processing 3D coral reef models from video footage.

## Overview

This project provides a set of Python scripts to automate the workflow of processing underwater video footage into 3D models of coral reefs. The pipeline uses Agisoft Metashape for 3D reconstruction and is designed to work with the Territorial Coral Reef Monitoring Program (TCRMP) methodology.

## Requirements

- Agisoft Metashape Pro (v2.1.1 or later)
- Python 3.9+
- Required Python packages (specific versions in `requirements.txt`):
  - PyYAML
  - pandas
  - numpy
  - opencv-python

## Project Structure

```
TCRMP_3D/
├── config/                  # Configuration files
│   └── analysis_params.yaml # Base configuration template
├── examples/                # Example projects
│   └── sample_project/      # Sample project with demo data
├── presets/                 # Preset files for software
│   ├── lightroom/           # Adobe Lightroom presets
│   └── premiere/            # Adobe Premiere presets
├── src/                     # Source code
│   ├── config.py            # Configuration utilities
│   ├── step0.py             # Frame extraction
│   ├── step1.py             # Initial 3D processing
│   ├── step2.py             # Chunk management
│   ├── step3.py             # Model processing and exports
│   └── step4.py             # Final exports and web publishing
├── install_metashape_deps.sh    # Script to install dependencies for Metashape (macOS/Linux)
├── install_metashape_deps.bat   # Script to install dependencies for Metashape (Windows)
└── README.md                # This file
```

## Initial Setup

### 1. Repository Setup

Clone this repository to your local machine:
```bash
git clone https://github.com/yourusername/TCRMP_3D.git
cd TCRMP_3D
```

### 2. Installing Dependencies

The pipeline requires dependencies in two Python environments:
1. Your local environment (for frame extraction - step0.py)
2. Metashape's Python environment (for 3D processing - step1.py and beyond)

#### Local Environment Setup

Create a Python virtual environment in your project:
```bash
# Navigate to your project directory
cd examples/sample_project

# Create virtual environment
python -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install requirements
pip install -r ../../requirements.txt
```

#### Metashape Environment Setup (IMPORTANT)

For steps that use Metashape (step1.py and beyond), you need to install dependencies in Metashape's Python environment. We provide scripts to simplify this process:

**On macOS/Linux**:
```bash
# Make the script executable
chmod +x ../../install_metashape_deps.sh

# Run the installation script
../../install_metashape_deps.sh
```

**On Windows**:
```cmd
..\..\install_metashape_deps.bat
```

These scripts will install the necessary packages directly in Metashape's Python environment.

### 3. Project Configuration

Copy the sample project as a template for your own project and edit the configuration:
```bash
cp -r examples/sample_project my_new_project
cd my_new_project
# Edit analysis_params.yaml to configure your project
```

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

## Detailed Workflow

### Step 0: Frame Extraction

This step extracts frames from video footage at a specified rate.

```bash
# Activate the virtual environment first
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Run step0.py
python ../../src/step0.py
```

This will:
1. Scan the `video_source` directory for video files
2. Create a subdirectory for each video in the `frames` directory
3. Extract frames according to the settings in `analysis_params.yaml`
4. Create a tracking CSV file for each model
5. Generate a summary of extracted frames

### Step 1: Initial 3D Processing

This step performs the initial 3D reconstruction using the extracted frames. It creates batched PSX files with multiple models grouped together for efficiency.

**Important**: Make sure you've installed the dependencies in Metashape's Python environment as explained in the setup section.

**On macOS**:
```bash
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r ../../src/step1.py
```

**On Windows**:
```cmd
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r ..\..\src\step1.py
```

This will:
1. Find all model directories in the `frames` directory
2. Group models into batches (maximum 5 models per batch by default)
3. For each model:
   - Add photos and align cameras
   - Filter points and optimize cameras
   - Build depth maps and create 3D model
   - Apply textures and generate report
4. Save each batch as a separate PSX file in the `psx_input` directory
5. Create a batch summary CSV file mapping models to PSX files

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
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r ../../src/step2.py
```

**On Windows**:
```cmd
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r ..\..\src\step2.py
```

This will:
1. Read the tracking files to identify completed models
2. Group models by site
3. Create new PSX files organized by site in the `psx_output` directory
4. Update tracking information for each model

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
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r ../../src/step3.py
```

**On Windows**:
```cmd
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r ..\..\src\step3.py
```

This will:
1. Process each project in the `psx_output` directory
2. For each model (chunk) in the project:
   - Add scale bars if coded targets are present
   - Remove small disconnected components from the model
   - Build and export orthomosaic
   - Export textured model
   - Generate report
3. Save exports to the appropriate directories

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
/Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r ../../src/step4.py
```

**On Windows**:
```cmd
"C:\Program Files\Agisoft\Metashape Pro\metashape.exe" -r ..\..\src\step4.py
```

This will:
1. For each model (chunk) in the project:
   - Create a decimated copy for web viewing
   - Upload to Sketchfab (if API token is provided)
   - Export high-resolution orthomosaic
   - Export high-resolution textured model
   - Export point cloud
   - Generate comprehensive report
2. Save all exports to the `final_outputs` directory

## Configuration

The processing pipeline is configured through YAML files:

- Base configuration: `config/analysis_params.yaml`
- Project-specific configuration: `examples/sample_project/analysis_params.yaml`

Modify these files to adjust processing parameters to your needs.

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