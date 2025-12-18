"""
Utility: Migrate Old CSV Format to New Format

This script adds the new columns (Scale, Scale Error (m), Cameras Removed) 
to existing status CSV files that were created with the old format.

Usage:
    python src/utility/migrate_csv_to_new_format.py /path/to/old_status.csv
    
    Or to migrate the current project CSV:
    python src/utility/migrate_csv_to_new_format.py examples/TCRMP2025_3D/status_TCRMP2025_3D.csv
"""

import sys
import csv
import os
import shutil
from datetime import datetime

OLD_COLUMN_COUNT = 36
NEW_COLUMNS = ["Scale", "Scale Error (m)", "Cameras Removed"]

def migrate_csv(csv_path):
    """
    Migrate an old format CSV to the new format by adding new columns.
    
    Args:
        csv_path (str): Path to the CSV file to migrate
    """
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return False
    
    backup_path = f"{csv_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(csv_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    rows = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        print("Error: CSV file is empty")
        return False
    
    header = rows[0]
    current_col_count = len(header)
    
    print(f"Current CSV has {current_col_count} columns")
    
    if "Scale" in header and "Scale Error (m)" in header and "Cameras Removed" in header:
        print("CSV already has new format columns. No migration needed.")
        return True
    
    if current_col_count != OLD_COLUMN_COUNT:
        print(f"Warning: Expected {OLD_COLUMN_COUNT} columns in old format, found {current_col_count}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled")
            return False
    
    new_header = header + NEW_COLUMNS
    print(f"Adding columns: {NEW_COLUMNS}")
    print(f"New column count: {len(new_header)}")
    
    new_rows = [new_header]
    for i, row in enumerate(rows[1:], start=2):
        if not row or (len(row) == 1 and row[0] == ""):
            continue
        
        while len(row) < len(header):
            row.append("")
        
        new_row = row + ["", "", ""]
        new_rows.append(new_row)
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)
    
    print(f"\nMigration complete!")
    print(f"Migrated {len(new_rows)-1} data rows")
    print(f"Original backed up to: {backup_path}")
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.reader(f)
        verify_rows = list(reader)
        verify_header = verify_rows[0]
        print(f"\nVerification: CSV now has {len(verify_header)} columns")
        print(f"Last 3 columns: {verify_header[-3:]}")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python src/utility/migrate_csv_to_new_format.py /path/to/status.csv")
        print("\nExample:")
        print("  python src/utility/migrate_csv_to_new_format.py examples/TCRMP2025_3D/status_TCRMP2025_3D.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    success = migrate_csv(csv_path)
    
    if success:
        print("\nCSV migration successful!")
        sys.exit(0)
    else:
        print("\nCSV migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()


