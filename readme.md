# TCRMP 3D Processing: Standard Operating Procedure

This repository provides a standardized framework for 3D reconstruction of coral reef transects, developed by the Territorial Coral Reef Monitoring Program (TCRMP).

## Quick Start

1. Open `src/config.py` and set these required parameters:
   ```python
   # Directory containing your MP4/MOV video files
   VIDEO_SOURCE_DIRECTORY = "/path/to/your/videos"  

   # Base directory for all outputs
   OUTPUT_BASE_DIRECTORY = "/path/to/store/outputs"  
   ```

2. Run the frame extraction script:
   ```bash
   python src/extract_frames.py
   ```

3. Follow the remaining steps in this SOP to complete the 3D reconstruction

## Repository Structure

The repository follows standard software development practices:

```
├── src/                     # Source code
│   ├── config.py            # Configuration module
│   ├── extract_frames.py    # Frame extraction script
│   ├── step1.py             # Initial 3D processing 
│   ├── step2.py             # Chunk management
│   ├── step3.py             # Exports and scale bars
│   └── step4.py             # Web publishing
│
├── data/                    # Data directories
│   ├── frames/              # Extracted video frames
│   ├── processed_frames/    # Edited frames (if needed)
│   ├── psx_input/           # Input Metashape projects
│   └── tracking.csv         # Processing progress tracker
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

- Sample configuration file (`src/config.py`)
- Example tracking CSV with sample data
- Complete directory structure matching the recommended layout
- README explaining how to use the example as a template

You can examine this example to see how to organize your own data and workflows.

## Configuration

- **User-friendly configuration**: Edit the clearly marked configuration area at the top of `src/config.py`
- **Flexible Paths**: Point to videos stored anywhere on your system
- **Automatic Directory Creation**: All required directories are created automatically
- **Customizable Parameters**: Adjust frame extraction and model quality settings

## field methods

### materials

-   camera + lights, memory card

-   scale bars

-   ...

### procedure (4-pass method)

-   general

    -   everything with the pink ziptie belongs to the 3d camera

-   camera maintenance:

    -   camera cinema gear

    -   settings

    -   programmable buttons

-   housing maintenance (every few weeks, or if any leaks detected)

    -   o-rings greasing

-   day before

    -   check housing/o-rings

    -   charge camera

    -   charge external battery pack

    -   charge strobe light batteries

    -   memory card- initialize media

-   morning of:

    -   **closing / sealing cam**

        -   install battery and memory card into camera

        -   attach lens

        -   check autofocus on (switch on lens)

        -   remove camera lens cap

        -   check for smudges on lens

        -   pull switch on housing so that can insert camera with the cinema camera gear

        -   seat camera in housing (pull out stage thing, screw camera on.

        -   put camera into housing (careful to not scratch lens)

        -   connect to external battery

        -   add external battery to camera

        -   once in housing:

            -   turn alarm on

            -   check for smudges on housing lens

            -   check o-ring

            -   close housing

            -   use vacuum device until light turns green.

    -   **check have materials**:

        -   camera + mem card

        -   housing

        -   field box with extra stuff/towels, o-ring grease, cleaning materials, dry towels, etc.

        -   slate

        -   scale bars x 2

        -   handle (clips, rope)

    -   **check camera settings**:

        -   CP file : C2: Canon log 3 / C.Gamut Color matrix neutral.

        -   Sensor mode: full frame

        -   freq 59.94hz

        -   Rec = RAW LT

        -   Dest = CFexpress

        -   Frame = 59.94 fps

### in water :

-   **Start of dive:**

    -   **B**uttons: press all buttons to prime them

    -   **Power:** turn on camera and lights (hold in/out buttons 1s, press middle button). put lights to sleep (hold center 2s)

    -   **L**eaks: green light stays green, if turn red, return to boat.

-   **Transect and Camera Setup**

    -   **S**cale bars: Place at each end of transect, one perpendicular, one parallel to transect. make sure targets visible in some footage and scale bars do not move at any time during filming.

    -   **T**ime code: reset (Mode button).

    -   **A**rms: extend to position lights as far apart as possible

    -   **L**ights: turn on (hold Center Button 2 sec).

    -   **W**hite balance: press Button 13, hold camera over white part of one of the scale bars.

    -   **E**xposure: open WFM (Button 6) and false color (Button 9), Use F-stop dial to slightly overexpose, just below 100% on WFM.

    -   **A**ltitude: position camera so viewfinder covers length of scale bar, note height (should be \~70cm). Maintain this altitude throughout filming.

    -   **R**ecord: Record button, show transect number, autofocus

-   **Filming (4 passes, 10 m each, \~1 min, consistent altitude):**

    -   Pass 1: Start at one end, camera facing straight down, transect line visible in left quarter of viewfinder.

    -   Pass 2: Turn around, camera facing straight down, slightly away from transect line such that viewfinder sees 1m distance from transect while keeping \~0.5 m overlap with Pass 1 (\~arm's length from transect)

    -   Pass 3 & 4: Move \~20 cm from pass 1/2 position, tilt camera 45°, capture angled view of transect from either side.

-   **After Filming:** press center button on each light for 2s to put light to sleep.

## Processing Workflow

### Getting Started

Download and unzip this repository. The system is designed to be flexible - you can store videos, frames, and outputs in any location on your system.

### Configuration Setup

1. Open `src/config.py` in any text editor
2. In the USER CONFIGURATION AREA at the top of the file:
   - Set `VIDEO_SOURCE_DIRECTORY` to the folder containing your videos
   - Set `BASE_DIRECTORY` to the root location for all inputs and outputs
   - Optionally set `DATA_DIRECTORY` and `OUTPUT_DIRECTORY` for custom locations
   - Adjust other parameters as needed (frames per transect, quality, etc.)
3. Save the file - no other modifications are needed

Example configuration:
```python
# Directory containing your MP4/MOV video files
VIDEO_SOURCE_DIRECTORY = "/Users/researcher/Dropbox/CoralReefVideos/June2023"

