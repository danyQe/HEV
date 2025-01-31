#!/bin/bash

# Check if Python is installed
echo "Checking for Python installation..."
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Failed to create a virtual environment. Please check your Python installation."
    exit 1
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate the virtual environment. Ensure you are running this script with bash."
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "Failed to upgrade pip."
    exit 1
fi

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please check the requirements file or your internet connection."
    exit 1
fi

# Notify completion
echo "Setup completed successfully! Run 'python main.py' to start the application."
