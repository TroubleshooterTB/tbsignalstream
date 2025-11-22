#!/bin/bash
set -e

echo "--- Preparing for deployment ---"

echo "Installing dependencies for Cloud Functions..."
cd functions
if [ ! -d "venv" ]; then
    python3.13 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo "Deploying to Firebase..."
firebase deploy

echo "--- Deployment finished successfully ---"
