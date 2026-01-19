# 🎯 Macrocomm BI Platform

**Enterprise-Grade Data Analytics & Visualization Platform with AI-Powered Insights**

Version 1.0.0 | Production Ready | January 2026

---

## 🚀 Quick Start

### Start Everything (3 Terminals)

**Terminal 1 - Backend:**
```bash
python src/main_production_with_rag.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

**Terminal 3 - Desktop App:**
```bash
cd desktop-app && npm start
```

### Access URLs:
- **BI Platform:** http://localhost:3000
- **Admin Portal:** http://localhost:3000/admin
- **Desktop App:** Press Ctrl+Shift+M

**📚 See QUICK_START.md and START_GUIDE.md for detailed instructions**

---

## ✨ What Can It Do?

- 🤖 **Natural Language Queries** - Ask questions about your data in plain English
- 📊 **84 Chart Types** - Automatically recommended and generated
- 🎨 **Smart Dashboards** - AI-powered dashboard creation with KPIs
- 💬 **RAG-Powered Chat** - Context-aware conversations using your documents
- 🖥️ **Multi-Platform** - Web app, desktop app, embeddable widget

---

## 🏗️ Architecture

**Backend:** Python + FastAPI + OpenAI GPT-4o-mini + Qdrant Vector DB
**Frontend:** React + Next.js 14 + TypeScript + Tailwind CSS + Plotly
**Desktop:** Electron with system tray integration

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **QUICK_START.md** | Essential commands (30 seconds) |
| **START_GUIDE.md** | Comprehensive startup guide |
| **INTEGRATION_TEST_PLAN.md** | 120+ test cases |
| **FINAL_SUMMARY.md** | Complete system documentation |

---

## 🎯 Key Features

### Data Analytics
- Upload CSV, Excel, PDF, DOCX, TXT
- AI-powered chart recommendations
- 84 visualization types
- Interactive dashboards
- Real-time insights

### Smart Chat
- RAG-enhanced responses
- Source citations
- Conversation history
- Streaming responses

### Desktop App
- Global hotkey (Ctrl+Shift+M)
- System tray integration
- Dashboard button to open BI Platform
- Offline-capable

---

## 🔧 System Requirements

- Python 3.10+
- Node.js 18+
- Qdrant (Docker or local)
- OpenAI API key

---

## 📊 System Status

✅ **All systems production-ready**

- Backend: Running on port 8000
- Frontend: Running on port 3000
- Desktop: Electron app
- Documentation: Complete

---

**Built with ❤️ by Macrocomm Team | Last Updated: January 9, 2026**