# 🧪 MACROCOMM BI PLATFORM - INTEGRATION TEST PLAN

## Date: January 9, 2026
## Status: Ready for Testing

---

# 📋 PRE-TEST CHECKLIST

## ✅ Fixed Issues:
- [x] Backend port changed from 8000 to 8000 (Windows permission fix)
- [x] Admin portal upload endpoint fixed (`/api/upload` instead of `/api/documents/upload`)
- [x] Desktop app port updated to 8000
- [x] Frontend environment variables point to port 8000
- [x] All visualization components created (ChartWidget, KPICard, DashboardWidget, DataTable)

## ✅ Backend API Endpoints Verified:

### Document Management:
- `/api/upload` - Upload documents (POST)
- `/api/documents/list` - List all documents (GET)
- `/api/documents/{doc_id}` - Get document details (GET)
- `/api/documents/{doc_id}` - Delete document (DELETE)

### Analytics:
- `/api/analytics/summary` - Get analytics summary (GET)
- `/api/analytics/budget-alert` - Get budget alerts (GET)
- `/api/analytics/cost-breakdown` - Get cost breakdown (GET)
- `/api/analytics/trends` - Get trends (GET)

### Health & Status:
- `/health` - Backend health check (GET)
- `/api/rag/status` - RAG system status (GET)

### Chat:
- `/api/chat` - Chat with data analyst (POST)
- WebSocket streaming for real-time responses

---

# 🚀 TESTING PROCEDURE

## Step 1: Start Backend

```bash
# Navigate to project root
cd c:\Users\Malusi\OneDrive - MACROCOMM\Desktop\agentic-rag-pipeline

# Start backend
python src/main_production_with_rag.py
```

**Expected Output:**
```
🚀 STARTING MACROCOMM BI PLATFORM...
✅ Qdrant connection successful
✅ RAG system initialized
✅ Analytics database initialized
✅ Server running on http://127.0.0.1:8000
```

**Verify:**
- [ ] Backend starts without errors
- [ ] Port 8000 is accessible
- [ ] Qdrant connection successful
- [ ] No import errors

**Test Health Endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "rag_initialized": true,
  "documents_indexed": 0
}
```

---

## Step 2: Start Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies (if not done)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
✓ Ready in 2.5s
○ Local:   http://localhost:3000
```

**Verify:**
- [ ] Frontend starts without errors
- [ ] No compilation errors
- [ ] Accessible at http://localhost:3000

---

## Step 3: Start Desktop App (Optional)

```bash
# Open new terminal
cd desktop-app

# Install dependencies (if not done)
npm install

# Start app
npm start
```

**Expected:**
- [ ] Electron window appears (hidden by default)
- [ ] System tray icon visible
- [ ] Press Ctrl+Shift+M to toggle window
- [ ] Window shows Macrocomm AI Assistant

---

# 🔍 COMPONENT TESTING

## Test 1: Landing Page

**URL:** http://localhost:3000/landing

**Test Cases:**

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 1.1 | Visit landing page | Page loads with Macrocomm branding | [ ] |
| 1.2 | Check font | Font is Inter/Segoe UI throughout | [ ] |
| 1.3 | Check theme | Dark glossy theme, Orange #FF6E00 | [ ] |
| 1.4 | Click "BI Platform" button | Navigate to http://localhost:3000/ | [ ] |
| 1.5 | Click "Admin Portal" button | Navigate to http://localhost:3000/admin | [ ] |
| 1.6 | Check responsive design | Layout adapts to window resize | [ ] |

**Screenshots:**
- [ ] Landing page (desktop)
- [ ] Landing page (mobile view)

---

## Test 2: BI Platform (Main Chat Interface)

**URL:** http://localhost:3000/

**Test Cases:**

### Basic Functionality:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.1 | Visit BI Platform | Chat interface loads | [ ] |
| 2.2 | Check font | Font is Inter/Segoe UI | [ ] |
| 2.3 | Type in input | Can type message | [ ] |
| 2.4 | Press Enter | Message doesn't send (no data uploaded yet) | [ ] |
| 2.5 | Check connection indicator | Shows "Connected" or "Disconnected" | [ ] |

### File Upload:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.6 | Click upload button | File picker opens | [ ] |
| 2.7 | Upload CSV file | File uploads successfully | [ ] |
| 2.8 | Check response | Shows "File uploaded: X rows, Y columns" | [ ] |
| 2.9 | Upload invalid file (e.g., .exe) | Shows error message | [ ] |
| 2.10 | Upload large file (>100MB) | Shows size limit error | [ ] |

