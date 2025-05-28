#!/bin/bash

# Create build directory
mkdir -p build-dir

# Build the flatpak
flatpak-builder --force-clean build-dir io.github.Cookiiieee.WSelector.json

# Build the flatpak bundle
flatpak build-bundle build-dir wselector.flatpak io.github.Cookiiieee.WSelector

# Install the flatpak bundle
flatpak install wselector.flatpak

# Run the application
flatpak run io.github.Cookiiieee.WSelector
