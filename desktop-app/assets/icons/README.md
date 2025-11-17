# Desktop App Icons

## Required Icon Files

The desktop app requires the following icon files for full cross-platform support:

### Main Application Icons
- **icon.png** - 512x512px - Main application icon (all platforms)
- **icon.ico** - Windows icon file (16x16, 32x32, 48x48, 256x256)
- **icon.icns** - macOS icon file (16x16 to 512x512 @1x and @2x)

### System Tray Icons
- **tray-icon.png** - 22x22px - System tray icon (Linux/Windows)
- **tray-iconTemplate.png** - 22x22px - macOS tray icon (monochrome)

## Generating Icons from SVG

We've provided SVG source files (`icon.svg` and `tray-icon.svg`) that can be converted to the required formats:

### Using electron-icon-builder (Recommended)
```bash
npm install -g electron-icon-builder
electron-icon-builder --input=./icon.svg --output=./
```

### Using ImageMagick
```bash
# Generate PNG
convert icon.svg -resize 512x512 icon.png

# Generate ICO (Windows)
convert icon.svg -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico

# Generate ICNS (macOS) - requires iconutil
mkdir icon.iconset
sips -z 16 16 icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32 icon.png --out icon.iconset/icon_16x16@2x.png
# ... (repeat for all sizes)
iconutil -c icns icon.iconset
```

### Using Online Tools
- **CloudConvert**: https://cloudconvert.com/svg-to-png
- **SVG to ICO**: https://convertio.co/svg-ico/
- **SVG to ICNS**: https://anyconv.com/svg-to-icns-converter/

### Tray Icon Specifications

**Windows/Linux:**
- Size: 22x22px (or 16x16px)
- Format: PNG with transparency
- Name: `tray-icon.png`

**macOS:**
- Size: 22x22px @1x, 44x44px @2x
- Format: PNG with transparency
- Name: `tray-iconTemplate.png` (automatically inverts in dark mode)
- Should be monochrome with alpha channel

## Quick Setup (Temporary)

For development/testing, you can use the SVG files directly or create simple placeholder PNGs:

```bash
# If you have ImageMagick installed:
cd desktop-app/assets/icons/
convert icon.svg -resize 512x512 icon.png
convert tray-icon.svg -resize 22x22 tray-icon.png

# Copy for all platforms during development:
cp icon.png icon.ico
cp icon.png icon.icns
```

## Design Notes

The current icon design features:
- **Primary colors**: Purple gradient (#667eea to #764ba2)
- **Symbol**: Chat bubble with three dots (representing AI conversation)
- **Style**: Modern, clean, professional
- **Visibility**: High contrast for both light and dark system themes

## Customization

To customize the icons:
1. Edit `icon.svg` and `tray-icon.svg` with your preferred vector graphics editor (Inkscape, Figma, Adobe Illustrator)
2. Regenerate the platform-specific formats using the commands above
3. Test the icons at various sizes to ensure they remain legible
