#!/usr/bin/env python3
"""
Reset After Step 2: Preserve Steps 0-2, Clear Steps 3+

This script resets a project to AFTER Step 2 by:
1. PRESERVING frames (Step 0), PSX files (Step 1), and scaling (Step 2)
2. CLEARING all Step 3+ outputs (models, orthomosaics, reports, output PSX, moved frames)
3. RESETTING tracking to "Step 2 complete" status (Scale=PASS, ready for Step 3)

Usage: python src/utility/reset_step2.py [project_directory]
"""

import os
import sys
import shutil
import csv
import glob
from pathlib import Path

def reset_after_step2(project_dir):
    """
    Reset project to AFTER Step 2 - preserves Steps 0-2, clears Steps 3+.
    
    Args:
        project_dir (str): Path to the project directory
    """
    print(f"RESET to AFTER STEP 2")
    print(f"Project: {project_dir}")
    print("PRESERVING Steps 0-2 (frames, PSX files, scaling)")
    print("CLEARING Steps 3+ outputs")
    print("=" * 60)
    
    # Define directories
    processing_dir = os.path.join(project_dir, "processing")
    frames_dir = os.path.join(processing_dir, "frames")
    psxraw_dir = os.path.join(processing_dir, "psxraw")
    output_dir = os.path.join(project_dir, "output")
    logs_dir = os.path.join(output_dir, "logs")
    
    print("RESET PLAN:")
    print("  Will PRESERVE (keep untouched):")
    if os.path.exists(frames_dir):
        print(f"    - {frames_dir} (Step 0 frames)")
    else:
        print(f"    - {frames_dir} (Step 0 frames - not found)")
    
    if os.path.exists(psxraw_dir):
        print(f"    - {psxraw_dir} (Step 1 PSX files with Step 2 scaling)")
    else:
        print(f"    - {psxraw_dir} (Step 1 PSX files - not found)")
    
    if os.path.exists(logs_dir):
        print(f"    - {logs_dir} (all logs)")
    else:
        print(f"    - {logs_dir} (logs - not found)")
    
    print("\n  Will CLEAR (remove contents, keep directories):")
    if os.path.exists(output_dir):
        subdirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d != "logs"]
        if subdirs:
            for subdir in subdirs:
                print(f"    - output/{subdir}/")
        else:
            print(f"    - (no Step 3+ outputs found)")
    else:
        print(f"    - {output_dir} (output directory - not found)")
    
    print("\n  Will RESET tracking:")
    print("    - Scale: DONE -> PASS (ready to re-export)")
    print("    - Status: -> Step 2 complete (ready for Step 3)")
    print("    - Clear Step 3+ columns (Step 3 complete, processing time, etc.)")
    
    print("\n" + "=" * 60)
    print("WARNING: This will clear all Step 3+ outputs!")
    print("This resets the project to AFTER Step 2 (ready for Step 3)")
    print("=" * 60)
    
    confirm = input("\nProceed with reset to AFTER Step 2? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("Reset cancelled")
        return False
    
    print("\nEXECUTING RESET to AFTER STEP 2...")
    
    # 1. PRESERVE Step 0-2 outputs (do nothing - they stay)
    if os.path.exists(frames_dir):
        frame_count = len(glob.glob(os.path.join(frames_dir, "**", "*"), recursive=True))
        print(f"PRESERVING frames directory: {frames_dir} ({frame_count} items)")
    
    if os.path.exists(psxraw_dir):
        psx_count = len(glob.glob(os.path.join(psxraw_dir, "*.psx")))
        print(f"PRESERVING PSX directory: {psxraw_dir} ({psx_count} PSX files)")
    
    if os.path.exists(logs_dir):
        print(f"PRESERVING logs directory: {logs_dir}")
    
    # 2. CLEAR Step 3+ outputs (output subdirectories except logs)
    if os.path.exists(output_dir):
        print(f"Clearing Step 3+ outputs in: {output_dir}")
        try:
            # Remove all subdirectories except logs
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path) and item != "logs":
                    shutil.rmtree(item_path)
                    print(f"    Removed subdirectory: {item}")
                elif os.path.isfile(item_path):
                    # Remove any files in output/ root (shouldn't be any normally)
                    os.remove(item_path)
                    print(f"    Removed file: {item}")
        except Exception as e:
            print(f"    Error clearing {output_dir}: {e}")
    else:
        print(f"Output directory not found, skipping: {output_dir}")
    
    # 3. Reset tracking CSV to Step 2 complete
    project_name = os.path.basename(project_dir.rstrip('/'))
    tracking_file = os.path.join(project_dir, f"status_{project_name}.csv")
    
    if os.path.exists(tracking_file):
        print(f"Resetting tracking to Step 2 complete: {tracking_file}")
        
        # Read current CSV
        rows = []
        with open(tracking_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        if len(rows) > 1:  # Header + data rows
            header = rows[0]
            
            # Reset Step 3+ columns
            step3_plus_columns = [
                "Step 3 complete", "Step 3 scale method", "Step 3 scale applied", 
                "Step 3 ortho exported", "Step 3 model exported", "Step 3 processing time",
                "Step 4 complete", "Step 4 web published", "Sketchfab URL", 
                "Step 4 high-res exported", "Step 4 processing time",
                "Cameras Removed"
            ]
            
            # Reset Step 3+ status for all rows
            for i in range(1, len(rows)):  # Skip header
                # Reset Step 3+ columns
                for col_name in step3_plus_columns:
                    if col_name in header:
                        col_idx = header.index(col_name)
                        if col_idx < len(rows[i]):
                            rows[i][col_idx] = ""  # Clear the value
                
                # Reset Scale from DONE back to PASS (ready to re-export)
                if "Scale" in header:
                    scale_idx = header.index("Scale")
                    if scale_idx < len(rows[i]):
                        if rows[i][scale_idx] == "DONE":
                            rows[i][scale_idx] = "PASS"
                            print(f"   Reset Scale: DONE -> PASS for row {i}")
                
                # Update status to Step 2 complete (ready for Step 3)
                if "Status" in header:
                    status_idx = header.index("Status")
                    if status_idx < len(rows[i]):
                        current_status = str(rows[i][status_idx])
                        if any(step in current_status for step in ["Step 3", "Step 4", "DONE"]):
                            rows[i][status_idx] = "Step 2 complete"
            
            # Write updated CSV
            with open(tracking_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
            
            print("   Tracking reset to Step 2 complete")
        else:
            print("   No data rows found in tracking file")
    else:
        print(f"   Tracking file not found: {tracking_file}")
    
    print("\nRESET to AFTER STEP 2 COMPLETE!")
    print("\nWhat was PRESERVED:")
    print("- Step 0: Extracted frames (processing/frames/)")
    print("- Step 1: PSX files (processing/psxraw/)")
    print("- Step 2: Scaling data in PSX files and tracking")
    print("- All logs (output/logs/)")
    print("\nWhat was CLEARED:")
    print("- Step 3+: Models, orthomosaics, reports, output PSX files")
    print("- Step 3+: Moved frames (if any)")
    print("- Step 3+ tracking status")
    print("\nProject status: Ready for Step 3")
    print("Scale status: PASS (ready to export models)")
    print("\nNext step:")
    print("1. Run Step 3 to re-export models: python src/step3.py")
    print("\nHours of Steps 0-2 processing time preserved!")
    return True

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1].strip().strip('\'\"').rstrip('/')
    else:
        print("Please enter the absolute path to your project directory:")
        project_dir = input("Project directory: ").strip().strip('\'\"').rstrip('/')
    
    if not os.path.isdir(project_dir):
        print(f"ERROR: Project directory not found: {project_dir}")
        return 1
    
    success = reset_after_step2(project_dir)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

