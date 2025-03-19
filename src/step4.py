"""
Step 4: Final Exports and Cleanup

This script performs final exports and cleanup operations,
according to the configuration specified in analysis_params.yaml.
"""

import os
import shutil
import logging
import Metashape
from config import (
    DIRECTORIES,
    PROJECT_NAME,
    update_tracking,
    get_transect_status
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

def process_chunk(chunk, transect_id):
    """
    Process a single chunk for final exports.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        transect_id (str): The transect identifier
    """
    # Check if already processed
    status = get_transect_status(transect_id)
    if status.get("Step 4 complete", "False") == "True":
        logging.info(f"Transect {transect_id} already processed, skipping...")
        return
    
    try:
        # Export final orthomosaic with higher resolution
        if chunk.orthomosaic:
            ortho_path = os.path.join(DIRECTORIES["orthomosaics"], f"{transect_id}_ortho_final.tif")
            chunk.exportOrthomosaic(
                ortho_path,
                resolution=0.0005,  # 0.5mm resolution
                save_alpha=True,
                save_world=True,
                save_xyz=True
            )
            logging.info(f"Exported final orthomosaic to {ortho_path}")
        
        # Export final model with higher quality
        if chunk.model:
            model_path = os.path.join(DIRECTORIES["models"], f"{transect_id}_model_final.obj")
            chunk.exportModel(
                model_path,
                texture_format=Metashape.ImageFormatJPEG,
                save_texture=True,
                save_uv=True,
                save_normals=True,
                save_colors=True,
                texture_size=4096  # Higher resolution textures
            )
            logging.info(f"Exported final model to {model_path}")
        
        # Export point cloud
        if chunk.dense_cloud:
            cloud_path = os.path.join(DIRECTORIES["point_clouds"], f"{transect_id}_cloud.las")
            chunk.exportPoints(
                cloud_path,
                format=Metashape.PointsFormatLAS,
                save_colors=True,
                save_normals=True
            )
            logging.info(f"Exported point cloud to {cloud_path}")
        
        # Update tracking file
        update_tracking(transect_id, {
            "Status": "Step 4 complete",
            "Step 4 complete": "True",
            "Final Orthomosaic": os.path.join(DIRECTORIES["orthomosaics"], f"{transect_id}_ortho_final.tif"),
            "Final Model": os.path.join(DIRECTORIES["models"], f"{transect_id}_model_final.obj"),
            "Point Cloud": os.path.join(DIRECTORIES["point_clouds"], f"{transect_id}_cloud.las"),
            "Notes": "Final exports complete"
        })
        
        logging.info(f"Successfully processed chunk for transect {transect_id}")
        
    except Exception as e:
        logging.error(f"Error processing chunk for transect {transect_id}: {str(e)}")
        update_tracking(transect_id, {
            "Status": "Error in Step 4",
            "Notes": f"Error: {str(e)}"
        })

def process_site(site_id):
    """
    Process all chunks in a site project.
    
    Args:
        site_id (str): The site identifier
    """
    try:
        # Open site project
        psx_path = os.path.join(DIRECTORIES["psx_output"], f"{site_id}_step2.psx")
        if not os.path.exists(psx_path):
            logging.error(f"Step 2 project not found for site {site_id}")
            return
        
        doc = Metashape.Document()
        doc.open(psx_path)
        
        # Process each chunk
        for chunk in doc.chunks:
            transect_id = chunk.label
            process_chunk(chunk, transect_id)
        
        # Save project
        doc.save(psx_path)
        logging.info(f"Successfully processed all chunks for site {site_id}")
        
    except Exception as e:
        logging.error(f"Error processing site {site_id}: {str(e)}")

def cleanup_processing_files():
    """Clean up temporary processing files."""
    try:
        # Remove temporary frame directories
        for transect_dir in os.listdir(DIRECTORIES["frames"]):
            if transect_dir.startswith("temp_"):
                shutil.rmtree(os.path.join(DIRECTORIES["frames"], transect_dir))
                logging.info(f"Removed temporary directory: {transect_dir}")
        
        # Remove temporary PSX files
        for psx_file in os.listdir(DIRECTORIES["psx_output"]):
            if psx_file.endswith("_temp.psx"):
                os.remove(os.path.join(DIRECTORIES["psx_output"], psx_file))
                logging.info(f"Removed temporary PSX file: {psx_file}")
        
        logging.info("Cleanup complete")
        
    except Exception as e:
        logging.error(f"Error during cleanup: {str(e)}")

def main():
    """Main function to process all sites and perform cleanup."""
    # Get list of site projects
    site_projects = [f for f in os.listdir(DIRECTORIES["psx_output"]) 
                    if f.endswith('_step2.psx')]
    
    if not site_projects:
        logging.error(f"No site projects found in {DIRECTORIES['psx_output']}")
        return
    
    # Process each site
    for project_file in site_projects:
        site_id = project_file.replace('_step2.psx', '')
        logging.info(f"Processing site {site_id}")
        process_site(site_id)
    
    # Clean up temporary files
    cleanup_processing_files()
    
    logging.info("Final exports and cleanup complete")

if __name__ == "__main__":
    main() 