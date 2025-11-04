"""
Widget routes for serving the frontend chat interface.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/demo.html", response_class=HTMLResponse)
async def get_demo_page():
    """Serve a demo page for testing the chat widget."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RAG Chat Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .chat-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
            }
            .user-message {
                background-color: #007bff;
                color: white;
                text-align: right;
            }
            .bot-message {
                background-color: #f8f9fa;
                border-left: 4px solid #28a745;
            }
            .input-container {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            #queryInput {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            #sendButton {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            #sendButton:hover {
                background-color: #0056b3;
            }
            #sendButton:disabled {
                background-color: #6c757d;
                cursor: not-allowed;
            }
            .status {
                padding: 5px 10px;
                margin: 5px 0;
                border-radius: 3px;
                font-size: 0.9em;
            }
            .status.processing {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
            }
            .status.error {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body>
        <h1>Agentic RAG Chat Demo</h1>
        <div class="chat-container">
            <div id="messages"></div>
            <div class="input-container">
                <input type="text" id="queryInput" placeholder="Ask me anything..." />
                <button id="sendButton">Send</button>
            </div>
        </div>
        
        <div class="chat-container">
            <h3>WebSocket Status</h3>
            <div id="wsStatus">Disconnected</div>
            <button id="connectButton">Connect WebSocket</button>
        </div>

        <script>
            let ws = null;
            const messages = document.getElementById('messages');
            const queryInput = document.getElementById('queryInput');
            const sendButton = document.getElementById('sendButton');
            const wsStatus = document.getElementById('wsStatus');
            const connectButton = document.getElementById('connectButton');

            function addMessage(content, isUser = false, isStatus = false, statusType = 'processing') {
                const div = document.createElement('div');
                if (isStatus) {
                    div.className = `status ${statusType}`;
                } else {
                    div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
                }
                div.innerHTML = content;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }

            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    wsStatus.textContent = 'Connected';
                    wsStatus.style.color = 'green';
                    connectButton.textContent = 'Disconnect';
                    addMessage('WebSocket connected! You can now chat in real-time.', false, true, 'processing');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'response') {
                        addMessage(`<strong>Response:</strong><br>${data.response}<br><br>
                                   <small>Intent: ${data.intent} | Confidence: ${data.confidence.toFixed(2)} | 
                                   Time: ${data.execution_time.toFixed(2)}s | Chunks: ${data.chunks_retrieved}</small>`);
                        
                        if (data.citations && data.citations.length > 0) {
                            let citations = '<br><strong>Sources:</strong><ul>';
                            data.citations.forEach(cite => {
                                citations += `<li>${cite.source} (relevance: ${cite.relevance.toFixed(2)})</li>`;
                            });
                            citations += '</ul>';
                            addMessage(citations);
                        }
                    } else if (data.type === 'progress') {
                        addMessage(`Step ${data.step_number}/${data.total_steps}: ${data.stage} - ${data.reasoning}`, 
                                  false, true, 'processing');
                    } else if (data.type === 'error') {
                        addMessage(`Error: ${data.message}`, false, true, 'error');
                    } else if (data.type === 'status') {
                        addMessage(data.message, false, true, 'processing');
                    }
                    
                    sendButton.disabled = false;
                    sendButton.textContent = 'Send';
                };
                
                ws.onclose = function() {
                    wsStatus.textContent = 'Disconnected';
                    wsStatus.style.color = 'red';
                    connectButton.textContent = 'Connect WebSocket';
                    addMessage('WebSocket disconnected.', false, true, 'error');
                };
                
                ws.onerror = function(error) {
                    addMessage('WebSocket error occurred.', false, true, 'error');
                };
            }

            function sendMessage() {
                const query = queryInput.value.trim();
                if (!query) return;
                
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('Please connect WebSocket first.', false, true, 'error');
                    return;
                }
                
                addMessage(query, true);
                queryInput.value = '';
                sendButton.disabled = true;
                sendButton.textContent = 'Processing...';
                
                ws.send(JSON.stringify({
                    query: query,
                    user_id: 'demo_user',
                    session_id: 'demo_session'
                }));
            }

            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            queryInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            connectButton.addEventListener('click', function() {
                if (!ws || ws.readyState === WebSocket.CLOSED) {
                    connectWebSocket();
                } else {
                    ws.close();
                }
            });

            // Add welcome message
            addMessage('Welcome to the Agentic RAG Chat Demo! Click "Connect WebSocket" to start chatting.', false, true, 'processing');
        </script>
    </body>
    </html>
    """
    return html_content


@router.get("/config.js")
async def get_widget_config():
    """Get widget configuration for embedding."""
    js_config = """
    // Agentic RAG Widget Configuration
    window.AgenticRAGWidget = {
        host: window.location.origin,
        endpoints: {
            chat: '/v1/chat/query',
            websocket: '/ws/chat',
            health: '/health'
        },
        theme: {
            primary: '#007bff',
            accent: '#28a745',
            background: '#ffffff'
        },
        features: {
            fileUpload: true,
            realTimeStreaming: true,
            darkMode: true
        }
    };
    """
    return js_config