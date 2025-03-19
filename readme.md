# TCRMP 3D Processing: Standard Operating Procedure

This repository provides a standardized framework for 3D reconstruction of coral reef transects, developed by the Territorial Coral Reef Monitoring Program (TCRMP).

## Quick Start

1. Create a new project directory and copy the example project structure:
   ```bash
   cp -r examples/sample_project my_new_project
   ```

2. Edit `analysis_params.yaml` in your project directory to set your parameters:
   ```yaml
   # Project Information
   project:
     name: "My_Project_Name"
     notes: |
       Description of your project and any important notes.

   # Directory Configuration
   directories:
     video_source: "/path/to/your/videos"  # Directory containing MP4/MOV files
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

3. Run the frame extraction script:
   ```bash
   cd my_new_project
   python src/step0.py
   ```

4. Follow the remaining steps in this SOP to complete the 3D reconstruction

## Repository Structure

The repository follows standard software development practices:

```
├── src/                     # Source code
│   ├── config.py            # Configuration module (loads from YAML)
│   ├── step0.py             # Frame extraction script
│   ├── step1.py             # Initial 3D processing 
│   ├── step2.py             # Chunk management
│   ├── step3.py             # Exports and scale bars
│   └── step4.py             # Web publishing
│
├── data/                    # Data directories
│   ├── frames/              # Extracted video frames
│   ├── processed_frames/    # Edited frames (if needed)
│   ├── psx_input/           # Input Metashape projects
│   └── *_processing_status.txt  # Auto-generated status files
│
├── output/                  # Processing outputs
│   ├── models/              # 3D models
│   ├── orthomosaics/        # Orthomosaic images
│   ├── psx/                 # Final Metashape projects
│   ├── reports/             # Reports
│   └── reports_initial/     # Initial processing reports
│
├── presets/                 # Application presets
│   ├── lightroom/           # Lightroom presets
│   └── premiere/            # Premiere Pro presets
│
├── docs/                    # Documentation
│
└── examples/                # Example project structures
    └── sample_project/      # Sample project with example configuration
```

## Example Project

The repository includes an example project structure in the `examples/sample_project/` directory that demonstrates:

- Sample YAML configuration file (`analysis_params.yaml`)
- Complete directory structure matching the recommended layout
- README explaining how to use the example as a template

You can examine this example to see how to organize your own data and workflows.

## Configuration

The project uses a YAML-based configuration system for easy parameter management:

- **User-friendly configuration**: Edit `analysis_params.yaml` in your project directory
- **Flexible Paths**: Point to videos and outputs stored anywhere on your system
- **Automatic Directory Creation**: All required directories are created automatically
- **Customizable Parameters**: Adjust frame extraction, model quality, and other settings
- **Status Tracking**: Automatic generation and updating of processing status files

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

## Processing Workflow

### Getting Started

Download and unzip this repository. The system is designed to be flexible - you can store videos, frames, and outputs in any location on your system.

### Configuration Setup

1. Edit `analysis_params.yaml` in your project directory to set your parameters:
   ```yaml
   # Project Information
   project:
     name: "My_Project_Name"
     notes: |
       Description of your project and any important notes.

   # Directory Configuration
   directories:
     video_source: "/path/to/your/videos"  # Directory containing MP4/MOV files
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

2. The configuration system will:
   - Automatically create all required directories
   - Generate a unique status file for tracking progress
   - Apply settings to all processing steps
   - Handle paths and file organization

3. Key features:
   - **User-friendly configuration**: Edit YAML file instead of Python code
   - **Flexible paths**: Point to videos and outputs stored anywhere
   - **Automatic directory creation**: All required directories are created automatically
   - **Customizable parameters**: Adjust frame extraction, model quality, and other settings
   - **Status tracking**: Automatic generation and updating of processing status files

### Data Tracking

The repository automatically maintains a CSV file (`data/tracking.csv`) that tracks:

- Transect identifiers
- Source video locations
- Extracted frame locations
- Processing status for each step
- Output file locations

This CSV is automatically updated by each script as processing progresses.

## Video Encoding (Premier Pro)

-   Upload contents of memory card into computer (connect using special mem card reader compatible with CF Express, careful of magnets on the mem card reader)

-   **Starting with .CRM, export to MP4 or MOV without applying LUTs**

-   Export preset: `presets/premiere/step0_premierepro_uhd_8k_23sept2024.epr` 

-   Use the following naming convention for consistent transect identification:

    -   Example: `TCRMP20240311_3D_BID_T1_3.MP4`

        -   `TCRMP20240311` = TCRMP plus date (YYYYMMDD)

        -   `3D` = demographic

        -   `BID` = sitecode

        -   `T1` = transect number

        -   `3` = pass number (if separated vids by pass)

-   Save videos to your preferred directory - set this location in the configuration file

-   Format/wipe/initialize memory card after the videos have been uploaded and backed up

## Extract Frames (Python)

The frame extraction process uses a Python script (`src/step0.py`) that leverages ffmpeg.

### Requirements

- ffmpeg and ffprobe must be installed and available in your system PATH
- Python 3.6+ with the required libraries

### Running the Script

After configuring `analysis_params.yaml` with your video source directory:

