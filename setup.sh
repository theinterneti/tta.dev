#!/bin/bash
# Setup script for TTA.dev environment

echo "Setting up TTA.dev environment..."

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p data logs 2>/dev/null || true

# Set up environment variables
if [ -f .env ]; then
    source .env
else
    echo "Warning: .env file not found. Using default environment variables."
fi

echo "Setup complete. Starting application..."

# Start the application
python src/main.py

# Start the Streamlit app
streamlit run src/app.py
