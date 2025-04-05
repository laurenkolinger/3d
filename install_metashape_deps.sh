#!/bin/bash

# Path to Metashape's Python directory
METASHAPE_PYTHON_DIR="/Applications/MetashapePro.app/Contents/Frameworks/Python.framework/Versions/3.9"
METASHAPE_PYTHON="$METASHAPE_PYTHON_DIR/bin/python3.9"

# Check if Metashape Python exists
if [ ! -f "$METASHAPE_PYTHON" ]; then
    echo "Error: Metashape Python not found at $METASHAPE_PYTHON"
    exit 1
fi

# Install dependencies using Metashape's Python pip
echo "Installing dependencies in Metashape's Python environment..."
echo "This will require sudo access to install packages in Metashape's Python environment"

# Download get-pip.py if it doesn't exist
if [ ! -f "get-pip.py" ]; then
    echo "Downloading get-pip.py..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
fi

# Install pip
echo "Installing pip..."
sudo "$METASHAPE_PYTHON" get-pip.py

# Install dependencies
echo "Installing dependencies..."
sudo "$METASHAPE_PYTHON" -m pip install -r requirements.txt

# Clean up
rm -f get-pip.py

echo "Done installing dependencies in Metashape's Python environment" 