```bash
# Navigate to your project directory
cd my_new_project

# Run the extraction script
python src/step0.py
```

The script will:
1. Read your configured video source directory
2. Find all MP4 and MOV files
3. Group videos by transect ID based on filename
4. Extract frames from each video
5. Save frames in the configured output directory
6. Update the status file with progress information

### Advanced Options

You can override the configuration file settings using command-line arguments:

```bash
# Override source and output directories
python src/step0.py --video-dir /different/video/path --output-dir /custom/output/path

# Custom frame count
python src/step0.py --frames 1800
```

## Optional: Photo Editing

While not required, you can optionally edit the extracted frames in Adobe Lightroom Classic:

1. Import the extracted frames into Lightroom
2. Apply the preset `presets/lightroom/step0_lightroom_hdrphoto_r5c.xmp`
3. Export to the processed frames directory (`data/processed_frames`)

Future versions may incorporate algorithmic color correction methods like [Sea Thru](https://www.deryaakkaynak.com/sea-thru).

## 3D processing (metashape pro)

### File setup

- Open new Metashape file
- Add photos to it corresponding to each transect. You can use the frames directory created during the extraction step.
- Save as PSX in your designated input PSX directory (as configured in `analysis_params.yaml`, default is `data/psx_input`).

### step1.py

Run `src/step1.py`: in Metashape, select Tools, Run Script, and point to the `src/step1.py`.

::: callout-warning
This is the most time-consuming step and can take a few hours per chunk.
:::

This script performs the following operations:

1. Aligns photos
2. Removes points with high reconstruction uncertainty (configurable in analysis_params.yaml)
3. Optimizes cameras
4. Removes points with high reprojection error (configurable in analysis_params.yaml)
5. Removes points with high projection accuracy (configurable in analysis_params.yaml)
6. Rotates the coordinate system to the bounding box
7. Builds dense cloud with quality setting (configurable in analysis_params.yaml)
8. Builds model
9. Builds UV maps
10. Builds texture
11. Generates a report in the configured output directory
12. Saves the project

The script uses the paths and parameters defined in the configuration file.

### Check models

Go through each chunk and check:

- Each transect is roughly visible when you use 0 to reset view
- There are no mirror images or huge gaps in photos (< 90% photos aligned should be a red flag)
- Scale bars are visible

Disable chunks that are not good quality (e.g., < 90% of photos aligned)

### step2.py

Run `src/step2.py`: in Metashape, select Tools, Run Script, and point to the `src/step2.py`.

This script:

1. Reads the status file
2. Groups chunks by site
3. Creates new PSX projects in the output directory (configurable in analysis_params.yaml)
4. Copies the appropriate chunks from source projects to destination projects
5. Updates the status file with progress information

### Straighten / scale models

Open each project and do the following for each chunk:

**Straightening**

- Load textured model
- Auto change brightness and contrast in one of the images; this will be applied to the texture
- Change to rotate model view and rotate the transect so the transect line lines up horizontally and is top of view
- Model > Region > Rotate region to view
- Resize region to "crop" to transect area (do this for top xy and side views)
- Use rectangular crop tool to crop to transect area bound by region

**Scaling (only if scaling manually)**

- Place markers on scales - set up at least 2 scale bars
- Set distance in reference pane
- Press refresh button - make sure error less than .01

**Save project**

### step3.py

Run `src/step3.py`: in Metashape, select Tools, Run Script, and point to the `src/step3.py`.

This script:

1. Adds scale bars to the model if markers are detected
2. Removes small components from the model
3. Exports orthomosaic to the configured output directory
4. Exports textured model to the configured output directory
5. Exports report to the configured output directory
6. Saves the project

The script processes all projects listed in the status file, using the paths defined in the configuration file.

### step4.py

Run `src/step4.py`: in Metashape, select Tools, Run Script, and point to the `src/step4.py` file.

This script:

1. Duplicates each chunk and creates a temporary version
2. Decimates the model to a specified number of vertices (configurable in analysis_params.yaml)
3. Uploads the decimated model to Sketchfab using an API token (configurable in analysis_params.yaml)
4. Deletes the temporary chunk after upload
5. Saves the project

## Example Project

The repository includes an example project structure in the `examples/sample_project/` directory that demonstrates:

- Sample configuration file (`src/config.py`)
- Example tracking CSV with sample data
- Complete directory structure matching the recommended layout
- README explaining how to use the example as a template

You can examine this example to see how to organize your own data and workflows.

## Summary of improvements

The repository has been restructured with the following benefits:

1. **Standardized directory structure**: Following software development best practices
2. **User-friendly configuration**: Simple setup at the top of config.py
3. **Flexible directory structure**: Point to videos stored anywhere on your system
4. **No file copying required**: Process videos in-place without unnecessary duplication
5. **Support for multiple video formats**: Works with both MP4 and MOV files
6. **Automatic tracking**: CSV file automatically tracks progress and file locations
7. **Configurable parameters**: All settings are centralized and clearly documented
8. **Command-line options**: Run scripts with custom parameters without editing files
9. **All-Python workflow**: Consistent programming language across all processing steps
10. **Example project**: Sample setup to guide new users