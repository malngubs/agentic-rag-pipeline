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
 
// WebSocket state
let websocket = null;
let wsConnected = false;
let useWebSocket = true; // Prefer WebSocket when available
let pendingWsMessages = new Map(); // Track pending messages for streaming
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

    // Initialize WebSocket for streaming responses
    if (isConnected && useWebSocket) {
        initWebSocket();
    }
 
    // Always load previous conversation history
    loadCachedConversations();
 
    // Setup event listeners
    setupEventListeners();
 
    // Focus chat input
    document.getElementById('chat-input').focus();
 
    console.log('✅ App initialized');
}
 
// =============================================================================
// WEBSOCKET STREAMING - World-Class Real-Time Responses
// =============================================================================
 
/**
 * Initialize WebSocket connection for streaming responses
 */
function initWebSocket() {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        return; // Already connected
    }
 
    const wsUrl = config.apiUrl.replace('http', 'ws') + '/ws/chat';
    console.log('🔌 Connecting WebSocket:', wsUrl);
 
    try {
        websocket = new WebSocket(wsUrl);
 
        websocket.onopen = () => {
            wsConnected = true;
            console.log('✅ WebSocket connected');
        };
 
        websocket.onmessage = (event) => {
            handleWebSocketMessage(event.data);
        };
 
        websocket.onclose = (event) => {
            wsConnected = false;
            console.log('🔌 WebSocket closed:', event.code, event.reason);
 
            // Attempt to reconnect after 5 seconds
            if (isConnected) {
                setTimeout(() => {
                    console.log('🔄 Attempting WebSocket reconnect...');
                    initWebSocket();
                }, 5000);
            }
        };
 
        websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            wsConnected = false;
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        wsConnected = false;
    }
}
 
/**
 * Handle incoming WebSocket messages
 */
function handleWebSocketMessage(data) {
    try {
        const message = JSON.parse(data);
        console.log('📨 WS Message:', message.type);
 
        switch (message.type) {
            case 'system':
                // System message (welcome, etc.)
                console.log('System:', message.message);
                break;
 
            case 'stream_start':
                // Start of streaming response
                handleStreamStart(message);
                break;
 
            case 'stream_chunk':
                // Chunk of streaming response
                handleStreamChunk(message);
                break;
 
            case 'stream_end':
                // End of streaming response
                handleStreamEnd(message);
                break;
 
            case 'response':
                // Complete response (non-streaming)
                handleCompleteResponse(message);
                break;
 
            case 'error':
                // Error message
                handleWsError(message);
                break;
 
            default:
                console.log('Unknown message type:', message.type);
        }
    } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
    }
}
 
/**
 * Handle start of streaming response
 */
function handleStreamStart(message) {
    const messageId = message.message_id || Date.now().toString();
 
    // Create message placeholder
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant streaming';
    messageDiv.id = `msg-${messageId}`;
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
        </div>
        <div class="message-content">
            <span class="streaming-cursor"></span>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
 
    // Track streaming message
    pendingWsMessages.set(messageId, {
        content: '',
        element: messageDiv
    });
 
    // Remove typing indicator if present
    removeTypingIndicator();
}
 
/**
 * Handle streaming chunk
 */