### Chart Generation:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.11 | Ask: "Show me a chart" | Backend generates chart | [ ] |
| 2.12 | Verify chart renders | ChartWidget displays Plotly chart | [ ] |
| 2.13 | Check chart theme | Macrocomm branding applied | [ ] |
| 2.14 | Hover over chart | Tooltips appear | [ ] |
| 2.15 | Click fullscreen | Chart expands to fullscreen | [ ] |
| 2.16 | Click export | PNG download works | [ ] |

### Dashboard Generation:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.17 | Ask: "Create a dashboard" | Backend generates dashboard | [ ] |
| 2.18 | Verify KPIs display | KPICard components show metrics | [ ] |
| 2.19 | Verify charts display | Multiple charts in grid layout | [ ] |
| 2.20 | Check responsive grid | Grid adapts to window size | [ ] |
| 2.21 | Check theme consistency | All widgets use Macrocomm theme | [ ] |

### Data Table:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.22 | Ask: "Show me the data" | DataTable renders | [ ] |
| 2.23 | Click column header | Column sorts | [ ] |
| 2.24 | Click pagination | Next/previous page works | [ ] |
| 2.25 | Check number formatting | Numbers formatted correctly | [ ] |

**Screenshots:**
- [ ] Empty chat state
- [ ] File uploaded
- [ ] Chart rendered inline
- [ ] Dashboard with KPIs and charts
- [ ] Data table

---

## Test 3: Admin Portal

**URL:** http://localhost:3000/admin

**Test Cases:**

### Page Load:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.1 | Visit admin portal | Page loads | [ ] |
| 3.2 | Check font | Font is Inter/Segoe UI | [ ] |
| 3.3 | Check theme | Dark glossy, Macrocomm Orange | [ ] |
| 3.4 | Check sidebar | Navigation links present | [ ] |

### Analytics Dashboard:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.5 | View analytics cards | 4 KPI cards display | [ ] |
| 3.6 | Check total queries | Shows number from backend | [ ] |
| 3.7 | Check total documents | Shows number from backend | [ ] |
| 3.8 | Check avg response time | Shows value in ms | [ ] |
| 3.9 | Check total cost | Shows cost in dollars | [ ] |

### Document Management:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.10 | View document list | All uploaded documents shown | [ ] |
| 3.11 | Click upload button | File picker opens | [ ] |
| 3.12 | Upload PDF file | File uploads, appears in list | [ ] |
| 3.13 | Upload DOCX file | File uploads successfully | [ ] |
| 3.14 | Upload Excel file | File uploads successfully | [ ] |
| 3.15 | Upload TXT file | File uploads successfully | [ ] |
| 3.16 | Click delete button | Confirmation dialog appears | [ ] |
| 3.17 | Confirm delete | Document deleted from list | [ ] |
| 3.18 | Refresh page | Document list persists | [ ] |

### System Health:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.19 | View system health | Status indicators show | [ ] |
| 3.20 | Check Qdrant status | Shows "Connected" or status | [ ] |
| 3.21 | Check RAG status | Shows initialized status | [ ] |

### Navigation:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.22 | Click "BI Platform" link | Navigate to main platform | [ ] |
| 3.23 | Click logo | Navigate somewhere or refresh | [ ] |

**Screenshots:**
- [ ] Admin dashboard overview
- [ ] Document list (with documents)
- [ ] File upload in progress
- [ ] Delete confirmation dialog

---

## Test 4: Desktop App

**Launch:** Press Ctrl+Shift+M or click system tray icon

**Test Cases:**

### Basic Functionality:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 4.1 | Launch app | Window appears | [ ] |
| 4.2 | Check connection | Shows "Connected" to backend | [ ] |
| 4.3 | Press Ctrl+Shift+M | Window toggles (hide/show) | [ ] |
| 4.4 | Double-click tray icon | Window shows | [ ] |
| 4.5 | Right-click tray icon | Context menu appears | [ ] |

### Chat Functionality:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 4.6 | Type in search box | Can type | [ ] |
| 4.7 | Press Enter | Sends message to backend | [ ] |
| 4.8 | Receive response | Assistant message appears | [ ] |
| 4.9 | Check message history | Messages persist in chat | [ ] |

