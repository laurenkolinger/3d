import Metashape
import os
import pandas as pd

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

# Get the directory one level above the project directory and read in the csv. 
project_dir = os.path.dirname(doc.path)
template_dir = os.path.join(project_dir, "../..")
csv_file_path = os.path.join(template_dir, "00_list.csv")

# Read the CSV file
df = pd.read_csv(csv_file_path)

# Create the reports and orthomosaics directories if they don't exist
report_dir = os.path.join(project_dir, "..", "reports")
orthomosaic_dir = os.path.join(project_dir, "..", "orthomosaics")
model_dir = os.path.join(project_dir, "..", "models")
os.makedirs(report_dir, exist_ok=True)
os.makedirs(orthomosaic_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

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
        
    # Get the directory and file paths from the CSV
    matching_rows = df.loc[df['psx_finalname'] == destination]
    
    final_dir = df.loc[df['psx_finalname'] == destination, 'psx_finaldir'].values[0]
    dest_project_path = os.path.join(template_dir, final_dir, destination)

    # Check if the project exists, and open it if it does
    if os.path.exists(dest_project_path):
        doc = Metashape.Document()
        doc.open(dest_project_path, read_only=False)
        print(f"Opened project: {dest_project_path}")
    else:
        print(f"Project not found: {dest_project_path}")
        continue
    
    # Get the project directory
    project_dir = os.path.dirname(doc.path)
    
    # Iterate over each chunk in the project
    for chunk in doc.chunks:
        # print({chunk})
        
        # scale the model
        add_scale_bars(chunk, hascodedscales)
        
        # remove small components 
        remove_small_components(chunk)

        # Generate and export orthomosaic
        # chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ModelData)
        # orthomosaic_file_path = os.path.join(orthomosaic_dir, f"{chunk.label}_orthomosaic.tif")
        
        # Build orthomosaic if it hasn't been built yet
        if not chunk.orthomosaic:
            print("Building orthomosaic...")
            chunk.buildOrthomosaic(
                surface_data=Metashape.DataSource.ModelData,
                blending_mode=Metashape.BlendingMode.MosaicBlending,
                fill_holes=True
            )
            
            chunk.orthomosaic.updateRenderData()
            doc.save()   
                 
        # Set up the output path
        ortho_path = os.path.join(orthomosaic_dir, f"{chunk.label}_orthomosaic.tif")
        #ortho_path = os.path.join(output_dir, "orthomosaic_tiled.tif")
    
        # Set up compression parameters
        compression = Metashape.ImageCompression()
        compression.tiff_tiled = True
        compression.tiff_overviews = True
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionLZW  # Changed to LZW compression
    
        print("Exporting tiled orthomosaic...")
        try:
            chunk.exportRaster(
                path=ortho_path,
                resolution=0,  # Use original resolution
                source_data=Metashape.DataSource.OrthomosaicData,
                image_format=Metashape.ImageFormatTIFF,
                image_compression=compression,
                white_background=True,
                tile_width=2048,        # Reduced tile size
                tile_height=2048,       # Reduced tile size
                split_in_blocks=True,   # Enable tiled export
                save_world=True,        # Save world file
                save_scheme=True,       # Save tile scheme files
                raster_transform=Metashape.RasterTransformType.RasterTransformNone
            )
            print(f"Tiled orthomosaic exported to: {ortho_path}")
        
        except RuntimeError as e:
            print(f"Error during export: {str(e)}")
            print("Trying alternative export settings...")
        
            # Try alternative export with different settings
            try:
                chunk.exportRaster(
                    path=ortho_path,
                    resolution=0,
                    source_data=Metashape.DataSource.OrthomosaicData,
                    image_format=Metashape.ImageFormatTIFF,
                    split_in_blocks=True,
                    tile_width=2048,
                    tile_height=2048,
                    save_world=True,
                    white_background=True
                )
                print(f"Tiled orthomosaic exported successfully with alternative settings to: {ortho_path}")
            except Exception as e2:
                print(f"Alternative export also failed: {str(e2)}")
        
        print(f"Orthomosaic exported to: {orthomosaic_file_path}")
        
        # Export textured model
        model_file_path = os.path.join(model_dir, f"{chunk.label}_textured_model", f"{chunk.label}_textured_model.obj")
        chunk.exportModel(path=model_file_path, binary=False, format = Metashape.ModelFormatOBJ, texture_format=Metashape.ImageFormatTIFF, save_texture=True)
        print(f"Textured model exported to: {model_file_path}")
        
        # Generate report
        report_file_path = os.path.join(report_dir,f"{chunk.label}_report.pdf")
        chunk.exportReport(report_file_path, title = f"{chunk.label}")
    
        # Save the project
        doc.save()
        
    print(f"Processing completed for project: {destination}")

print("All processing completed successfully.")
