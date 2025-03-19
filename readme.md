# TCRMP 3D processing SOP and file structure template

This is a template folder structure and scripts for 3D Processing, generated for reconstructing TCRMP coral reef models, but applicable to other projects as well. All contents are found in the template.zip. 

When you unzip template, you will find the following contents:

## Template Contents

### 00_3Dprotocol.qmd
- A Quarto Markdown document outlining the full 3D processing protocol, including field methods, preprocessing, and final output generation.
- **Usage**: Follow this file for step-by-step guidance on data collection and processing.

### 00_3Dprotocol.Rproj
- RStudio project file containing the environment and settings for running all R-based scripts and analyses.
- Use this file to load the project environment in RStudio.

### 00_list.csv

- **Description**: This CSV file tracks metadata and the progress of the 3D processing pipeline for each dataset.
  
- **Columns**:
  - **index**: Unique identifier for each row or dataset.
  - **year**: The year the data was collected (e.g., 2024).
  - **site**: Name or code of the collection site (e.g., BPT).
  - **transect**: Transect number associated with the dataset (e.g., 1).
  - **extract**: Indicates whether data extraction has been performed (marked with "x").
  - **lightroom**: Indicates if data has been processed using Adobe Lightroom (marked with "x").
  - **psx_startdir**: Directory containing the initial PSX files (e.g., "03_psx").
  - **psx_startname**: Name of the initial PSX file (e.g., "BCK_BIT_BLK.psx").
  - **step1**: Status of the first processing step (marked with "x" when completed).
  - **step2**: Status of the second processing step (marked with "x" when completed).
  - **psx_finaldir**: Directory where the final PSX files are stored (e.g., "04_outputs/psx").
  - **psx_finalname**: Final name of the processed PSX file (e.g., "BPT.psx").
  - **step3**: Status of the third processing step (marked with "x" when completed).
  - **step4**: Status of the fourth processing step (marked with "x" when completed).
  - **action**: Notes any specific action to be taken next (e.g., "do something").
  - **notes**: Additional information or relevant notes regarding the dataset (e.g., "here to add some notes").

### 00_scripts/
- Contains all custom scripts, automation tools, and R code used for the processing steps.
- See descriotions in 00_3Dprotocol.pdf

### 01_vids/
- Folder containing original videos

### 02_pics/
- Folder containing original images or datasets collected in the field.

### 03_editedpics/
- Edited or pre-processed versions of the images, prepared for further analysis or modeling.

### 04_psx/
- Intermediate files generated during the processing pipeline.

### 05_outputs/
- Final results of the 3D processing, including models, orthomosaics, and reports.
  - **models/**: Contains final 3D models created from the image datasets.
  - **orthomosaics/**: Folder for orthomosaic images compiled from the processed data.
  - **psx/**: Final PSX output files.
  - **reports/**: Contains documentation and reports generated during or after the processing workflow.

## Processing Instructions

download and unzip this template, and follow instructions in 00_3Dprotocol.pdf, which is rendered from 00_3Dprotocol.qmd. 
