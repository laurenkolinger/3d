import Metashape
import os
import pandas as pd
import config

# this script
# 1. adds scale bars to the model
# 2. removes small components
# 3. exports orthomosaic
# 4. exports textured model
# 5. exports report
# 6. saves the project

# does it have coded scales? (FIX THIS! IT DOESNT TEST CONDITION PROPERLY)
hascodedscales = False

# Open the existing project
doc = Metashape.app.document

# Get metadata CSV file path
csv_file_path = config.METADATA_CSV

# Read the CSV file
df = pd.read_csv(csv_file_path)

# Get output directories
report_dir = config.OUTPUT_DIRS["reports"]
orthomosaic_dir = config.OUTPUT_DIRS["orthomosaics"]
model_dir = config.OUTPUT_DIRS["models"]

# Ensure the directories exist
config.create_output_directories()

# Function to find a marker by its label (name)
def find_marker_by_label(chunk, label):
    for marker in chunk.markers:
        if marker.label == label:
            return marker
    return None
    
# encapsulates the scale bar addition logic.
def add_scale_bars(chunk, has_coded_scales):
    if has_coded_scales:
        # Detect circular 20-bit markers
        chunk.detectMarkers(target_type=Metashape.TargetType.CircularTarget20bit)
    
        # Define the marker pairs and their distances
        scale_bar_data = [
            ("target 1000", "target 1010", 0.75),
            ("target 1020", "target 1030", 0.75)
        ]
    
        for start_label, end_label, distance in scale_bar_data:
            start_marker = find_marker_by_label(chunk, start_label)
            end_marker = find_marker_by_label(chunk, end_label)
        
            if start_marker and end_marker:
                scale_bar = chunk.addScalebar(start_marker, end_marker)
                scale_bar.reference.distance = distance
                print(f"Added scale bar between {start_label} and {end_label}")
            else:
                print(f"Could not find markers for {start_label} and/or {end_label}")
    
        # Refresh the region and save the project
        chunk.updateTransform()
        doc.save()
    else:
        print("Coded scales are not present. Skipping scale bar addition.")
            
#remove small components             
def remove_small_components(chunk):
    # Ensure there's a model in the chunk
    if not chunk.model:
        print("No model found in the chunk. Please build a model first.")
        return

    print("Starting component analysis...")
    
    # Get the model statistics
    stats = chunk.model.statistics().components
    
    # Get the number of components
    num_components1 = chunk.model.statistics().components
    
    if num_components1 <= 1:
        print("Only one component found. No removal necessary.")
        return
    
    # Remove small components
    chunk.model.removeComponents(99)
    
    num_components2 = chunk.model.statistics().components
    
    num_removed = num_components1-num_components2
       
    print(f"Removed {num_removed} components. Model now has {num_components2}")


# Iterate over unique values of `psx_finalname` in the CSV
for destination in df['psx_finalname'].unique():
    # Get the project path from the CSV file
    matching_rows = df.loc[df['psx_finalname'] == destination]
    
    final_dir = df.loc[df['psx_finalname'] == destination, 'psx_finaldir'].values[0]
    if isinstance(final_dir, str) and final_dir == 'psx_finaldir':
        final_dir = config.OUTPUT_DIRS["psx_output"]
    
    dest_project_path = os.path.join(final_dir, destination)
    
    # Check if the project exists and open it if it does
    if os.path.exists(dest_project_path):
        doc = Metashape.Document()
        doc.open(dest_project_path, read_only=False)
        print(f"Opened project: {dest_project_path}")
    else:
        print(f"Project not found: {dest_project_path}")
        continue
        
    # Iterate over chunks
    for chunk in doc.chunks:
        # Add scale bars
        add_scale_bars(chunk, hascodedscales)
        
        # Remove small components
        remove_small_components(chunk)
        
        # Export orthomosaic
        orthomosaic_path = os.path.join(orthomosaic_dir, f"{chunk.label}_orthomosaic.tif")
        chunk.exportRaster(path=orthomosaic_path, format=Metashape.RasterFormatTIFF)
        print(f"Exported orthomosaic to: {orthomosaic_path}")
        
        # Export textured model
        model_path = os.path.join(model_dir, f"{chunk.label}_model.obj")
        chunk.exportModel(path=model_path, texture_format=Metashape.ImageFormatJPEG)
        print(f"Exported textured model to: {model_path}")
        
        # Export report
        report_path = os.path.join(report_dir, f"{chunk.label}_report.pdf")
        chunk.exportReport(path=report_path)
        print(f"Exported report to: {report_path}")
        
    # Save the project after all operations
    doc.save()
    print(f"Processing completed for project: {destination}")

print("All processing completed successfully.")
