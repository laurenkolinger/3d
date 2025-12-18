"""
Step 2: Automatic Scaling and Validation

This script automatically detects coded targets, applies scale bars, and validates
scale accuracy for models that have completed Step 1.

Works on: processing/psxraw/*.psx files
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
    get_transect_status,
    PARAMS,
    TIMESTAMP
)
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["logs"], f"step2_autoscale_{PROJECT_NAME}_{TIMESTAMP}.log")),
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

def remove_unlisted_markers(chunk, scale_bars_config):
    """
    Remove all markers except those listed in scale_bars configuration.
    
    Args:
        chunk (Metashape.Chunk): The chunk to clean
        scale_bars_config (list): List of scale bar definitions
        
    Returns:
        int: Number of markers removed
    """
    allowed_labels = set()
    for scale_bar in scale_bars_config:
        allowed_labels.add(scale_bar["start_marker"])
        allowed_labels.add(scale_bar["end_marker"])
    
    markers_to_remove = []
    for marker in chunk.markers:
        if marker.label not in allowed_labels:
            markers_to_remove.append(marker)
    
    if markers_to_remove:
        chunk.remove(markers_to_remove)
        logging.info(f"Removed {len(markers_to_remove)} unlisted markers")
    
    return len(markers_to_remove)

def add_scale_bars_and_calculate_error(chunk, scale_bars_config):
    """
    Add scale bars to chunk and calculate average scale error.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        scale_bars_config (list): List of scale bar definitions
        
    Returns:
        tuple: (success: bool, avg_error: float)
    """
    errors = []
    scale_bars_added = 0
    
    for scale_bar_def in scale_bars_config:
        start_marker = find_marker_by_label(chunk, scale_bar_def["start_marker"])
        end_marker = find_marker_by_label(chunk, scale_bar_def["end_marker"])
        
        if start_marker and end_marker:
            scalebar = chunk.addScalebar(start_marker, end_marker)
            scalebar.reference.distance = scale_bar_def["distance"]
            scalebar.reference.accuracy = 0.001
            scalebar.reference.enabled = True
            
            scale_bars_added += 1
            logging.info(f"Added scale bar between {scale_bar_def['start_marker']} and {scale_bar_def['end_marker']} with distance {scale_bar_def['distance']}m")
        else:
            missing = []
            if not start_marker:
                missing.append(scale_bar_def['start_marker'])
            if not end_marker:
                missing.append(scale_bar_def['end_marker'])
            logging.warning(f"Could not find markers: {', '.join(missing)}")
    
    if scale_bars_added == 0:
        logging.error("No scale bars could be added")
        return False, 999.0
    
    logging.info("Applying scale transformation...")
    chunk.updateTransform()
    
    logging.info("Calculating scale errors...")
    for scalebar in chunk.scalebars:
        pos1 = chunk.transform.matrix.mulp(scalebar.point0.position)
        pos2 = chunk.transform.matrix.mulp(scalebar.point1.position)
        
        actual_distance = (pos2 - pos1).norm()
        reference_distance = scalebar.reference.distance
        error = abs(actual_distance - reference_distance)
        
        errors.append(error)
        logging.info(f"Scalebar {scalebar.label}: reference={reference_distance:.4f}m, actual={actual_distance:.4f}m, error={error:.4f}m")
    
    avg_error = sum(errors) / len(errors) if errors else 999.0
    logging.info(f"Average scale error: {avg_error:.6f}m")
    
    return True, avg_error

def process_chunk(chunk, doc, config):
    """
    Process a single chunk for automatic scaling.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        doc (Metashape.Document): The document containing the chunk
        config (dict): Configuration parameters
        
    Returns:
        bool: True if successful, False otherwise
    """
    model_id = chunk.label
    
    status = get_transect_status(model_id)
    current_scale = status.get("Scale", "")
    
    if current_scale in ["PASS", "DONE"]:
        logging.info(f"Chunk {model_id} already has Scale={current_scale}, skipping...")
        return True
    
    logging.info(f"Processing chunk: {model_id}")
    
    if not chunk.model:
        logging.error(f"No model found in chunk {model_id}")
        update_tracking(model_id, {
            "Scale": "FAIL",
            "Scale Error (m)": "999.0",
            "Notes": "No model found"
        })
        return False
    
    logging.info("Removing small disconnected components...")
    chunk.model.removeComponents(99)
    
    logging.info("Detecting circular 20-bit coded targets...")
    chunk.detectMarkers(
        target_type=Metashape.TargetType.CircularTarget20bit,
        tolerance=50,
        filter_mask=False
    )
    logging.info(f"Found {len(chunk.markers)} markers after detection")
    
    if config.get("remove_unlisted_markers", True):
        remove_unlisted_markers(chunk, config["scale_bars"])
        logging.info(f"After cleanup: {len(chunk.markers)} markers remaining")
    
    success, avg_error = add_scale_bars_and_calculate_error(chunk, config["scale_bars"])
    
    if not success:
        update_tracking(model_id, {
            "Scale": "FAIL",
            "Scale Error (m)": f"{avg_error:.6f}",
            "Step 2 complete": "True"
        })
        return False
    
    threshold = config.get("scale_error_threshold", 0.009)
    
    if avg_error < threshold:
        logging.info(f"Scale validation PASSED (error {avg_error:.6f}m < threshold {threshold}m)")
        update_tracking(model_id, {
            "Scale": "PASS",
            "Scale Error (m)": f"{avg_error:.6f}",
            "Step 2 complete": "True"
        })
        return True
    else:
        logging.warning(f"Scale validation FAILED (error {avg_error:.6f}m >= threshold {threshold}m)")
        update_tracking(model_id, {
            "Scale": "FAIL",
            "Scale Error (m)": f"{avg_error:.6f}",
            "Step 2 complete": "True"
        })
        return False

def main():
    """Main function to process automatic scaling for all chunks."""
    project_dir = DIRECTORIES["base"]
    psxraw_dir = DIRECTORIES["psxraw"]
    
    if not os.path.exists(psxraw_dir):
        logging.error(f"PSX raw directory not found: {psxraw_dir}")
        return
    
    tracking_files = get_tracking_files()
    
    if not tracking_files:
        logging.error("No tracking files found. Run step1.py first.")
        return
    
    config = PARAMS['processing']['model_processing']
    
    psx_files = [f for f in os.listdir(psxraw_dir) if f.endswith('.psx')]
    
    if not psx_files:
        logging.error(f"No PSX files found in {psxraw_dir}")
        return
    
    logging.info(f"Found {len(psx_files)} PSX files to process")
    
    for psx_file in psx_files:
        psx_path = os.path.join(psxraw_dir, psx_file)
        logging.info(f"\n{'='*60}")
        logging.info(f"Processing PSX file: {psx_file}")
        logging.info(f"{'='*60}")
        
        doc = Metashape.Document()
        doc.open(psx_path, read_only=False, ignore_lock=True)
        
        for chunk in doc.chunks:
            try:
                process_chunk(chunk, doc, config)
            except Exception as e:
                logging.error(f"Error processing chunk {chunk.label}: {str(e)}")
                import traceback
                traceback.print_exc()
                update_tracking(chunk.label, {
                    "Scale": "FAIL",
                    "Scale Error (m)": "999.0",
                    "Notes": f"Error: {str(e)}"
                })
        
        doc.save()
        logging.info(f"Saved {psx_file} with updated scaling")
    
    logging.info("\nStep 2 automatic scaling completed for all models.")

if __name__ == "__main__":
    main()
