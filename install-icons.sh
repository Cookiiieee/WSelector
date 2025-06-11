#!/bin/bash

set -e  # Exit on error

FLATPAK_DEST=$1
ICON_NAME="io.github.Cookiiieee.WSelector"

# Create target directories and copy all available icons from data/icons/hicolor
for size in 16 32 48 64 96 128 192 256 512; do
    SRC_ICON="data/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png"
    DEST_DIR="${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps"
    
    if [ -f "${SRC_ICON}" ]; then
        mkdir -p "${DEST_DIR}"
        cp "${SRC_ICON}" "${DEST_DIR}/"
        echo "Installed ${size}x${size} icon"
    fi
done

# Ensure we have at least the 256x256 icon (create from largest available if needed)
if [ ! -f "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" ]; then
    for size in 512 256 192 128 96 64 48 32 16; do
        SRC_ICON="${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png"
        if [ -f "${SRC_ICON}" ]; then
            mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/"
            cp "${SRC_ICON}" "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png"
            echo "Created 256x256 icon from ${size}x${size} version"
            break
        fi
    done
fi

# Create fallback icons for any missing sizes using the 256x256 version
if [ -f "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" ]; then
    for size in 16 32 48 64 96 128 192 512; do
        DEST_ICON="${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png"
        if [ ! -f "${DEST_ICON}" ]; then
            mkdir -p "$(dirname "${DEST_ICON}")"
            cp "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" "${DEST_ICON}"
            echo "Created ${size}x${size} fallback icon"
        fi
    done
    
    # Install SVG icon for scalable folder
    SVG_ICON="data/icons/hicolor/scalable/apps/${ICON_NAME}.svg"
    if [ -f "${SVG_ICON}" ]; then
        SCALABLE_DIR="${FLATPAK_DEST}/share/icons/hicolor/scalable/apps"
        mkdir -p "${SCALABLE_DIR}"
        cp "${SVG_ICON}" "${SCALABLE_DIR}/"
        echo "Installed scalable SVG icon"
    else
        echo "Warning: SVG icon not found at ${SVG_ICON}"
    fi
    
    # Create a symbolic link in pixmaps for compatibility
    PIXMAPS_DIR="${FLATPAK_DEST}/share/pixmaps"
    mkdir -p "${PIXMAPS_DIR}"
    if [ ! -e "${PIXMAPS_DIR}/${ICON_NAME}.png" ]; then
        ln -sf "../icons/hicolor/256x256/apps/${ICON_NAME}.png" "${PIXMAPS_DIR}/${ICON_NAME}.png"
        echo "Created pixmaps symlink"
    fi
fi

# Verify that at least one icon was installed
if [ -z "$(find "${FLATPAK_DEST}/share/icons" -name "${ICON_NAME}.png" -print -quit)" ]; then
    echo "ERROR: No icons were installed for ${ICON_NAME}" >&2
    exit 1
fi

echo "Icon installation completed successfully!"
