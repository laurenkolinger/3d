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
    get_transect_status
)

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
        int: Number of frames extracted
    """
    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
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
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            output_path = os.path.join(output_dir, f"frame_{frame_idx:06d}.jpg")
            cv2.imwrite(output_path, frame)
            frames_extracted += 1
    
    cap.release()
    return frames_extracted

def process_video(video_path):
    """
    Process a single video file.
    
    Args:
        video_path (str): Path to the video file
    """
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Create output directory for this video
    output_dir = os.path.join(DIRECTORIES["frames"], video_name)
    
    # Check if already processed
    status = get_transect_status(video_name)
    if status.get("Frames extracted", "0") != "0":
        logging.info(f"Video {video_name} already processed, skipping...")
        return
    
    try:
        # Extract frames
        frames_extracted = extract_frames(
            video_path,
            output_dir,
            FRAMES_PER_TRANSECT,
            EXTRACTION_RATE
        )
        
        # Update tracking file
        update_tracking(video_name, {
            "Status": "Frames extracted",
            "Frames extracted": str(frames_extracted),
            "Step 0 complete": "True",
            "Notes": f"Extracted {frames_extracted} frames"
        })
        
        logging.info(f"Successfully extracted {frames_extracted} frames from {video_name}")
        
    except Exception as e:
        logging.error(f"Error processing {video_name}: {str(e)}")
        update_tracking(video_name, {
            "Status": "Error in frame extraction",
            "Notes": f"Error: {str(e)}"
        })

def main():
    """Main function to process all videos in the source directory."""
    # Get list of video files
    video_files = []
    for ext in ['.mov', '.mp4']:
        video_files.extend(Path(VIDEO_SOURCE_DIRECTORY).glob(f"*{ext}"))
    
    if not video_files:
        logging.error(f"No video files found in {VIDEO_SOURCE_DIRECTORY}")
        return
    
    logging.info(f"Found {len(video_files)} video files to process")
    
    # Process each video
    for video_path in video_files:
        process_video(str(video_path))
    
    logging.info("Frame extraction complete")

if __name__ == "__main__":
    main() 