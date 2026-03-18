# 🚀 COMPLETE STARTUP GUIDE

## Date: January 9, 2026
## How to Start Everything: Backend, Frontend, Desktop App, Admin Portal

---

# 📋 PRE-STARTUP CHECKLIST

## 1. Install Required Dependencies

### Frontend - Install Plotly (REQUIRED):
```bash
cd frontend
npm install plotly.js-dist-min
npm install --save-dev @types/plotly.js
```

## 2. Fix Port Configuration (REQUIRED)

The backend runs on port 8000, but frontend is configured for 8000. Fix this:

### Update Frontend .env.local:
```bash
cd frontend
# Windows (PowerShell):
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
echo NEXT_PUBLIC_WS_URL=ws://localhost:8000 >> .env.local

# Or manually edit frontend/.env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Update Desktop App (Optional - if backend stays on 8000):
Edit `desktop-app/src/main.js` line 13:
```javascript
apiUrl: 'http://localhost:8000',  // Changed from 8000
```

## 3. Verify Qdrant is Running

Check if Qdrant vector database is running:
```bash
curl http://localhost:6333
```

**Expected response:**
```json
{
  "title": "qdrant - vector search engine",
  "version": "1.15.4"
}
```

**If not running, start Qdrant:**
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
# Or if you have it installed locally:
qdrant
```

---

# 🚀 STARTUP SEQUENCE

## TERMINAL 1: Start Backend (Port 8000)

### Step 1: Navigate to project root
```bash
cd "c:\Users\Malusi\OneDrive - MACROCOMM\Desktop\agentic-rag-pipeline"
```

### Step 2: Activate virtual environment (if using one)
```bash
# If you have a venv:
.venv\Scripts\activate

# Or conda:
conda activate your-env-name
```

### Step 3: Start the backend
```bash
python src/main_production_with_rag.py
```

### Expected Output:
```
🚀 STARTING MACROCOMM BI PLATFORM...
✅ Qdrant connection successful
✅ RAG system initialized
✅ Analytics database initialized
✅ Data analyst module loaded
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Verify Backend is Running:
Open browser or use curl:
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "components": {
    "rag_system": {"status": "healthy"},
    "vector_store": {"status": "healthy"},
    "llm_service": {"status": "healthy"}
  }
}
```

**⚠️ IMPORTANT:** Wait for backend to fully start (30-60 seconds on first run due to model loading)

---

## TERMINAL 2: Start Frontend (Port 3000)

### Step 1: Open new terminal and navigate to frontend
```bash
cd "c:\Users\Malusi\OneDrive - MACROCOMM\Desktop\agentic-rag-pipeline\frontend"
```

### Step 2: Install dependencies (if not done)
```bash
npm install
```

### Step 3: Start development server
```bash
npm run dev
```

### Expected Output:
```
▲ Next.js 14.0.4
- Local:        http://localhost:3000
- Environments: .env.local

✓ Ready in 2.5s
○ Compiling / ...
✓ Compiled / in 3.2s
```

### Verify Frontend is Running:
Open browser: **http://localhost:3000**

You should see the BI Platform chat interface.

---

## TERMINAL 3: Start Desktop App (Electron)

### Step 1: Open new terminal and navigate to desktop-app
```bash
cd "c:\Users\Malusi\OneDrive - MACROCOMM\Desktop\agentic-rag-pipeline\desktop-app"
```

### Step 2: Install dependencies (if not done)
```bash
npm install
```

### Step 3: Start Electron app
```bash
npm start
```

### Expected Behavior:
- Electron app starts (may be hidden initially)
- System tray icon appears (Macrocomm logo)
- Press **Ctrl+Shift+M** to toggle window visibility

### Desktop App Features:
- **Ctrl+Shift+M** - Show/hide window
- **Double-click tray icon** - Show window
- **Right-click tray icon** - Context menu
- **Dashboard button** (grid icon in header) - Opens BI Platform in browser

---

# 🧪 TESTING ALL COMPONENTS

## 1. Test Landing Page

### Access:
```
http://localhost:3000/landing
```

