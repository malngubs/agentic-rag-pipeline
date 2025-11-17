#!/bin/bash

# Icon Generation Script for Macrocomm Desktop App
# Requires: ImageMagick (convert command)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🎨 Generating desktop app icons..."

# Check for ImageMagick
if ! command -v convert &> /dev/null; then
    echo "❌ Error: ImageMagick is not installed"
    echo "   Install with: sudo apt-get install imagemagick (Linux)"
    echo "   or: brew install imagemagick (macOS)"
    exit 1
fi

# Generate main app icon (512x512 PNG)
echo "📦 Generating icon.png..."
convert icon.svg -resize 512x512 icon.png

# Generate Windows ICO (multiple sizes)
echo "🪟 Generating icon.ico..."
convert icon.svg -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico

# Generate tray icon (22x22 PNG)
echo "📌 Generating tray-icon.png..."
convert tray-icon.svg -resize 22x22 tray-icon.png

# macOS ICNS generation (requires iconutil, macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Generating icon.icns..."

    # Create iconset directory
    mkdir -p icon.iconset

    # Generate all required sizes
    convert icon.svg -resize 16x16 icon.iconset/icon_16x16.png
    convert icon.svg -resize 32x32 icon.iconset/icon_16x16@2x.png
    convert icon.svg -resize 32x32 icon.iconset/icon_32x32.png
    convert icon.svg -resize 64x64 icon.iconset/icon_32x32@2x.png
    convert icon.svg -resize 128x128 icon.iconset/icon_128x128.png
    convert icon.svg -resize 256x256 icon.iconset/icon_128x128@2x.png
    convert icon.svg -resize 256x256 icon.iconset/icon_256x256.png
    convert icon.svg -resize 512x512 icon.iconset/icon_256x256@2x.png
    convert icon.svg -resize 512x512 icon.iconset/icon_512x512.png
    convert icon.svg -resize 1024x1024 icon.iconset/icon_512x512@2x.png

    # Convert to ICNS
    iconutil -c icns icon.iconset

    # Clean up
    rm -rf icon.iconset

    echo "✅ macOS ICNS generated"
else
    echo "⚠️  Skipping ICNS generation (macOS only)"
    echo "   Creating placeholder ICNS..."
    cp icon.png icon.icns
fi

echo ""
echo "✅ Icon generation complete!"
echo ""
echo "Generated files:"
echo "  - icon.png (512x512)"
echo "  - icon.ico (Windows multi-size)"
echo "  - icon.icns (macOS)"
echo "  - tray-icon.png (22x22)"
echo ""
echo "🚀 You can now build the desktop app!"
