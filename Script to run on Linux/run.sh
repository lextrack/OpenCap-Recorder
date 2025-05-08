#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install it to run this application."
    exit 1
fi

# Activate the virtual environment
source "$DIR/venv/bin/activate"

# Make sure app.py is readable
chmod +r "$DIR/app.py"

# Run the Python app
python "$DIR/app.py"
