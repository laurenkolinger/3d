"""
Step 3: Exports and Scale Bars

This script exports models and orthomosaics, and adds scale bars,
according to the configuration specified in analysis_params.yaml.
"""

import os
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
        logging.FileHandler(os.path.join(DIRECTORIES["reports"], f"step3_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def process_chunk(chunk, transect_id):
    """
    Process a single chunk for exports and scale bars.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        transect_id (str): The transect identifier
    """
    # Check if already processed
    status = get_transect_status(transect_id)
    if status.get("Step 3 complete", "False") == "True":
        logging.info(f"Transect {transect_id} already processed, skipping...")
        return
    
    try:
        # Check for scale bar markers
        markers = chunk.markers
        if markers:
            logging.info(f"Found {len(markers)} markers for transect {transect_id}")
            
            # Set scale bar distances
            for marker in markers:
                if marker.reference.distance:
                    marker.reference.enabled = True
                    logging.info(f"Enabled scale bar {marker.label} with distance {marker.reference.distance}")
        
        # Remove small components
        if chunk.model:
            chunk.model.removeComponents(
                min_faces=100,  # Minimum number of faces to keep
                min_vertices=50  # Minimum number of vertices to keep
            )
            logging.info("Removed small components from model")
        
        # Export orthomosaic
        if chunk.orthomosaic:
            ortho_path = os.path.join(DIRECTORIES["orthomosaics"], f"{transect_id}_ortho.tif")
            chunk.exportOrthomosaic(
                ortho_path,
                resolution=0.001,  # 1mm resolution
                save_alpha=True,
                save_world=True,
                save_xyz=True
            )
            logging.info(f"Exported orthomosaic to {ortho_path}")
        
        # Export textured model
        if chunk.model:
            model_path = os.path.join(DIRECTORIES["models"], f"{transect_id}_model.obj")
            chunk.exportModel(
                model_path,
                texture_format=Metashape.ImageFormatJPEG,
                save_texture=True,
                save_uv=True,
                save_normals=True,
                save_colors=True
            )
            logging.info(f"Exported model to {model_path}")
        
        # Update tracking file
        update_tracking(transect_id, {
            "Status": "Step 3 complete",
            "Step 3 complete": "True",
            "Orthomosaic": os.path.join(DIRECTORIES["orthomosaics"], f"{transect_id}_ortho.tif"),
            "Model": os.path.join(DIRECTORIES["models"], f"{transect_id}_model.obj"),
            "Notes": "Exports and scale bars complete"
        })
        
        logging.info(f"Successfully processed chunk for transect {transect_id}")
        
    except Exception as e:
        logging.error(f"Error processing chunk for transect {transect_id}: {str(e)}")
        update_tracking(transect_id, {
            "Status": "Error in Step 3",
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

def main():
    """Main function to process all sites."""
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
    
    logging.info("Exports and scale bars complete")

if __name__ == "__main__":
    main() 