/**
 * Macrocomm AI Assistant Widget
 * A production-ready chat widget implementing Macrocomm's brand guidelines
 * Motto: "SMART MADE SIMPLE"
 */

class MacrocommBubble {
    constructor(config = {}) {
        // Configuration with Macrocomm defaults
        this.config = {
            // API Configuration
            host: config.host || window.location.origin,
            tenant: config.tenant || 'default',
            
            // Branding (Macrocomm Brand Guidelines)
            theme: {
                primary: '#FF6E00',        // Sunset Orange
                secondary: '#FF923F',      // Bright Orange  
                accent: '#FFB67F',         // Sand
                background: '#FFFFFF',     // White
                text: '#000000',          // Black
                textSecondary: '#565A5C',  // Stone
                border: '#7C8082',        // Light Grey
                ...config.theme
            },
            
            // Widget Behavior
            position: config.position || 'bottom-right',
            autoOpen: config.autoOpen || false,
            showWelcome: config.showWelcome !== false,
            enableFileUpload: config.enableFileUpload || false,
            enableVoice: config.enableVoice || false,
            
            // Messages
            welcomeMessage: config.welcomeMessage || "Hi! I'm your Macrocomm AI Assistant. How can I help you today?",
            placeholder: config.placeholder || "Type your question here...",
            
            // Technical
            maxMessageLength: config.maxMessageLength || 4000,
            reconnectAttempts: config.reconnectAttempts || 5,
            
            ...config
        };
        
        // State management
        this.state = {
            isOpen: false,
            isConnected: false,
            isTyping: false,
            messages: [],
            connectionAttempts: 0,
            currentConversationId: null
        };
        
        // WebSocket connection
        this.ws = null;
        this.reconnectTimer = null;
        
        // DOM elements
        this.elements = {};
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the widget
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.render());
        } else {
            this.render();
        }
    }
    
    /**
     * Render the widget UI
     */
    render() {
        // Create widget container
        this.createWidgetContainer();
        
        // Create bubble button
        this.createBubbleButton();
        
        // Create chat interface
        this.createChatInterface();
        
        // Apply theme
        this.applyTheme();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize WebSocket connection
        this.connectWebSocket();
        
        // Show welcome message if enabled
        if (this.config.showWelcome && this.config.autoOpen) {
            this.openChat();
        }
    }
    
    /**
     * Create the main widget container
     */
    createWidgetContainer() {
        const container = document.createElement('div');
        container.id = 'macrocomm-widget';
        container.className = `macrocomm-widget macrocomm-widget-${this.config.position}`;
        
        container.innerHTML = `
            <style>
                /* Widget Styles - Macrocomm Brand Guidelines */
                .macrocomm-widget {
                    position: fixed !important;
                    bottom: 20px !important;
                    right: 20px !important;
                    z-index: 999999 !important;
                    font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    line-height: 1.4;
                    color: #000000;
                    box-sizing: border-box;
                }

                .macrocomm-widget *, 
                .macrocomm-widget *::before, 
                .macrocomm-widget *::after {
                    box-sizing: border-box;
                }
                
                /* Position variants */
                .macrocomm-widget-bottom-right {
                    bottom: 20px !important;
                    right: 20px !important;
                }
                
                .macrocomm-widget-bottom-left {
                    bottom: 20px;
                    left: 20px;
                }
                
                .macrocomm-widget-top-right {
                    top: 20px;
                    right: 20px;
                }
                
                .macrocomm-widget-top-left {
                    top: 20px;
                    left: 20px;
                }
                
                /* Bubble button */
                .macrocomm-bubble {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #FF6E00 0%, #FF923F 100%);
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 20px rgba(255, 110, 0, 0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }
                
                .macrocomm-bubble:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 25px rgba(255, 110, 0, 0.4);
                }
                
                .macrocomm-bubble::before {
                    content: '';
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.2); opacity: 0.7; }
                    100% { transform: scale(1.4); opacity: 0; }
                }
                
                .macrocomm-bubble-icon {
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    z-index: 1;
                }
                
                /* Chat interface */
                .macrocomm-chat {
                    position: fixed !important;
                    bottom: 80px !important;
                    right: 20px !important;
                    width: 380px !important;
                    height: 500px !important;
                    max-width: calc(100vw - 40px) !important;
                    max-height: calc(100vh - 120px) !important;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15);
                    transform: translateY(100%) scale(0.8);
                    opacity: 0;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    z-index: 999999 !important;
                }
                
                .macrocomm-chat.open {
                    transform: translateY(0) scale(1);
                    opacity: 1;
                }
                
                /* Header */
                .macrocomm-header {
                    background: linear-gradient(135deg, #FF6E00 0%, #FF923F 100%);
                    color: white;
                    padding: 16px 20px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                
                .macrocomm-header-content {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                
                .macrocomm-logo {
                    width: 32px;
                    height: 32px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 16px;
                }
                
                .macrocomm-header-text h3 {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                
                .macrocomm-header-text p {
                    margin: 0;
                    font-size: 12px;
                    opacity: 0.9;
                }
                
                .macrocomm-close {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 20px;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }
                
                .macrocomm-close:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
                
                /* Messages area */
                .macrocomm-messages {
                    flex: 1;
                    padding: 20px;
                    overflow-y: auto;
                    background: #fafafa;
                }
                
                .macrocomm-message {
                    margin-bottom: 16px;
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                }
                
                .macrocomm-message.user {
                    justify-content: flex-end;
                }
                
                .macrocomm-message.user .macrocomm-message-content {
                    background: #FF6E00;
                    color: white;
                    order: -1;
                }
                
                .macrocomm-message-avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: #FF6E00;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                    flex-shrink: 0;
                }
                
                .macrocomm-message.user .macrocomm-message-avatar {
                    background: #565A5C;
                }
                
                .macrocomm-message-content {
                    background: white;
                    padding: 12px 16px;
                    border-radius: 16px;
                    max-width: 280px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                /* Typing indicator */
                .macrocomm-typing {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    color: #7C8082;
                    font-size: 12px;
                    margin-bottom: 8px;
                }
                
                .macrocomm-typing-dots {
                    display: flex;
                    gap: 4px;
                }
                
                .macrocomm-typing-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: #FF6E00;
                    animation: typing 1.4s infinite ease-in-out;
                }
                
                .macrocomm-typing-dot:nth-child(2) { animation-delay: 0.2s; }
                .macrocomm-typing-dot:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes typing {
                    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
                    30% { transform: translateY(-10px); opacity: 1; }
                }
                
                /* Input area */
                .macrocomm-input {
                    padding: 16px 20px;
                    background: white;
                    border-top: 1px solid #e5e5e5;
                }
                
                .macrocomm-input-form {
                    display: flex;
                    gap: 8px;
                    align-items: flex-end;
                }
                
                .macrocomm-input-field {
                    flex: 1;
                    border: 1px solid #e5e5e5;
                    border-radius: 20px;
                    padding: 10px 16px;
                    font-size: 14px;
                    resize: none;
                    max-height: 100px;
                    min-height: 40px;
                    font-family: inherit;
                    outline: none;
                    transition: border-color 0.2s;
                }
                
                .macrocomm-input-field:focus {
                    border-color: #FF6E00;
                }
                
                .macrocomm-send {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #FF6E00;
                    border: none;
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                    flex-shrink: 0;
                }
                
                .macrocomm-send:hover {
                    background: #FF923F;
                }
                
                .macrocomm-send:disabled {
                    background: #e5e5e5;
                    cursor: not-allowed;
                }
                
                /* Connection status */
                .macrocomm-status {
                    padding: 8px 20px;
                    text-align: center;
                    font-size: 12px;
                    background: #f0f0f0;
                    color: #565A5C;
                }
                
                .macrocomm-status.connected {
                    background: rgba(40, 167, 69, 0.1);
                    color: #28a745;
                }
                
                .macrocomm-status.disconnected {
                    background: rgba(220, 53, 69, 0.1);
                    color: #dc3545;
                }
                
                /* Mobile responsive */
                @media (max-width: 480px) {
                    .macrocomm-chat {
                        width: calc(100vw - 40px);
                        height: calc(100vh - 140px);
                        bottom: 80px;
                    }
                    
                    .macrocomm-widget-bottom-right,
                    .macrocomm-widget-bottom-left {
                        right: 20px;
                        left: 20px;
                    }
                }
                
                /* Accessibility */
                .macrocomm-widget [role="button"]:focus {
                    outline: 2px solid #FF6E00;
                    outline-offset: 2px;
                }
                
                /* Hide scrollbar for messages */
                .macrocomm-messages::-webkit-scrollbar {
                    width: 4px;
                }
                
                .macrocomm-messages::-webkit-scrollbar-track {
                    background: transparent;
                }
                
                .macrocomm-messages::-webkit-scrollbar-thumb {
                    background: rgba(255, 110, 0, 0.3);
                    border-radius: 2px;
                }
                
                .macrocomm-messages::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 110, 0, 0.5);
                }
            </style>
        `;
        
        document.body.appendChild(container);
        this.elements.container = container;
    }
    
    /**
     * Create the bubble button
     */
    createBubbleButton() {
        const bubble = document.createElement('button');
        bubble.className = 'macrocomm-bubble';
        bubble.setAttribute('aria-label', 'Open Macrocomm AI Assistant');
        bubble.innerHTML = `
            <span class="macrocomm-bubble-icon">M</span>
        `;
        
        this.elements.container.appendChild(bubble);
        this.elements.bubble = bubble;
    }
    
    /**
     * Create the chat interface
     */
    createChatInterface() {
        const chat = document.createElement('div');
        chat.className = 'macrocomm-chat';
        chat.innerHTML = `
            <div class="macrocomm-header">
                <div class="macrocomm-header-content">
                    <div class="macrocomm-logo">M</div>
                    <div class="macrocomm-header-text">
                        <h3>Macrocomm Assistant</h3>
                        <p>Smart Made Simple</p>
                    </div>
                </div>
                <button class="macrocomm-close" aria-label="Close chat">×</button>
            </div>
            
            <div class="macrocomm-status connecting">Connecting...</div>
            
            <div class="macrocomm-messages" role="log" aria-live="polite" aria-label="Chat messages">
                <!-- Messages will be inserted here -->
            </div>
            
            <div class="macrocomm-input">
                <form class="macrocomm-input-form">
                    <textarea 
                        class="macrocomm-input-field" 
                        placeholder="${this.config.placeholder}"
                        rows="1"
                        maxlength="${this.config.maxMessageLength}"
                        aria-label="Type your message"
                    ></textarea>
                    <button type="submit" class="macrocomm-send" aria-label="Send message" disabled>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                        </svg>
                    </button>
                </form>
            </div>
        `;
        
        this.elements.container.appendChild(chat);
        this.elements.chat = chat;
        this.elements.messages = chat.querySelector('.macrocomm-messages');
        this.elements.inputForm = chat.querySelector('.macrocomm-input-form');
        this.elements.inputField = chat.querySelector('.macrocomm-input-field');
        this.elements.sendButton = chat.querySelector('.macrocomm-send');
        this.elements.closeButton = chat.querySelector('.macrocomm-close');
        this.elements.status = chat.querySelector('.macrocomm-status');
    }
    
    /**
     * Apply custom theme
     */
    applyTheme() {
        const theme = this.config.theme;
        
        // Create custom CSS variables
        const style = document.createElement('style');
        style.textContent = `
            .macrocomm-widget {
                --primary-color: ${theme.primary};
                --secondary-color: ${theme.secondary};
                --accent-color: ${theme.accent};
                --background-color: ${theme.background};
                --text-color: ${theme.text};
                --text-secondary-color: ${theme.textSecondary};
                --border-color: ${theme.border};
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Bubble click
        this.elements.bubble.addEventListener('click', () => {
            this.toggleChat();
        });

        // Close button
        this.elements.closeButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.closeChat();
        });

        // Form submission
        this.elements.inputForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Input field auto-resize
        this.elements.inputField.addEventListener('input', () => {
            this.autoResizeInput();
            this.updateSendButton();
        });
        
        // Keyboard shortcuts
        this.elements.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.state.isOpen) {
                this.closeChat();
            }
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (this.state.isOpen && !this.elements.container.contains(e.target)) {
                this.closeChat();
            }
        });
    }
    
    /**
     * Connect to WebSocket
     */
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${this.config.host.replace(/^https?:\/\//, '')}/ws/chat`;
        
        this.updateStatus('Connecting...', 'connecting');
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.state.isConnected = true;
                this.state.connectionAttempts = 0;
                this.updateStatus('Connected', 'connected');
                
                // Send initial message if this is the first connection
                if (this.config.showWelcome && this.state.messages.length === 0) {
                    this.addMessage(this.config.welcomeMessage, 'assistant');
                }
                
                // Hide status after successful connection
                setTimeout(() => {
                    this.elements.status.style.display = 'none';
                }, 2000);
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                this.state.isConnected = false;
                this.updateStatus('Disconnected', 'disconnected');
                this.elements.status.style.display = 'block';
                
                // Attempt to reconnect
                if (this.state.connectionAttempts < this.config.reconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Connection error', 'disconnected');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateStatus('Connection failed', 'disconnected');
            this.scheduleReconnect();
        }
    }
    
    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'response':
                this.hideTyping();
                this.addMessage(data.response, 'assistant', {
                    intent: data.intent,
                    confidence: data.confidence,
                    sources: data.sources
                });
                break;
                
            case 'workflow_step':
                // Show progress for agentic workflow
                this.showWorkflowStep(data);
                break;
                
            case 'error':
                this.hideTyping();
                this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
                break;
                
            case 'typing':
                if (data.is_typing) {
                    this.showTyping();
                } else {
                    this.hideTyping();
                }
                break;
        }
    }
    
    /**
     * Schedule WebSocket reconnection
     */
    scheduleReconnect() {
        this.state.connectionAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.state.connectionAttempts), 30000);
        
        this.updateStatus(`Reconnecting in ${Math.ceil(delay / 1000)}s...`, 'disconnected');
        
        this.reconnectTimer = setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }
    
    /**
     * Send a message
     */
    sendMessage() {
        const message = this.elements.inputField.value.trim();
        
        if (!message || !this.state.isConnected) {
            return;
        }
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.elements.inputField.value = '';
        this.autoResizeInput();
        this.updateSendButton();
        
        // Show typing indicator
        this.showTyping();
        
        // Send via WebSocket
        this.ws.send(JSON.stringify({
            type: 'chat',  // Make sure this is 'chat' not 'chat_message'
            message: message,
            conversation_id: this.state.currentConversationId || null,
            tenant: this.config.tenant
        }));
    }
    
    /**
     * Add a message to the chat
     */
    addMessage(content, sender, metadata = {}) {
        const message = {
            id: Date.now(),
            content,
            sender,
            timestamp: new Date(),
            metadata
        };
        
        this.state.messages.push(message);
        
        const messageElement = document.createElement('div');
        messageElement.className = `macrocomm-message ${sender}`;
        messageElement.innerHTML = `
            <div class="macrocomm-message-avatar">
                ${sender === 'user' ? 'U' : 'M'}
            </div>
            <div class="macrocomm-message-content">
                ${this.formatMessage(content)}
                ${metadata.sources ? this.formatSources(metadata.sources) : ''}
            </div>
        `;
        
        this.elements.messages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    /**
     * Format message content
     */
    formatMessage(content) {
        // Basic formatting with null checks
        if (!content || typeof content !== 'string') {
            return content || '';
        }
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    /**
     * Format sources
     */
    formatSources(sources) {
        if (!sources || sources.length === 0) return '';
        
        return `
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e5e5; font-size: 12px; color: #7C8082;">
                <strong>Sources:</strong>
                ${sources.map(source => `<br>• ${source.title || 'Document'}`).join('')}
            </div>
        `;
    }
    
    /**
     * Show typing indicator
     */
    showTyping() {
        if (this.elements.typing) return;
        
        this.state.isTyping = true;
        
        const typing = document.createElement('div');
        typing.className = 'macrocomm-typing';
        typing.innerHTML = `
            <div class="macrocomm-message-avatar">M</div>
            <div>
                <div class="macrocomm-typing-dots">
                    <div class="macrocomm-typing-dot"></div>
                    <div class="macrocomm-typing-dot"></div>
                    <div class="macrocomm-typing-dot"></div>
                </div>
            </div>
        `;
        
        this.elements.messages.appendChild(typing);
        this.elements.typing = typing;
        this.scrollToBottom();
    }
    
    /**
     * Hide typing indicator
     */
    hideTyping() {
        if (this.elements.typing) {
            this.elements.typing.remove();
            this.elements.typing = null;
        }
        this.state.isTyping = false;
    }
    
    /**
     * Show workflow step
     */
    showWorkflowStep(data) {
        // For now, just update typing with step info
        if (this.elements.typing) {
            const dots = this.elements.typing.querySelector('.macrocomm-typing-dots');
            if (dots) {
                dots.innerHTML = `<span style="font-size: 12px;">${data.reasoning}</span>`;
            }
        }
    }
    
    /**
     * Update connection status
     */
    updateStatus(message, type) {
        this.elements.status.textContent = message;
        this.elements.status.className = `macrocomm-status ${type}`;
    }
    
    /**
     * Auto-resize input field
     */
    autoResizeInput() {
        const field = this.elements.inputField;
        field.style.height = 'auto';
        field.style.height = Math.min(field.scrollHeight, 100) + 'px';
    }
    
    /**
     * Update send button state
     */
    updateSendButton() {
        const hasText = this.elements.inputField.value.trim().length > 0;
        this.elements.sendButton.disabled = !hasText || !this.state.isConnected;
    }
    
    /**
     * Scroll messages to bottom
     */
    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }
    
    /**
     * Toggle chat open/closed
     */
    toggleChat() {
        if (this.state.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    /**
     * Open chat
     */
    openChat() {
        this.state.isOpen = true;
        this.elements.chat.classList.add('open');
        this.elements.inputField.focus();
    }
    
    /**
     * Close chat
     */
    closeChat() {
        this.state.isOpen = false;
        this.elements.chat.classList.remove('open');
    }
    
    /**
     * Destroy widget
     */
    destroy() {
        if (this.ws) {
            this.ws.close();
        }
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        if (this.elements.container) {
            this.elements.container.remove();
        }
    }
}

// Global initialization function
window.MacrocommBubble = function(config) {
    return new MacrocommBubble(config);  // ← Added 'new'
};

// Auto-initialization if config is found
if (window.MacrocommConfig) {
    window.MacrocommBubble(window.MacrocommConfig);
}