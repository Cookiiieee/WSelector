#!/bin/bash

FLATPAK_DEST=$1

# Map of standard icon sizes to available icon files
declare -A icon_map=(
    ["16"]="16x16"
    ["32"]="32x32"
    ["48"]="48x48"
    ["64"]="64x64"
    ["96"]="96x96"
    ["128"]="128x128"
    ["192"]="192x192"
    ["256"]="256x256"
    ["512"]="512x512"
)

# Create target directories and copy icons
for size in "${!icon_map[@]}"; do
    icon_size=${icon_map[$size]}
    icon_src="icons/icon_1748228995_${icon_size}.png"
    
    if [ -f "$icon_src" ]; then
        mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/"
        cp "$icon_src" \
           "${FLATPAK_DEST}/share/icons/hicolor/${size}x${size}/apps/io.github.Cookiiieee.WSelector.png"
    fi
done

# Also create a symbolic link for the default icon
if [ -f "icons/icon_1748228995_256x256.png" ]; then
    mkdir -p "${FLATPAK_DEST}/share/icons/hicolor/scalable/apps/"
    ln -sf "${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/io.github.Cookiiieee.WSelector.png" \
            "${FLATPAK_DEST}/share/icons/hicolor/scalable/apps/io.github.Cookiiieee.WSelector.png"
fi
