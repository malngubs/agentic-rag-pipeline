/**
 * Preload Script - Bridge between main and renderer processes
 * Provides secure API for renderer to communicate with main process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Configuration
    getConfig: () => ipcRenderer.invoke('get-config'),
    updateConfig: (config) => ipcRenderer.invoke('update-config', config),

    // Window controls
    minimizeToTray: () => ipcRenderer.send('minimize-to-tray'),

    // Notifications
    showNotification: (title, body) => ipcRenderer.send('show-notification', { title, body }),

    // Event listeners
    onFocusSearch: (callback) => {
        ipcRenderer.on('focus-search', callback);
    },
    onShowSettings: (callback) => {
        ipcRenderer.on('show-settings', callback);
    },

    // Utility
    platform: process.platform
});
