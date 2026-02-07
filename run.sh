#!/bin/bash

# Mantra WebLogix - Linux/macOS Startup Script

echo "========================================"
echo "Mantra WebLogix - Flask Application"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Start the Flask application
echo ""
echo "========================================"
echo "Starting Flask Application..."
echo "========================================"
echo ""
echo "The application will be available at:"
echo "http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
