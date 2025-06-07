#!/bin/bash
# Wrapper script for WSelector Flatpak

# Set up Python path
export PYTHONPATH="${FLATPAK_DEST}/lib/python3.12/site-packages:${PYTHONPATH}"

# Launch the application
python3 -m wselector "$@"