### Settings:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 4.10 | Click settings icon | Settings panel opens | [ ] |
| 4.11 | Toggle "Always on Top" | Window behavior changes | [ ] |
| 4.12 | Toggle "Auto-start" | Setting saved | [ ] |
| 4.13 | Change API URL | Can edit URL | [ ] |

### Integration (if dashboard button exists):

| Test | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 4.14 | Look for dashboard button | Button visible in header? | [ ] |
| 4.15 | Click dashboard button (if exists) | Opens http://localhost:3000 in browser | [ ] |

**Screenshots:**
- [ ] Desktop app main window
- [ ] System tray icon and menu
- [ ] Settings panel
- [ ] Chat conversation

---

## Test 5: Navigation Flow

**Test all navigation paths:**

| Start | Action | Destination | Pass/Fail |
|-------|--------|-------------|-----------|
| Landing | Click "BI Platform" | BI Platform (/) | [ ] |
| Landing | Click "Admin Portal" | Admin (/admin) | [ ] |
| Landing | Click "Desktop App" | Launch desktop app | [ ] |
| BI Platform | Type URL /landing | Landing page | [ ] |
| BI Platform | Type URL /admin | Admin portal | [ ] |
| Admin | Click "BI Platform" link | BI Platform (/) | [ ] |
| Admin | Type URL /landing | Landing page | [ ] |
| Desktop App | Click dashboard button | Opens BI Platform in browser | [ ] |

---

## Test 6: End-to-End User Flow

**Scenario:** User wants to analyze sales data

**Steps:**

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 6.1 | Visit http://localhost:3000 | BI Platform loads | [ ] |
| 6.2 | Upload sales_data.csv | File uploaded successfully | [ ] |
| 6.3 | Backend processes file | Shows "X rows, Y columns" | [ ] |
| 6.4 | Ask: "Show me sales trends" | Assistant responds | [ ] |
| 6.5 | Backend generates chart | Line chart appears inline | [ ] |
| 6.6 | Chart is interactive | Can hover, zoom, pan | [ ] |
| 6.7 | Chart has Macrocomm theme | Orange accent, dark background | [ ] |
| 6.8 | Ask: "Create a sales dashboard" | Assistant responds | [ ] |
| 6.9 | Backend generates dashboard | Dashboard widget appears | [ ] |
| 6.10 | KPIs display | 4 KPI cards with metrics | [ ] |
| 6.11 | Multiple charts display | 3-4 charts in grid | [ ] |
| 6.12 | Ask: "What insights do you see?" | Assistant provides analysis | [ ] |
| 6.13 | Ask: "Predict next month sales" | Forecast chart appears | [ ] |
| 6.14 | Export chart | PNG downloads | [ ] |
| 6.15 | Navigate to /admin | Admin portal loads | [ ] |
| 6.16 | See uploaded file in list | sales_data.csv appears | [ ] |
| 6.17 | Check analytics | Query count increased | [ ] |

**Screenshots:**
- [ ] Full end-to-end flow (multiple screenshots)

---

## Test 7: Error Handling

**Test error scenarios:**

| Test | Scenario | Expected Result | Pass/Fail |
|------|----------|----------------|-----------|
| 7.1 | Backend stopped, visit BI Platform | Shows "Disconnected" or error | [ ] |
| 7.2 | Upload invalid file type | Clear error message | [ ] |
| 7.3 | Upload corrupted file | Error handled gracefully | [ ] |
| 7.4 | Ask question without data | Helpful error message | [ ] |
| 7.5 | Backend crashes during chat | Frontend shows error | [ ] |
| 7.6 | Network disconnected | Shows offline mode | [ ] |
| 7.7 | Qdrant down | Backend shows error | [ ] |

---

## Test 8: Performance

**Test performance characteristics:**

| Test | Scenario | Expected Result | Pass/Fail |
|------|----------|----------------|-----------|
| 8.1 | Upload 1MB file | Uploads in <5 seconds | [ ] |
| 8.2 | Upload 50MB file | Uploads successfully | [ ] |
| 8.3 | Chart with 1K points | Renders in <2 seconds | [ ] |
| 8.4 | Chart with 10K points | Renders smoothly | [ ] |
| 8.5 | Dashboard with 4 charts | All render without lag | [ ] |
| 8.6 | Chat response time | <3 seconds for simple queries | [ ] |
| 8.7 | Page load time | <2 seconds for all pages | [ ] |

---

## Test 9: Visual Consistency

