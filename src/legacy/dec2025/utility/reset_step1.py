#!/usr/bin/env python3
"""
Reset After Step 1: Preserve Steps 0 & 1, Clear Steps 2+

This script resets a project to AFTER Step 1 by:
1. PRESERVING frames (Step 0) and PSX files (Step 1) - the time-consuming work
2. CLEARING all Step 2+ outputs (consolidated PSX, orthomosaics, models, reports)
3. RESETTING tracking to "Step 1 complete" status

Usage: python src/utility/reset_step1.py [project_directory]
"""

import os
import sys
import shutil
import csv
import glob
from pathlib import Path

def reset_after_step1(project_dir):
    """
    Reset project to AFTER Step 1 - preserves Steps 0 & 1, clears Steps 2+.
    
    Args:
        project_dir (str): Path to the project directory
    """
    print(f"🔄 RESET to AFTER STEP 1")
    print(f"📁 Project: {project_dir}")
    print("🔒 PRESERVING Steps 0 & 1 (frames & PSX files)")
    print("🗑️  CLEARING Steps 2+ outputs")
    print("=" * 60)
    
    # Define directories
    processing_dir = os.path.join(project_dir, "processing")
    frames_dir = os.path.join(processing_dir, "frames")
    psxraw_dir = os.path.join(processing_dir, "psxraw")
    output_dir = os.path.join(project_dir, "output")
    
    print("📋 RESET PLAN:")
    print("  Will PRESERVE (keep untouched):")
    if os.path.exists(frames_dir):
        print(f"    ✓ {frames_dir} (Step 0 frames)")
    else:
        print(f"    - {frames_dir} (Step 0 frames - not found)")
    
    if os.path.exists(psxraw_dir):
        print(f"    ✓ {psxraw_dir} (Step 1 PSX files)")
    else:
        print(f"    - {psxraw_dir} (Step 1 PSX files - not found)")
    
    print("\n  Will CLEAR (remove all contents):")
    if os.path.exists(output_dir):
        print(f"    ✓ {output_dir} (all Step 2+ outputs)")
    else:
        print(f"    - {output_dir} (Step 2+ outputs - not found)")
    
    print("\n  Will RESET tracking to Step 1 complete status")
    
    print("\n" + "=" * 60)
    print("⚠️  WARNING: This will clear all Step 2+ outputs!")
    print("This resets the project to AFTER Step 1 (ready for Step 2)")
    print("=" * 60)
    
    confirm = input("\nProceed with reset to AFTER Step 1? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("❌ Reset cancelled")
        return False
    
    print("\n🗑️  EXECUTING RESET to AFTER STEP 1...")
    
    # 1. PRESERVE Step 0 & Step 1 outputs (do nothing - they stay)
    if os.path.exists(frames_dir):
        frame_count = len(glob.glob(os.path.join(frames_dir, "**", "*"), recursive=True))
        print(f"🔒 PRESERVING frames directory: {frames_dir} ({frame_count} items)")
    
    if os.path.exists(psxraw_dir):
        psx_count = len(glob.glob(os.path.join(psxraw_dir, "*.psx")))
        print(f"🔒 PRESERVING PSX directory: {psxraw_dir} ({psx_count} PSX files)")
    
    # 2. CLEAR all Step 2+ outputs (entire output directory)
    if os.path.exists(output_dir):
        print(f"🗑️  Clearing output directory: {output_dir}")
        try:
            # Remove all contents but keep the directory
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"    ✅ Removed subdirectory: {item}")
                else:
                    os.remove(item_path)
                    print(f"    ✅ Removed file: {item}")
        except Exception as e:
            print(f"    ⚠️  Error clearing {output_dir}: {e}")
    else:
        print(f"🔍 Output directory not found, skipping: {output_dir}")
    
    # 3. Reset tracking CSV to Step 1 complete
    project_name = os.path.basename(project_dir.rstrip('/'))
    tracking_file = os.path.join(project_dir, f"status_{project_name}.csv")
    
    if os.path.exists(tracking_file):
        print(f"📝 Resetting tracking to Step 1 complete: {tracking_file}")
        
        # Read current CSV
        rows = []
        with open(tracking_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        if len(rows) > 1:  # Header + data rows
            header = rows[0]
            
            # Reset Step 2+ columns (preserve Step 0 & Step 1!)
            step2_plus_columns = [
                "Step 2 complete", "Step 2 site", "Step 2 consolidation time",
                "Step 3 complete", "Step 3 scale method", "Step 3 scale applied", 
                "Step 3 ortho exported", "Step 3 model exported", "Step 3 processing time",
                "Step 4 complete", "Step 4 web published", "Sketchfab URL", 
                "Step 4 high-res exported", "Step 4 processing time"
            ]
            
            # Reset Step 2+ status for all rows
            for i in range(1, len(rows)):  # Skip header
                # Reset Step 2+ columns
                for col_name in step2_plus_columns:
                    if col_name in header:
                        col_idx = header.index(col_name)
                        if col_idx < len(rows[i]):
                            rows[i][col_idx] = ""  # Clear the value
                
                # Update status to Step 1 complete (ready for Step 2)
                if "Status" in header:
                    status_idx = header.index("Status")
                    if status_idx < len(rows[i]):
                        current_status = str(rows[i][status_idx])
                        if any(step in current_status for step in ["Step 2", "Step 3", "Step 4"]):
                            rows[i][status_idx] = "Step 1 complete"  # Reset to ready for Step 2
            
            # Write updated CSV
            with open(tracking_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
            
            print("   ✅ Tracking reset to Step 1 complete")
        else:
            print("   ℹ️  No data rows found in tracking file")
    else:
        print(f"   ℹ️  Tracking file not found: {tracking_file}")
    
    print("\n🎯 RESET to AFTER STEP 1 COMPLETE!")
    print("\nWhat was PRESERVED:")
    print("🔒 Step 0: Extracted frames (processing/frames/)")
    print("🔒 Step 1: PSX files (processing/psxraw/)")
    print("🔒 Step 0 & Step 1 tracking status")
    print("\nWhat was CLEARED:")
    print("🗑️  Step 2+: All output/ directory contents")
    print("🗑️  Step 2+ tracking status")
    print("\nProject status: Ready for Step 2")
    print("\nNext steps:")
    print("1. Run: python src/step2.py (chunk management)")
    print("2. Then: python src/step3.py (model processing)")
    print("\n⚡ Hours of Step 0 & Step 1 processing time preserved!")
    return True

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1].strip().strip('\'\"').rstrip('/')
    else:
        print("Please enter the absolute path to your project directory:")
        project_dir = input("Project directory: ").strip().strip('\'\"').rstrip('/')
    
    if not os.path.isdir(project_dir):
        print(f"❌ ERROR: Project directory not found: {project_dir}")
        return 1
    
    success = reset_after_step1(project_dir)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 