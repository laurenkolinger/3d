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
    PARAMS,
    update_tracking,
    get_transect_status,
    get_tracking_files
)
import datetime
import glob
import math
import pandas as pd
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["logs"], f"step1_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

# Maximum number of chunks per PSX file
MAX_CHUNKS_PER_PSX = PARAMS['processing'].get('max_chunks_per_psx', 5)

def process_transect(transect_id, doc=None, psx_path=None):
    """
    Process a single transect through initial 3D reconstruction.
    
    Args:
        transect_id (str): The transect identifier
        doc (Metashape.Document, optional): Existing document to add chunk to
        psx_path (str, optional): Path to save the document
        
    Returns:
        tuple: (success: bool, doc: Metashape.Document, chunk: Metashape.Chunk)
    """
    # Check if already processed
    status = get_transect_status(transect_id)
    if status.get("Step 1 complete", "False") == "True":
        logging.info(f"Model {transect_id} already processed, skipping...")
        return (False, doc, None)
    
    try:
        start_time = datetime.datetime.now()
        
        # Create new Metashape document if none provided
        if doc is None:
            doc = Metashape.Document()
            
            # Set project path if not provided
            if psx_path is None:
                # Create psxraw directory if it doesn't exist
                os.makedirs(DIRECTORIES["psxraw"], exist_ok=True)
                psx_path = os.path.join(DIRECTORIES["psxraw"], f"{transect_id}_step1.psx")
        
        # Set up processing parameters
        if USE_GPU:
            Metashape.app.gpu_mask = 1  # Use first GPU device (correct for Apple Silicon)
            logging.info("GPU acceleration enabled for Apple Silicon")
        
        # Create new chunk
        chunk = doc.addChunk()
        chunk.label = transect_id
        
        Metashape.app.update()

        # Add photos from frames directory
        frames_dir = os.path.join(DIRECTORIES["frames"], transect_id)
        if not os.path.exists(frames_dir):
            raise ValueError(f"Frames directory not found: {frames_dir}")
        
        # Get list of frame files
        frame_files = [f for f in os.listdir(frames_dir) if f.lower().endswith(('.jpg', '.jpeg', '.tif', '.tiff'))]
        if not frame_files:
            raise ValueError(f"No image files found in {frames_dir}")
        
        # Add photos to chunk
        logging.info(f"Adding {len(frame_files)} photos for model {transect_id}")
        chunk.addPhotos([os.path.join(frames_dir, f) for f in frame_files])
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Match photos and align cameras
        logging.info(f"Matching photos for model {transect_id}")
        chunk.matchPhotos(
            downscale=METASHAPE_DEFAULTS["downscale"],
            keypoint_limit=METASHAPE_DEFAULTS["keypoint_limit"],
            tiepoint_limit=METASHAPE_DEFAULTS["tiepoint_limit"],
            generic_preselection=METASHAPE_DEFAULTS["generic_preselection"],
            reference_preselection=METASHAPE_DEFAULTS["reference_preselection"],
            filter_stationary_points=METASHAPE_DEFAULTS["filter_stationary_points"]
        )
        chunk.alignCameras(adaptive_fitting=METASHAPE_DEFAULTS["adaptive_fitting"])
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Select cameras that were not aligned initially
        unaligned_cameras = [camera for camera in chunk.cameras if not camera.transform]
        
        # Reset the alignment for the unaligned cameras
        for camera in unaligned_cameras:
            camera.transform = None


        # Attempt to align the unaligned cameras
        chunk.alignCameras(cameras=unaligned_cameras, reset_alignment=False)
        
        # Reset the region
        chunk.resetRegion()
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()
        
        # Filter points based on reconstruction uncertainty
        logging.info("Filtering points based on reconstruction uncertainty")
        f1 = Metashape.TiePoints.Filter()
        f1.init(chunk, Metashape.TiePoints.Filter.ReconstructionUncertainty)
        f1.removePoints(METASHAPE_DEFAULTS["reconstruction_uncertainty"])
        
        # Optimize cameras
        logging.info(f"Optimizing cameras for model {transect_id}")
        chunk.optimizeCameras(
            fit_k4=METASHAPE_DEFAULTS["fit_k4"],
            adaptive_fitting=METASHAPE_DEFAULTS["adaptive_fitting"]
        )
        
        # Filter points based on reprojection error
        logging.info("Filtering points based on reprojection error")
        f2 = Metashape.TiePoints.Filter()
        f2.init(chunk, Metashape.TiePoints.Filter.ReprojectionError)
        f2.removePoints(METASHAPE_DEFAULTS["reprojection_error"])
        
        # Filter points based on projection accuracy
        logging.info("Filtering points based on projection accuracy")
        f3 = Metashape.TiePoints.Filter()
        f3.init(chunk, Metashape.TiePoints.Filter.ProjectionAccuracy)
        f3.removePoints(METASHAPE_DEFAULTS["projection_accuracy"])
        
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()
        
        # Rotate coordinate system to bounding box
        logging.info("Rotating coordinate system to bounding box")
        R = chunk.region.rot     # Bounding box rotation matrix
        C = chunk.region.center  # Bounding box center vector
        
        if chunk.transform.matrix:
            T = chunk.transform.matrix
            s = math.sqrt(T[0, 0] ** 2 + T[0, 1] ** 2 + T[0, 2] ** 2)  # scaling
            S = Metashape.Matrix().Diag([s, s, s, 1])                  # scale matrix
        else:
            S = Metashape.Matrix().Diag([1, 1, 1, 1])
            
        T = Metashape.Matrix([[R[0, 0], R[0, 1], R[0, 2], C[0]],
                             [R[1, 0], R[1, 1], R[1, 2], C[1]],
                             [R[2, 0], R[2, 1], R[2, 2], C[2]],
                             [     0,      0,      0,    1]])
                             
        chunk.transform.matrix = S * T.inv()  # resulting chunk transformation matrix
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()
        
        # Build depth maps
        logging.info(f"Building depth maps for model {transect_id}")
        chunk.buildDepthMaps(
            downscale=METASHAPE_DEFAULTS["depth_downscale"],
            filter_mode=getattr(Metashape, METASHAPE_DEFAULTS["depth_filter_mode"])
        )
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Build model
        logging.info(f"Building model for {transect_id}")
        chunk.buildModel(
            source_data=Metashape.DepthMapsData,
            surface_type=getattr(Metashape, METASHAPE_DEFAULTS["surface_type"]),
            face_count=getattr(Metashape, METASHAPE_DEFAULTS["face_count"]),
            volumetric_masks=METASHAPE_DEFAULTS["volumetric_masks"],
            interpolation=getattr(Metashape, METASHAPE_DEFAULTS["interpolation"]),
            vertex_colors=METASHAPE_DEFAULTS["vertex_colors"]
        )
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Smooth model
        logging.info(f"Smoothing model for {transect_id}")
        chunk.smoothModel(
            strength=METASHAPE_DEFAULTS["smooth_strength"],
            apply_to_selection=False,
            fix_borders=METASHAPE_DEFAULTS["fix_borders"],
            preserve_edges=METASHAPE_DEFAULTS["preserve_edges"]
        )
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Build UV
        logging.info(f"Building UV for model {transect_id}")
        chunk.buildUV(
            mapping_mode=getattr(Metashape, METASHAPE_DEFAULTS["mapping_mode"]),
            texture_size=METASHAPE_DEFAULTS["texture_size"],
            page_count=METASHAPE_DEFAULTS["page_count"]
        )
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Build texture
        logging.info(f"Building texture for model {transect_id}")
        chunk.buildTexture(
            texture_size=METASHAPE_DEFAULTS["texture_size"],
            texture_type=getattr(Metashape.Model, METASHAPE_DEFAULTS["texture_type"]),
            blending_mode=getattr(Metashape, METASHAPE_DEFAULTS["blending_mode"]),
            fill_holes=METASHAPE_DEFAULTS["fill_holes"],
            ghosting_filter=METASHAPE_DEFAULTS["ghosting_filter"],
            enable_gpu=METASHAPE_DEFAULTS["enable_gpu"],
            relaxed_precision=METASHAPE_DEFAULTS["relaxed_precision"]
        )
        if psx_path:
            doc.save(psx_path)
        
        Metashape.app.update()

        # Generate report
        logging.info(f"Generating report for model {transect_id}")
        report_file_path = os.path.join(DIRECTORIES["reports"], f"{transect_id}_step1.pdf")
        chunk.exportReport(report_file_path, title=f"Model {transect_id} - Step 1 Report")
        
        end_time = datetime.datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Update tracking file
        update_tracking(transect_id, {
            "Status": "Step 1 complete",
            "Step 1 complete": "True",
            "Step 1 start time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Step 1 end time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Step 1 processing time (s)": str(processing_time),
            "Aligned cameras": str(len([c for c in chunk.cameras if c.transform])),
            "Total cameras": str(len(chunk.cameras)),
            "PSX file": psx_path if psx_path else "",
            "Report file": report_file_path
        })
        
        logging.info(f"Successfully processed model {transect_id} in {processing_time:.1f} seconds")
        return (True, doc, chunk)
        
    except Exception as e:
        error_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"Error processing model {transect_id}: {str(e)}"
        logging.error(error_msg)
        update_tracking(transect_id, {
            "Status": "Error in Step 1",
            "Step 1 complete": "False",
            "Step 1 error time": error_time,
            "Notes": error_msg
        })
        return (False, doc, None)

