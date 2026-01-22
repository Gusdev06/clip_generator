#!/bin/bash
# Run script for clips_generator

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: ./setup.sh"
    exit 1
fi

# Activate virtual environment and run
source venv/bin/activate
python main.py "$@"
