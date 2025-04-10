#!/bin/zsh
# reset_project_for_step0.sh
# Resets a project directory for rerunning Step 0 by emptying data/output folders.

# --- Configuration ---
# Top-level directories inside the project folder whose CONTENTS will be removed
DIRS_TO_EMPTY=(
    "data"
    "output"
)

# Files/patterns in the project root to remove
FILES_TO_REMOVE=(
    "*.csv"
)

# Essential items to KEEP (relative to project root)
# Note: The directories listed in DIRS_TO_EMPTY are kept, but their contents are removed.
ITEMS_TO_KEEP=(
    ".venv"
    "analysis_params.yaml"
    "video_source"
    "data"           # Keep the directory itself
    "output"         # Keep the directory itself
)
# --- End Configuration ---

# Check if project directory argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_project_directory>"
    echo "Example: $0 examples/sample_project_10april25_merged_paramssimplified"
    exit 1
fi

PROJECT_DIR=$(realpath "$1") # Get absolute path

# Check if the provided path is a directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory not found: $PROJECT_DIR"
    exit 1
fi

echo "-----------------------------------------------------"
echo "Resetting Project for Step 0:"
echo "  Project Directory: $PROJECT_DIR"
echo "-----------------------------------------------------"
echo ""
echo "This script will REMOVE THE CONTENTS of the following directories (if they exist):"
for dir in "${DIRS_TO_EMPTY[@]}"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
      echo "  - $PROJECT_DIR/$dir"
    fi
done
echo ""
echo "This script will REMOVE the following files/patterns from the project root (if they exist):"
for pattern in "${FILES_TO_REMOVE[@]}"; do
    matches=$(print -l "$PROJECT_DIR/$pattern"(N))
    if [ -n "$matches" ]; then
        echo "  - $PROJECT_DIR/$pattern"
    fi
done
echo ""
echo "The following items will BE KEPT:"
for item in "${ITEMS_TO_KEEP[@]}"; do
    if [ -e "$PROJECT_DIR/$item" ]; then
        echo "  - $PROJECT_DIR/$item"
    fi
done
echo "  - Contents of $PROJECT_DIR/video_source (if it exists)"
echo ""
echo "-----------------------------------------------------"
echo "!!! WARNING: This operation cannot be undone !!!"
echo "-----------------------------------------------------"

# --- Deletion ---
echo "Proceeding with deletion..."

# Empty specified directories
for dir in "${DIRS_TO_EMPTY[@]}"; do
    TARGET_PATH="$PROJECT_DIR/$dir"
    if [ -d "$TARGET_PATH" ]; then
        echo "Emptying directory: $TARGET_PATH"
        find "$TARGET_PATH" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
        if [ $? -ne 0 ]; then
            echo "Potential error emptying $TARGET_PATH (some contents might remain)"
        fi
    else
         echo "Directory not found, skipping: $TARGET_PATH"
    fi
done

# Derive the project ID (base name of the project directory)
PROJECT_ID=$(basename "$PROJECT_DIR")

# Construct the specific status CSV filename based on the derived PROJECT_ID
STATUS_CSV_FILENAME="status_${PROJECT_ID}.csv"
SPECIFIC_CSV_PATH="$PROJECT_DIR/$STATUS_CSV_FILENAME"

echo "--- Debugging Specific CSV Removal ---"
echo "Looking for specific file: $SPECIFIC_CSV_PATH"
ls -l "$SPECIFIC_CSV_PATH" # Check if the specific file exists
echo "Attempting removal with: rm -vf \"$SPECIFIC_CSV_PATH\""
rm -vf "$SPECIFIC_CSV_PATH"  # Use verbose, force, and target specific quoted path
echo "--- End Debugging Specific CSV Removal ---"

echo "-----------------------------------------------------"
echo "Project reset complete."
echo "-----------------------------------------------------"

exit 0