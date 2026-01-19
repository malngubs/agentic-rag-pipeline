/**
 * Macrocomm Desktop App - Main Process
 * Handles system tray, global hotkeys, and window management
 * Now with React frontend integration for premium UI
 */

const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, nativeImage, screen } = require('electron');
const path = require('path');
const Store = require('electron-store');
const http = require('http');

// Initialize persistent storage
const store = new Store({
    defaults: {
        apiUrl: 'http://localhost:8001',
        frontendUrl: 'http://localhost:3000',
        autoStart: true,
        alwaysOnTop: true,
        theme: 'dark',
        hotkey: 'CommandOrControl+Shift+M',
        windowBounds: { width: 420, height: 700 },
        offlineMode: false,
        useReactUI: true  // Enable React frontend
    }
});

/**
 * Check if a server is running on a given URL
 */
function checkServer(url) {
    return new Promise((resolve) => {
        const urlObj = new URL(url);
        const options = {
            hostname: urlObj.hostname,
            port: urlObj.port || 80,
            path: '/',
            method: 'HEAD',
            timeout: 2000
        };

        const req = http.request(options, (res) => {
            resolve(res.statusCode < 500);
        });

        req.on('error', () => resolve(false));
        req.on('timeout', () => {
            req.destroy();
            resolve(false);
        });

        req.end();
    });
}

let mainWindow = null;
let tray = null;
let isQuitting = false;

/**
 * Create the main application window
 */
async function createWindow() {
    // Get stored window bounds or defaults
    const bounds = store.get('windowBounds');

    // Get primary display
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

    // Position window in bottom-right corner by default
    const x = screenWidth - bounds.width - 20;
    const y = screenHeight - bounds.height - 20;

    mainWindow = new BrowserWindow({
        width: bounds.width,
        height: bounds.height,
        x: x,
        y: y,
        show: false, // Don't show initially
        frame: false, // Frameless window - completely removes title bar
        resizable: true,
        transparent: false,
        alwaysOnTop: store.get('alwaysOnTop'),
        backgroundColor: '#0a0a0a', // Dark background for premium feel
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../assets/icons/icon.png'),
        title: 'Macrocomm AI Assistant',
        skipTaskbar: false
    });

    // Remove application menu completely for professional look
    Menu.setApplicationMenu(null);

    // Determine which UI to load
    const useReactUI = store.get('useReactUI');
    const frontendUrl = store.get('frontendUrl');

    if (useReactUI) {
        // Check if React frontend is available
        const frontendAvailable = await checkServer(frontendUrl);

        if (frontendAvailable) {
            // Load React frontend for premium UI
            console.log('🎨 Loading React frontend from', frontendUrl);
            mainWindow.loadURL(frontendUrl);
        } else {
            // Fallback to local HTML
            console.log('⚠️ React frontend not available, using local UI');
            console.log('   Start frontend with: cd frontend && npm run dev');
            mainWindow.loadFile(path.join(__dirname, 'index.html'));
        }
    } else {
        // Use local HTML UI
        mainWindow.loadFile(path.join(__dirname, 'index.html'));
    }

    // Open DevTools in development mode
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    // Handle window close
    mainWindow.on('close', (event) => {
        if (!isQuitting) {
            event.preventDefault();
            mainWindow.hide();
            return false;
        }
    });

    // Save window bounds on resize/move
    mainWindow.on('resize', saveBounds);
    mainWindow.on('move', saveBounds);

    // Handle window ready
    mainWindow.once('ready-to-show', () => {
        // Don't show automatically - wait for hotkey or tray click
        console.log('✅ Window ready (hidden)');
    });

    // Handle load errors gracefully
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('❌ Failed to load:', errorDescription);
        // Fallback to local UI
        mainWindow.loadFile(path.join(__dirname, 'index.html'));
    });
}

/**
 * Save window bounds to persistent storage
 */
function saveBounds() {
    if (mainWindow) {
        const bounds = mainWindow.getBounds();
        store.set('windowBounds', bounds);
    }
}

/**
 * Create system tray icon and menu
 */
function createTray() {
    // Create tray icon
    const iconPath = path.join(__dirname, '../assets/icons/tray-icon.png');
    const trayIcon = nativeImage.createFromPath(iconPath);

    tray = new Tray(trayIcon.resize({ width: 16, height: 16 }));

    // Set tooltip
    tray.setToolTip('Macrocomm AI Assistant');

    // Create context menu
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show Assistant',
            click: () => {
                showWindow();
            },
            accelerator: store.get('hotkey')
        },
        { type: 'separator' },
        {
            label: 'Quick Search',
            click: () => {
                showQuickSearch();
            }
        },
        {
            label: 'Settings',
            click: () => {
                showSettings();
            }
        },
        { type: 'separator' },
        {
            label: 'Always on Top',
            type: 'checkbox',
            checked: store.get('alwaysOnTop'),
            click: (menuItem) => {
                const alwaysOnTop = menuItem.checked;
                store.set('alwaysOnTop', alwaysOnTop);
                if (mainWindow) {
                    mainWindow.setAlwaysOnTop(alwaysOnTop);
                }
            }
        },
        {
            label: 'Auto-start on Boot',
            type: 'checkbox',
            checked: store.get('autoStart'),
            click: (menuItem) => {
                const autoStart = menuItem.checked;
                store.set('autoStart', autoStart);
                app.setLoginItemSettings({
                    openAtLogin: autoStart
                });
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                isQuitting = true;
                app.quit();
            },
            accelerator: 'CommandOrControl+Q'
        }
    ]);

    tray.setContextMenu(contextMenu);

    // Double-click tray icon to show window
    tray.on('double-click', () => {
        showWindow();
    });
}

