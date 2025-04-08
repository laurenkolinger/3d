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
import subprocess
import tempfile
import shutil
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

def extract_frames_ffmpeg(video_path, output_dir, frames_per_transect, extraction_rate):
    """
    Extract frames from a video file using FFmpeg with TIFF format (rgb24) and hardware acceleration.
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save frames
        frames_per_transect (int): Number of frames to extract
        extraction_rate (float): Rate at which to extract frames (1.0 = all frames)
    
    Returns:
        tuple: (frames_extracted, extracted_frame_paths, video_length_seconds, total_video_frames)
    """
    # Open video file with OpenCV just to get properties
    logging.info(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # Calculate video length in seconds
    video_length_seconds = total_frames / fps if fps > 0 else 0
    
    logging.info(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames, {video_length_seconds:.2f} seconds")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate fps value for the extraction
    if frames_per_transect > 0:
        # Calculate the fps needed to get exactly frames_per_transect frames
        extract_fps = frames_per_transect / video_length_seconds
        logging.info(f"Setting fps={extract_fps} to extract {frames_per_transect} frames from {video_length_seconds:.2f}s video")
    else:
        # Use the specified extraction rate
        extract_fps = fps * extraction_rate
        logging.info(f"Setting fps={extract_fps} (extraction rate={extraction_rate})")
    
    # Extract frames using FFmpeg with TIFF format
    logging.info(f"Extracting frames using TIFF format with rgb24")
    print(f"Starting TIFF frame extraction from {os.path.basename(video_path)}")
    
    # Define output pattern for the frames
    output_pattern = os.path.join(output_dir, f"frame_%06d.tiff")
    
    # FFmpeg command for TIFF extraction with hardware acceleration
    ffmpeg_cmd = [
        'ffmpeg',
        '-hwaccel', 'videotoolbox',     # Hardware acceleration
        '-hwaccel_output_format', 'videotoolbox_vld',  # Force hardware decoding
        '-i', video_path,
        '-vf', f'fps={extract_fps}',    # Set frames per second for extraction
        '-c:v', 'tiff',                 # Use TIFF codec 
        '-pix_fmt', 'rgb24',            # Standard 8-bit RGB
        '-compression_level', '0',      # No compression
        '-v', 'info',                   # Show information
        '-stats',                       # Show progress
        output_pattern
    ]
    
    try:
        # Run FFmpeg with output visible to user
        print("Running FFmpeg with hardware acceleration for TIFF extraction...")
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Display FFmpeg output to monitor hardware acceleration
        for line in process.stdout:
            line = line.strip()
            print(line)
            # Look for hardware acceleration confirmation messages
            if 'hwaccel' in line.lower() or 'videotoolbox' in line.lower():
                print(f"HARDWARE ACCELERATION INDICATOR: {line}")
        
        process.wait()
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, ffmpeg_cmd)
        
        # Get list of extracted frames
        extracted_frame_paths = sorted([
            os.path.join(output_dir, f) for f in os.listdir(output_dir) 
            if f.endswith('.tiff')
        ])
        frames_extracted = len(extracted_frame_paths)
        
        # Check size of first frame
        if frames_extracted > 0:
            size_mb = os.path.getsize(extracted_frame_paths[0]) / (1024 * 1024)
            print(f"First TIFF frame size: {size_mb:.2f} MB")
        else:
            print("No frames were extracted!")
    
    except subprocess.CalledProcessError as e:
        error_msg = "Unknown FFmpeg error"
        if hasattr(e, 'output') and e.output:
            error_msg = e.output
        elif hasattr(e, 'stderr') and e.stderr:
            error_msg = e.stderr.decode()
            
        logging.error(f"FFmpeg error: {error_msg}")
        print(f"ERROR: FFmpeg failed: {error_msg}")
        
        # Try simpler command without some options
        print("Attempting simpler FFmpeg command...")
        
        # Simpler FFmpeg command without some options that might be causing problems
        ffmpeg_cmd = [
            'ffmpeg',
            '-hwaccel', 'videotoolbox',
            '-i', video_path,
            '-vf', f'fps={extract_fps}',
            '-pix_fmt', 'rgb24',
            output_pattern
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            
            # Get list of extracted frames
            extracted_frame_paths = sorted([
                os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                if f.endswith('.tiff')
            ])
            frames_extracted = len(extracted_frame_paths)
            
        except Exception as e2:
            logging.error(f"Second FFmpeg attempt failed: {str(e2)}")
            return 0, [], video_length_seconds, total_frames
    
    if frames_extracted == 0:
        logging.error("No frames were extracted!")
        print("ERROR: Failed to extract any frames")
    else:
        logging.info(f"Successfully extracted {frames_extracted} TIFF frames")
        print(f"SUCCESS: Extracted {frames_extracted} TIFF frames to {output_dir}")
    
    return frames_extracted, extracted_frame_paths, video_length_seconds, total_frames

def extract_frames_ffmpeg_alternative(video_path, output_dir, frames_per_transect, extraction_rate):
    """
    Alternative high-quality extraction method for cinema footage using EXR format.
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save frames
        frames_per_transect (int): Number of frames to extract
        extraction_rate (float): Rate at which to extract frames (1.0 = all frames)
    
    Returns:
        tuple: (frames_extracted, extracted_frame_paths, video_length_seconds, total_video_frames)
    """
    # Open video file with OpenCV just to get properties
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # Calculate video length in seconds
    video_length_seconds = total_frames / fps if fps > 0 else 0
    
    # Calculate which frames to extract
    if frames_per_transect > 0:
        # Extract specific number of frames
        frame_indices = np.linspace(0, total_frames-1, frames_per_transect, dtype=int)
        logging.info(f"Will extract {frames_per_transect} frames evenly spaced throughout video")
    else:
        # Calculate frame interval based on extraction rate
        frame_interval = int(1 / extraction_rate)
        frame_indices = range(0, total_frames, frame_interval)
        logging.info(f"Will extract frames at interval of {frame_interval} (rate={extraction_rate})")
    
    extracted_frame_paths = []
    frames_extracted = 0
    
    print(f"Starting direct extraction of {len(frame_indices)} frames using individual frame method")
    
    # Try each format in order of preference until one works
    formats_to_try = [
        # ('.exr', ['-c:v', 'exr', '-pix_fmt', 'rgb48le']),  # EXR format (best for HDR)
        # ('.tiff', ['-c:v', 'tiff', '-pix_fmt', 'rgb48']),   # 16-bit TIFF
        ('.tiff', ['-c:v', 'tiff', '-pix_fmt', 'rgb24'])   # 8-bit TIFF
        #('.png', ['-c:v', 'png', '-pix_fmt', 'rgb24', '-compression_level', '0'])  # PNG lossless
    ]
    
    # Find which format works with this video
    working_format = None
    for ext, params in formats_to_try:
        try:
            test_output = os.path.join(output_dir, f"test_frame{ext}")
            test_cmd = [
                'ffmpeg',
                '-hwaccel', 'videotoolbox',
                '-ss', '0',
                '-i', video_path,
                '-vframes', '1'
            ] + params + ['-y', test_output]
            
            subprocess.run(test_cmd, check=True, capture_output=True)
            
            if os.path.exists(test_output):
                working_format = (ext, params)
                os.remove(test_output)
                break
        except:
            continue
    
    if not working_format:
        logging.error("Could not find a working high-quality format for this video")
        return 0, [], video_length_seconds, total_frames
    
    ext, params = working_format
    print(f"Using format: {ext} with parameters: {params}")
    
    # Extract each frame using the working format
    for i, frame_idx in enumerate(frame_indices):
        if i % max(1, len(frame_indices) // 10) == 0:
            progress = (i / len(frame_indices)) * 100
            print(f"Extraction progress: {progress:.1f}% ({i}/{len(frame_indices)})")
        
        # Calculate timestamp for this frame
        timestamp = frame_idx / fps if fps > 0 else 0
        
        # Output path
        output_path = os.path.join(output_dir, f"frame_{frame_idx:06d}{ext}")
        
        # Extract this specific frame
        frame_cmd = [
            'ffmpeg',
            '-hwaccel', 'videotoolbox',
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1'
        ] + params + [
            '-v', 'error',
            output_path
        ]
        
        try:
            subprocess.run(frame_cmd, check=True, 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                extracted_frame_paths.append(output_path)
                frames_extracted += 1
                
                # Check size of first frame
                if frames_extracted == 1:
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"First frame size: {size_mb:.2f} MB using {ext} format")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error extracting frame {frame_idx}: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")
    
    return frames_extracted, extracted_frame_paths, video_length_seconds, total_frames

def extract_frames_ffmpeg_png(video_path, output_dir, frames_per_transect, extraction_rate):
    """
    Extract frames from a video file using FFmpeg for highest quality as PNG (lossless).
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save frames
        frames_per_transect (int): Number of frames to extract
        extraction_rate (float): Rate at which to extract frames (1.0 = all frames)
    
    Returns:
        tuple: (frames_extracted, extracted_frame_paths, video_length_seconds, total_video_frames)
    """
    # Open video file with OpenCV just to get properties
    logging.info(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # Calculate video length in seconds
    video_length_seconds = total_frames / fps if fps > 0 else 0
    
    logging.info(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames, {video_length_seconds:.2f} seconds")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate which frames to extract
    if frames_per_transect > 0:
        # Extract specific number of frames
        frame_indices = np.linspace(0, total_frames-1, frames_per_transect, dtype=int)
        logging.info(f"Will extract {frames_per_transect} PNG frames evenly spaced throughout video")
    else:
        # Calculate frame interval based on extraction rate
        frame_interval = int(1 / extraction_rate)
        frame_indices = range(0, total_frames, frame_interval)
        logging.info(f"Will extract PNG frames at interval of {frame_interval} (rate={extraction_rate})")
    
    extracted_frame_paths = []
    frames_extracted = 0
    
    print(f"Starting direct PNG extraction of {len(frame_indices)} frames...")
    logging.info(f"Using direct PNG extraction method for highest quality")
    
    # Extract frames directly one by one (slower but better quality)
    for i, frame_idx in enumerate(frame_indices):
        if i % max(1, len(frame_indices) // 10) == 0:
            progress = (i / len(frame_indices)) * 100
            print(f"PNG extraction progress: {progress:.1f}% ({i}/{len(frame_indices)})")
        
        # Calculate exact timestamp for this frame
        timestamp = frame_idx / fps if fps > 0 else 0
        
        # Output file path (PNG for lossless quality)
        output_path = os.path.join(output_dir, f"frame_{frame_idx:06d}.png")
        
        # Extract just this one frame as PNG (lossless)
        frame_cmd = [
            'ffmpeg',
            '-hwaccel', 'videotoolbox',
            '-ss', str(timestamp),   # Seek to timestamp
            '-i', video_path,
            '-vframes', '1',         # Extract just one frame
            '-pix_fmt', 'rgb24',     # Use RGB color space
            '-vsync', '0',           # No frame rate conversion
            '-vf', 'format=rgb24',   # Force RGB format
            '-compression_level', '0', # No compression (max quality)
            output_path
        ]
        
        try:
            # Run with minimal output to avoid clutter
            subprocess.run(frame_cmd, check=True, 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                extracted_frame_paths.append(output_path)
                frames_extracted += 1
                
                # Check size of first frame
                if frames_extracted == 1:
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"First PNG frame size: {size_mb:.2f} MB")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error extracting PNG frame {frame_idx}: {e.stderr.decode() if e.stderr else str(e)}")
    
    if frames_extracted == 0:
        logging.error("No PNG frames were extracted!")
        print("ERROR: Failed to extract any PNG frames")
    else:
        logging.info(f"Successfully extracted {frames_extracted} PNG frames")
        print(f"SUCCESS: Extracted {frames_extracted} lossless PNG frames to {output_dir}")
    
    return frames_extracted, extracted_frame_paths, video_length_seconds, total_frames

def extract_frames_png(video_path, output_dir, frames_per_transect, extraction_rate):
    """
    Extract frames as PNG files for lossless quality.
    
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
    
    # Calculate which frames to extract
    if frames_per_transect > 0:
        # Extract specific number of frames
        frame_indices = np.linspace(0, total_frames-1, frames_per_transect, dtype=int)
    else:
        # Calculate frame interval based on extraction rate
        frame_interval = int(1 / extraction_rate)
        frame_indices = range(0, total_frames, frame_interval)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract frames as PNG (lossless)
    frames_extracted = 0
    extracted_frame_paths = []
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            # Save as PNG for lossless quality
            output_path = os.path.join(output_dir, f"frame_{frame_idx:06d}.png")
            cv2.imwrite(output_path, frame)
            frames_extracted += 1
            extracted_frame_paths.append(output_path)
    
    cap.release()
    return frames_extracted, extracted_frame_paths, video_length_seconds, total_frames

def extract_frames(video_path, output_dir, frames_per_transect, extraction_rate):
    """
    Extract frames from a video file using OpenCV (legacy method).
    
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
            cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
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
        
        # For highest quality, use TIFF extraction method
        frames_extracted, frame_paths, video_length, total_frames = extract_frames_ffmpeg(
            video_path,
            output_dir,
            FRAMES_PER_TRANSECT,
            EXTRACTION_RATE
        )
        
        # Method 2: Lossless PNG frames
        # frames_extracted, frame_paths, video_length, total_frames = extract_frames_ffmpeg_png(
        #     video_path,
        #     output_dir, 
        #     FRAMES_PER_TRANSECT,
        #     EXTRACTION_RATE
        # )
        
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
            "Notes": f"Extracted {frames_extracted} high quality frames from {total_frames} total frames ({video_length:.2f}s video)"
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