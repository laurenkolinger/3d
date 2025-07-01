#!/usr/bin/env python3
"""
Reset Step 3: Remove all Step 3 outputs and reset tracking status

This script:
1. Deletes all orthomosaics, models, and reports created by step 3
2. Resets step 3 status in the tracking CSV
3. Allows you to re-run step 3 cleanly

Usage: python src/utility/reset_step3.py [project_directory]
"""

import os
import sys
import shutil
import csv
import glob
from pathlib import Path

def reset_step3(project_dir):
    """
    Reset all Step 3 outputs and tracking status.
    
    Args:
        project_dir (str): Path to the project directory
    """
    print(f"🔄 RESETTING STEP 3 for project: {project_dir}")
    
    # Define output directories
    output_dir = os.path.join(project_dir, "output")
    orthomosaics_dir = os.path.join(output_dir, "orthomosaics")
    models_dir = os.path.join(output_dir, "models") 
    reports_dir = os.path.join(output_dir, "reports")
    
    # 1. Delete all orthomosaics
    if os.path.exists(orthomosaics_dir):
        print(f"🗑️  Deleting orthomosaics: {orthomosaics_dir}")
        shutil.rmtree(orthomosaics_dir)
        print("   ✅ Orthomosaics deleted")
    
    # 2. Delete all models
    if os.path.exists(models_dir):
        print(f"🗑️  Deleting models: {models_dir}")
        shutil.rmtree(models_dir)
        print("   ✅ Models deleted")
    
    # 3. Delete all reports (step 3 reports only)
    if os.path.exists(reports_dir):
        step3_reports = glob.glob(os.path.join(reports_dir, "*_step3_report.pdf"))
        step3_reports.extend(glob.glob(os.path.join(reports_dir, "*_report.pdf")))
        step3_reports.extend(glob.glob(os.path.join(reports_dir, "*_report_manualScale.pdf")))
        for report in step3_reports:
            os.remove(report)
            print(f"   🗑️  Deleted: {os.path.basename(report)}")
        if step3_reports:
            print("   ✅ Step 3 reports deleted")
    
    # 4. Delete all PSX files AND their .files directories (step 2 outputs with step 3 modifications!)
    psx_patterns = [
        os.path.join(output_dir, "*.psx"),
        os.path.join(output_dir, "psx", "*.psx"),
        os.path.join(output_dir, "**", "*.psx")
    ]
    
    psx_files_deleted = 0
    files_dirs_deleted = 0
    
    for pattern in psx_patterns:
        psx_files = glob.glob(pattern, recursive=True)
        for psx_file in psx_files:
            # Delete the PSX file
            os.remove(psx_file)
            print(f"   🗑️  Deleted PSX: {os.path.basename(psx_file)}")
            psx_files_deleted += 1
            
            # Delete the corresponding .files directory
            files_dir = psx_file.replace('.psx', '.files')
            if os.path.exists(files_dir) and os.path.isdir(files_dir):
                shutil.rmtree(files_dir)
                print(f"   🗑️  Deleted .files: {os.path.basename(files_dir)}")
                files_dirs_deleted += 1
    
    if psx_files_deleted > 0:
        print(f"   ✅ {psx_files_deleted} PSX files + {files_dirs_deleted} .files directories deleted")
    else:
        print("   ℹ️  No PSX files found to delete")
    
    # 5. Reset tracking CSV
    project_name = os.path.basename(project_dir.rstrip('/'))
    tracking_file = os.path.join(project_dir, f"status_{project_name}.csv")
    
    if os.path.exists(tracking_file):
        print(f"📝 Resetting tracking file: {tracking_file}")
        
        # Read current CSV
        rows = []
        with open(tracking_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        if len(rows) > 1:  # Header + data rows
            header = rows[0]
            
            # Find step 2 and step 3 columns to reset both (FIXED: use actual column names)
            step2_columns = [
                "Step 2 complete", "Step 2 site", "Step 2 consolidation time"
            ]
            step3_columns = [
                "Step 3 complete", "Step 3 scale method", "Step 3 scale applied", 
                "Step 3 ortho exported", "Step 3 model exported", "Step 3 processing time"
            ]
            
            # Reset both step 2 and step 3 status for all rows
            for i in range(1, len(rows)):  # Skip header
                # Reset step 2 columns
                for col_name in step2_columns:
                    if col_name in header:
                        col_idx = header.index(col_name)
                        if col_idx < len(rows[i]):
                            rows[i][col_idx] = ""  # Clear the value
                
                # Reset step 3 columns
                for col_name in step3_columns:
                    if col_name in header:
                        col_idx = header.index(col_name)
                        if col_idx < len(rows[i]):
                            rows[i][col_idx] = ""  # Clear the value
                
                # Update status to step 1 complete (so both step 2 and 3 will reprocess)
                if "Status" in header:
                    status_idx = header.index("Status")
                    if status_idx < len(rows[i]) and ("Step 2" in str(rows[i][status_idx]) or "Step 3" in str(rows[i][status_idx])):
                        rows[i][status_idx] = "Step 1 complete"  # Reset to step 1 so both 2 and 3 reprocess
            
            # Write updated CSV
            with open(tracking_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
            
            print("   ✅ Tracking status reset")
    
    print("\n🎯 STEP 3 & STEP 2 RESET COMPLETE!")
    print("What was reset:")
    print("✅ All Step 3 outputs (orthomosaics, models, reports)")
    print("✅ All PSX files + .files directories from Step 2 (contained Step 3 modifications)")
    print("✅ Step 3 tracking status") 
    print("✅ Step 2 tracking status (forces PSX regeneration)")
    print("\nNow you can:")
    print("1. Re-run step 2 → Will regenerate clean PSX files (removes scale bars & component changes)")
    print("2. Re-run step 3 → For automatic scale bars")
    print("   OR")
    print("   Manually add scale bars in Metashape GUI → Run step3_manualScale.py")
    print("\nCommands:")
    print(f"PYTHONPATH=RELATIVE_PATH_TO_PROJECT/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step2.py")
    print(f"PYTHONPATH=RELATIVE_PATH_TO_PROJECT/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3.py")
    print(f"# OR for manual scale workflow:")
    print(f"PYTHONPATH=RELATIVE_PATH_TO_PROJECT/.venv/lib/python3.9/site-packages /Applications/MetashapePro.app/Contents/MacOS/MetashapePro -r src/step3_manualScale.py")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1].strip().strip('\'\"').rstrip('/')
    else:
        print("Please enter the absolute path to your project directory:")
        project_dir = input("Project directory: ").strip().strip('\'\"').rstrip('/')
    
    if not os.path.isdir(project_dir):
        print(f"❌ ERROR: Project directory not found: {project_dir}")
        return
    
    # Confirm reset
    print(f"\n⚠️  WARNING: This will reset Step 2 & Step 3 in: {project_dir}")
    print("   🗑️  Delete all Step 3 outputs:")
    print("      - All orthomosaics")
    print("      - All textured models") 
    print("      - All step 3 reports")
    print("      - All PSX files + .files directories from Step 2 (contain Step 3 modifications)")
    print("   📝 Reset tracking status:")
    print("      - Step 3 tracking status")
    print("      - Step 2 tracking status (forces PSX regeneration)")
    print("   ⚠️  You'll need to re-run both step 2 and step 3")
    
    confirm = input("\nProceed with reset? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("❌ Reset cancelled")
        return
    
    reset_step3(project_dir)

if __name__ == "__main__":
    main() 