def create_or_update_batch_summary(batch_mapping):
    """
    Create or update the batch summary CSV file.
    
    Args:
        batch_mapping (dict): Mapping of PSX batch files to transects
    """
    summary_path = os.path.join(DIRECTORIES["processing_root"], "psx_batch_summary.csv")
    
    # Create data for CSV
    data = []
    for psx_file, transects in batch_mapping.items():
        for transect_id in transects:
            data.append({
                "PSX File": psx_file,
                "Model ID": transect_id,
                "Date Processed": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(data)
    df.to_csv(summary_path, index=False)
    logging.info(f"Batch summary saved to {summary_path}")

def main():
    """Main function to process all models."""
    # Get list of transect directories (which contain frames)
    transect_dirs = []
    frames_dir = DIRECTORIES["frames"]
    if os.path.exists(frames_dir):
        transect_dirs = [d for d in os.listdir(frames_dir) 
                        if os.path.isdir(os.path.join(frames_dir, d))]
    
    if not transect_dirs:
        logging.error(f"No model directories found in {frames_dir}")
        return
    
    # Filter for transects that haven't been processed yet
    unprocessed_transects = []
    for transect_id in transect_dirs:
        status = get_transect_status(transect_id)
        if status.get("Step 1 complete", "False") != "True":
            unprocessed_transects.append(transect_id)
    
    if not unprocessed_transects:
        logging.info("All models have already been processed")
        return
    
    logging.info(f"Found {len(unprocessed_transects)} models to process")
    
    # Process transects in batches
    batch_mapping = {}  # Maps PSX files to contained transects
    current_batch = []
    current_doc = None
    current_psx_path = None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    
    # Create first batch immediately instead of incrementing
    batch_num = 1
    
    for i, transect_id in enumerate(unprocessed_transects):
        # If we're starting a new batch or the current batch is full
        if not current_batch or len(current_batch) >= MAX_CHUNKS_PER_PSX:
            # Save previous document if it exists
            if current_doc and current_psx_path:
                try:
                    current_doc.save(current_psx_path)
                    logging.info(f"Saved batch to {current_psx_path}")
                except Exception as e:
                    logging.error(f"Error saving document to {current_psx_path}: {str(e)}")
                # Only increment batch_num after the first batch
                batch_num += 1
            
            # Create new batch
            current_batch = []
            
            # Create new document for this batch
            current_doc = Metashape.Document()
            
            # Create psxraw directory if it doesn't exist
            os.makedirs(DIRECTORIES["psxraw"], exist_ok=True)
            
            # Generate PSX path for this batch
            current_psx_path = os.path.join(DIRECTORIES["psxraw"], f"psx_{batch_num}_{timestamp}.psx")
            logging.info(f"Starting new batch {batch_num} with PSX file {current_psx_path}")
            
            # Initialize the batch mapping for this PSX file
            batch_mapping[current_psx_path] = []
            
            # Save the empty document to establish the file
            try:
                current_doc.save(current_psx_path)
                logging.info(f"Created empty document at {current_psx_path}")
            except Exception as e:
                logging.error(f"Error creating empty document at {current_psx_path}: {str(e)}")
        
        # Add transect to current batch
        current_batch.append(transect_id)
        
        # Process the transect
        logging.info(f"Processing model {transect_id} ({i+1}/{len(unprocessed_transects)})")
        success, updated_doc, _ = process_transect(transect_id, current_doc, current_psx_path)
        
        # Make sure we keep using the updated document reference
        if updated_doc is not None:
            current_doc = updated_doc
        
        if success:
            batch_mapping[current_psx_path].append(transect_id)
            
            # Save after each successful transect processing
            try:
                current_doc.save(current_psx_path)
                logging.info(f"Saved progress to {current_psx_path} after processing {transect_id}")
            except Exception as e:
                logging.error(f"Error saving document to {current_psx_path}: {str(e)}")
    
    # Save final batch if it exists
    if current_doc and current_psx_path:
        try:
            # Update app state before saving
            Metashape.app.update()
            # Let the update complete
            time.sleep(1)
            # Now save the document
            current_doc.save(current_psx_path)
            # Allow time for the save to complete
            time.sleep(1)
            logging.info(f"Saved final batch to {current_psx_path}")
        except Exception as e:
            logging.error(f"Error saving final document to {current_psx_path}: {str(e)}")
    
    # Create batch summary
    create_or_update_batch_summary(batch_mapping)
    
    logging.info("Step 1 processing complete")

if __name__ == "__main__":
    main() 