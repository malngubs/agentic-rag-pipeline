/**
 * 🎈 MACROCOMM BUBBLE CHATBOT - ENHANCED VERSION
 * ================================================
 * Production-ready chat widget with:
 * - ✅ Streaming responses (token-by-token like ChatGPT)
 * - ✅ Follow-up question suggestions
 * - ✅ Voice input (browser speech recognition)
 * - ✅ Enhanced UI with animations
 * - ✅ Message reactions (thumbs up/down)
 * 
 * Version: 3.0 - Enhanced Features
 */

class MacrocommBubbleChatbot {
    constructor(config = {}) {
        // Configuration
        this.config = {
            position: config.position || 'bottom-right',
            theme: config.theme || 'light',
            apiBaseUrl: config.apiBaseUrl || 'ws://localhost:8000',  // Match backend port
            primaryColor: config.primaryColor || '#FF6E00',
            secondaryColor: config.secondaryColor || '#FF923F',
            enableStreaming: config.enableStreaming !== false, // Default: true
            enableVoice: config.enableVoice !== false,         // Default: true
            enableFollowUps: config.enableFollowUps !== false, // Default: true
            branding: config.branding !== false
        };
        
        // State
        this.isOpen = false;
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.isStreaming = false;
        this.currentStreamingMessageEl = null;

        // ✨ PHASE 5: Multi-Conversation Tabs
        this.tabs = [];
        this.activeTabIndex = 0;
        this.tabCounter = 1;
        this.createInitialTab();

        // Voice recognition
        this.recognition = null;
        this.isListening = false;
        
        // DOM elements (will be set after initialization)
        this.bubble = null;
        this.chatWindow = null;
        this.messagesContainer = null;
        this.inputField = null;
        
        // Initialize
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Macrocomm Chatbot (Enhanced with Tabs)');
        this.createBubble();
        this.createChatWindow();
        this.setupWebSocket();
        this.setupVoiceRecognition();
        this.setupKeyboardShortcuts();
    }

    // =========================================================================
    // ✨ TAB MANAGEMENT (Phase 5)
    // =========================================================================

    createInitialTab() {
        this.tabs.push({
            id: this.generateUUID(),
            conversationId: this.generateUUID(),
            name: `Chat ${this.tabCounter}`,
            messages: [],
            createdAt: new Date()
        });
    }

    createNewTab() {
        this.tabCounter++;
        const newTab = {
            id: this.generateUUID(),
            conversationId: this.generateUUID(),
            name: `Chat ${this.tabCounter}`,
            messages: [],
            createdAt: new Date()
        };
        this.tabs.push(newTab);
        this.activeTabIndex = this.tabs.length - 1;
        this.renderTabs();
        this.renderMessages();
        this.scrollToBottom();

        // Send welcome message for new tab
        setTimeout(() => this.addBotMessage('Hello! I\'m your AI assistant. How can I help you today?'), 300);
    }

    switchTab(index) {
        if (index >= 0 && index < this.tabs.length) {
            this.activeTabIndex = index;
            this.renderTabs();
            this.renderMessages();
            this.scrollToBottom();
        }
    }

    closeTab(index) {
        if (this.tabs.length <= 1) {
            alert('Cannot close the last tab');
            return;
        }

        this.tabs.splice(index, 1);

        // Adjust active tab index
        if (this.activeTabIndex >= this.tabs.length) {
            this.activeTabIndex = this.tabs.length - 1;
        } else if (this.activeTabIndex > index) {
            this.activeTabIndex--;
        }

        this.renderTabs();
        this.renderMessages();
    }

    renameTab(index, newName) {
        if (index >= 0 && index < this.tabs.length) {
            this.tabs[index].name = newName;
            this.renderTabs();
        }
    }

    getActiveTab() {
        return this.tabs[this.activeTabIndex];
    }

    get conversationId() {
        return this.getActiveTab().conversationId;
    }