/**
 * Show/toggle the main window
 */
function showWindow() {
    if (mainWindow) {
        if (mainWindow.isVisible()) {
            mainWindow.hide();
        } else {
            mainWindow.show();
            mainWindow.focus();
        }
    }
}

/**
 * Show quick search overlay
 */
function showQuickSearch() {
    if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
        mainWindow.webContents.send('focus-search');
    }
}

/**
 * Show settings panel
 */
function showSettings() {
    if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
        mainWindow.webContents.send('show-settings');
    }
}

/**
 * Register global hotkey
 */
function registerHotkey() {
    const hotkey = store.get('hotkey');

    // Unregister previous hotkey
    globalShortcut.unregisterAll();

    // Register new hotkey
    const success = globalShortcut.register(hotkey, () => {
        console.log(`🔥 Hotkey triggered: ${hotkey}`);
        showWindow();
    });

    if (success) {
        console.log(`✅ Global hotkey registered: ${hotkey}`);
    } else {
        console.error(`❌ Failed to register hotkey: ${hotkey}`);
    }
}

/**
 * Handle IPC messages from renderer
 */
function setupIPC() {
    // Get app configuration
    ipcMain.handle('get-config', () => {
        return {
            apiUrl: store.get('apiUrl'),
            frontendUrl: store.get('frontendUrl'),
            autoStart: store.get('autoStart'),
            alwaysOnTop: store.get('alwaysOnTop'),
            theme: store.get('theme'),
            hotkey: store.get('hotkey'),
            offlineMode: store.get('offlineMode'),
            useReactUI: store.get('useReactUI')
        };
    });

    // Update app configuration
    ipcMain.handle('update-config', (event, config) => {
        Object.keys(config).forEach(key => {
            store.set(key, config[key]);
        });

        // Apply changes
        if (config.alwaysOnTop !== undefined && mainWindow) {
            mainWindow.setAlwaysOnTop(config.alwaysOnTop);
        }

        if (config.hotkey !== undefined) {
            registerHotkey();
        }

        if (config.autoStart !== undefined) {
            app.setLoginItemSettings({
                openAtLogin: config.autoStart
            });
        }

        return { success: true };
    });

    // Minimize to tray
    ipcMain.on('minimize-to-tray', () => {
        if (mainWindow) {
            mainWindow.hide();
        }
    });

    // Open BI Platform dashboard
    ipcMain.on('open-dashboard', () => {
        const { shell } = require('electron');
        const frontendUrl = store.get('frontendUrl');
        shell.openExternal(`${frontendUrl}/dashboards`);
        console.log('📊 Opening BI Platform in browser:', `${frontendUrl}/dashboards`);
    });

    // Show notification
    ipcMain.on('show-notification', (event, { title, body }) => {
        const { Notification } = require('electron');
        new Notification({
            title: title,
            body: body,
            icon: path.join(__dirname, '../assets/icons/icon.png')
        }).show();
    });
}

/**
 * App initialization
 */
app.whenReady().then(async () => {
    console.log('🚀 Macrocomm Desktop App starting...');
    console.log('🎨 Premium React UI enabled');

    // Create window and tray
    await createWindow();
    createTray();

    // Register global hotkey
    registerHotkey();

    // Setup IPC handlers
    setupIPC();

    // Set auto-start if enabled
    if (store.get('autoStart')) {
        app.setLoginItemSettings({
            openAtLogin: true
        });
    }

    console.log('✅ App initialized successfully');
    console.log(`📍 Backend API: ${store.get('apiUrl')}`);
    console.log(`🌐 Frontend URL: ${store.get('frontendUrl')}`);
    console.log(`⌨️  Global hotkey: ${store.get('hotkey')}`);
});

/**
 * Quit when all windows are closed (except on macOS)
 */
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        // Don't quit - keep running in tray
        console.log('All windows closed - running in background');
    }
});

/**
 * macOS: Re-create window when dock icon clicked
 */
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    } else {
        showWindow();
    }
});

/**
 * Before quit: cleanup
 */
app.on('before-quit', () => {
    isQuitting = true;
});

/**
 * App quit: unregister hotkeys
 */
app.on('will-quit', () => {
    globalShortcut.unregisterAll();
});

/**
 * Handle errors
 */
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
});
