# 🚀 Quick Start Guide - Agentic RAG Pipeline

Get your enterprise RAG system running in 5 minutes!

---

## ⚡ Super Quick Start (3 Commands)

```bash
# 1. Start Qdrant vector database
./start-qdrant.sh

# 2. Create .env file with your OpenAI key
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 3. Start the server
cd src && python main_production_with_rag.py
```

**Done!** Open http://localhost:8000 in your browser.

---

## 📋 Step-by-Step Setup

### Step 1: Start Qdrant Vector Database

Qdrant stores your document embeddings for semantic search.

```bash
./start-qdrant.sh
```

This will:
- ✅ Check Docker installation
- ✅ Create data directories
- ✅ Start Qdrant in Docker
- ✅ Verify it's running

**Verify it worked:**
```bash
curl http://localhost:6333/collections
# Should return: {"result":{"collections":[]}}
```

---

### Step 2: Configure OpenAI API Key

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
ENVIRONMENT=production
DEBUG=false
EOF
```

**Where to get your OpenAI API key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Copy and paste it into `.env`

---

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 4: Start the RAG Server

```bash
cd src
python main_production_with_rag.py
```

You should see:
```
🚀 Starting Agentic RAG Pipeline with Phase 1 Features...
✅ RAG System (OpenAI GPT-4o-mini)
🎯 System initialization complete!
INFO:     Application startup complete!
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### Step 5: Access the System

Open your browser and visit:

**🏠 Main Page (User Interface)**
```
http://localhost:8000
```
- Chat with the AI assistant
- Test the widget
- Beautiful landing page

**⚙️ Admin Portal**
```
http://localhost:8000/admin.html
```
- Upload documents
- View analytics
- Manage system
- Monitor performance

---

## 📤 Upload Your First Document

### Via Admin Portal (Easiest):

1. Go to http://localhost:8000/admin.html
2. Click "Documents" in sidebar
3. Click "Upload Document" button
4. Select a PDF, DOCX, or TXT file
5. Wait for processing (shows green success message)

### Via API (Programmatic):

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/your/document.pdf"
```

---

## 💬 Test the Chat

### Option 1: Web Interface

1. Go to http://localhost:8000
2. Click "Open Chat Assistant" button
3. Type a question about your uploaded documents
4. Watch the streaming response with citations!

### Option 2: API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this document about?",
    "conversation_id": "test-123"
  }'
```

### Option 3: WebSocket (for streaming)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/stream');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'chat',
        message: 'Hello!',
        conversation_id: 'test-123'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

---

## 🔍 Verify Everything is Working

Run the verification script:

```bash
./verify-setup.sh
```

This checks:
- ✅ Docker and Docker Compose installed
- ✅ Qdrant running and accessible
- ✅ .env file configured correctly
- ✅ All source files present
- ✅ Python environment ready

---

## 🛑 Stop the System

### Stop Qdrant (preserves data):
```bash
./stop-qdrant.sh
```

### Stop FastAPI server:
Press `Ctrl+C` in the terminal where it's running

### Stop Everything and Remove Data (⚠️ WARNING):
```bash
./stop-qdrant.sh --remove-data
```

---

## 🔧 Common Issues

### Issue: "Docker not found"
**Solution:** Install Docker Desktop
- Mac: https://docs.docker.com/desktop/install/mac-install/
- Windows: https://docs.docker.com/desktop/install/windows-install/
- Linux: https://docs.docker.com/engine/install/

---

### Issue: "Port 6333 already in use"
**Solution:** Check what's using the port
```bash
lsof -i :6333
# Kill the process or change the port in docker-compose.yml
```

---

### Issue: "OpenAI API key not found"
**Solution:** Make sure `.env` file exists with correct key
```bash
cat .env  # Check the file
# Should contain: OPENAI_API_KEY=sk-...
```

---

### Issue: "Module not found" errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

---

### Issue: "Cannot connect to Qdrant"
**Solution:** Make sure Qdrant is running
```bash
docker ps | grep qdrant
curl http://localhost:6333/health
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  index.html  │  │  admin.html  │  │ Chat Widget  │ │
│  │ (Landing)    │  │  (Admin)     │  │ (Embeddable) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Server (Port 8000)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  main_production_with_rag.py                     │  │
│  │  • REST API endpoints                             │  │
│  │  • WebSocket support (streaming)                  │  │
│  │  • Document upload/management                     │  │
│  │  • Conversation history                           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
            │                    │                │
            ▼                    ▼                ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────┐
│  RAG Components  │  │  OpenAI GPT-4o   │  │ Analytics│
│  ┌────────────┐  │  │  ┌────────────┐  │  │ Database │
│  │ Doc Process│  │  │  │ LLM Manager│  │  │ (SQLite) │
│  │ Embeddings │  │  │  │ Streaming  │  │  │          │
│  │ Search     │  │  │  │ Citations  │  │  │ • Costs  │
│  └────────────┘  │  │  └────────────┘  │  │ • Metrics│
└──────────────────┘  └──────────────────┘  └──────────┘
            │
            ▼
┌──────────────────────────────────────────────────────┐
│         Qdrant Vector Database (Port 6333)           │
│  • Semantic search                                   │
│  • Document embeddings storage                       │
│  • Fast similarity matching                          │
└──────────────────────────────────────────────────────┘
```

---

## 🎯 Next Steps

After your system is running:

1. **Upload Documents**
   - Company policies
   - Product manuals
   - Knowledge base articles
   - FAQs

2. **Configure the Widget**
   - Customize colors in admin panel
   - Set welcome message
   - Generate embed code

3. **Monitor Analytics**
   - View usage statistics
   - Track costs
   - Monitor performance

4. **Embed on Website**
   - Copy embed code from admin panel
   - Paste into your website
   - Test with users

---

## 📚 Documentation

- **Full Setup Guide**: `DOCKER_SETUP.md`
- **API Documentation**: http://localhost:8000/docs (when server is running)
- **System Status**: http://localhost:8000/health

---

## 🆘 Need Help?

**Check logs:**
```bash
# Qdrant logs
docker-compose logs -f qdrant

# Server logs
# (shown in terminal where server is running)
```

**Run verification:**
```bash
./verify-setup.sh
```

**Common commands:**
```bash
# Restart Qdrant
docker-compose restart qdrant

# Check Qdrant status
docker-compose ps

# View collections
curl http://localhost:6333/collections

# Test server health
curl http://localhost:8000/health
```

---

## 🎉 You're All Set!

Your enterprise RAG system is now running with:
- ✅ Real-time streaming responses
- ✅ Source citations with confidence scores
- ✅ Follow-up question suggestions
- ✅ Conversation history
- ✅ Usage analytics and cost tracking
- ✅ Admin dashboard
- ✅ Embeddable chat widget

**Start chatting at**: http://localhost:8000

**Happy building!** 🚀
