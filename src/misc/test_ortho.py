import Metashape
import os

def build_tiled_ortho(project_path, output_dir):
    """
    Opens a Metashape project and exports a tiled orthomosaic.
    
    Args:
        project_path (str): Full path to the .psx project file
        output_dir (str): Directory where the orthomosaic should be saved
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the project
    doc = Metashape.Document()
    doc.open(project_path, read_only=False)
    print(f"Opened project: {project_path}")
    
    # Get the chunk
    chunk = doc.chunk
    
    # Build orthomosaic if it hasn't been built yet
    if not chunk.orthomosaic:
        print("Building orthomosaic...")
        chunk.buildOrthomosaic(
            surface_data=Metashape.DataSource.ModelData,
            blending_mode=Metashape.BlendingMode.MosaicBlending,
            fill_holes=True
        )
    
    # Set up the output path
    ortho_path = os.path.join(output_dir, "orthomosaic_tiled.tif")
    
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
    
    doc.save()

# Example usage
if __name__ == "__main__":
    # Replace these paths with your test project and output directory
    PROJECT_PATH = r"/Users/laurenkay/UVI Dropbox/SMITH LAB TEAM FOLDER/TCRMP/TCRMP_3D/TCRMP2024_3D/PROCESSING/EGR1_SRD1/05_outputs/psx/TCRMP20241114_3D_EGR.psx"
    OUTPUT_DIR = r"/Users/laurenkay/UVI Dropbox/SMITH LAB TEAM FOLDER/TCRMP/TCRMP_3D/TCRMP2024_3D/PROCESSING/EGR1_SRD1/05_outputs/orthomosaics"
    
    build_tiled_ortho(PROJECT_PATH, OUTPUT_DIR)