"""
Step 3: Model Processing and Exports

This script:
1. Adds scale bars to the model (if coded targets are present)
2. Removes small disconnected components
3. Exports orthomosaic
4. Exports textured model
5. Exports report
6. Saves the project
"""

import os
import logging
import Metashape
import pandas as pd
from config import (
    DIRECTORIES,
    PROJECT_NAME,
    METASHAPE_DEFAULTS,
    get_tracking_files
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["reports"], f"step3_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def find_marker_by_label(chunk, label):
    """
    Find a marker in the chunk by its label.
    
    Args:
        chunk (Metashape.Chunk): The chunk to search in
        label (str): The marker label to find
        
    Returns:
        Metashape.Marker or None: The found marker or None if not found
    """
    for marker in chunk.markers:
        if marker.label == label:
            return marker
    return None

def add_scale_bars(chunk, has_coded_scales, scale_bars):
    """
    Add scale bars to the model.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        has_coded_scales (bool): Whether coded scales are present
        scale_bars (list): List of scale bar definitions (start_marker, end_marker, distance)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not has_coded_scales:
        logging.info("Coded scales are not present. Skipping scale bar addition.")
        return True
    
    try:
        # Detect circular 20-bit markers
        chunk.detectMarkers(target_type=Metashape.TargetType.CircularTarget20bit)
        
        scale_bars_added = 0
        for scale_bar_def in scale_bars:
            start_marker = find_marker_by_label(chunk, scale_bar_def["start_marker"])
            end_marker = find_marker_by_label(chunk, scale_bar_def["end_marker"])
            
            if start_marker and end_marker:
                scale_bar = chunk.addScalebar(start_marker, end_marker)
                scale_bar.reference.distance = scale_bar_def["distance"]
                scale_bars_added += 1
                logging.info(f"Added scale bar between {scale_bar_def['start_marker']} and {scale_bar_def['end_marker']}")
            else:
                logging.warning(f"Could not find markers for {scale_bar_def['start_marker']} and/or {scale_bar_def['end_marker']}")
        
        # Refresh the region and save the project
        if scale_bars_added > 0:
            chunk.updateTransform()
            logging.info(f"Added {scale_bars_added} scale bars to chunk {chunk.label}")
            return True
        else:
            logging.warning(f"No scale bars added to chunk {chunk.label}")
            return False
            
    except Exception as e:
        logging.error(f"Error adding scale bars: {str(e)}")
        return False

def remove_small_components(chunk, min_faces=100):
    """
    Remove small disconnected components from the model.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        min_faces (int): Minimum number of faces for a component to be kept
        
    Returns:
        int: Number of components removed
    """
    # Ensure there's a model in the chunk
    if not chunk.model:
        logging.warning("No model found in the chunk. Cannot remove small components.")
        return 0

    logging.info("Starting component analysis...")
    
    # Get the initial number of components
    num_components_before = chunk.model.statistics().components
    
    if num_components_before <= 1:
        logging.info("Only one component found. No removal necessary.")
        return 0
    
    # Remove small components (keeping largest 1%)
    chunk.model.removeComponents(99)
    
    # Get the final number of components
    num_components_after = chunk.model.statistics().components
    
    num_removed = num_components_before - num_components_after
       
    logging.info(f"Removed {num_removed} components. Model now has {num_components_after} components.")
    return num_removed

def export_orthomosaic(chunk, output_dir, compression):
    """
    Build and export orthomosaic.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        output_dir (str): Directory to save the orthomosaic
        compression (Metashape.ImageCompression): Compression settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Build orthomosaic if it hasn't been built yet
        if not chunk.orthomosaic:
            logging.info("Building orthomosaic...")
            chunk.buildOrthomosaic(
                surface_data=Metashape.DataSource.ModelData,
                blending_mode=getattr(Metashape.BlendingMode, METASHAPE_DEFAULTS["blending_mode"]),
                fill_holes=METASHAPE_DEFAULTS["fill_holes"]
            )
            
            chunk.orthomosaic.updateRenderData()
                 
        # Set up the output path
        ortho_path = os.path.join(output_dir, f"{chunk.label}_orthomosaic.tif")
        
        logging.info("Exporting tiled orthomosaic...")
        try:
            chunk.exportRaster(
                path=ortho_path,
                resolution=METASHAPE_DEFAULTS["resolution"],
                source_data=Metashape.DataSource.OrthomosaicData,
                image_format=Metashape.ImageFormatTIFF,
                image_compression=compression,
                white_background=True,
                tile_width=METASHAPE_DEFAULTS["tile_width"],
                tile_height=METASHAPE_DEFAULTS["tile_height"],
                split_in_blocks=True,
                save_world=METASHAPE_DEFAULTS["save_world"],
                save_scheme=True,
                raster_transform=Metashape.RasterTransformType.RasterTransformNone
            )
            logging.info(f"Tiled orthomosaic exported to: {ortho_path}")
            return True
        
        except RuntimeError as e:
            logging.error(f"Error during export: {str(e)}")
            logging.warning("Trying alternative export settings...")
        
            # Try alternative export with different settings
            try:
                chunk.exportRaster(
                    path=ortho_path,
                    resolution=METASHAPE_DEFAULTS["resolution"],
                    source_data=Metashape.DataSource.OrthomosaicData,
                    image_format=Metashape.ImageFormatTIFF,
                    split_in_blocks=True,
                    tile_width=METASHAPE_DEFAULTS["tile_width"],
                    tile_height=METASHAPE_DEFAULTS["tile_height"],
                    save_world=METASHAPE_DEFAULTS["save_world"],
                    white_background=True
                )
                logging.info(f"Tiled orthomosaic exported successfully with alternative settings to: {ortho_path}")
                return True
            except Exception as e2:
                logging.error(f"Alternative export also failed: {str(e2)}")
                return False
    
    except Exception as e:
        logging.error(f"Error building/exporting orthomosaic: {str(e)}")
        return False

def export_model(chunk, output_dir):
    """
    Export textured model.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        output_dir (str): Directory to save the model
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create subdirectory for model files
        model_subdir = os.path.join(output_dir, f"{chunk.label}_textured_model")
        os.makedirs(model_subdir, exist_ok=True)
        
        # Set model export path
        model_path = os.path.join(model_subdir, f"{chunk.label}_textured_model.obj")
        
        # Export model
        chunk.exportModel(
            path=model_path,
            binary=False,
            format=Metashape.ModelFormatOBJ,
            texture_format=getattr(Metashape, f"ImageFormat{METASHAPE_DEFAULTS['texture_format'].upper()}"),
            save_texture=METASHAPE_DEFAULTS["save_texture"],
            save_uv=METASHAPE_DEFAULTS["save_uv"],
            save_normals=METASHAPE_DEFAULTS["save_normals"],
            save_colors=METASHAPE_DEFAULTS["save_colors"]
        )
        
        logging.info(f"Textured model exported to: {model_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error exporting model: {str(e)}")
        return False

def export_report(chunk, output_dir):
    """
    Export processing report.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        output_dir (str): Directory to save the report
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        report_path = os.path.join(output_dir, f"{chunk.label}_report.pdf")
        chunk.exportReport(report_path, title=f"{chunk.label}")
        logging.info(f"Report exported to: {report_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error exporting report: {str(e)}")
        return False

def main():
    """Main function to process models and create exports."""
    # Open the existing document if running in Metashape GUI
    if Metashape.app.document:
        doc = Metashape.app.document
    else:
        doc = Metashape.Document()
    
    # Get the project directory
    project_dir = DIRECTORIES["base"]
    
    # Create output directories if they don't exist
    report_dir = os.path.join(project_dir, DIRECTORIES["reports"])
    orthomosaic_dir = os.path.join(project_dir, DIRECTORIES["orthomosaics"])
    model_dir = os.path.join(project_dir, DIRECTORIES["models"])
    
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(orthomosaic_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    # Load configuration
    has_coded_scales = METASHAPE_DEFAULTS.get("has_coded_scales", False)
    scale_bars = METASHAPE_DEFAULTS.get("scale_bars", [])
    
    # Set up compression for orthomosaic export
    compression = Metashape.ImageCompression()
    compression.tiff_tiled = True
    compression.tiff_overviews = True
    
    # Set compression type based on configuration
    compression_type = METASHAPE_DEFAULTS.get("compression", "LZW")
    if compression_type == "LZW":
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionLZW
    elif compression_type == "JPEG":
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionJPEG
    elif compression_type == "Packbits":
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionPackbits
    else:
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionNone
    
    # Get tracking files to determine which projects to process
    tracking_files = get_tracking_files()
    
    if not tracking_files:
        logging.error("No tracking files found. Run step1.py and step2.py first.")
        return
    
    # Create or load tracking DataFrame
    df = pd.DataFrame()
    for tracking_file in tracking_files:
        tracking_data = pd.read_csv(tracking_file)
        df = pd.concat([df, tracking_data])
    
    # Find site projects from step2
    if "psx_finalname" in df.columns and "psx_finaldir" in df.columns:
        site_projects = df[["psx_finalname", "psx_finaldir"]].drop_duplicates()
        
        # Process each site project
        for _, row in site_projects.iterrows():
            project_path = os.path.join(project_dir, row["psx_finaldir"], row["psx_finalname"])
            
            if not os.path.exists(project_path):
                logging.warning(f"Project not found: {project_path}")
                continue
            
            logging.info(f"Processing project: {project_path}")
            
            # Open the project
            doc = Metashape.Document()
            doc.open(project_path, read_only=False)
            
            # Process each chunk in the project
            for chunk in doc.chunks:
                logging.info(f"Processing chunk: {chunk.label}")
                
                # Add scale bars
                if has_coded_scales:
                    add_scale_bars(chunk, has_coded_scales, scale_bars)
                
                # Remove small components
                if METASHAPE_DEFAULTS.get("remove_small_components", True):
                    remove_small_components(chunk, METASHAPE_DEFAULTS.get("min_faces", 100))
                
                # Export orthomosaic
                export_orthomosaic(chunk, orthomosaic_dir, compression)
                
                # Export textured model
                export_model(chunk, model_dir)
                
                # Export report
                export_report(chunk, report_dir)
            
            # Save the project
            doc.save()
            logging.info(f"Saved project: {project_path}")
    else:
        # If DataFrame doesn't have the expected columns, look for projects directly
        psx_finaldir = DIRECTORIES.get("psx_output", "05_outputs/psx")
        psx_dir_path = os.path.join(project_dir, psx_finaldir)
        
        if os.path.exists(psx_dir_path):
            project_files = [f for f in os.listdir(psx_dir_path) if f.endswith('.psx')]
            
            for project_file in project_files:
                project_path = os.path.join(psx_dir_path, project_file)
                logging.info(f"Processing project: {project_path}")
                
                # Open the project
                doc = Metashape.Document()
                doc.open(project_path, read_only=False)
                
                # Process each chunk in the project
                for chunk in doc.chunks:
                    logging.info(f"Processing chunk: {chunk.label}")
                    
                    # Add scale bars
                    if has_coded_scales:
                        add_scale_bars(chunk, has_coded_scales, scale_bars)
                    
                    # Remove small components
                    if METASHAPE_DEFAULTS.get("remove_small_components", True):
                        remove_small_components(chunk, METASHAPE_DEFAULTS.get("min_faces", 100))
                    
                    # Export orthomosaic
                    export_orthomosaic(chunk, orthomosaic_dir, compression)
                    
                    # Export textured model
                    export_model(chunk, model_dir)
                    
                    # Export report
                    export_report(chunk, report_dir)
                
                # Save the project
                doc.save()
                logging.info(f"Saved project: {project_path}")
        else:
            logging.error(f"PSX output directory not found: {psx_dir_path}")
    
    logging.info("All model processing and exports completed successfully.")

if __name__ == "__main__":
    main() 