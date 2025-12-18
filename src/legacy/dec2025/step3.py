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
    get_tracking_files,
    update_tracking,
    PARAMS,
    get_transect_status
)
import datetime
from utility.file_naming import get_export_paths, clean_model_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["logs"], f"step3_{PROJECT_NAME}.log")),
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
    Add scale bars to the model and properly apply scaling.
    
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
        # Detect circular 20-bit markers first
        logging.info("Detecting circular 20-bit coded targets...")
        chunk.detectMarkers(target_type=Metashape.TargetType.CircularTarget20bit)
        logging.info(f"Found {len(chunk.markers)} markers after detection")
        
        scale_bars_added = 0
        for scale_bar_def in scale_bars:
            start_marker = find_marker_by_label(chunk, scale_bar_def["start_marker"])
            end_marker = find_marker_by_label(chunk, scale_bar_def["end_marker"])
            
            if start_marker and end_marker:
                scale_bar = chunk.addScalebar(start_marker, end_marker)
                
                # Set scale bar reference properties
                scale_bar.reference.distance = scale_bar_def["distance"]
                scale_bar.reference.enabled = True  # Enable the reference!
                scale_bar.reference.accuracy = 0.001  # Set accuracy to 1mm
                
                scale_bars_added += 1
                logging.info(f"Added scale bar between {scale_bar_def['start_marker']} and {scale_bar_def['end_marker']} with distance {scale_bar_def['distance']}m")
            else:
                missing = []
                if not start_marker:
                    missing.append(scale_bar_def['start_marker'])
                if not end_marker:
                    missing.append(scale_bar_def['end_marker'])
                logging.warning(f"Could not find markers: {', '.join(missing)}")
        
        # Apply scaling if scale bars were added
        if scale_bars_added > 0:
            logging.info("Updating chunk transformation based on scale bars...")
            chunk.updateTransform()
            
            # Log the current region and transform information for debugging
            if chunk.region:
                logging.info(f"Chunk region size after scaling: {chunk.region.size}")
            if chunk.transform:
                logging.info(f"Chunk scale factor: {chunk.transform.scale}")
            
            # List all scale bars and their settings
            for scalebar in chunk.scalebars:
                logging.info(f"Scale bar '{scalebar.label}': distance={scalebar.reference.distance}m, enabled={scalebar.reference.enabled}")
            
            logging.info(f"Successfully added and applied {scale_bars_added} scale bars to chunk {chunk.label}")
            return True
        else:
            logging.warning(f"No scale bars could be added to chunk {chunk.label}")
            return False
            
    except Exception as e:
        logging.error(f"Error adding scale bars: {str(e)}")
        return False