**Verify design consistency:**

| Test | Check | Expected | Pass/Fail |
|------|-------|----------|-----------|
| 9.1 | Landing page font | Inter, Segoe UI | [ ] |
| 9.2 | BI Platform font | Inter, Segoe UI | [ ] |
| 9.3 | Admin portal font | Inter, Segoe UI | [ ] |
| 9.4 | Chart widget font | Inter, Segoe UI | [ ] |
| 9.5 | All pages use Orange #FF6E00 | Consistent accent color | [ ] |
| 9.6 | All pages dark glossy theme | Consistent background | [ ] |
| 9.7 | Button styles consistent | Same style everywhere | [ ] |
| 9.8 | Card styles consistent | Same glass morphism | [ ] |

---

## Test 10: Browser Compatibility

**Test on multiple browsers:**

| Browser | Version | Landing | BI Platform | Admin | Pass/Fail |
|---------|---------|---------|-------------|-------|-----------|
| Chrome | Latest | [ ] | [ ] | [ ] | [ ] |
| Firefox | Latest | [ ] | [ ] | [ ] | [ ] |
| Edge | Latest | [ ] | [ ] | [ ] | [ ] |
| Safari | Latest | [ ] | [ ] | [ ] | [ ] |

---

# 📊 BACKEND CAPABILITIES TEST

## Test Backend Chart Types

**Verify backend can generate all chart categories:**

| Category | Test Query | Expected Chart Type | Pass/Fail |
|----------|-----------|-------------------|-----------|
| Comparison | "Compare sales by region" | Bar chart | [ ] |
| Correlation | "Show relationship between marketing and sales" | Scatter plot | [ ] |
| Part-to-Whole | "Show market share distribution" | Pie chart | [ ] |
| Time Series | "Show sales over time" | Line chart | [ ] |
| Distribution | "Show sales distribution" | Histogram | [ ] |
| Geospatial | "Show sales by location" | Map/choropleth | [ ] |

---

# 🐛 ISSUES FOUND

| # | Component | Issue | Severity | Status |
|---|-----------|-------|----------|--------|
| 1 | Admin Portal | Upload endpoint was `/api/documents/upload` instead of `/api/upload` | High | ✅ Fixed |
| 2 | Desktop App | Port was 8000 instead of 8000 | High | ✅ Fixed |
| 3 | Desktop App | No dashboard button to open BI Platform | Medium | ⚠️ Pending |
| 4 | ChatInterface | Visualization components not integrated | High | ⚠️ Pending |
| 5 | | | | |

---

# ✅ SUCCESS CRITERIA

## Must Pass:

- [ ] Backend starts without errors on port 8000
- [ ] Frontend loads all pages (landing, BI platform, admin)
- [ ] File upload works in both BI Platform and Admin
- [ ] Charts render inline in chat messages
- [ ] Admin portal displays analytics and documents
- [ ] All fonts are Inter/Segoe UI
- [ ] All pages use Macrocomm Orange (#FF6E00) theme
- [ ] All navigation buttons work
- [ ] No console errors in browser

## Should Pass:

- [ ] Desktop app connects to backend
- [ ] Dashboard generation works
- [ ] KPI cards display correctly
- [ ] Data tables are sortable and paginated
- [ ] Export functionality works
- [ ] All 84 chart types can be generated
- [ ] Performance is acceptable (<3s response time)

## Nice to Have:

- [ ] Desktop app has dashboard button
- [ ] Offline mode works
- [ ] Mobile responsive design works
- [ ] All browsers supported

---

# 📝 TEST RESULTS SUMMARY

**Date Tested:** _______________

**Tested By:** _______________

**Total Tests:** 120+

**Passed:** _____

**Failed:** _____

**Blocked:** _____

**Pass Rate:** _____%

---

# 🚀 NEXT STEPS AFTER TESTING

1. **Fix Critical Issues:**
   - Integrate visualization components into ChatInterface.tsx
   - Add dashboard button to desktop app
   - Fix any broken navigation

2. **Optimize Performance:**
   - Check bundle size
   - Optimize Plotly loading
   - Add loading skeletons

3. **Enhance UX:**
   - Add error boundaries
   - Add loading states
   - Add success notifications

4. **Documentation:**
   - Update README with test results
   - Document any workarounds
   - Create user guide

---

**Status:** ✅ TEST PLAN COMPLETE - READY FOR EXECUTION

**Last Updated:** January 9, 2026
