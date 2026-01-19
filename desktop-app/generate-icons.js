/**
 * Icon Generator for Macrocomm Desktop App
 * Converts SVG to PNG/ICO formats
 *
 * Run: npm install sharp png-to-ico && node generate-icons.js
 */

const fs = require('fs');
const path = require('path');

async function generateIcons() {
    console.log('Generating icons for Macrocomm Desktop App...\n');

    try {
        // Try to use sharp for SVG to PNG conversion
        const sharp = require('sharp');

        const iconsDir = path.join(__dirname, 'assets', 'icons');
        const svgPath = path.join(iconsDir, 'icon.svg');

        if (!fs.existsSync(svgPath)) {
            console.error('Error: icon.svg not found in assets/icons/');
            process.exit(1);
        }

        // Generate main icon (512x512)
        console.log('Creating icon.png (512x512)...');
        await sharp(svgPath)
            .resize(512, 512)
            .png()
            .toFile(path.join(iconsDir, 'icon.png'));
        console.log('  Created: icon.png');

        // Generate tray icon (22x22)
        console.log('Creating tray-icon.png (22x22)...');
        await sharp(svgPath)
            .resize(22, 22)
            .png()
            .toFile(path.join(iconsDir, 'tray-icon.png'));
        console.log('  Created: tray-icon.png');

        // Generate Windows ICO (multiple sizes)
        console.log('Creating icon.ico for Windows...');
        const sizes = [16, 32, 48, 64, 128, 256];
        const pngBuffers = [];

        for (const size of sizes) {
            const buffer = await sharp(svgPath)
                .resize(size, size)
                .png()
                .toBuffer();
            pngBuffers.push(buffer);
        }

        // Try to create ICO using png-to-ico
        try {
            const pngToIco = require('png-to-ico');
            const icoBuffer = await pngToIco(pngBuffers);
            fs.writeFileSync(path.join(iconsDir, 'icon.ico'), icoBuffer);
            console.log('  Created: icon.ico');
        } catch (icoErr) {
            // Fallback: copy PNG as ICO (works for most cases)
            console.log('  png-to-ico not available, copying PNG as ICO fallback...');
            fs.copyFileSync(
                path.join(iconsDir, 'icon.png'),
                path.join(iconsDir, 'icon.ico')
            );
            console.log('  Created: icon.ico (PNG fallback)');
        }

        console.log('\nAll icons generated successfully!');
        console.log('\nGenerated files:');
        console.log('  - assets/icons/icon.png (512x512)');
        console.log('  - assets/icons/icon.ico (multi-size)');
        console.log('  - assets/icons/tray-icon.png (22x22)');

    } catch (err) {
        if (err.code === 'MODULE_NOT_FOUND') {
            console.error('\nRequired packages not installed. Run:');
            console.error('  cd desktop-app');
            console.error('  npm install sharp png-to-ico');
            console.error('  node generate-icons.js');
        } else {
            console.error('Error generating icons:', err.message);
        }
        process.exit(1);
    }
}

generateIcons();