### What to Test:
- [ ] Page loads with Macrocomm branding
- [ ] "Open BI Platform" button → navigates to /
- [ ] "Admin Portal" button → navigates to /admin
- [ ] "Desktop App" section shows instructions
- [ ] Fonts are Inter/Segoe UI
- [ ] Theme is dark with orange (#FF6E00) accents

---

## 2. Test BI Platform (Main Chat Interface)

### Access:
```
http://localhost:3000/
```

### What to Test:

#### Basic UI:
- [ ] Chat interface loads
- [ ] Can type in message input box
- [ ] Send button is visible
- [ ] Sidebar shows navigation
- [ ] No console errors

#### File Upload:
1. Click upload button (📎 icon)
2. Select a CSV file (create test file if needed)
3. **Expected:** File uploads, shows success message
4. **Backend should show:** "Processing document..." in logs

#### Chat Functionality:
1. Type: "Hello, what can you do?"
2. Press Enter or click Send
3. **Expected:**
   - Message appears in chat
   - Streaming response from assistant
   - Response completes with checkmark

#### Visualization Test (THE BIG ONE):
1. Upload a CSV with data (or use sample):
   ```csv
   Month,Sales,Region
   Jan,10000,North
   Feb,12000,North
   Mar,15000,North
   Jan,8000,South
   Feb,9000,South
   Mar,11000,South
   ```
2. Ask: "Show me sales trends over time"
3. **Expected:**
   - Assistant responds with text
   - **Chart renders inline** in chat message
   - Chart is interactive (hover shows values)
   - Macrocomm orange theme applied
   - Fullscreen and export buttons visible

4. Ask: "Create a sales dashboard"
5. **Expected:**
   - Dashboard widget renders
   - KPI cards at top (Total Sales, Growth %, etc.)
   - Multiple charts in grid layout
   - All charts interactive

---

## 3. Test Admin Portal

### Access:
```
http://localhost:3000/admin
```

### What to Test:

#### Dashboard View:
- [ ] Analytics cards display:
  - Total Queries
  - Total Documents
  - Average Response Time
  - Total Cost
- [ ] System Health section shows status
- [ ] Charts render (if any data)

#### Document Management:
1. Click "Documents" in sidebar
2. **Expected:** List of uploaded documents
3. Click "Upload Document" button
4. Select a PDF, DOCX, or TXT file
5. **Expected:**
   - Upload progress shows
   - Document appears in list
   - Can see file size, upload date
6. Click delete button on a document
7. **Expected:** Confirmation dialog, then document deleted

#### Navigation:
- [ ] Click "BI Platform" link → navigates to /
- [ ] Sidebar shows all sections
- [ ] Active section highlighted

---

## 4. Test Desktop App

### Access:
Press **Ctrl+Shift+M** (if app is running in background)

### What to Test:

#### Window Toggle:
1. Press **Ctrl+Shift+M**
2. **Expected:** Window shows/hides
3. Press again
4. **Expected:** Window toggles

#### System Tray:
1. Right-click tray icon
2. **Expected:** Context menu appears with:
   - Show Assistant
   - Quick Search
   - Settings
   - Always on Top (checkbox)
   - Auto-start on Boot (checkbox)
   - Quit
3. Double-click tray icon
4. **Expected:** Window shows

#### Dashboard Button (NEW FEATURE):
1. Look at header of desktop app
2. Find **grid icon** (left of settings button)
3. Click dashboard button
4. **Expected:**
   - Message in chat: "🎨 Opening BI Platform in your browser..."
   - **Browser opens to http://localhost:3000**
   - BI Platform loads in browser

#### Chat in Desktop App:
1. Type in search box or chat input
2. Press Enter
3. **Expected:**
   - Message sent to backend
   - Response streams back
   - Chat history preserved

#### Settings:
1. Click settings icon (gear)
2. **Expected:** Settings panel opens
3. Change settings (API URL, Always on Top, etc.)
4. Click Save
5. **Expected:** Settings saved and applied

---

## 5. Test Standalone Chatbot Widget (Bubble)

### Access:
The standalone bubble widget is in `static/macrocomm-bubble.js`

### How to Test:

#### Option A: Create Test HTML Page
Create `test-bubble.html` in root:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Test Bubble Widget</title>
</head>
<body>
    <h1>Test Page with Chatbot</h1>
    <p>The chatbot bubble should appear in bottom-right corner.</p>

    <script src="/static/macrocomm-bubble.js"></script>
    <script>
        // Initialize the widget
        const chat = new MacrocommBubbleChatbot({
            apiUrl: 'http://localhost:8000',
            position: 'bottom-right',
            theme: 'light'
        });
    </script>
</body>
</html>
```

Then open: `http://localhost:8000/test-bubble.html`

#### Option B: Embed in External Site
Copy `static/macrocomm-bubble.js` to another website and include it.

### What to Test:
- [ ] Bubble appears in corner (orange circle with icon)
- [ ] Click bubble → chat window opens
- [ ] Can type and send messages
- [ ] Receives responses from backend
- [ ] Click X → chat closes
- [ ] Bubble persists as you navigate

---

# 🌐 ALL ACCESS URLS

## Frontend Pages:
- **BI Platform (Main):** http://localhost:3000/
- **Landing Page:** http://localhost:3000/landing
- **Admin Portal:** http://localhost:3000/admin
- **Settings:** http://localhost:3000/settings
- **Dashboards:** http://localhost:3000/dashboards

## Backend Endpoints:
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **RAG Status:** http://localhost:8000/api/rag/status
- **Analytics:** http://localhost:8000/api/analytics/summary

## Desktop App:
- **Hotkey:** Ctrl+Shift+M
- **Tray Icon:** Right-click for menu

## Qdrant:
- **Dashboard:** http://localhost:6333/dashboard
- **Collections:** http://localhost:6333/collections

---

# 🐛 TROUBLESHOOTING

## Backend Won't Start

### Problem: Port 8000 already in use
```
OSError: [WinError 10048] Only one usage of each socket address
```

**Solution:**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use a different port - edit .env
API_PORT=8000
```

### Problem: Qdrant connection failed
```
Failed to connect to Qdrant
```

**Solution:**
```bash
# Check if Qdrant is running
curl http://localhost:6333

# If not, start it:
docker run -p 6333:6333 qdrant/qdrant
```

### Problem: Model loading very slow
```
Loading embedding model... (takes 30+ seconds)
```

**Solution:** This is normal on first run. Be patient. Models are cached after first load.

---

## Frontend Won't Start

### Problem: Can't connect to backend
```
Failed to fetch http://localhost:8000
```

**Solution:**
Check `.env.local` has correct port:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Problem: Charts don't render
```
Cannot find module 'plotly.js-dist-min'
```

**Solution:**
```bash
cd frontend
npm install plotly.js-dist-min
```

### Problem: TypeScript errors
```
Property 'chart' does not exist on type 'ChatResponse'
```

**Solution:** Already fixed in client.ts, but if error persists:
```bash
cd frontend
npm run build
# Check for errors
```

---

## Desktop App Won't Start

### Problem: Electron not found
```
'electron' is not recognized
```

**Solution:**
```bash
cd desktop-app
npm install
```

### Problem: Dashboard button doesn't open browser
**Solution:** Check `main.js` has IPC handler (lines 285-289)

### Problem: Hotkey doesn't work
**Solution:** Check another app isn't using Ctrl+Shift+M. Change in settings.

---

## Admin Portal Issues

### Problem: No documents show
**Solution:** Upload a document first via /admin or main BI Platform

### Problem: Analytics show zero
**Solution:** Use the system first (upload docs, ask questions) to generate analytics

---

# ✅ SUCCESS CHECKLIST

After starting everything, verify:

## Backend:
- [ ] Starts without errors
- [ ] Health check returns 200
- [ ] Can access /docs (Swagger)
- [ ] Qdrant connected

## Frontend:
- [ ] Loads on port 3000
- [ ] Chat interface visible
- [ ] Can type in input
- [ ] No console errors

## Desktop App:
- [ ] Electron window appears (or in tray)
- [ ] Ctrl+Shift+M toggles window
- [ ] Dashboard button opens browser
- [ ] Can send messages

## Integration:
- [ ] Upload file in BI Platform → appears in Admin
- [ ] Ask for chart → renders inline
- [ ] Desktop app connects to backend
- [ ] All navigation works

---

# 🎯 QUICK TEST FLOW (5 MINUTES)

## 1. Start Everything (2 minutes)
```bash
# Terminal 1: Backend
python src/main_production_with_rag.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Desktop App
cd desktop-app && npm start
```

## 2. Test BI Platform (2 minutes)
1. Go to http://localhost:3000
2. Upload a CSV file
3. Ask: "Show me a chart of this data"
4. ✅ Verify: Chart renders inline

## 3. Test Desktop App (1 minute)
1. Press Ctrl+Shift+M
2. Click dashboard button (grid icon)
3. ✅ Verify: Browser opens to BI Platform

---

# 📊 EXPECTED SYSTEM STATE

Once everything is running:

## Ports in Use:
- **6333** - Qdrant vector database
- **8000** - Backend (FastAPI)
- **3000** - Frontend (Next.js)
- **Electron** - Desktop app (no fixed port)

## Processes Running:
- **Python** - Backend server
- **Node** - Next.js dev server
- **Electron** - Desktop app

## System Resources:
- **CPU:** Moderate (10-30% depending on activity)
- **RAM:** 2-4 GB total
- **GPU:** If available, used for embedding models

---

# 🎉 YOU'RE READY!

Once all three terminals show success messages:

✅ **Backend:** "Uvicorn running on http://127.0.0.1:8000"
✅ **Frontend:** "Ready in 2.5s"
✅ **Desktop:** Electron window visible or in tray

**Your complete Macrocomm BI Platform is now running!**

## What You Can Do Now:
1. **Upload data** (CSV, Excel, PDF, DOCX, TXT)
2. **Ask questions** about your data
3. **Generate charts** (84 types available!)
4. **Create dashboards** with KPIs and visualizations
5. **Use desktop app** for quick access
6. **Manage documents** in admin portal
7. **View analytics** on system usage

---

**Happy analyzing! 📊🎉**

---

**Last Updated:** January 9, 2026
**System Version:** 1.0.0 Production
