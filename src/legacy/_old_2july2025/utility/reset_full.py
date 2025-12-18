#!/usr/bin/env python3
"""
Complete Project Reset Utility

This script resets a project directory to BEFORE Step 0 by emptying 
processing/ and output/ directories while keeping the folder structure and 
preserving video_source/ and analysis_params.yaml.

Usage: python src/utility/reset_full.py [project_directory]
"""

import os
import sys
import shutil
import glob
from pathlib import Path

def reset_complete(project_dir):
    """
    Complete project reset to BEFORE Step 0 - empties processing/ and output/ directories.
    
    Args:
        project_dir (str): Path to the project directory
    """
    print(f"🔄 COMPLETE PROJECT RESET to BEFORE Step 0")
    print(f"📁 Project: {project_dir}")
    print("=" * 60)
    
    # Top-level directories inside the project folder whose CONTENTS will be removed
    dirs_to_empty = [
        "processing",
        "output"
    ]
    
    # Files/patterns in the project root to remove
    files_to_remove = [
        "*.csv"
    ]
    
    # Essential items to KEEP (relative to project root)
    items_to_keep = [
        ".venv",
        "analysis_params.yaml", 
        "video_source"
    ]
    
    print("📋 RESET PLAN:")
    print("  Will EMPTY contents of these directories (but keep folders):")
    for dir_name in dirs_to_empty:
        target_path = os.path.join(project_dir, dir_name)
        if os.path.isdir(target_path):
            print(f"    ✓ {target_path}")
        else:
            print(f"    - {target_path} (not found - will create empty)")
    
    print("\n  Will REMOVE these files from project root:")
    for pattern in files_to_remove:
        matches = glob.glob(os.path.join(project_dir, pattern))
        if matches:
            for match in matches:
                print(f"    ✓ {os.path.basename(match)}")
        else:
            print(f"    - {pattern} (none found)")
    
    print("\n  Will KEEP these items UNTOUCHED:")
    for item in items_to_keep:
        item_path = os.path.join(project_dir, item)
        if os.path.exists(item_path):
            print(f"    ✓ {item}")
    print("    ✓ Folder structure (empty processing/, output/ directories)")
    
    print("\n" + "=" * 60)
    print("⚠️  WARNING: This operation cannot be undone!")
    print("This will reset the project to BEFORE Step 0 (frame extraction)")
    print("=" * 60)
    
    confirm = input("\nProceed with COMPLETE reset? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("❌ Reset cancelled")
        return False
    
    print("\n🗑️  EXECUTING COMPLETE RESET...")
    
    # Empty specified directories but keep the directory structure
    for dir_name in dirs_to_empty:
        target_path = os.path.join(project_dir, dir_name)
        
        if os.path.isdir(target_path):
            print(f"🗑️  Emptying directory: {target_path}")
            try:
                # Remove all contents but keep the directory
                for item in os.listdir(target_path):
                    item_path = os.path.join(target_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"    ✅ Removed subdirectory: {item}")
                    else:
                        os.remove(item_path)
                        print(f"    ✅ Removed file: {item}")
                print(f"    📁 Kept empty directory: {target_path}")
            except Exception as e:
                print(f"    ⚠️  Error emptying {target_path}: {e}")
        else:
            # Create the directory if it doesn't exist
            print(f"📁 Creating empty directory: {target_path}")
            try:
                os.makedirs(target_path, exist_ok=True)
                print(f"    ✅ Created: {target_path}")
            except Exception as e:
                print(f"    ⚠️  Error creating {target_path}: {e}")
    
    # Remove specific CSV files
    project_name = os.path.basename(project_dir.rstrip('/'))
    status_csv_filename = f"status_{project_name}.csv"
    specific_csv_path = os.path.join(project_dir, status_csv_filename)
    
    print(f"🗑️  Looking for tracking file: {specific_csv_path}")
    if os.path.exists(specific_csv_path):
        os.remove(specific_csv_path)
        print(f"    ✅ Removed: {status_csv_filename}")
    else:
        print(f"    ℹ️  Not found: {status_csv_filename}")
    
    # Remove other CSV files matching patterns
    for pattern in files_to_remove:
        matches = glob.glob(os.path.join(project_dir, pattern))
        for match in matches:
            if os.path.basename(match) != status_csv_filename:  # Don't double-delete
                os.remove(match)
                print(f"    ✅ Removed: {os.path.basename(match)}")
    
    print("\n🎯 COMPLETE PROJECT RESET FINISHED!")
    print("✅ All processing and output data cleared")
    print("✅ Empty folder structure maintained")
    print("✅ Project reset to BEFORE Step 0")
    print("\nNext steps:")
    print("1. Add video files to video_source/ directory (if not already there)")
    print("2. Run: python src/step0.py")
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
    
    success = reset_complete(project_dir)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 