#!/bin/bash

# Variables
REPO_NAME=$(basename "$PWD")  # Get the current directory name as the repo name
TARGET_DIR="/opt/$REPO_NAME"  # Target directory in /opt
VENV_DIR="$TARGET_DIR/venv"   # Virtual environment directory

# Copy the current directory (repo) to /opt
echo "Copying repository to /opt..."
sudo cp -r "$PWD" "$TARGET_DIR"

# Navigate to the new directory
cd "$TARGET_DIR" || { echo "Failed to navigate to $TARGET_DIR"; exit 1; }

# Create a Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install the dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found!"
fi

# Deactivate the virtual environment
deactivate

echo "Done!"
