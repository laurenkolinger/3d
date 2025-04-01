# Example Project: TCRMP 3D Processing

This is an example project demonstrating how to use the TCRMP 3D processing workflow. The project includes sample video files and a complete configuration setup.

## Project Structure

```
sample_project/
├── README.md
├── analysis_params.yaml
├── data/                  # Will be created automatically
│   ├── frames/           # Extracted frames
│   ├── processed_frames/ # Edited frames
│   └── psx_input/        # Place your Metashape project files here
├── video_source/          # Contains your video files
│   ├── TCRMP20241014_3D_BWR_T1.mov
│   └── TCRMP20241014_3D_BWR_T2.mov
├── src/                   # Processing scripts
└── output/               # Will be created automatically
    ├── psx/              # Final processed Metashape project files
    ├── reports/          # Processing logs and reports
    └── polished/         # Customizable location for final polished outputs
```

## Included Files

1. **Video Files**:
   - `TCRMP20241014_3D_BWR_T1.mov`
   - `TCRMP20241014_3D_BWR_T2.mov`

2. **Configuration**:
   - `analysis_params.yaml` - Complete configuration file with all processing parameters

## Configuration Details

The `analysis_params.yaml` file is pre-configured with:

1. **Project Information**:
   ```yaml
   project:
     name: "TCRMP_3D_Example"
     notes: "Example project demonstrating the TCRMP 3D processing workflow."
   ```

2. **Directory Configuration**:
   ```yaml
   directories:
     video_source: "video_source"
     base: "."
     data: "data"
     output: "output"
     adobe_presets: "../../presets/lightroom"
     metashape_presets: "../../presets/premiere"
     scripts: "../../src"
     config: "../../src/config.py"
     polished_outputs: "output/polished"  # Customizable location for final polished outputs
   ```

3. **Processing Parameters**:
   ```yaml
   processing:
     frames_per_transect: 1200
     extraction_rate: 0.5
     chunk_size: 400
     use_gpu: true
     metashape:
       quality: 2
       defaults:
         accuracy: "high"
         quality: "high"
         depth_filtering: "moderate"
         max_neighbors: 100
       alignment:
         downscale: 2
         generic_preselection: true
         reference_preselection: false
       optimization:
         fit_f: true
         fit_cx: true
         fit_cy: true
         fit_b1: true
         fit_b2: true
         fit_k1: true
         fit_k2: true
         fit_k3: true
         fit_k4: true
         fit_p1: true
         fit_p2: true
         fit_p3: true
         fit_p4: true
         adaptive_fitting: false
       mesh:
         surface_type: "Arbitrary"
         interpolation: "EnabledInterpolation"
         face_count: "HighFaceCount"
         source_data: "DenseCloudData"
     chunk_quality:
       min_cameras: 10
       min_alignment_percentage: 90
     model_cleanup:
       min_faces: 100
       min_vertices: 50
     orthomosaic:
       resolution: 0.001
       save_alpha: true
       save_world: true
       save_xyz: true
     model_export:
       texture_format: "JPEG"
       save_texture: true
       save_uv: true
       save_normals: true
       save_colors: true
     final_orthomosaic:
       resolution: 0.0005
       save_alpha: true
       save_world: true
       save_xyz: true
     final_model:
       texture_format: "JPEG"
       texture_size: 4096
       save_texture: true
       save_uv: true
       save_normals: true
       save_colors: true
     point_cloud:
       format: "LAS"
       save_colors: true
       save_normals: true
     sketchfab:
       token: "your_sketchfab_api_token_here"
       decimated_vertices: 3000000
   ```

## Initial Setup

1. **Create Metashape Projects**:
   - Open Metashape
   - Create your project(s) however you want to divide up the dataset
   - Save your PSX files in the `data/psx_input/` directory
   - This is the only location where PSX files should be placed

2. **Setup Python Environment**:
   ```bash
   # Create and activate virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

## Processing Steps

1. **Extract Frames**:
   ```bash
   python src/step0.py
   ```

2. **Initial 3D Processing**:
   ```bash
   python src/step1.py
   ```

3. **Chunk Management**:
   ```bash
   python src/step2.py
   ```

4. **Exports and Scale Bars**:
   ```bash
   python src/step3.py
   ```

5. **Final Exports**:
   ```bash
   python src/step4.py
   ```

## Status Tracking

The workflow uses a status tracking system to monitor progress:

1. **Status Files**:
   - Created in `output/reports/`
   - Named `{project_name}_status.yaml`
   - Tracks progress of each processing step

2. **Status Updates**:
   - Each step updates the status file
   - Includes timestamps and error messages
   - Helps resume interrupted processing

## Notes

- The example uses two transects from the same site (BWR)
- All processing parameters are optimized for coral reef monitoring
- The configuration can be modified for different project needs
- PSX files must be placed in the `data/psx_input/` directory
- The location of final polished outputs can be customized in `analysis_params.yaml` 