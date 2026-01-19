/**
 * Macrocomm Desktop App - Renderer Process
 * Handles UI interactions and API communication
 */

// =============================================================================
// THEME DEFINITIONS - Synced with ThemeProvider
// =============================================================================

const THEMES = {
    orange: {
        id: 'orange',
        name: 'Sunset Orange',
        colors: {
            50: '#FFF7ED', 100: '#FFEDD5', 200: '#FED7AA', 300: '#FDBA74',
            400: '#FB923C', 500: '#FF923F', 600: '#FF6E00', 700: '#E65100',
            800: '#C2410C', 900: '#9A3412', 950: '#7C2D12'
        }
    },
    blue: {
        id: 'blue',
        name: 'Ocean Blue',
        colors: {
            50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE', 300: '#93C5FD',
            400: '#60A5FA', 500: '#3B82F6', 600: '#2563EB', 700: '#1D4ED8',
            800: '#1E40AF', 900: '#1E3A8A', 950: '#172554'
        }
    },
    green: {
        id: 'green',
        name: 'Forest Green',
        colors: {
            50: '#ECFDF5', 100: '#D1FAE5', 200: '#A7F3D0', 300: '#6EE7B7',
            400: '#34D399', 500: '#10B981', 600: '#059669', 700: '#047857',
            800: '#065F46', 900: '#064E3B', 950: '#022C22'
        }
    },
    purple: {
        id: 'purple',
        name: 'Royal Purple',
        colors: {
            50: '#FAF5FF', 100: '#F3E8FF', 200: '#E9D5FF', 300: '#D8B4FE',
            400: '#C084FC', 500: '#A855F7', 600: '#9333EA', 700: '#7E22CE',
            800: '#6B21A8', 900: '#581C87', 950: '#3B0764'
        }
    },
    pink: {
        id: 'pink',
        name: 'Hot Pink',
        colors: {
            50: '#FDF2F8', 100: '#FCE7F3', 200: '#FBCFE8', 300: '#F9A8D4',
            400: '#F472B6', 500: '#EC4899', 600: '#DB2777', 700: '#BE185D',
            800: '#9D174D', 900: '#831843', 950: '#500724'
        }
    },
    cyan: {
        id: 'cyan',
        name: 'Electric Cyan',
        colors: {
            50: '#ECFEFF', 100: '#CFFAFE', 200: '#A5F3FC', 300: '#67E8F9',
            400: '#22D3EE', 500: '#06B6D4', 600: '#0891B2', 700: '#0E7490',
            800: '#155E75', 900: '#164E63', 950: '#083344'
        }
    },
    red: {
        id: 'red',
        name: 'Ruby Red',
        colors: {
            50: '#FEF2F2', 100: '#FEE2E2', 200: '#FECACA', 300: '#FCA5A5',
            400: '#F87171', 500: '#EF4444', 600: '#DC2626', 700: '#B91C1C',
            800: '#991B1B', 900: '#7F1D1D', 950: '#450A0A'
        }
    },
    amber: {
        id: 'amber',
        name: 'Golden Amber',
        colors: {
            50: '#FFFBEB', 100: '#FEF3C7', 200: '#FDE68A', 300: '#FCD34D',
            400: '#FBBF24', 500: '#F59E0B', 600: '#D97706', 700: '#B45309',
            800: '#92400E', 900: '#78350F', 950: '#451A03'
        }
    }
};

const THEME_STORAGE_KEY = 'macrocomm-theme';

// =============================================================================
// STATE
// =============================================================================

let config = {};
let conversationId = generateUUID();
let isConnected = false;
let messageHistory = [];
let currentTheme = THEMES.orange;

// =============================================================================
// THEME FUNCTIONS
// =============================================================================

/**
 * Apply theme to CSS variables
 */
function applyTheme(theme) {
    if (!theme || !theme.colors) return;

    const root = document.documentElement;

    // Set all brand color shades as CSS variables
    Object.entries(theme.colors).forEach(([shade, color]) => {
        root.style.setProperty(`--color-brand-${shade}`, color);
    });

    // Set RGB values for rgba() usage
    const hexToRgb = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
            ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
            : '255, 110, 0';
    };

    root.style.setProperty('--color-brand-rgb', hexToRgb(theme.colors[600]));

    // Update current theme
    currentTheme = theme;

    console.log(`🎨 Theme applied: ${theme.name}`);
}

/**
 * Load theme from localStorage
 */
