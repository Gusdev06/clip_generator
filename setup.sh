#!/bin/bash
# Setup script for clips_generator

echo "Setting up YouTube to Vertical Clips Generator..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "To use the tool:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the tool: python main.py"
echo ""
echo "Or use the run.sh script: ./run.sh"
