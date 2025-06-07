#!/bin/bash

set -e  # Exit on error

FLATPAK_DEST=$1
ICON_NAME="io.github.Cookiiieee.WSelector"

# Create target directories and copy all available icons
for size in 16 32 48 64 96 128 192 256 512; do
    # Check both possible source locations and naming conventions
    for src_dir in "data/icons/hicolor" "icons"; do
        # Check for icons in standard hicolor directory structure first
        if [ -f "${src_dir}/${size}x${size}/apps/org.example.WSelector.png" ]; then
            mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/"
            cp "${src_dir}/${size}x${size}/apps/org.example.WSelector.png" \
               "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png"
            break
        # Check for icons with size in filename
        elif [ -f "${src_dir}/icon_1748228995_${size}x${size}.png" ]; then
            mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/"
            cp "${src_dir}/icon_1748228995_${size}x${size}.png" \
               "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png"
            break
        fi
    done
done

# Ensure we have at least the 256x256 icon
if [ ! -f "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" ]; then
    # Try to find any icon we can use as fallback
    for size in 512 128 64 48 32 16; do
        if [ -f "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png" ]; then
            mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/"
            cp "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png" \
               "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png"
            break
        fi
    done
fi

# Create symbolic links for any missing sizes using the 256x256 version
if [ -f "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" ]; then
    for size in 16 32 48 64 96 128 192 512; do
        if [ ! -f "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png" ]; then
            mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/"
            cp "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" \
               "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/${ICON_NAME}.png"
        fi
    done
    
    # Create a scalable icon symlink
    mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/scalable/apps/"
    ln -sf "../256x256/apps/${ICON_NAME}.png" \
           "${FLATPAK_DEST}/share/icons/hicolor/scalable/apps/${ICON_NAME}.png"
    
    # Also create a symbolic link in pixmaps for compatibility
    mkdir -p "${FLATPAK_DEST}/share/pixmaps/"
    ln -sf "../icons/hicolor/256x256/apps/${ICON_NAME}.png" \
           "${FLATPAK_DEST}/share/pixmaps/${ICON_NAME}.png"
fi

# Verify that at least one icon was installed
if [ -z "$(find "${FLATPAK_DEST}/share/icons" -name "${ICON_NAME}.png" -print -quit)" ]; then
    echo "ERROR: No icons were installed for ${ICON_NAME}" >&2
    exit 1
fi
