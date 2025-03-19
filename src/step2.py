"""
Step 2: Chunk Management

This script groups chunks by site and creates new Metashape projects,
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
        logging.FileHandler(os.path.join(DIRECTORIES["reports"], f"step2_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def get_site_from_transect(transect_id):
    """
    Extract site code from transect ID.
    
    Args:
        transect_id (str): The transect identifier (e.g., "TCRMP20240311_3D_BID_T1")
    
    Returns:
        str: The site code (e.g., "BID")
    """
    parts = transect_id.split('_')
    if len(parts) >= 3:
        return parts[2]  # Site code is the third part
    return "unknown"

def process_transect(transect_id, source_doc):
    """
    Process a single transect's chunk.
    
    Args:
        transect_id (str): The transect identifier
        source_doc (Metashape.Document): The source Metashape document
    
    Returns:
        Metashape.Chunk: The processed chunk, or None if not found
    """
    # Find the chunk for this transect
    chunk = None
    for c in source_doc.chunks:
        if c.label == transect_id:
            chunk = c
            break
    
    if not chunk:
        logging.error(f"Chunk not found for transect {transect_id}")
        return None
    
    # Check if already processed
    status = get_transect_status(transect_id)
    if status.get("Step 2 complete", "False") == "True":
        logging.info(f"Transect {transect_id} already processed, skipping...")
        return chunk
    
    try:
        # Check chunk quality
        if len(chunk.cameras) < 10:
            raise ValueError(f"Too few cameras ({len(chunk.cameras)}) in chunk")
        
        # Check alignment quality
        aligned_cameras = sum(1 for camera in chunk.cameras if camera.transform)
        alignment_percentage = (aligned_cameras / len(chunk.cameras)) * 100
        
        if alignment_percentage < 90:
            raise ValueError(f"Poor alignment ({alignment_percentage:.1f}% cameras aligned)")
        
        logging.info(f"Successfully processed chunk for transect {transect_id}")
        return chunk
        
    except Exception as e:
        logging.error(f"Error processing chunk for transect {transect_id}: {str(e)}")
        update_tracking(transect_id, {
            "Status": "Error in Step 2",
            "Notes": f"Error: {str(e)}"
        })
        return None

def process_site(site_id, transect_chunks):
    """
    Create a new Metashape project for a site.
    
    Args:
        site_id (str): The site identifier
        transect_chunks (list): List of (transect_id, chunk) tuples
    """
    try:
        # Create new document
        doc = Metashape.Document()
        
        # Copy chunks
        for transect_id, chunk in transect_chunks:
            if chunk:
                new_chunk = doc.addChunk()
                chunk.copy(new_chunk)
                new_chunk.label = transect_id
        
        # Save project
        psx_path = os.path.join(DIRECTORIES["psx_output"], f"{site_id}_step2.psx")
        doc.save(psx_path)
        
        # Update tracking for all transects
        for transect_id, _ in transect_chunks:
            update_tracking(transect_id, {
                "Status": "Step 2 complete",
                "Step 2 complete": "True",
                "Site PSX file": psx_path,
                "Notes": f"Grouped with site {site_id}"
            })
        
        logging.info(f"Successfully created project for site {site_id}")
        
    except Exception as e:
        logging.error(f"Error creating project for site {site_id}: {str(e)}")
        # Update tracking to indicate error
        for transect_id, _ in transect_chunks:
            update_tracking(transect_id, {
                "Status": "Error in Step 2",
                "Notes": f"Error creating site project: {str(e)}"
            })

def main():
    """Main function to process all transects and group by site."""
    # Get list of transect directories
    transect_dirs = [d for d in os.listdir(DIRECTORIES["frames"]) 
                    if os.path.isdir(os.path.join(DIRECTORIES["frames"], d))]
    
    if not transect_dirs:
        logging.error(f"No transect directories found in {DIRECTORIES['frames']}")
        return
    
    # Group transects by site
    site_groups = {}
    for transect_id in transect_dirs:
        site_id = get_site_from_transect(transect_id)
        if site_id not in site_groups:
            site_groups[site_id] = []
        site_groups[site_id].append(transect_id)
    
    logging.info(f"Found {len(site_groups)} sites to process")
    
    # Process each site
    for site_id, transect_ids in site_groups.items():
        logging.info(f"Processing site {site_id} with {len(transect_ids)} transects")
        
        # Process each transect in this site
        transect_chunks = []
        for transect_id in transect_ids:
            # Open the step1 project for this transect
            psx_path = os.path.join(DIRECTORIES["psx_input"], f"{transect_id}_step1.psx")
            if not os.path.exists(psx_path):
                logging.error(f"Step 1 project not found for transect {transect_id}")
                continue
            
            doc = Metashape.Document()
            doc.open(psx_path)
            
            # Process the chunk
            chunk = process_transect(transect_id, doc)
            if chunk:
                transect_chunks.append((transect_id, chunk))
        
        # Create site project if we have any valid chunks
        if transect_chunks:
            process_site(site_id, transect_chunks)
    
    logging.info("Chunk management complete")

if __name__ == "__main__":
    main() 