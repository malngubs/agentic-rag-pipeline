# 🔧 STARTUP FIX - Port 3000 Issue Resolved

## Problem Identified:
1. **Port 3000 was already in use** - Old Node.js process running
2. **Memory allocation issue** - RangeError during startup

## Solutions Implemented:

### ✅ Created Startup Scripts

I've created 3 Windows batch files to handle everything automatically:

1. **START-BACKEND.bat** - Starts backend on port 8000
2. **START-FRONTEND.bat** - Kills old processes, cleans build, starts frontend
3. **START-DESKTOP.bat** - Starts Electron desktop app

---

## 🚀 NEW EASY STARTUP (Use These!)

### Option 1: Use Batch Files (RECOMMENDED)

**Double-click these files in order:**

1. **START-BACKEND.bat** - Start this first
2. **START-FRONTEND.bat** - Start this second (waits for you)
3. **START-DESKTOP.bat** - Start this third (optional)

Each script:
- Checks prerequisites
- Cleans up old processes
- Starts the component
- Shows clear status messages

---

### Option 2: Manual Commands (If scripts don't work)

#### Terminal 1 - Backend:
```bash
python src\main_production_with_rag.py
```

#### Terminal 2 - Frontend (with fixes):
```bash
cd frontend

# Kill any process on port 3000
powershell -Command "Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force"

# Clean build
rmdir /s /q .next

# Start with more memory
set NODE_OPTIONS=--max-old-space-size=4096
npm run dev
```

#### Terminal 3 - Desktop App:
```bash
cd desktop-app
npm start
```

---

## 🐛 About the "Uvicorn" Tab Issue

The "Uvicorn" tab you see is likely one of these:

### Issue 1: Browser Tab Title from Backend
When you visit `http://localhost:8000` directly, you might see "Uvicorn" because that's the backend server name.

**Solution:** Always use the frontend URL: `http://localhost:3000`

### Issue 2: WebSocket Connection in DevTools
The browser developer tools might show "Uvicorn" in the WebSocket connection.

**Solution:** This is normal and doesn't affect users. It's just the server identification.

### Issue 3: Redirect Issue
If the frontend redirects to backend, check:

1. `.env.local` in frontend folder has:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

2. You're accessing `http://localhost:3000` NOT `http://localhost:8000`

---

## ✅ Verification Steps

After starting everything:

1. **Check Backend:**
   ```
   Open: http://localhost:8000/health
   Should see: {"status": "healthy"}
   ```

2. **Check Frontend:**
   ```
   Open: http://localhost:3000
   Should see: Chat interface with "Macrocomm BI Platform" title
   ```

3. **Check Desktop:**
   ```
   Press: Ctrl+Shift+M
   Should see: Desktop app window
   ```

---

## 🔍 Troubleshooting Port 3000

### If port 3000 is still in use:

**Option A - Kill all Node processes:**
```powershell
powershell -Command "Get-Process node | Stop-Process -Force"
```

**Option B - Find and kill specific process:**
```bash
# Find PID
netstat -ano | findstr :3000

# Kill it (replace 12345 with actual PID)
powershell -Command "Stop-Process -Id 12345 -Force"
```

**Option C - Use different port:**
Edit `frontend/package.json`:
```json
{
  "scripts": {
    "dev": "next dev -p 3001"
  }
}
```

Then access: `http://localhost:3001`

---

## 🎯 Expected Behavior

### After Starting Backend:
```
🚀 STARTING MACROCOMM BI PLATFORM...
✅ Qdrant connection successful
✅ RAG system initialized
INFO: Uvicorn running on http://127.0.0.1:8000
```
**Browser Tab Title:** "Uvicorn" (if you visit directly) - This is OK!

### After Starting Frontend:
```
▲ Next.js 14.0.4
- Local: http://localhost:3000
✓ Ready in 2.5s
```
**Browser Tab Title:** "Macrocomm BI Platform" - This is what you want!

### After Starting Desktop:
```
Electron app window or system tray icon
```
**Window Title:** "Macrocomm AI Assistant"

---

## 📝 Quick Reference

| Component | Port | URL | Tab Title |
|-----------|------|-----|-----------|
| **Backend** | 8000 | http://localhost:8000 | "Uvicorn" (don't visit directly) |
| **Frontend** | 3000 | http://localhost:3000 | "Macrocomm BI Platform" ✅ |
| **Admin** | 3000 | http://localhost:3000/admin | "Admin | Macrocomm BI" ✅ |
| **Desktop** | N/A | Press Ctrl+Shift+M | "Macrocomm AI Assistant" ✅ |

---

## 🎉 Summary

### What Was Fixed:
1. ✅ Created automatic startup scripts (.bat files)
2. ✅ Scripts kill old processes on port 3000
3. ✅ Scripts clean build folders
4. ✅ Scripts set proper memory allocation
5. ✅ Clear instructions for "Uvicorn" tab issue

### What You Should Do:
1. **Use START-BACKEND.bat** (double-click)
2. **Use START-FRONTEND.bat** (double-click)
3. **Visit http://localhost:3000** (not localhost:8000!)
4. ✅ You should see "Macrocomm BI Platform" in the tab

### If You Still See "Uvicorn":
- Make sure you're at `http://localhost:3000` (NOT 8000)
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito/private browsing mode
- Check the URL bar - it should say "localhost:3000"

---

**Problem Solved! Use the .bat files for easy startup! 🎉**

**Last Updated:** January 9, 2026
