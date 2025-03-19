#!/usr/bin/env python3
"""
Frame extraction script for 3D modeling workflow.
This script extracts frames from video files (MP4, MOV) for photogrammetry processing.
"""

import os
import subprocess
import glob
import json
import argparse
import sys
import config

def get_video_duration(video_path):
    """Get the duration of a video in seconds using ffprobe."""
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'json', 
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Error getting duration for {video_path}: {result.stderr.decode()}")
        return 0
    
    try:
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing duration for {video_path}: {e}")
        return 0

def extract_frames(video_path, fps, dest_folder):
    """Extract frames from a video using ffmpeg."""
    # Create output directory if it doesn't exist
    os.makedirs(dest_folder, exist_ok=True)
    
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_pattern = os.path.join(dest_folder, f"{video_name}_%04d.tiff")
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'fps={fps}',
        '-c:v', 'tiff',
        '-pix_fmt', 'rgb24',
        output_pattern
    ]
    
    # Run the command
    print(f"Extracting frames from {video_path} at {fps} fps to {dest_folder}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Error extracting frames from {video_path}: {result.stderr.decode()}")
        return False
    
    print(f"Successfully extracted frames from {video_path}")
    return True

def get_transect_id_from_filename(file_path):
    """Extract transect ID from filename.
    
    Example formats supported:
    - TCRMP20240311_3D_BID_T1_3.mp4
    - TCRMP20240311_3D_BID_T1.mov
    
    Returns the site+transect identifier (e.g., TCRMP20240311_3D_BID_T1)
    """
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Split by underscore
    parts = name_without_ext.split('_')
    
    # If it has at least 4 parts (prefix, type, site, transect), use them as the ID
    if len(parts) >= 4:
        # Join the first 4 parts as the transect ID
        return '_'.join(parts[:4])
    
    # If filename doesn't match expected format, use the whole name without extension
    return name_without_ext

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract frames from videos for 3D processing')
    parser.add_argument('--video-dir', type=str, help='Directory containing video files to process')
    parser.add_argument('--output-dir', type=str, help='Directory to save extracted frames')
    parser.add_argument('--frames', type=int, default=1200,
                       help='Number of frames to extract per transect (default: 1200)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up paths based on arguments or defaults
    custom_paths = {}
    if args.video_dir:
        custom_paths['video_source'] = args.video_dir
    if args.output_dir:
        custom_paths['extracted_frames'] = args.output_dir
    
    # Apply custom paths if provided
    if custom_paths:
        config.set_paths(custom_paths)
    
    # Get parameters
    n_pics = args.frames or config.PROCESSING_PARAMS["extract_frames"]["frames_per_transect"]
    
    # Get video source directory
    videos_dir = config.PATHS.get("video_source", "")
    if not videos_dir:
        print("Error: No video source directory specified. Use --video-dir or set in config.")
        sys.exit(1)
    
    if not os.path.exists(videos_dir):
        print(f"Error: Video directory not found: {videos_dir}")
        sys.exit(1)
    
    # Get output directory
    output_dir = config.PATHS.get("extracted_frames", "")
    if not output_dir:
        print("Error: No output directory specified. Use --output-dir or set in config.")
        sys.exit(1)
    
    # Initialize the CSV file
    df = config.initialize_csv()
    
    # Find all video files (MP4 and MOV)
    video_files = []
    for ext in ['*.mp4', '*.MP4', '*.mov', '*.MOV']:
        video_files.extend(glob.glob(os.path.join(videos_dir, ext)))
    
    if not video_files:
        print(f"No video files found in {videos_dir}")
        return
    
    # Get unique transect IDs
    transect_info = {}
    for file in video_files:
        transect_id = get_transect_id_from_filename(file)
        if transect_id not in transect_info:
            transect_info[transect_id] = []
        transect_info[transect_id].append(file)
    
    print(f"Found {len(transect_info)} unique transects")
    
    # Process each transect
    for transect_id, videos in transect_info.items():
        print(f"Processing transect: {transect_id}")
        print(f"Found {len(videos)} videos for this transect")
        
        # Create folder for this transect
        transect_folder = os.path.join(output_dir, transect_id)
        
        # Calculate total duration across all videos for this transect
        total_duration = sum(get_video_duration(video) for video in videos)
        
        if total_duration <= 0:
            print(f"Error: Couldn't determine duration for videos in transect {transect_id}")
            continue
        
        # Extract frames from each video
        all_succeeded = True
        for video in videos:
            duration = get_video_duration(video)
            if duration <= 0:
                print(f"Skipping {video} (couldn't determine duration)")
                continue
                
            # Calculate how many frames to extract from this video
            # proportional to its duration relative to the total
            frames_to_extract = round(n_pics * (duration / total_duration))
            
            # Calculate FPS for extraction
            fps = frames_to_extract / duration
            
            # Extract frames
            success = extract_frames(video, fps, transect_folder)
            if not success:
                all_succeeded = False
        
        # Update the CSV with this transect's information
        config.update_csv_row(transect_id, {
            'video_source': videos_dir,
            'frames_dir': transect_folder,
            'extract_frames_complete': 'Yes' if all_succeeded else 'Error'
        })
        
        if all_succeeded:
            print(f"Completed frame extraction for transect {transect_id}")
        else:
            print(f"Encountered errors during frame extraction for transect {transect_id}")

if __name__ == "__main__":
    main()
    print("Frame extraction completed") 