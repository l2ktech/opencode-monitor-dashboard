#!/bin/bash
# Install dependencies if not present (simple check)
if ! python3 -c "import flask" &> /dev/null; then
    echo "Flask not found. Installing requirements..."
    pip install -r requirements.txt
fi

echo "Starting OCMonitor Dashboard on port 38002..."
python3 app.py