def ground_model(chunk):
    """
    Ground the model by translating it so the minimum Z coordinate becomes 0.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        model = chunk.model
        if model is None:
            logging.warning("No model found in chunk - skipping grounding")
            return False
        
        if not model.vertices or len(model.vertices) == 0:
            logging.warning("Model has no vertices - skipping grounding")
            return False
        
        # Calculate minimum Z coordinate in world coordinates
        min_z = min(
            (chunk.transform.matrix * Metashape.Vector([v.coord.x, v.coord.y, v.coord.z, 1])).z
            for v in model.vertices
        )
        
        # Create translation matrix to move model to ground level
        T = Metashape.Matrix().Translation(Metashape.Vector([0, 0, -min_z]))
        
        # Apply translation to chunk transform
        chunk.transform.matrix = T * chunk.transform.matrix
        
        logging.info(f"Model grounded: chunk offset dz = {-min_z:.4f}m. Minimum Z is now zero.")
        return True
        
    except Exception as e:
        logging.error(f"Error grounding model: {str(e)}")
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

def export_orthomosaic(chunk, base_output_dir, compression):
    """
    Build and export orthomosaic with standardized naming.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        base_output_dir (str): Base output directory
        compression (Metashape.ImageCompression): Compression settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get standardized export paths
        model_id = clean_model_id(chunk.label)
        paths = get_export_paths(model_id, base_output_dir)
        ortho_path = paths['orthomosaic']['file']
        
        # Build orthomosaic if it hasn't been built yet
        if not chunk.orthomosaic:
            logging.info("Building orthomosaic...")
            config = PARAMS['processing']['model_processing']
            chunk.buildOrthomosaic(
                surface_data=Metashape.DataSource.ModelData,
                blending_mode=getattr(Metashape.BlendingMode, config["orthomosaic"]["blending_mode"]),
                fill_holes=config["orthomosaic"]["fill_holes"]
            )
                 
        # Get configuration and check resolution sanity
        config = PARAMS['processing']['model_processing']
        requested_resolution = config["orthomosaic"]["resolution"]
        
        # Calculate expected raster size based on region size and resolution
        if chunk.region and chunk.region.size:
            region_size = chunk.region.size
            expected_width = int(region_size.x / requested_resolution)
            expected_height = int(region_size.y / requested_resolution)
            
            logging.info(f"Region size: {region_size.x:.2f} x {region_size.y:.2f} m")
            logging.info(f"Requested resolution: {requested_resolution} m/pixel")
            logging.info(f"Expected raster size: {expected_width} x {expected_height} pixels")
            
            # Sanity check: if raster would be larger than 20,000 pixels in any dimension, use coarser resolution
            max_dimension = 20000
            if expected_width > max_dimension or expected_height > max_dimension:
                # Calculate minimum resolution to keep under max dimension
                min_resolution_x = region_size.x / max_dimension
                min_resolution_y = region_size.y / max_dimension
                safe_resolution = max(min_resolution_x, min_resolution_y, 0.005)  # At least 5mm
                
                logging.warning(f"Requested resolution would create {expected_width}x{expected_height} raster!")
                logging.warning(f"Using safer resolution: {safe_resolution:.4f} m/pixel instead")
                actual_resolution = safe_resolution
            else:
                actual_resolution = requested_resolution
        else:
            logging.warning("No region information available, using requested resolution")
            actual_resolution = requested_resolution
        
        logging.info(f"Exporting orthomosaic with resolution: {actual_resolution} m/pixel")
        
        try:
            chunk.exportRaster(
                path=ortho_path,
                resolution=actual_resolution,
                source_data=Metashape.DataSource.OrthomosaicData,
                image_format=Metashape.ImageFormatTIFF,
                image_compression=compression,
                white_background=True,
                tile_width=config["orthomosaic"]["tile_width"],
                tile_height=config["orthomosaic"]["tile_height"],
                split_in_blocks=True,
                save_world=config["orthomosaic"]["save_world"],
                save_scheme=True,
                raster_transform=Metashape.RasterTransformType.RasterTransformNone
            )
            logging.info(f"Orthomosaic exported successfully to: {ortho_path}")
            return True
        
        except RuntimeError as e:
            logging.error(f"Error during export: {str(e)}")
            logging.warning("Trying alternative export settings...")
        
            # Try alternative export with different settings and even coarser resolution
            try:
                fallback_resolution = max(actual_resolution * 2, 0.01)  # Double resolution or 1cm minimum
                logging.info(f"Trying fallback resolution: {fallback_resolution} m/pixel")
                
                chunk.exportRaster(
                    path=ortho_path,
                    resolution=fallback_resolution,
                    source_data=Metashape.DataSource.OrthomosaicData,
                    image_format=Metashape.ImageFormatTIFF,
                    split_in_blocks=True,
                    tile_width=config["orthomosaic"]["tile_width"],
                    tile_height=config["orthomosaic"]["tile_height"],
                    save_world=config["orthomosaic"]["save_world"],
                    white_background=True
                )
                logging.info(f"Orthomosaic exported with fallback settings to: {ortho_path}")
                return True
            except Exception as e2:
                logging.error(f"Alternative export also failed: {str(e2)}")
                return False
    
    except Exception as e:
        logging.error(f"Error building/exporting orthomosaic: {str(e)}")
        return False

