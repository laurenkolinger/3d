"""
Step 1: Initial 3D Processing

This script performs the initial 3D reconstruction using Metashape,
according to the configuration specified in analysis_params.yaml.
"""

import os
import logging
import Metashape
from config import (
    DIRECTORIES,
    PROJECT_NAME,
    METASHAPE_DEFAULTS,
    USE_GPU,
    update_tracking,
    get_transect_status
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["reports"], f"step1_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def process_transect(transect_id):
    """
    Process a single transect through initial 3D reconstruction.
    
    Args:
        transect_id (str): The transect identifier
    """
    # Check if already processed
    status = get_transect_status(transect_id)
    if status.get("Step 1 complete", "False") == "True":
        logging.info(f"Transect {transect_id} already processed, skipping...")
        return
    
    try:
        # Create new Metashape document
        doc = Metashape.Document()
        
        # Set up processing parameters
        if USE_GPU:
            Metashape.app.gpu_mask = 2**32 - 1  # Use all available GPUs
        
        # Create new chunk
        chunk = doc.addChunk()
        chunk.label = transect_id
        
        # Add photos from frames directory
        frames_dir = os.path.join(DIRECTORIES["frames"], transect_id)
        if not os.path.exists(frames_dir):
            raise ValueError(f"Frames directory not found: {frames_dir}")
        
        # Get list of frame files
        frame_files = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
        if not frame_files:
            raise ValueError(f"No frame files found in {frames_dir}")
        
        # Add photos to chunk
        chunk.addPhotos([os.path.join(frames_dir, f) for f in frame_files])
        
        # Align photos
        chunk.matchPhotos(
            downscale=METASHAPE_DEFAULTS["quality"],
            generic_preselection=True,
            reference_preselection=False
        )
        
        # Optimize cameras
        chunk.optimizeCameras(
            fit_f=True,
            fit_cx=True,
            fit_cy=True,
            fit_b1=True,
            fit_b2=True,
            fit_k1=True,
            fit_k2=True,
            fit_k3=True,
            fit_k4=True,
            fit_p1=True,
            fit_p2=True,
            fit_p3=True,
            fit_p4=True,
            adaptive_fitting=False
        )
        
        # Build dense cloud
        chunk.buildDenseCloud(
            quality=METASHAPE_DEFAULTS["quality"],
            filter=METASHAPE_DEFAULTS["depth_filtering"],
            max_neighbors=METASHAPE_DEFAULTS["max_neighbors"]
        )
        
        # Build mesh
        chunk.buildModel(
            surface_type=Metashape.Arbitrary,
            interpolation=Metashape.EnabledInterpolation,
            face_count=Metashape.HighFaceCount,
            source_data=Metashape.DenseCloudData
        )
        
        # Save project
        psx_path = os.path.join(DIRECTORIES["psx_input"], f"{transect_id}_step1.psx")
        doc.save(psx_path)
        
        # Update tracking file
        update_tracking(transect_id, {
            "Status": "Step 1 complete",
            "Step 1 complete": "True",
            "PSX file": psx_path,
            "Notes": "Initial 3D reconstruction complete"
        })
        
        logging.info(f"Successfully processed transect {transect_id}")
        
    except Exception as e:
        logging.error(f"Error processing transect {transect_id}: {str(e)}")
        update_tracking(transect_id, {
            "Status": "Error in Step 1",
            "Notes": f"Error: {str(e)}"
        })

def main():
    """Main function to process all transects."""
    # Get list of transect directories
    transect_dirs = [d for d in os.listdir(DIRECTORIES["frames"]) 
                    if os.path.isdir(os.path.join(DIRECTORIES["frames"], d))]
    
    if not transect_dirs:
        logging.error(f"No transect directories found in {DIRECTORIES['frames']}")
        return
    
    logging.info(f"Found {len(transect_dirs)} transects to process")
    
    # Process each transect
    for transect_id in transect_dirs:
        process_transect(transect_id)
    
    logging.info("Initial 3D processing complete")

if __name__ == "__main__":
    main() 