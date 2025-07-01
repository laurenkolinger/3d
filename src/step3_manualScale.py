"""
Step 3 Manual Scale: Model Processing and Exports (Manual Scale Bar Workflow)

This script assumes scale bars have been manually added in Metashape GUI and:
1. Skips automatic scale bar creation (assumes manually added)
2. Removes small disconnected components
3. Exports orthomosaic
4. Exports textured model
5. Exports report
6. Saves the project

WORKFLOW: 
1. Run reset_step3.py to clean previous step 3 outputs
2. Manually add scale bars in Metashape GUI
3. Save the PSX project
4. Run this script to complete remaining step 3 operations
"""

import os
import logging
import Metashape
import pandas as pd
from config import (
    DIRECTORIES,
    PROJECT_NAME,
    PARAMS,
    get_tracking_files,
    get_transect_status,
    update_tracking
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["logs"], f"step3_manualScale_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def check_existing_scale_bars(chunk):
    """
    Check if scale bars already exist in the chunk.
    
    Args:
        chunk (Metashape.Chunk): The chunk to check
        
    Returns:
        tuple: (has_scale_bars, scale_bar_count, scale_bar_info)
    """
    scale_bar_count = len(chunk.scalebars)
    scale_bar_info = []
    
    if scale_bar_count > 0:
        logging.info(f"Found {scale_bar_count} existing scale bars in chunk {chunk.label}")
        for i, scalebar in enumerate(chunk.scalebars):
            enabled = scalebar.reference.enabled if scalebar.reference else False
            distance = scalebar.reference.distance if scalebar.reference else "Unknown"
            accuracy = scalebar.reference.accuracy if scalebar.reference else "Unknown"
            
            info = {
                'label': scalebar.label,
                'enabled': enabled,
                'distance': distance,
                'accuracy': accuracy
            }
            scale_bar_info.append(info)
            
            logging.info(f"  Scale bar {i+1}: '{scalebar.label}' - Distance: {distance}m, Enabled: {enabled}, Accuracy: {accuracy}")
        
        return True, scale_bar_count, scale_bar_info
    else:
        logging.warning(f"No existing scale bars found in chunk {chunk.label}")
        logging.warning("This script assumes scale bars have been manually added. Consider:")
        logging.warning("1. Adding scale bars manually in Metashape GUI")
        logging.warning("2. Using regular step3.py for automatic scale bar creation")
        return False, 0, []

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

def export_orthomosaic(chunk, output_dir, compression):
    """
    Build and export orthomosaic with reasonable resolution.
    
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
            config = PARAMS['processing']['model_processing']
            chunk.buildOrthomosaic(
                surface_data=Metashape.DataSource.ModelData,
                blending_mode=getattr(Metashape.BlendingMode, config["orthomosaic"]["blending_mode"]),
                fill_holes=config["orthomosaic"]["fill_holes"]
            )
                 
        # Set up the output path
        ortho_path = os.path.join(output_dir, f"{chunk.label}_orthomosaic_manualScale.tif")
        
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
            logging.info(f"Orthomosaic (manual scale) exported successfully to: {ortho_path}")
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
                logging.info(f"Orthomosaic (manual scale) exported with fallback settings to: {ortho_path}")
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
        model_subdir = os.path.join(output_dir, f"{chunk.label}_textured_model_manualScale")
        os.makedirs(model_subdir, exist_ok=True)
        
        # Set model export path
        model_path = os.path.join(model_subdir, f"{chunk.label}_textured_model_manualScale.obj")
        
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
        
        logging.info(f"Textured model (manual scale) exported to: {model_path}")
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
        report_path = os.path.join(output_dir, f"{chunk.label}_report_manualScale.pdf")
        chunk.exportReport(report_path, title=f"{chunk.label} (Manual Scale)")
        logging.info(f"Report (manual scale) exported to: {report_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error exporting report: {str(e)}")
        return False

def main():
    """Main function to process models and create exports with manual scale workflow."""
    logging.info("="*60)
    logging.info("STEP 3 MANUAL SCALE: Model Processing and Exports")
    logging.info("This script assumes scale bars have been manually added")
    logging.info("="*60)
    
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
            
            try:
                doc.open(project_path, read_only=False)
            except Exception as e:
                logging.error(f"Could not open project {project_path}: {str(e)}")
                continue
            
            # Process each chunk in the project
            for chunk in doc.chunks:
                # Check if already processed (skip if step 3 complete with manual scale)
                status = get_transect_status(chunk.label)
                if status.get("Step 3 complete", "") == "True" and status.get("Step 3 scale method", "") == "Manual":
                    logging.info(f"Chunk {chunk.label} already processed with manual scale, skipping...")
                    continue
                    
                logging.info(f"Processing chunk: {chunk.label} (Manual Scale Workflow)")
                
                # Check for existing scale bars (manual workflow assumes they exist)
                has_scale_bars, scale_bar_count, scale_bar_info = check_existing_scale_bars(chunk)
                
                # Ground the model (move minimum Z to 0)
                ground_model(chunk)
                
                # Remove small components
                if config["model_cleanup"].get("remove_small_components", True):
                    remove_small_components(chunk, config["model_cleanup"].get("min_faces", 100))
                
                # Export orthomosaic (with manual scaling applied)
                ortho_success = export_orthomosaic(chunk, orthomosaic_dir, compression)
                
                # Export textured model
                model_success = export_model(chunk, model_dir)
                
                # Export report
                report_success = export_report(chunk, report_dir)
                
                # Update tracking with manual scale indicators (FIXED: use only existing columns)
                update_tracking(chunk.label, {
                    "Status": "Step 3 complete",
                    "Step 3 complete": "True",
                    "Step 3 scale method": "Manual",
                    "Step 3 scale applied": "True" if scale_bar_count > 0 else "False",
                    "Step 3 model grounded": "True",
                    "Step 3 ortho exported": str(ortho_success),
                    "Step 3 model exported": str(model_success),
                    "Notes": f"Manual scale: {scale_bar_count} scale bars, {sum(1 for sb in scale_bar_info if sb['enabled'])} enabled"
                })
                
                logging.info(f"Completed manual scale processing for chunk {chunk.label}")
            
            # Save the project
            try:
                doc.save()
                logging.info(f"Saved project: {project_path}")
            except Exception as e:
                logging.error(f"Could not save project {project_path}: {str(e)}")
                logging.warning("If file is read-only, run reset_step3.py or use regular step3.py")
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
                
                try:
                    doc.open(project_path, read_only=False)
                except Exception as e:
                    logging.error(f"Could not open project {project_path}: {str(e)}")
                    continue
                
                # Process each chunk in the project
                for chunk in doc.chunks:
                    # Check if already processed (skip if step 3 complete with manual scale)
                    status = get_transect_status(chunk.label)
                    if status.get("Step 3 complete", "") == "True" and status.get("Step 3 scale method", "") == "Manual":
                        logging.info(f"Chunk {chunk.label} already processed with manual scale, skipping...")
                        continue
                        
                    logging.info(f"Processing chunk: {chunk.label} (Manual Scale Workflow)")
                    
                    # Check for existing scale bars (manual workflow assumes they exist)
                    has_scale_bars, scale_bar_count, scale_bar_info = check_existing_scale_bars(chunk)
                    
                    # Ground the model (move minimum Z to 0)
                    ground_model(chunk)
                    
                    # Remove small components
                    if config["model_cleanup"].get("remove_small_components", True):
                        remove_small_components(chunk, config["model_cleanup"].get("min_faces", 100))
                    
                    # Export orthomosaic (with manual scaling applied)
                    ortho_success = export_orthomosaic(chunk, orthomosaic_dir, compression)
                    
                    # Export textured model
                    model_success = export_model(chunk, model_dir)
                    
                    # Export report
                    report_success = export_report(chunk, report_dir)
                    
                    # Update tracking with manual scale indicators (FIXED: use only existing columns)
                    update_tracking(chunk.label, {
                        "Status": "Step 3 complete",
                        "Step 3 complete": "True",
                        "Step 3 scale method": "Manual",
                        "Step 3 scale applied": "True" if scale_bar_count > 0 else "False",
                        "Step 3 model grounded": "True",
                        "Step 3 ortho exported": str(ortho_success),
                        "Step 3 model exported": str(model_success),
                        "Notes": f"Manual scale: {scale_bar_count} scale bars, {sum(1 for sb in scale_bar_info if sb['enabled'])} enabled"
                    })
                    
                    logging.info(f"Completed manual scale processing for chunk {chunk.label}")
                
                # Save the project
                try:
                    doc.save()
                    logging.info(f"Saved project: {project_path}")
                except Exception as e:
                    logging.error(f"Could not save project {project_path}: {str(e)}")
                    logging.warning("If file is read-only, run reset_step3.py or use regular step3.py")
        else:
            logging.error(f"PSX output directory not found: {psx_dir_path}")
    
    logging.info("="*60)
    logging.info("STEP 3 MANUAL SCALE: All processing completed successfully.")
    logging.info("Outputs marked with '_manualScale' suffix to distinguish from automatic workflow.")
    logging.info("="*60)

if __name__ == "__main__":
    main() 