function loadTheme() {
    try {
        const savedThemeId = localStorage.getItem(THEME_STORAGE_KEY);
        if (savedThemeId && THEMES[savedThemeId]) {
            applyTheme(THEMES[savedThemeId]);
            return THEMES[savedThemeId];
        }
    } catch (e) {
        console.warn('Failed to load theme from storage:', e);
    }

    // Default to orange
    applyTheme(THEMES.orange);
    return THEMES.orange;
}

/**
 * Listen for theme changes from other windows/tabs
 */
function setupThemeSync() {
    // Listen for storage changes (when React frontend changes theme)
    window.addEventListener('storage', (event) => {
        if (event.key === THEME_STORAGE_KEY && event.newValue) {
            const theme = THEMES[event.newValue];
            if (theme) {
                applyTheme(theme);
                console.log('🔄 Theme synced from storage:', theme.name);
            }
        }
    });

    // Listen for custom theme change events
    window.addEventListener('macrocomm-theme-change', (event) => {
        if (event.detail?.themeId) {
            const theme = THEMES[event.detail.themeId];
            if (theme) {
                applyTheme(theme);
                console.log('🔄 Theme synced via event:', theme.name);
            }
        }
    });

    // Periodically check localStorage for theme changes (fallback sync)
    setInterval(() => {
        try {
            const savedThemeId = localStorage.getItem(THEME_STORAGE_KEY);
            if (savedThemeId && THEMES[savedThemeId] && currentTheme.id !== savedThemeId) {
                applyTheme(THEMES[savedThemeId]);
                console.log('🔄 Theme synced via polling:', THEMES[savedThemeId].name);
            }
        } catch (e) {
            // Ignore errors
        }
    }, 2000); // Check every 2 seconds
}

// =============================================================================
// INITIALIZATION
// =============================================================================

// Initialize app
async function init() {
    console.log('🚀 Initializing desktop app...');

    // Load and apply theme first (before content renders)
    loadTheme();
    setupThemeSync();

    // Load configuration
    config = await window.electronAPI.getConfig();
    console.log('📋 Config loaded:', config);

    // Update UI with hotkey
    document.querySelectorAll('.input-hint').forEach(el => {
        el.innerHTML = el.innerHTML.replace('{{ hotkey }}', config.hotkey);
    });

    // Check backend connection
    await checkConnection();

    // Load cached conversations if offline
    if (config.offlineMode) {
        loadCachedConversations();
    }

    // Setup event listeners
    setupEventListeners();

    // Focus chat input
    document.getElementById('chat-input').focus();

    console.log('✅ App initialized');
}

/**
 * Check backend API connection
 */
async function checkConnection() {
    try {
        const response = await fetch(`${config.apiUrl}/health`, {
            method: 'GET',
            timeout: 5000
        });

        if (response.ok) {
            setConnectionStatus(true);
        } else {
            setConnectionStatus(false);
        }
    } catch (error) {
        console.error('Connection check failed:', error);
        setConnectionStatus(false);
    }
}

/**
 * Set connection status
 */
function setConnectionStatus(connected) {
    isConnected = connected;

    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const offlineBadge = document.getElementById('offline-badge');

    if (connected) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'Connected';
        offlineBadge.style.display = 'none';
    } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline';
        offlineBadge.style.display = config.offlineMode ? 'flex' : 'none';
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Focus search on hotkey event
    window.electronAPI.onFocusSearch(() => {
        document.getElementById('search-input').focus();
    });

    // Show settings on event
    window.electronAPI.onShowSettings(() => {
        showSettings();
    });

    // Recheck connection periodically
    setInterval(checkConnection, 30000); // Every 30 seconds
}

/**
 * Handle search input keypress
 */
function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        const query = event.target.value.trim();
        if (query) {
            askQuestion(query);
            event.target.value = '';
        }
    }
}

/**
 * Handle chat input keypress
 */
function handleChatKeypress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Auto-resize textarea
 */
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

/**
 * Ask a question (from quick buttons or search)
 */
function askQuestion(question) {
    const input = document.getElementById('chat-input');
    input.value = question;
    input.focus();
    sendMessage();
}

