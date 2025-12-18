#!/usr/bin/env python3
"""
Selective Reset via CSV Tracking

This script marks specific model IDs for reprocessing by setting their 
step completion flags to FALSE in the CSV tracking file.

Much simpler and safer than file-based reset operations.

Usage: 
  python src/utility/reset_selective.py [project_directory] --model-ids ID1,ID2,ID3 --steps 2,3
  python src/utility/reset_selective.py [project_directory] --model-ids ID1 --steps 2,3,4 --dry-run
"""

import os
import sys
import argparse

# Add the src directory to the path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    get_tracking_file,
    get_transect_status,
    mark_step_for_reprocessing,
    update_tracking,
    get_current_timestamp
)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Selective reset via CSV tracking flags')
    parser.add_argument('project_dir', nargs='?', help='Path to the project directory')
    parser.add_argument('--model-ids', required=True, help='Comma-separated list of model IDs to reset')
    parser.add_argument('--steps', required=True, help='Comma-separated list of step numbers to reset (e.g., 2,3,4)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    
    return parser.parse_args()

def get_project_directory(project_dir=None):
    """Get and validate project directory."""
    if project_dir:
        project_dir = project_dir.strip().strip('\'\"').rstrip('/')
    else:
        print("Please enter the absolute path to your project directory:")
        project_dir = input("Project directory: ").strip().strip('\'\"').rstrip('/')
    
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    return project_dir

def selective_reset_csv(model_ids, steps, dry_run=False):
    """Reset specific model IDs and steps via CSV tracking flags."""
    print(f"🎯 SELECTIVE RESET (CSV-based)")
    print(f"📝 Model IDs: {', '.join(model_ids)}")
    print(f"🔄 Steps to reset: {', '.join(map(str, steps))}")
    print("=" * 60)
    
    # Check which models exist
    existing_models = {}
    missing_models = []
    
    for model_id in model_ids:
        status = get_transect_status(model_id)
        if status:
            existing_models[model_id] = status
        else:
            missing_models.append(model_id)
    
    if missing_models:
        print(f"⚠️  Model IDs not found in tracking: {', '.join(missing_models)}")
    
    if not existing_models:
        print("❌ No valid model IDs found in tracking file")
        return False
    
    print("📋 RESET PLAN:")
    for model_id in existing_models.keys():
        current_status = existing_models[model_id].get("Status", "Unknown")
        print(f"  📍 {model_id} (current: {current_status})")
        for step in steps:
            current_complete = existing_models[model_id].get(f"Step {step} complete", "")
            print(f"    Step {step}: {current_complete} → FALSE")
    
    if dry_run:
        print(f"\n[DRY RUN] Would reset {len(existing_models)} models, {len(steps)} steps each")
        return True
    
    print(f"\n🔄 EXECUTING SELECTIVE RESET...")
    
    reset_count = 0
    for model_id in existing_models.keys():
        try:
            # Reset each specified step
            for step in steps:
                mark_step_for_reprocessing(model_id, step)
                print(f"  ✅ Reset Step {step} for {model_id}")
                reset_count += 1
            
            # Update overall status
            reset_steps_text = ", ".join([f"Step {s}" for s in steps])
            update_tracking(model_id, {
                "Status": f"Reset for reprocessing: {reset_steps_text}",
                "Notes": f"Selective reset on {get_current_timestamp()}: {reset_steps_text}"
            })
            
        except Exception as e:
            print(f"  ❌ Error resetting {model_id}: {e}")
            return False
    
    print(f"\n🎯 SELECTIVE RESET COMPLETE!")
    print(f"✅ Reset {reset_count} step flags across {len(existing_models)} models")
    print("\nNext steps:")
    if 2 in steps:
        print("1. Run: python src/step2.py (will process models with 'Step 2 complete' = FALSE)")
    if 3 in steps:
        print("2. Run: python src/step3.py (will process models with 'Step 3 complete' = FALSE)")
    if 4 in steps:
        print("3. Run: python src/step4.py (will process models with 'Step 4 complete' = FALSE)")
    
    return True

def main():
    """Main function"""
    args = parse_arguments()
    
    try:
        # Don't need project_dir for CSV-based reset, but validate for consistency
        if args.project_dir:
            get_project_directory(args.project_dir)
        
        model_ids = [mid.strip() for mid in args.model_ids.split(',')]
        steps = [int(s.strip()) for s in args.steps.split(',')]
        
        # Validate step numbers
        valid_steps = [0, 1, 2, 3, 4]
        invalid_steps = [s for s in steps if s not in valid_steps]
        if invalid_steps:
            raise ValueError(f"Invalid step numbers: {invalid_steps}. Valid steps: {valid_steps}")
        
        if not args.force and not args.dry_run:
            print(f"Will reset {len(model_ids)} model IDs for steps {steps}")
            print("This will mark the specified steps as incomplete (FALSE) in the CSV.")
            print("The main step scripts will then reprocess these models.")
            confirm = input("Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Reset cancelled")
                return 1
        
        success = selective_reset_csv(model_ids, steps, args.dry_run)
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n❌ Reset cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 