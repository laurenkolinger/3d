#!/usr/bin/env python3
"""
Step 0: Frame Extraction

This script extracts frames from video files according to the configuration
specified in analysis_params.yaml.
"""

import os
import cv2
import numpy as np
from pathlib import Path
import logging
from config import (
    VIDEO_SOURCE_DIRECTORY,
    DIRECTORIES,
    FRAMES_PER_TRANSECT,
    EXTRACTION_RATE,
    PROJECT_NAME,
    update_tracking,
    get_transect_status,
    initialize_tracking
)
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["reports"], f"step0_{PROJECT_NAME}.log")),
        logging.StreamHandler()
    ]
)

def extract_frames(video_path, output_dir, frames_per_transect, extraction_rate):
    """
    Extract frames from a video file.
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save frames
        frames_per_transect (int): Number of frames to extract
        extraction_rate (float): Rate at which to extract frames (1.0 = all frames)
    
    Returns:
        tuple: (frames_extracted, extracted_frame_paths, video_length_seconds, total_video_frames)
    """
    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Calculate video length in seconds
    video_length_seconds = total_frames / fps if fps > 0 else 0
    
    # Calculate frame interval based on extraction rate
    frame_interval = int(1 / extraction_rate)
    
    # Calculate which frames to extract
    if frames_per_transect > 0:
        # Extract specific number of frames
        frame_indices = np.linspace(0, total_frames-1, frames_per_transect, dtype=int)
    else:
        # Extract frames at specified interval
        frame_indices = range(0, total_frames, frame_interval)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract frames
    frames_extracted = 0
    extracted_frame_paths = []
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            output_path = os.path.join(output_dir, f"frame_{frame_idx:06d}.jpg")
            cv2.imwrite(output_path, frame)
            frames_extracted += 1
            extracted_frame_paths.append(output_path)
    
    cap.release()
    return frames_extracted, extracted_frame_paths, video_length_seconds, total_frames

def process_video(video_path):
    """
    Process a single video file.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        str, bool: Transect ID and success status
    """
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Create output directory for this video
    output_dir = os.path.join(DIRECTORIES["frames"], video_name)
    
    # Initialize tracking file
    initialize_tracking(video_name)
    
    # Check if already processed
    status = get_transect_status(video_name)
    if status.get("Step 0 complete", "False") == "True":
        logging.info(f"Video {video_name} already processed, skipping...")
        return video_name, True
    
    try:
        start_time = datetime.datetime.now()
        logging.info(f"Starting frame extraction for {video_name}")
        
        # Extract frames
        frames_extracted, frame_paths, video_length, total_frames = extract_frames(
            video_path,
            output_dir,
            FRAMES_PER_TRANSECT,
            EXTRACTION_RATE
        )
        
        end_time = datetime.datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        extraction_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Update tracking file
        update_tracking(video_name, {
            "Status": "Frames extracted",
            "Step 0 complete": "True",
            "Video Length (s)": f"{video_length:.2f}",
            "Total Video Frames": str(total_frames),
            "Frames Extracted": str(frames_extracted),
            "Video Source": video_path,
            "Extraction Timestamp": extraction_timestamp,
            "Step 0 start time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Step 0 end time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Step 0 processing time (s)": str(processing_time),
            "Frames directory": output_dir,
            "Notes": f"Extracted {frames_extracted} frames from {total_frames} total frames ({video_length:.2f}s video)"
        })
        
        logging.info(f"Successfully extracted {frames_extracted} frames from {video_name} (duration: {video_length:.2f}s) in {processing_time:.1f} seconds")
        return video_name, True
        
    except Exception as e:
        error_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"Error processing {video_name}: {str(e)}"
        logging.error(error_msg)
        
        update_tracking(video_name, {
            "Status": "Error in frame extraction",
            "Step 0 complete": "False",
            "Step 0 error time": error_time,
            "Notes": f"Error: {str(e)}"
        })
        return video_name, False

def create_frame_summary():
    """Create a summary of extracted frames for all transects."""
    # Use data_root directory which user is expected to create
    summary_path = os.path.join(DIRECTORIES["data_root"], "frame_extraction_summary.csv")
    
    # Get all transect directories
    frames_dir = DIRECTORIES["frames"]
    transect_dirs = []
    if os.path.exists(frames_dir):
        transect_dirs = [d for d in os.listdir(frames_dir) 
                        if os.path.isdir(os.path.join(frames_dir, d))]
    
    # Write summary to CSV
    with open(summary_path, 'w') as f:
        f.write("Transect ID,Video Length (s),Total Frames,Frames Extracted,Extraction Date,Processing Time (s),Status\n")
        
        for transect_id in transect_dirs:
            status = get_transect_status(transect_id)
            frames = status.get("Frames Extracted", "0")
            total_frames = status.get("Total Video Frames", "0")
            video_length = status.get("Video Length (s)", "0")
            date = status.get("Extraction Timestamp", status.get("Step 0 end time", ""))
            processing_time = status.get("Step 0 processing time (s)", "0")
            complete = status.get("Step 0 complete", "False")
            
            status_text = "Complete" if complete == "True" else "Failed"
            f.write(f"{transect_id},{video_length},{total_frames},{frames},{date},{processing_time},{status_text}\n")
    
    logging.info(f"Frame extraction summary saved to {summary_path}")

def main():
    """Main function to process all videos in the source directory."""
    # Create only needed subdirectories
    os.makedirs(DIRECTORIES["frames"], exist_ok=True)
    os.makedirs(DIRECTORIES["reports"], exist_ok=True)
    
    # Get list of video files
    video_files = []
    for ext in ['.mov', '.mp4', '.MOV', '.MP4']:
        video_files.extend(Path(VIDEO_SOURCE_DIRECTORY).glob(f"*{ext}"))
    
    if not video_files:
        logging.error(f"No video files found in {VIDEO_SOURCE_DIRECTORY}")
        return
    
    logging.info(f"Found {len(video_files)} video files to process")
    
    # Process each video and track success
    results = []
    for i, video_path in enumerate(video_files):
        logging.info(f"Processing video {i+1}/{len(video_files)}: {video_path.name}")
        transect_id, success = process_video(str(video_path))
        results.append((transect_id, success))
    
    # Create summary of results
    create_frame_summary()
    
    # Report final status
    successful = sum(1 for _, success in results if success)
    logging.info(f"Frame extraction complete. Successfully processed {successful}/{len(video_files)} videos.")
    
    if successful != len(video_files):
        failed = [transect_id for transect_id, success in results if not success]
        logging.warning(f"Failed to process: {', '.join(failed)}")

if __name__ == "__main__":
    main()