    renderTabs() {
        const tabsContainer = document.getElementById('macrocomm-tabs');
        if (!tabsContainer) return;

        tabsContainer.innerHTML = `
            <div style="display: flex; align-items: center; gap: 4px; overflow-x: auto; padding: 8px 12px; background: #f8f9fa; border-bottom: 1px solid #e0e0e0;">
                ${this.tabs.map((tab, index) => `
                    <div class="chat-tab ${index === this.activeTabIndex ? 'active' : ''}"
                         onclick="macrocommChat.switchTab(${index})"
                         style="
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            padding: 6px 12px;
                            background: ${index === this.activeTabIndex ? 'white' : 'transparent'};
                            border: 1px solid ${index === this.activeTabIndex ? '#ddd' : 'transparent'};
                            border-radius: 8px 8px 0 0;
                            cursor: pointer;
                            font-size: 13px;
                            white-space: nowrap;
                            transition: all 0.2s;
                            ${index === this.activeTabIndex ? 'font-weight: 600;' : ''}
                         ">
                        <span>${tab.name}</span>
                        ${this.tabs.length > 1 ? `
                            <button onclick="event.stopPropagation(); macrocommChat.closeTab(${index})"
                                    style="
                                        background: none;
                                        border: none;
                                        padding: 2px;
                                        cursor: pointer;
                                        opacity: 0.6;
                                        transition: opacity 0.2s;
                                        line-height: 1;
                                    "
                                    onmouseover="this.style.opacity='1'"
                                    onmouseout="this.style.opacity='0.6'">
                                ✕
                            </button>
                        ` : ''}
                    </div>
                `).join('')}
                <button onclick="macrocommChat.createNewTab()"
                        style="
                            background: none;
                            border: 1px solid #ddd;
                            padding: 6px 10px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                            transition: all 0.2s;
                            color: #666;
                        "
                        onmouseover="this.style.background='#e0e0e0'"
                        onmouseout="this.style.background='none'"
                        title="New conversation">
                    +
                </button>
            </div>
        `;
    }

    renderMessages() {
        if (!this.messagesContainer) return;

        this.messagesContainer.innerHTML = '';
        const activeTab = this.getActiveTab();

        activeTab.messages.forEach(msg => {
            if (msg.type === 'user') {
                this.displayUserMessage(msg.text, msg.timestamp);
            } else if (msg.type === 'assistant') {
                this.displayAssistantMessage(msg.text, msg.metadata, msg.timestamp);
            } else if (msg.type === 'system') {
                this.displaySystemMessage(msg.text, msg.level, msg.timestamp);
            }
        });
    }

    // =========================================================================
    // 🎨 UI CREATION
    // =========================================================================
    
    createBubble() {
        // Create floating bubble button
        this.bubble = document.createElement('div');
        this.bubble.className = 'macrocomm-bubble';
        this.bubble.innerHTML = `
            <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
                <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3 .97 4.29L2 22l5.71-.97C9 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.38 0-2.67-.31-3.83-.86l-.27-.14-2.77.47.47-2.77-.14-.27C4.31 14.67 4 13.38 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8z"/>
            </svg>
            <span class="unread-badge" style="display: none;">0</span>
        `;
        
        // Styling
        Object.assign(this.bubble.style, {
            position: 'fixed',
            bottom: '24px',
            right: this.config.position.includes('right') ? '24px' : 'auto',
            left: this.config.position.includes('left') ? '24px' : 'auto',
            width: '60px',
            height: '60px',
            background: `linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%)`,
            borderRadius: '50%',
            boxShadow: `0 4px 20px rgba(255, 110, 0, 0.4)`,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            zIndex: '999999'
        });
        
        // Hover effects
        this.bubble.addEventListener('mouseenter', () => {
            this.bubble.style.transform = 'scale(1.1) translateY(-4px)';
            this.bubble.style.boxShadow = '0 8px 30px rgba(255, 110, 0, 0.5)';
        });
        
        this.bubble.addEventListener('mouseleave', () => {
            this.bubble.style.transform = 'scale(1) translateY(0)';
            this.bubble.style.boxShadow = '0 4px 20px rgba(255, 110, 0, 0.4)';
        });
        
        // Click to toggle chat
        this.bubble.addEventListener('click', () => this.toggleChat());
        
        document.body.appendChild(this.bubble);
    }
    