function handleStreamChunk(message) {
    const messageId = message.message_id;
    const pending = pendingWsMessages.get(messageId);
 
    if (pending) {
        pending.content += message.chunk || '';
 
        // Update message content with Markdown rendering
        const contentEl = pending.element.querySelector('.message-content');
        contentEl.innerHTML = renderMarkdown(pending.content) + '<span class="streaming-cursor"></span>';
 
        // Scroll to bottom
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}
 
/**
 * Handle end of streaming response
 */
function handleStreamEnd(message) {
    const messageId = message.message_id;
    const pending = pendingWsMessages.get(messageId);
 
    if (pending) {
        // Remove streaming cursor
        pending.element.classList.remove('streaming');
        const contentEl = pending.element.querySelector('.message-content');
        contentEl.innerHTML = renderMarkdown(pending.content);
 
        // Add sources if available
        if (message.sources && message.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = `
                <div class="sources-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                    </svg>
                    <span>Sources (${message.sources.length})</span>
                </div>
                <div class="sources-list">
                    ${message.sources.map(src => `<span class="source-tag">${src}</span>`).join('')}
                </div>
            `;
            pending.element.appendChild(sourcesDiv);
        }
 
        // Save to history
        messageHistory.push({
            role: 'assistant',
            content: pending.content,
            timestamp: Date.now(),
            metadata: { sources: message.sources, confidence: message.confidence }
        });
 
        // Save to cache
        const lastUserMsg = messageHistory.filter(m => m.role === 'user').pop();
        if (lastUserMsg) {
            saveToCache(lastUserMsg.content, pending.content);
        }
 
        // Cleanup
        pendingWsMessages.delete(messageId);
 
        // Re-enable send button
        document.getElementById('send-btn').disabled = false;
    }
}
 
/**
 * Handle complete (non-streaming) response
 */
function handleCompleteResponse(message) {
    removeTypingIndicator();
 
    addMessage('assistant', message.response || message.message, {
        sources: message.sources || [],
        confidence: message.confidence
    });
 
    // Re-enable send button
    document.getElementById('send-btn').disabled = false;
}
 
/**
 * Handle WebSocket error
 */
function handleWsError(message) {
    removeTypingIndicator();
 
    addMessage('assistant', `⚠️ ${message.message || 'An error occurred'}`, {});
 
    document.getElementById('send-btn').disabled = false;
}
 
/**
 * Send message via WebSocket
 */
function sendViaWebSocket(message) {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        return false;
    }
 
    try {
        websocket.send(JSON.stringify({
            type: 'chat',
            message: message,
            conversation_id: conversationId,
            stream: true // Request streaming response
        }));
        return true;
    } catch (error) {
        console.error('WebSocket send failed:', error);
        return false;
    }
}

// =============================================================================
// CONNECTION MANAGEMENT - World-Class Auto-Reconnect
// =============================================================================
 
let reconnectAttempts = 0;
let reconnectTimer = null;
let isReconnecting = false;
const MAX_RECONNECT_ATTEMPTS = 10;
const BASE_RECONNECT_DELAY = 2000; // 2 seconds
const MAX_RECONNECT_DELAY = 30000; // 30 seconds
 
/**
 * Check backend API connection with retry logic
 */
async function checkConnection(isManualRetry = false) {
    if (isManualRetry) {
        reconnectAttempts = 0;
        setConnectionStatus('connecting');
    }
 
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
 
        const response = await fetch(`${config.apiUrl}/health`, {
            method: 'GET',
            signal: controller.signal
        });
 
        clearTimeout(timeoutId);
 
        if (response.ok) {
            const wasOffline = !isConnected;
            setConnectionStatus('connected');
            reconnectAttempts = 0;
            isReconnecting = false;
 
            // Notify user if we just reconnected
            if (wasOffline && !isManualRetry) {
                console.log('🔄 Reconnected to backend');
                showConnectionToast('Connected to Macrocomm AI', 'success');
            }
        } else {
            handleConnectionFailure();
        }
    } catch (error) {
        console.error('Connection check failed:', error.message);
        handleConnectionFailure();
    }
}
 
/**
 * Handle connection failure with exponential backoff
 */
function handleConnectionFailure() {
    setConnectionStatus('offline');
 
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        isReconnecting = true;
        reconnectAttempts++;
 
        // Exponential backoff: 2s, 4s, 8s, 16s, max 30s
        const delay = Math.min(
            BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts - 1),
            MAX_RECONNECT_DELAY
        );
 
        console.log(`🔄 Reconnect attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay/1000}s`);
 
        // Clear existing timer
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
        }
 
        reconnectTimer = setTimeout(() => {
            checkConnection();
        }, delay);
    } else {
        isReconnecting = false;
        console.log('❌ Max reconnect attempts reached');
        showConnectionToast('Unable to connect. Click to retry.', 'error');
    }
}
 
/**
 * Set connection status with visual feedback
 */
function setConnectionStatus(status) {
    // status: 'connected', 'offline', 'connecting'
    isConnected = status === 'connected';
 
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const offlineBadge = document.getElementById('offline-badge');
 
    switch (status) {
        case 'connected':
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connected';
            offlineBadge.style.display = 'none';
            break;
        case 'connecting':
            statusDot.className = 'status-dot connecting';
            statusText.textContent = 'Connecting...';
            offlineBadge.style.display = 'none';
            break;
        case 'offline':
        default:
            statusDot.className = 'status-dot offline';
            statusText.textContent = isReconnecting ? `Reconnecting (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...` : 'Offline';
            offlineBadge.style.display = config.offlineMode ? 'flex' : 'none';
            break;
    }
}
 
/**
 * Show connection status toast notification
 */