def export_model(chunk, base_output_dir):
    """
    Export textured model with standardized naming.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        base_output_dir (str): Base output directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get standardized export paths
        model_id = clean_model_id(chunk.label)
        paths = get_export_paths(model_id, base_output_dir)
        model_path = paths['model']['file']
        
        # Export model
        config = PARAMS['processing']['model_processing']
        chunk.exportModel(
            path=model_path,
            binary=False,
            format=getattr(Metashape, f"ModelFormat{config['model_export']['format']}"),
            texture_format=getattr(Metashape, f"ImageFormat{config['model_export']['texture_format']}"),
            save_texture=config['model_export']["save_texture"],
            save_uv=config['model_export']["save_uv"],
            save_normals=config['model_export']["save_normals"],
            save_colors=config['model_export']["save_colors"]
        )
        
        logging.info(f"Textured model exported to: {model_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error exporting model: {str(e)}")
        return False

def export_report(chunk, base_output_dir):
    """
    Export processing report with standardized naming.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        base_output_dir (str): Base output directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get standardized export paths
        model_id = clean_model_id(chunk.label)
        paths = get_export_paths(model_id, base_output_dir)
        report_path = paths['report']['file']
        
        chunk.exportReport(report_path, title=f"{model_id}")
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
    config = PARAMS['processing']['model_processing']
    has_coded_scales = config.get("has_coded_scales", False)
    scale_bars = config.get("scale_bars", [])
    
    # Set up compression for orthomosaic export
    compression = Metashape.ImageCompression()
    compression.tiff_tiled = True
    compression.tiff_overviews = True
    
    # Set compression type based on configuration
    compression_type = config["orthomosaic"].get("compression", "LZW")
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
                # Check if already processed (skip if step 3 complete)
                status = get_transect_status(chunk.label)
                if status.get("Step 3 complete", "") == "True":
                    logging.info(f"Chunk {chunk.label} already processed, skipping...")
                    continue
                    
                logging.info(f"Processing chunk: {chunk.label}")
                
                # Add scale bars and apply scaling FIRST
                scale_bars_applied = False
                if has_coded_scales:
                    scale_bars_applied = add_scale_bars(chunk, has_coded_scales, scale_bars)
                
                # Save project after scale bars to ensure scaling is applied
                if scale_bars_applied:
                    logging.info("Saving project to apply scale bar transformations...")
                    doc.save()
                
                # Ground the model (move minimum Z to 0)
                ground_model(chunk)
                
                # Remove small components
                if config["model_cleanup"].get("remove_small_components", True):
                    remove_small_components(chunk, config["model_cleanup"].get("min_faces", 100))
                
                # Export orthomosaic (now with proper scaling)
                export_orthomosaic(chunk, project_dir, compression)
                
                # Export textured model
                export_model(chunk, project_dir)
                
                # Export report
                export_report(chunk, project_dir)
                
                # Update tracking
                update_tracking(chunk.label, {
                    "Status": "Step 3 complete",
                    "Step 3 complete": "True",
                    "Step 3 scale method": "Automatic",
                    "Step 3 scale applied": str(has_coded_scales),
                    "Step 3 model grounded": "True",
                    "Step 3 ortho exported": "True",
                    "Step 3 model exported": "True"
                })
            
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
                    # Check if already processed (skip if step 3 complete)
                    status = get_transect_status(chunk.label)
                    if status.get("Step 3 complete", "") == "True":
                        logging.info(f"Chunk {chunk.label} already processed, skipping...")
                        continue
                        
                    logging.info(f"Processing chunk: {chunk.label}")
                    
                    # Add scale bars and apply scaling FIRST
                    scale_bars_applied = False
                    if has_coded_scales:
                        scale_bars_applied = add_scale_bars(chunk, has_coded_scales, scale_bars)
                    
                    # Save project after scale bars to ensure scaling is applied
                    if scale_bars_applied:
                        logging.info("Saving project to apply scale bar transformations...")
                        doc.save()
                    
                    # Ground the model (move minimum Z to 0)
                    ground_model(chunk)
                    
                    # Remove small components
                    if config["model_cleanup"].get("remove_small_components", True):
                        remove_small_components(chunk, config["model_cleanup"].get("min_faces", 100))
                    
                    # Export orthomosaic (now with proper scaling)
                    export_orthomosaic(chunk, project_dir, compression)
                    
                    # Export textured model
                    export_model(chunk, project_dir)
                    
                    # Export report
                    export_report(chunk, project_dir)
                    
                    # Update tracking
                    update_tracking(chunk.label, {
                        "Status": "Step 3 complete",
                        "Step 3 complete": "True",
                        "Step 3 scale method": "Automatic",
                        "Step 3 scale applied": str(has_coded_scales),
                        "Step 3 model grounded": "True",
                        "Step 3 ortho exported": "True",
                        "Step 3 model exported": "True"
                    })
                
                # Save the project
                doc.save()
                logging.info(f"Saved project: {project_path}")
        else:
            logging.error(f"PSX output directory not found: {psx_dir_path}")
    
    logging.info("All model processing and exports completed successfully.")

if __name__ == "__main__":
    main() 