    createChatWindow() {
        // Create chat window container
        this.chatWindow = document.createElement('div');
        this.chatWindow.className = 'macrocomm-chat-window';
        this.chatWindow.style.display = 'none';
        
        this.chatWindow.innerHTML = `
            <div class="chat-header">
                <div class="header-content">
                    <div class="header-logo">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3 .97 4.29L2 22l5.71-.97C9 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2z"/>
                        </svg>
                    </div>
                    <div class="header-text">
                        <div class="header-title">Macrocomm AI</div>
                        <div class="header-status">
                            <span class="status-dot"></span>
                            <span class="status-text">Online</span>
                        </div>
                    </div>
                </div>
                <div class="header-actions">
                    <button class="dashboard-btn" onclick="macrocommChat.openDashboard()" title="Open BI Platform">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                            <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
                        </svg>
                    </button>
                    <button class="close-btn" onclick="macrocommChat.toggleChat()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- ✨ PHASE 5: Tab Bar -->
            <div class="chat-tabs-bar" id="macrocomm-tabs">
                <!-- Tabs will be rendered here -->
            </div>

            <div class="chat-messages" id="macrocomm-messages">
                <!-- Messages will be added here -->
            </div>
            
            <div class="chat-input-container">
                <div class="voice-indicator" style="display: none;">
                    <div class="voice-animation">
                        <span></span><span></span><span></span>
                    </div>
                    <div class="voice-text">Listening...</div>
                </div>
                
                <div class="input-wrapper">
                    ${this.config.enableVoice ? `
                    <button class="voice-btn" title="Voice input (click to start)" onclick="macrocommChat.toggleVoice()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                        </svg>
                    </button>
                    ` : ''}
                    
                    <textarea 
                        id="macrocomm-input" 
                        placeholder="Type your message..."
                        rows="1"
                    ></textarea>
                    
                    <button class="send-btn" onclick="macrocommChat.sendMessage()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
                
                ${this.config.branding ? `
                <div class="branding">
                    Powered by <strong>Macrocomm AI</strong>
                </div>
                ` : ''}
            </div>
        `;
        
        // Styling
        Object.assign(this.chatWindow.style, {
            position: 'fixed',
            bottom: '100px',
            right: this.config.position.includes('right') ? '24px' : 'auto',
            left: this.config.position.includes('left') ? '24px' : 'auto',
            width: '380px',
            maxWidth: 'calc(100vw - 48px)',
            height: '600px',
            maxHeight: 'calc(100vh - 140px)',
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            zIndex: '999998',
            animation: 'slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        });
        
        document.body.appendChild(this.chatWindow);
        this.messagesContainer = document.getElementById('macrocomm-messages');
        this.inputField = document.getElementById('macrocomm-input');
        
        // Add enter key handler
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Add styles
        this.injectStyles();
    }
    
    injectStyles() {
        const styleId = 'macrocomm-chatbot-styles';
        if (document.getElementById(styleId)) return;
        
        const styles = document.createElement('style');
        styles.id = styleId;
        styles.textContent = `
            /* Animations */
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 0.6; }
                50% { opacity: 1; }
            }
            
            @keyframes typing {
                0%, 100% { opacity: 0.4; }
                50% { opacity: 1; }
            }
            
            /* Chat Header */
            .macrocomm-chat-window .chat-header {
                background: linear-gradient(135deg, ${this.config.primaryColor}, ${this.config.secondaryColor});
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: white;
            }
            
            .macrocomm-chat-window .header-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .macrocomm-chat-window .header-logo {
                width: 40px;
                height: 40px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .macrocomm-chat-window .header-title {
                font-weight: 600;
                font-size: 16px;
            }
            
            .macrocomm-chat-window .header-status {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                opacity: 0.9;
            }
            
            .macrocomm-chat-window .status-dot {
                width: 8px;
                height: 8px;
                background: #4ade80;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            
            .macrocomm-chat-window .header-actions {
                display: flex;
                gap: 8px;
                align-items: center;
            }

            .macrocomm-chat-window .dashboard-btn,
            .macrocomm-chat-window .close-btn {
                background: none;
                border: none;
                cursor: pointer;
                padding: 8px;
                border-radius: 8px;
                transition: background 0.2s;
            }

            .macrocomm-chat-window .dashboard-btn:hover,
            .macrocomm-chat-window .close-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* Messages Container */
            .macrocomm-chat-window .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f8fafc;
            }
            
            /* Message Bubbles */
            .message {
                margin-bottom: 16px;
                display: flex;
                flex-direction: column;
                animation: slideUp 0.3s ease-out;
            }
            
            .message.user {
                align-items: flex-end;
            }
            
            .message.assistant {
                align-items: flex-start;
            }
            
            .message-bubble {
                max-width: 75%;
                padding: 12px 16px;
                border-radius: 16px;
                word-wrap: break-word;
                position: relative;
            }
            
            .message.user .message-bubble {
                background: linear-gradient(135deg, ${this.config.primaryColor}, ${this.config.secondaryColor});
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .message.assistant .message-bubble {
                background: white;
                color: #1e293b;
                border-bottom-left-radius: 4px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .message-meta {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 6px;
                font-size: 11px;
                color: #64748b;
            }
            
            /* Message Reactions */
            .message-reactions {
                display: flex;
                gap: 4px;
                margin-top: 8px;
            }
            
            .reaction-btn {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 4px 8px;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 14px;
            }
            
            .reaction-btn:hover {
                background: #f1f5f9;
                transform: scale(1.1);
            }
            
            .reaction-btn.active {
                background: ${this.config.primaryColor};
                border-color: ${this.config.primaryColor};
                color: white;
            }
            
            /* Typing Indicator */
            .typing-indicator {
                display: flex;
                gap: 4px;
                padding: 12px 16px;
                background: white;
                border-radius: 16px;
                width: fit-content;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .typing-indicator span {
                width: 8px;
                height: 8px;
                background: #94a3b8;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }
            
            .typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            /* Follow-up Questions */
            .follow-up-questions {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-top: 12px;
                animation: slideUp 0.4s ease-out;
            }
            
            .follow-up-chip {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 8px 12px;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 13px;
                color: #475569;
                text-align: left;
            }
            
            .follow-up-chip:hover {
                background: #f8fafc;
                border-color: ${this.config.primaryColor};
                color: ${this.config.primaryColor};
                transform: translateX(4px);
            }
            
            /* Citations */
            .citations {
                margin-top: 12px;
                padding: 12px;
                background: #f8fafc;
                border-radius: 8px;
                font-size: 12px;
            }
            
            .citation-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 0;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .citation-item:last-child {
                border-bottom: none;
            }
            
            .citation-icon {
                color: ${this.config.primaryColor};
            }
            
            .citation-confidence {
                margin-left: auto;
                color: #64748b;
                font-size: 11px;
            }
            
            /* Input Container */
            .macrocomm-chat-window .chat-input-container {
                padding: 16px;
                background: white;
                border-top: 1px solid #e2e8f0;
            }
            
            .macrocomm-chat-window .voice-indicator {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: #fef3c7;
                border-radius: 8px;
                margin-bottom: 12px;
            }
            
            .voice-animation {
                display: flex;
                gap: 4px;
            }
            
            .voice-animation span {
                width: 4px;
                height: 20px;
                background: #f59e0b;
                border-radius: 2px;
                animation: typing 0.8s infinite;
            }
            
            .voice-animation span:nth-child(2) {
                animation-delay: 0.1s;
            }
            
            .voice-animation span:nth-child(3) {
                animation-delay: 0.2s;
            }
            
            .voice-text {
                color: #92400e;
                font-size: 14px;
                font-weight: 500;
            }
            
            .macrocomm-chat-window .input-wrapper {
                display: flex;
                gap: 8px;
                align-items: flex-end;
            }
            
            .macrocomm-chat-window .voice-btn,
            .macrocomm-chat-window .send-btn {
                background: ${this.config.primaryColor};
                border: none;
                border-radius: 8px;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s;
                color: white;
                flex-shrink: 0;
            }
            
            .macrocomm-chat-window .voice-btn:hover,
            .macrocomm-chat-window .send-btn:hover {
                background: ${this.config.secondaryColor};
                transform: scale(1.05);
            }
            
            .macrocomm-chat-window .voice-btn.listening {
                background: #ef4444;
                animation: pulse 1s infinite;
            }
            
            .macrocomm-chat-window #macrocomm-input {
                flex: 1;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 14px;
                resize: none;
                max-height: 120px;
                transition: border-color 0.2s;
            }
            
            .macrocomm-chat-window #macrocomm-input:focus {
                outline: none;
                border-color: ${this.config.primaryColor};
            }
            
            .macrocomm-chat-window .branding {
                text-align: center;
                font-size: 11px;
                color: #94a3b8;
                margin-top: 8px;
            }
            
            /* Scrollbar Styling */
            .macrocomm-chat-window .chat-messages::-webkit-scrollbar {
                width: 6px;
            }
            
            .macrocomm-chat-window .chat-messages::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .macrocomm-chat-window .chat-messages::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 3px;
            }
            
            .macrocomm-chat-window .chat-messages::-webkit-scrollbar-thumb:hover {
                background: #94a3b8;
            }
            
            /* Mobile Responsive */
            @media (max-width: 480px) {
                .macrocomm-chat-window {
                    width: calc(100vw - 16px) !important;
                    height: calc(100vh - 100px) !important;
                    bottom: 8px !important;
                    right: 8px !important;
                    left: 8px !important;
                }
                
                .message-bubble {
                    max-width: 85%;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    // =========================================================================
    // 🔌 WEBSOCKET CONNECTION
    // =========================================================================
    
    setupWebSocket() {
        try {
            // Use streaming endpoint if enabled
            const wsUrl = this.config.enableStreaming 
                ? `${this.config.apiBaseUrl}/ws/chat/stream`
                : `${this.config.apiBaseUrl}/ws/chat`;
            
            this.ws = new WebSocket(wsUrl.replace('http:', 'ws:').replace('https:', 'wss:'));
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.wsReconnectAttempts = 0;
                this.updateStatus('online');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.updateStatus('error');
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket closed');
                this.updateStatus('offline');
                this.attemptReconnect();
            };
            
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }
    
    attemptReconnect() {
        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
            this.wsReconnectAttempts++;
            console.log(`🔄 Reconnecting... (Attempt ${this.wsReconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.setupWebSocket(), 2000 * this.wsReconnectAttempts);
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('📨 Message received:', data);
        
        switch (data.type) {
            case 'system':
                this.addSystemMessage(data.message);
                break;
                
            case 'thinking':
                // Show typing indicator
                this.showTypingIndicator();
                break;
                
            case 'stream_token':
                // Handle streaming token
                this.handleStreamToken(data.token);
                break;
                
            case 'stream_complete':
                // Streaming complete - add metadata
                this.handleStreamComplete(data);
                break;
                
            case 'response':
                // Non-streaming response (legacy)
                this.hideTypingIndicator();
                this.addAssistantMessage(data.message || data.response, data);
                break;
                
            case 'error':
                this.hideTypingIndicator();
                this.addSystemMessage(data.message, 'error');
                break;
        }
    }
    
    // =========================================================================
    // 💬 MESSAGE HANDLING
    // =========================================================================
    
    sendMessage() {
        const message = this.inputField.value.trim();
        if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }
        
        // Add user message to UI
        this.addUserMessage(message);
        
        // Send to server
        this.ws.send(JSON.stringify({
            type: 'chat',
            message: message,
            conversation_id: this.conversationId
        }));
        
        // Clear input
        this.inputField.value = '';
        this.inputField.style.height = 'auto';
    }
    
    addUserMessage(text) {
        // Store message in active tab
        const activeTab = this.getActiveTab();
        const timestamp = new Date();
        activeTab.messages.push({
            type: 'user',
            text: text,
            timestamp: timestamp
        });

        // Display the message
        this.displayUserMessage(text, timestamp);
        this.scrollToBottom();
    }

    displayUserMessage(text, timestamp) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message user';
        messageEl.innerHTML = `
            <div class="message-bubble">${this.escapeHtml(text)}</div>
            <div class="message-meta">
                <span>${this.formatTime(timestamp)}</span>
            </div>
        `;

        this.messagesContainer.appendChild(messageEl);
    }
    
    addAssistantMessage(text, metadata = {}) {
        // Store message in active tab
        const activeTab = this.getActiveTab();
        const timestamp = new Date();
        activeTab.messages.push({
            type: 'assistant',
            text: text,
            metadata: metadata,
            timestamp: timestamp
        });

        // Display the message
        this.displayAssistantMessage(text, metadata, timestamp);

        // Add follow-up questions if available
        if (this.config.enableFollowUps && metadata.follow_up_questions && metadata.follow_up_questions.length > 0) {
            this.addFollowUpQuestions(metadata.follow_up_questions);
        }

        this.scrollToBottom();
    }

    displayAssistantMessage(text, metadata = {}, timestamp) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant';

        let html = `<div class="message-bubble">${this.escapeHtml(text)}</div>`;

        // Add citations if available
        if (metadata.citations && metadata.citations.length > 0) {
            html += '<div class="citations">';
            html += '<div style="font-weight: 600; margin-bottom: 8px;">📚 Sources:</div>';
            metadata.citations.forEach(citation => {
                html += `
                    <div class="citation-item">
                        <span class="citation-icon">📄</span>
                        <span>${citation.source}</span>
                        <span class="citation-confidence">${Math.round(citation.confidence * 100)}%</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Add metadata
        html += `
            <div class="message-meta">
                <span>${this.formatTime(timestamp)}</span>
                ${metadata.response_time ? `<span>• ${metadata.response_time.toFixed(2)}s</span>` : ''}
                ${metadata.using_rag ? '<span>• RAG</span>' : ''}
            </div>
        `;

        // Add reactions
        html += `
            <div class="message-reactions">
                <button class="reaction-btn" onclick="macrocommChat.react(this, '👍')">👍</button>
                <button class="reaction-btn" onclick="macrocommChat.react(this, '👎')">👎</button>
            </div>
        `;

        messageEl.innerHTML = html;
        this.messagesContainer.appendChild(messageEl);
    }
    
    addSystemMessage(text, level = 'info') {
        // Store message in active tab
        const activeTab = this.getActiveTab();
        const timestamp = new Date();
        activeTab.messages.push({
            type: 'system',
            text: text,
            level: level,
            timestamp: timestamp
        });

        // Display the message
        this.displaySystemMessage(text, level, timestamp);
        this.scrollToBottom();
    }

    displaySystemMessage(text, level = 'info', timestamp) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message system';
        messageEl.innerHTML = `
            <div style="
                padding: 8px 12px;
                background: ${level === 'error' ? '#fee2e2' : '#e0f2fe'};
                color: ${level === 'error' ? '#991b1b' : '#075985'};
                border-radius: 8px;
                font-size: 12px;
                text-align: center;
            ">
                ${this.escapeHtml(text)}
            </div>
        `;

        this.messagesContainer.appendChild(messageEl);
    }

    // Alias for backward compatibility
    addBotMessage(text, metadata = {}) {
        this.addAssistantMessage(text, metadata);
    }
    
    showTypingIndicator() {
        // Remove existing indicator
        this.hideTypingIndicator();
        
        const indicator = document.createElement('div');
        indicator.className = 'message assistant typing-message';
        indicator.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        this.messagesContainer.appendChild(indicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const indicator = this.messagesContainer.querySelector('.typing-message');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // =========================================================================
    // 🌊 STREAMING SUPPORT
    // =========================================================================
    
    handleStreamToken(token) {
        // Hide typing indicator on first token
        if (!this.isStreaming) {
            this.hideTypingIndicator();
            this.isStreaming = true;
            
            // Create new message element for streaming
            const messageEl = document.createElement('div');
            messageEl.className = 'message assistant streaming-message';
            messageEl.innerHTML = `
                <div class="message-bubble"></div>
            `;
            
            this.messagesContainer.appendChild(messageEl);
            this.currentStreamingMessageEl = messageEl.querySelector('.message-bubble');
        }
        
        // Append token
        if (this.currentStreamingMessageEl) {
            this.currentStreamingMessageEl.textContent += token;
            this.scrollToBottom();
        }
    }
    
    handleStreamComplete(data) {
        this.isStreaming = false;
        
        if (!this.currentStreamingMessageEl) return;
        
        const messageEl = this.currentStreamingMessageEl.closest('.message');
        messageEl.classList.remove('streaming-message');
        
        // Add metadata
        let metaHtml = `
            <div class="message-meta">
                <span>${this.formatTime(new Date())}</span>
                ${data.response_time ? `<span>• ${data.response_time.toFixed(2)}s</span>` : ''}
                ${data.using_rag ? '<span>• RAG</span>' : ''}
            </div>
        `;
        
        // Add reactions
        metaHtml += `
            <div class="message-reactions">
                <button class="reaction-btn" onclick="macrocommChat.react(this, '👍')">👍</button>
                <button class="reaction-btn" onclick="macrocommChat.react(this, '👎')">👎</button>
            </div>
        `;
        
        messageEl.innerHTML += metaHtml;
        
        // Add citations if available
        if (data.citations && data.citations.length > 0) {
            let citationsHtml = '<div class="citations">';
            citationsHtml += '<div style="font-weight: 600; margin-bottom: 8px;">📚 Sources:</div>';
            data.citations.forEach(citation => {
                citationsHtml += `
                    <div class="citation-item">
                        <span class="citation-icon">📄</span>
                        <span>${citation.source}</span>
                        <span class="citation-confidence">${Math.round(citation.confidence * 100)}%</span>
                    </div>
                `;
            });
            citationsHtml += '</div>';
            
            this.currentStreamingMessageEl.insertAdjacentHTML('afterend', citationsHtml);
        }
        
        // Add follow-up questions
        if (this.config.enableFollowUps && data.follow_up_questions && data.follow_up_questions.length > 0) {
            this.addFollowUpQuestions(data.follow_up_questions);
        }
        
        this.currentStreamingMessageEl = null;
        this.scrollToBottom();
    }
    
    addFollowUpQuestions(questions) {
        const followUpContainer = document.createElement('div');
        followUpContainer.className = 'follow-up-questions';
        
        questions.forEach(question => {
            const chip = document.createElement('div');
            chip.className = 'follow-up-chip';
            chip.textContent = question;
            chip.onclick = () => {
                this.inputField.value = question;
                this.sendMessage();
            };
            followUpContainer.appendChild(chip);
        });
        
        this.messagesContainer.appendChild(followUpContainer);
        this.scrollToBottom();
    }
    
    // =========================================================================
    // 🎤 VOICE INPUT
    // =========================================================================
    
    setupVoiceRecognition() {
        if (!this.config.enableVoice) return;
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('⚠️ Speech recognition not supported in this browser');
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.inputField.value = transcript;
            this.stopVoice();
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.stopVoice();
        };
        
        this.recognition.onend = () => {
            this.stopVoice();
        };
    }
    
    toggleVoice() {
        if (!this.recognition) {
            alert('Voice input is not supported in your browser');
            return;
        }
        
        if (this.isListening) {
            this.stopVoice();
        } else {
            this.startVoice();
        }
    }
    
    startVoice() {
        this.isListening = true;
        this.recognition.start();
        
        // Show voice indicator
        const indicator = this.chatWindow.querySelector('.voice-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }
        
        // Update button
        const voiceBtn = this.chatWindow.querySelector('.voice-btn');
        if (voiceBtn) {
            voiceBtn.classList.add('listening');
        }
    }
    
    stopVoice() {
        this.isListening = false;
        if (this.recognition) {
            this.recognition.stop();
        }
        
        // Hide voice indicator
        const indicator = this.chatWindow.querySelector('.voice-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // Update button
        const voiceBtn = this.chatWindow.querySelector('.voice-btn');
        if (voiceBtn) {
            voiceBtn.classList.remove('listening');
        }
    }
    
    // =========================================================================
    // 🎨 UI UTILITIES
    // =========================================================================
    
    toggleChat() {
        this.isOpen = !this.isOpen;
        this.chatWindow.style.display = this.isOpen ? 'flex' : 'none';

        if (this.isOpen) {
            // Render tabs and messages when opening
            this.renderTabs();
            this.renderMessages();
            this.inputField.focus();
        }
    }

    openDashboard() {
        // Open BI Platform Chat page in new tab (not dashboards)
        const biPlatformUrl = 'http://localhost:3000/chat';
        window.open(biPlatformUrl, '_blank');

        // Optional: Show notification that BI Platform is opening
        this.addBotMessage('🚀 Opening BI Platform in your browser...');
    }

    updateStatus(status) {
        const statusDot = this.chatWindow.querySelector('.status-dot');
        const statusText = this.chatWindow.querySelector('.status-text');
        
        if (statusDot && statusText) {
            if (status === 'online') {
                statusDot.style.background = '#4ade80';
                statusText.textContent = 'Online';
            } else if (status === 'offline') {
                statusDot.style.background = '#94a3b8';
                statusText.textContent = 'Offline';
            } else {
                statusDot.style.background = '#ef4444';
                statusText.textContent = 'Error';
            }
        }
    }
    
    react(button, emoji) {
        button.classList.toggle('active');
        console.log(`User reacted with: ${emoji}`);
        // TODO: Send reaction to analytics backend
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    setupKeyboardShortcuts() {
        // Global shortcut: Ctrl/Cmd + Shift + M to open chat
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'M') {
                e.preventDefault();
                this.toggleChat();
            }
        });
    }
    
    // =========================================================================
    // 🛠️ UTILITIES
    // =========================================================================
    
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatTime(date) {
        return date.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
    }
}

// =========================================================================
// 🚀 INITIALIZATION
// =========================================================================

// Global instance
let macrocommChat = null;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMacrocommChat);
} else {
    initMacrocommChat();
}

function initMacrocommChat() {
    macrocommChat = new MacrocommBubbleChatbot({
        apiBaseUrl: 'http://localhost:8000',  // Backend API port (matches uvicorn)
        enableStreaming: true,
        enableVoice: true,
        enableFollowUps: true
    });
}