function showConnectionToast(message, type = 'info') {
    // Remove existing toast if any
    const existingToast = document.querySelector('.connection-toast');
    if (existingToast) {
        existingToast.remove();
    }
 
    const toast = document.createElement('div');
    toast.className = `connection-toast ${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        ${type === 'error' ? '<button onclick="checkConnection(true)">Retry</button>' : ''}
    `;
 
    document.body.appendChild(toast);
 
    // Auto-remove success toasts after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
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
 
    // Periodic connection check (every 10 seconds when connected, faster when offline)
    setInterval(() => {
        if (isConnected) {
            checkConnection(); // Check every 10 seconds when connected
        }
    }, 10000);
 
    // Click on status to manually retry
    const statusContainer = document.querySelector('.status-container');
    if (statusContainer) {
        statusContainer.style.cursor = 'pointer';
        statusContainer.addEventListener('click', () => {
            if (!isConnected) {
                checkConnection(true);
            }
        });
    }
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

        // Try WebSocket first for streaming responses
        if (wsConnected && useWebSocket && sendViaWebSocket(message)) {
            // Show typing indicator - will be replaced by streaming message
            showTypingIndicator();
            console.log('📤 Message sent via WebSocket (streaming)');
            // Button will be re-enabled when stream ends
            return;
        }
 
        // Fallback to HTTP API
        console.log('📤 Message sent via HTTP (non-streaming)');
 
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
 
        sendBtn.disabled = false;
 
    } catch (error) {
        console.error('Send message error:', error);
        removeTypingIndicator();
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`);
        sendBtn.disabled = false;
    }
}

// =============================================================================
// MARKDOWN RENDERING - World-Class Message Display
// =============================================================================
 
/**
 * Parse and render Markdown to HTML
 * Supports: bold, italic, code, code blocks, links, lists, headers
 */
function renderMarkdown(text) {
    if (!text) return '';
 
    let html = text;
 
    // Escape HTML entities first (security)
    html = html
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
 
    // Code blocks (``` ... ```)
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
        const langClass = lang ? ` language-${lang}` : '';
        return `<pre class="code-block${langClass}"><code>${code.trim()}</code></pre>`;
    });
 
    // Inline code (`code`)
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
 
    // Bold (**text** or __text__)
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
 
    // Italic (*text* or _text_)
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
 
    // Headers (## Header)
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
 
    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
 
    // Unordered lists (- item or * item)
    html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
 
    // Ordered lists (1. item)
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
 
    // Line breaks (double newline = paragraph)
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
 
    // Wrap in paragraph if not already wrapped
    if (!html.startsWith('<')) {
        html = `<p>${html}</p>`;
    }
 
    return html;
}
 
/**
 * Add message to chat with rich Markdown rendering
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
 
    // Render Markdown for assistant messages, plain text for user
    if (role === 'assistant') {
        messageContent.innerHTML = renderMarkdown(content);
    } else {
        messageContent.textContent = content;
    }
 
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
 
    // Add sources if available (for assistant messages)
    if (role === 'assistant' && metadata.sources && metadata.sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = `
            <div class="sources-header">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                </svg>
                <span>Sources (${metadata.sources.length})</span>
            </div>
            <div class="sources-list">
                ${metadata.sources.map(src => `<span class="source-tag">${src}</span>`).join('')}
            </div>
        `;
        messageDiv.appendChild(sourcesDiv);
    }
 
    // Add confidence indicator if available
    if (role === 'assistant' && metadata.confidence !== undefined) {
        const confidenceDiv = document.createElement('div');
        confidenceDiv.className = 'message-confidence';
        const confidencePercent = Math.round(metadata.confidence * 100);
        const confidenceClass = confidencePercent >= 80 ? 'high' : confidencePercent >= 50 ? 'medium' : 'low';
        confidenceDiv.innerHTML = `<span class="confidence-badge ${confidenceClass}">${confidencePercent}% confidence</span>`;
        messageDiv.appendChild(confidenceDiv);
    }

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

// =============================================================================
// CONVERSATION PERSISTENCE - World-Class Chat History
// =============================================================================
 
const CONVERSATIONS_KEY = 'macrocomm-conversations';
const CURRENT_CONVERSATION_KEY = 'macrocomm-current-conversation';
const MAX_CONVERSATIONS = 50;
const MAX_MESSAGES_PER_CONVERSATION = 100;
 
/**
 * Save message to current conversation
 */
function saveToCache(userMessage, assistantResponse) {
    try {
        saveConversation();
    } catch (error) {
        console.error('Failed to save to cache:', error);
    }
}
 
/**
 * Save current conversation to localStorage
 */
function saveConversation() {
    try {
        const conversations = JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '{}');
 
        conversations[conversationId] = {
            id: conversationId,
            messages: messageHistory.slice(-MAX_MESSAGES_PER_CONVERSATION),
            updatedAt: Date.now(),
            createdAt: conversations[conversationId]?.createdAt || Date.now(),
            title: generateConversationTitle()
        };
 
        // Prune old conversations
        const conversationIds = Object.keys(conversations);
        if (conversationIds.length > MAX_CONVERSATIONS) {
            conversationIds
                .sort((a, b) => conversations[a].updatedAt - conversations[b].updatedAt)
                .slice(0, conversationIds.length - MAX_CONVERSATIONS)
                .forEach(id => delete conversations[id]);
        }
 
        localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
        localStorage.setItem(CURRENT_CONVERSATION_KEY, conversationId);
    } catch (error) {
        console.error('Failed to save conversation:', error);
    }
}
 
/**
 * Generate conversation title from first user message
 */
function generateConversationTitle() {
    const firstUserMessage = messageHistory.find(m => m.role === 'user');
    if (firstUserMessage) {
        const title = firstUserMessage.content.substring(0, 50);
        return title.length < firstUserMessage.content.length ? title + '...' : title;
    }
    return 'New Conversation';
}
 
/**
 * Load and restore previous conversation
 */
function loadCachedConversations() {
    try {
        const savedConversationId = localStorage.getItem(CURRENT_CONVERSATION_KEY);
        const conversations = JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '{}');
 
        console.log(`📦 Found ${Object.keys(conversations).length} saved conversations`);
 
        if (savedConversationId && conversations[savedConversationId]) {
            conversationId = savedConversationId;
            messageHistory = conversations[savedConversationId].messages || [];
            renderConversationHistory();
            console.log(`📂 Restored conversation: ${conversationId}`);
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
    }
}
 
/**
 * Render conversation history to the chat UI
 */
function renderConversationHistory() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
 
    messageHistory.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role}`;
 
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = msg.role === 'user'
            ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
            : '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>';
 
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
 
        if (msg.role === 'assistant') {
            messageContent.innerHTML = renderMarkdown(msg.content);
        } else {
            messageContent.textContent = msg.content;
        }
 
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
 
        if (msg.role === 'assistant' && msg.metadata?.sources?.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = `
                <div class="sources-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                    </svg>
                    <span>Sources (${msg.metadata.sources.length})</span>
                </div>
                <div class="sources-list">
                    ${msg.metadata.sources.map(src => `<span class="source-tag">${src}</span>`).join('')}
                </div>
            `;
            messageDiv.appendChild(sourcesDiv);
        }
 
        messagesContainer.appendChild(messageDiv);
    });
 
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
 