/**
 * Send message to backend
 */
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Add user message to UI
    addMessage('user', message);

    // Disable send button
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;

    try {
        if (!isConnected && !config.offlineMode) {
            addMessage('assistant', 'Sorry, I\'m currently offline. Please check your connection or enable offline mode in settings.');
            sendBtn.disabled = false;
            return;
        }

        // Show typing indicator
        const typingId = showTypingIndicator();

        // Send to backend API
        const response = await fetch(`${config.apiUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        });

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        // Add assistant response
        addMessage('assistant', data.response, {
            sources: data.sources || [],
            confidence: data.confidence
        });

        // Save to cache
        saveToCache(message, data.response);

        // Show notification if window is not focused
        if (document.hidden) {
            window.electronAPI.showNotification('New Response', data.response.substring(0, 100));
        }

    } catch (error) {
        console.error('Send message error:', error);
        removeTypingIndicator();
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`);
    }

    sendBtn.disabled = false;
}

/**
 * Add message to chat
 */
function addMessage(role, content, metadata = {}) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user'
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    // Add to container
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Save to history
    messageHistory.push({ role, content, timestamp: Date.now(), metadata });
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-indicator';
    typingDiv.id = 'typing-' + Date.now();

    typingDiv.innerHTML = `
        <div class="message-avatar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
        </div>
        <div class="message-content">
            <div class="loading">
                <div class="spinner"></div>
                Thinking...
            </div>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return typingDiv.id;
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator(id) {
    if (id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    } else {
        // Remove all typing indicators
        document.querySelectorAll('.typing-indicator').forEach(el => el.remove());
    }
}

/**
 * Save conversation to cache (localStorage)
 */
function saveToCache(userMessage, assistantResponse) {
    try {
        const cached = JSON.parse(localStorage.getItem('cachedConversations') || '[]');
        cached.push({
            conversationId,
            userMessage,
            assistantResponse,
            timestamp: Date.now()
        });

        // Keep only last 100 messages
        if (cached.length > 100) {
            cached.shift();
        }

        localStorage.setItem('cachedConversations', JSON.stringify(cached));
    } catch (error) {
        console.error('Failed to save to cache:', error);
    }
}

/**
 * Load cached conversations
 */
function loadCachedConversations() {
    try {
        const cached = JSON.parse(localStorage.getItem('cachedConversations') || '[]');
        console.log(`📦 Loaded ${cached.length} cached messages`);
    } catch (error) {
        console.error('Failed to load cache:', error);
    }
}

/**
 * Show settings panel
 */
async function showSettings() {
    document.getElementById('settings-panel').style.display = 'block';

    // Load current settings
    const config = await window.electronAPI.getConfig();

    document.getElementById('setting-api-url').value = config.apiUrl;
    document.getElementById('setting-hotkey').value = config.hotkey;
    document.getElementById('setting-always-on-top').checked = config.alwaysOnTop;
    document.getElementById('setting-auto-start').checked = config.autoStart;
    document.getElementById('setting-offline-mode').checked = config.offlineMode;
}

/**
 * Hide settings panel
 */
function hideSettings() {
    document.getElementById('settings-panel').style.display = 'none';
}

/**
 * Update single setting
 */
async function updateSetting(key, value) {
    const updates = {};
    updates[key] = value;
    await window.electronAPI.updateConfig(updates);
    config[key] = value;

    if (key === 'offlineMode') {
        setConnectionStatus(isConnected);
    }
}

/**
 * Save all settings
 */
async function saveSettings() {
    const apiUrl = document.getElementById('setting-api-url').value;
    const alwaysOnTop = document.getElementById('setting-always-on-top').checked;
    const autoStart = document.getElementById('setting-auto-start').checked;
    const offlineMode = document.getElementById('setting-offline-mode').checked;

    await window.electronAPI.updateConfig({
        apiUrl,
        alwaysOnTop,
        autoStart,
        offlineMode
    });

    // Update local config
    config.apiUrl = apiUrl;
    config.alwaysOnTop = alwaysOnTop;
    config.autoStart = autoStart;
    config.offlineMode = offlineMode;

    // Recheck connection
    await checkConnection();

    hideSettings();

    // Show success message
    addMessage('assistant', '✓ Settings saved successfully!');
}

/**
 * Minimize window to tray
 */
function minimizeWindow() {
    window.electronAPI.minimizeToTray();
}

/**
 * Open BI Platform dashboard in browser
 */
function openDashboard() {
    // Use IPC to open in default browser
    window.electronAPI.openDashboard();

    // Add message to chat
    addMessage('assistant', '🎨 Opening BI Platform in your browser...');

    console.log('📊 Opening BI Platform');
}

/**
 * Generate UUID
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
