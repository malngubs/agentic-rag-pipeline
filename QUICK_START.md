# ⚡ QUICK START - Macrocomm BI Platform

## SUPER EASY - Just Double-Click! 🖱️

---

## 🚀 Start Everything (USE THIS!)

### 1. Start Backend
**Double-click:** `START-BACKEND.bat`

### 2. Start Frontend
**Double-click:** `START-FRONTEND.bat`

### 3. Start Desktop App (Optional)
**Double-click:** `START-DESKTOP.bat`

**Done! That's it!** 🎉

---

## 🌐 Access URLs

| Component | URL |
|-----------|-----|
| **BI Platform** | http://localhost:3000 ⭐ USE THIS! |
| **Admin Portal** | http://localhost:3000/admin |
| **Landing Page** | http://localhost:3000/landing |
| **Backend Health** | http://localhost:8000/health |
| **API Docs** | http://localhost:8000/docs |
| **Desktop App** | Press Ctrl+Shift+M |

⚠️ **IMPORTANT:** Use `localhost:3000` NOT `localhost:8000`!

---

## 🔧 One-Time Setup (First Time Only)

Only do this once before first run:

```bash
# 1. Install Plotly
cd frontend
npm install plotly.js-dist-min

# 2. Verify Qdrant is running
curl http://localhost:6333
# If not: docker run -p 6333:6333 qdrant/qdrant
```

---

## ✅ Quick Test (30 seconds)

1. Open **http://localhost:3000** (tab should say "Macrocomm BI Platform")
2. Upload a CSV file
3. Ask: "Show me a chart"
4. ✅ Chart should render inline

---

## 🐛 Troubleshooting

### Port 3000 in use?
The `START-FRONTEND.bat` script automatically kills old processes!

### See "Uvicorn" in tab?
You're at the wrong URL! Use **http://localhost:3000** (NOT 8000)

### Frontend won't start?
1. Close all Node.js processes
2. Delete `frontend\.next` folder
3. Run `START-FRONTEND.bat` again

**See STARTUP-FIX.md for detailed troubleshooting**

---

## 🛑 Stop Everything

Just close the terminal windows or press Ctrl+C in each.

---

## 📚 More Help

- **STARTUP-FIX.md** - Port 3000 and "Uvicorn" tab issues
- **START_GUIDE.md** - Complete startup guide
- **INTEGRATION_TEST_PLAN.md** - Full testing guide

---

**Easy startup with .bat files! Double-click and go! 🚀**
