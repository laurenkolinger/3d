"""
Step 4: Final Exports and Web Publishing

This script:
1. Prepares decimated models for web viewing
2. Uploads models to Sketchfab
3. Creates final exports at high quality for archiving
"""

import os
import logging
import Metashape
import pandas as pd
from config import (
    DIRECTORIES,
    PROJECT_NAME,
    METASHAPE_DEFAULTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["reports"], f"step4_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def decimate_and_upload(chunk, decimate_vertices, sketchfab_settings):
    """
    Create a decimated version of the model for web viewing and upload to Sketchfab.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        decimate_vertices (int): Target number of vertices for decimation
        sketchfab_settings (dict): Sketchfab settings including API token
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Duplicate the chunk and name it with a "_temp" suffix
        logging.info(f"Duplicating chunk {chunk.label} for decimation")
        temp_chunk = chunk.copy()
        temp_chunk.label = f"{chunk.label}_temp"
        
        # Decimate the model to reduce complexity for web viewing
        logging.info(f"Decimating model to {decimate_vertices} vertices")
        temp_chunk.decimateModel(face_count=decimate_vertices)
        
        # Re-build texture if needed
        if not temp_chunk.model.hasTextures():
            logging.info("Building texture for decimated model")
            temp_chunk.buildTexture(
                texture_size=4096,
                texture_type=Metashape.Model.DiffuseMap,
                blending_mode=getattr(Metashape, METASHAPE_DEFAULTS["blending_mode"]),
                fill_holes=METASHAPE_DEFAULTS["fill_holes"],
                ghosting_filter=METASHAPE_DEFAULTS["ghosting_filter"]
            )
        
        # Set up Sketchfab upload task
        logging.info("Setting up Sketchfab upload")
        publish_task = Metashape.Tasks.PublishData()
        publish_task.service = Metashape.ServiceType.ServiceSketchfab
        publish_task.source_data = Metashape.DataSource.ModelData
        
        # Format the title using template
        title_template = sketchfab_settings.get("title_template", "Model: {chunk_label}")
        publish_task.title = title_template.format(chunk_label=chunk.label)
        
        # Use settings from config
        publish_task.description = sketchfab_settings.get("description", "Generated using Metashape")
        publish_task.tags = sketchfab_settings.get("tags", "3D, model, Metashape, coralreef")
        publish_task.token = sketchfab_settings.get("token", "")
        publish_task.is_draft = sketchfab_settings.get("is_draft", True)
        publish_task.is_private = sketchfab_settings.get("is_private", False)
        
        # Advanced settings
        publish_task.tile_size = 256
        publish_task.min_zoom_level = -1
        publish_task.max_zoom_level = -1
        
        # Apply the publish task to the temp chunk
        logging.info("Uploading to Sketchfab")
        upload_result = publish_task.apply(temp_chunk)
        
        if upload_result:
            logging.info(f"Model {temp_chunk.label} successfully uploaded to Sketchfab")
        else:
            logging.warning(f"Model upload may have failed. Check Sketchfab dashboard.")
        
        # Clean up - delete the temporary chunk
        logging.info(f"Cleaning up temporary chunk {temp_chunk.label}")
        doc = temp_chunk.document
        doc.remove(temp_chunk)
        doc.save()
        
        return True
        
    except Exception as e:
        logging.error(f"Error during decimation/upload: {str(e)}")
        # Try to clean up temporary chunk if it exists
        try:
            if 'temp_chunk' in locals() and temp_chunk and temp_chunk.document:
                doc = temp_chunk.document
                doc.remove(temp_chunk)
                doc.save()
        except:
            pass
        return False

def export_final_assets(chunk, export_settings):
    """
    Export final high-quality assets for archiving.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        export_settings (dict): Export settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directories if they don't exist
        final_dir = os.path.join(DIRECTORIES["final_outputs"], chunk.label)
        os.makedirs(final_dir, exist_ok=True)
        
        # Export high-resolution orthomosaic
        if chunk.orthomosaic:
            ortho_settings = export_settings.get("final_orthomosaic", {})
            ortho_path = os.path.join(final_dir, f"{chunk.label}_orthomosaic_hr.tif")
            
            logging.info(f"Exporting high-resolution orthomosaic to {ortho_path}")
            chunk.exportRaster(
                path=ortho_path,
                resolution=ortho_settings.get("resolution", 0.0005),  # 0.5mm resolution
                source_data=Metashape.DataSource.OrthomosaicData,
                image_format=Metashape.ImageFormatTIFF,
                save_alpha=ortho_settings.get("save_alpha", True),
                save_world=ortho_settings.get("save_world", True),
                save_scheme=True,
                white_background=True
            )
        
        # Export final textured model
        if chunk.model:
            model_settings = export_settings.get("final_model", {})
            model_path = os.path.join(final_dir, f"{chunk.label}_model_hr.obj")
            
            logging.info(f"Exporting high-resolution model to {model_path}")
            chunk.exportModel(
                path=model_path,
                binary=False,
                format=Metashape.ModelFormatOBJ,
                texture_format=getattr(Metashape, f"ImageFormat{model_settings.get('texture_format', 'JPEG').upper()}"),
                texture_size=model_settings.get("texture_size", 8192),  # Higher resolution texture
                save_texture=model_settings.get("save_texture", True),
                save_uv=model_settings.get("save_uv", True),
                save_normals=model_settings.get("save_normals", True),
                save_colors=model_settings.get("save_colors", True)
            )
        
        # Export dense point cloud
        if chunk.dense_cloud:
            cloud_settings = export_settings.get("point_cloud", {})
            cloud_path = os.path.join(final_dir, f"{chunk.label}_dense_cloud.las")
            
            logging.info(f"Exporting dense point cloud to {cloud_path}")
            chunk.exportPointCloud(
                path=cloud_path,
                format=Metashape.PointCloudFormatLAS,
                save_colors=cloud_settings.get("save_colors", True),
                save_normals=cloud_settings.get("save_normals", True)
            )
        
        # Export comprehensive report
        report_path = os.path.join(final_dir, f"{chunk.label}_final_report.pdf")
        logging.info(f"Exporting comprehensive report to {report_path}")
        chunk.exportReport(report_path, title=f"Final Report: {chunk.label}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error exporting final assets: {str(e)}")
        return False

def main():
    """Main function to prepare and upload models to Sketchfab."""
    # Open the existing document if running in Metashape GUI
    if Metashape.app.document:
        doc = Metashape.app.document
        if not doc.path:
            logging.error("No document open. Please open a Metashape project first.")
            return
    else:
        logging.error("This script must be run from within Metashape.")
        return
    
    # Get the project directory
    project_dir = os.path.dirname(doc.path)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.join(DIRECTORIES["base"], DIRECTORIES["final_outputs"]), exist_ok=True)
    
    # Load configuration
    sketchfab_settings = METASHAPE_DEFAULTS.get("sketchfab", {})
    decimate_vertices = METASHAPE_DEFAULTS.get("decimate_vertices", 3000000)
    
    # Create a list to track uploaded chunks
    processed_chunks = []
    
    # Process each chunk in the project
    for chunk in doc.chunks:
        logging.info(f"Processing chunk: {chunk.label}")
        
        # Check if the chunk has a valid model
        if not chunk.model or chunk.model.faces is None or len(chunk.model.faces) == 0:
            logging.warning(f"Chunk {chunk.label} has no valid model. Skipping.")
            continue
        
        # Decimate and upload to Sketchfab
        if "token" in sketchfab_settings and sketchfab_settings["token"]:
            if decimate_and_upload(chunk, decimate_vertices, sketchfab_settings):
                processed_chunks.append(f"{chunk.label} (uploaded to Sketchfab)")
            else:
                logging.warning(f"Failed to upload {chunk.label} to Sketchfab")
        else:
            logging.warning("No Sketchfab API token provided. Skipping upload.")
        
        # Export final assets
        if export_final_assets(chunk, METASHAPE_DEFAULTS):
            processed_chunks.append(f"{chunk.label} (final assets exported)")
        else:
            logging.warning(f"Failed to export final assets for {chunk.label}")
    
    # Save the project
    doc.save()
    
    # Summary
    if processed_chunks:
        logging.info("Successfully processed the following chunks:")
        for chunk_info in processed_chunks:
            logging.info(f"- {chunk_info}")
    else:
        logging.warning("No chunks were successfully processed.")
    
    logging.info("Final exports and web publishing completed successfully.")

if __name__ == "__main__":
    main() 