/**
 * Start a new conversation
 */
function startNewConversation() {
    if (messageHistory.length > 0) {
        saveConversation();
    }
 
    conversationId = generateUUID();
    messageHistory = [];
 
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
 
    addMessage('assistant', '👋 Hello! I\'m your Macrocomm AI assistant. How can I help you today?');
    localStorage.setItem(CURRENT_CONVERSATION_KEY, conversationId);
    console.log(`🆕 Started new conversation: ${conversationId}`);
}
 
/**
 * Get list of all conversations
 */
function getConversationList() {
    try {
        const conversations = JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '{}');
        return Object.values(conversations)
            .sort((a, b) => b.updatedAt - a.updatedAt)
            .map(conv => ({
                id: conv.id,
                title: conv.title,
                updatedAt: conv.updatedAt,
                messageCount: conv.messages?.length || 0,
                isCurrent: conv.id === conversationId
            }));
    } catch (error) {
        return [];
    }
}
 
/**
 * Load a specific conversation by ID
 */
function loadConversation(id) {
    try {
        if (messageHistory.length > 0) {
            saveConversation();
        }
 
        const conversations = JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '{}');
        if (conversations[id]) {
            conversationId = id;
            messageHistory = conversations[id].messages || [];
            renderConversationHistory();
            localStorage.setItem(CURRENT_CONVERSATION_KEY, id);
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}
 
/**
 * Delete a conversation
 */
function deleteConversation(id) {
    try {
        const conversations = JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '{}');
        delete conversations[id];
        localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
 
        if (id === conversationId) {
            startNewConversation();
        }
    } catch (error) {
        console.error('Failed to delete conversation:', error);
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