# Base directory for all inputs and outputs
BASE_DIRECTORY = "/Users/researcher/Documents/CoralReefModels"

# Optional custom directories (if you need separate locations)
DATA_DIRECTORY = "/Volumes/ExternalDrive/CoralReefData"  # Custom data location
OUTPUT_DIRECTORY = ""  # Leave empty to use BASE_DIRECTORY/output

# Number of frames to extract per transect
FRAMES_PER_TRANSECT = 1500  # Increased for higher quality
```

With this flexible configuration:
- You can process videos from any location
- Data and outputs can be stored wherever you want
- You can separate data and output directories (useful for limited space)
- All required directories are created automatically

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

The frame extraction process uses a Python script (`src/extract_frames.py`) that leverages ffmpeg.

### Requirements

- ffmpeg and ffprobe must be installed and available in your system PATH
- Python 3.6+ with the required libraries

### Running the Script

After configuring `src/config.py` with your video source directory:

```bash
# Navigate to the repository directory
cd path/to/3d-repository

# Run the extraction script
python src/extract_frames.py
```

The script will:
1. Read your configured video source directory
2. Find all MP4 and MOV files
3. Group videos by transect ID based on filename
4. Extract frames from each video
5. Save frames in the configured output directory
6. Update the tracking CSV with progress information

### Advanced Options

You can override the configuration file settings using command-line arguments:

```bash
# Override source and output directories
python src/extract_frames.py --video-dir /different/video/path --output-dir /custom/output/path

# Custom frame count
python src/extract_frames.py --frames 1800
```

## Optional: Photo Editing

While not required, you can optionally edit the extracted frames in Adobe Lightroom Classic:

1. Import the extracted frames into Lightroom
2. Apply the preset `presets/lightroom/step0_lightroom_hdrphoto_r5c.xmp`
3. Export to the processed frames directory (`data/processed_frames`)

Future versions may incorporate algorithmic color correction methods like [Sea Thru](https://www.deryaakkaynak.com/sea-thru).

## 3D processing (metashape pro)

### File setup

-   Open new Metashape file

-   Add photos to it corresponding to each transect. You can use the frames directory created during the extraction step.

-   Save as PSX in your designated input PSX directory (as configured in `src/config.py`, default is `data/psx_input`).

### step1.py

Run `src/step1.py`: in Metashape, select Tools, Run Script, and point to the `src/step1.py`.

::: callout-warning
This is the most time-consuming step and can take a few hours per chunk.
:::

This script performs the following operations:

1. Aligns photos
2. Removes points with high reconstruction uncertainty (configurable in config.py)
3. Optimizes cameras
4. Removes points with high reprojection error (configurable in config.py)
5. Removes points with high projection accuracy (configurable in config.py)
6. Rotates the coordinate system to the bounding box
7. Builds dense cloud with quality setting (configurable in config.py)
8. Builds model
9. Builds UV maps
10. Builds texture
11. Generates a report in the configured output directory
12. Saves the project

The script uses the paths and parameters defined in the configuration file.

### Check models

Go through each chunk and check:

-   Each transect is roughly visible when you use 0 to reset view

-   There are no mirror images or huge gaps in photos (< 90% photos aligned should be a red flag)

-   Scale bars are visible

Disable chunks that are not good quality (e.g., < 90% of photos aligned)

### step2.py

Run `src/step2.py`: in Metashape, select Tools, Run Script, and point to the `src/step2.py`.

This script:

1. Reads the tracking CSV file
2. Groups chunks by site
3. Creates new PSX projects in the output directory (configurable in config.py)
4. Copies the appropriate chunks from source projects to destination projects
5. Updates the CSV file with progress information

### Straighten / scale models

Open each project and do the following for each chunk:

**Straightening**

-   Load textured model

-   Auto change brightness and contrast in one of the images; this will be applied to the texture.

-   Change to rotate model view and rotate the transect so the transect line lines up horizontally and is top of view.

-   Model > Region > Rotate region to view

-   Resize region to "crop" to transect area (do this for top xy and side views)

-   Use rectangular crop tool to crop to transect area bound by region.

**Scaling (only if scaling manually)**

-   Place markers on scales - set up at least 2 scale bars

-   Set distance in reference pane

-   Press refresh button - make sure error less than .01

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

The script processes all projects listed in the CSV file, using the paths defined in the configuration file.

### step4.py

Run `src/step4.py`: in Metashape, select Tools, Run Script, and point to the `src/step4.py` file.

This script:

1. Duplicates each chunk and creates a temporary version
2. Decimates the model to a specified number of vertices (configurable in config.py)
3. Uploads the decimated model to Sketchfab using an API token (configurable in config.py)
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