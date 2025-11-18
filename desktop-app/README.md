# 🖥️ Macrocomm AI Assistant - Desktop App

A cross-platform desktop application that provides always-available, global access to your company's knowledge base through an AI-powered assistant.

![Platform Support](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Electron](https://img.shields.io/badge/electron-latest-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🚀 Core Capabilities
- **System Tray Integration** - Always accessible from your system tray
- **Global Hotkey** - Instant access with `Ctrl/Cmd + Shift + M`
- **Always-on-Top Window** - Optional floating window that stays above other apps
- **Offline Mode** - Cached conversations available without internet
- **Quick Search** - Search knowledge base without opening full chat interface
- **Native Notifications** - Desktop notifications for responses when window is hidden
- **Auto-Start** - Optionally launch on system boot
- **Minimal Resource Usage** - Lightweight and efficient

### 💡 Key Benefits
- **Zero Context Switching** - Access knowledge without leaving your current application
- **Instant Answers** - Global hotkey provides immediate access
- **Works Everywhere** - Available across all applications system-wide
- **Persistent History** - All conversations cached locally
- **Privacy-Focused** - Data stored locally on your machine

### 🎯 Target Users
- Knowledge workers who need quick access to company information
- Support teams handling customer inquiries
- Developers referencing technical documentation
- Executives accessing business intelligence

## 📋 Requirements

- **Node.js** 16.x or later
- **npm** 8.x or later
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, Fedora 32+)

### Backend Dependency
The desktop app requires the Macrocomm RAG backend to be running:
- Default backend URL: `http://localhost:8000`
- Configurable in app settings

## 🚀 Installation

### Development Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd agentic-rag-pipeline/desktop-app
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Generate app icons** (requires ImageMagick):
   ```bash
   cd assets/icons
   ./generate-icons.sh
   cd ../..
   ```

   If you don't have ImageMagick, see `assets/icons/README.md` for alternatives.

4. **Start the development app**:
   ```bash
   npm start
   ```

   Or with development tools:
   ```bash
   npm run dev
   ```

### Production Build

Build installers for your platform:

```bash
# Windows (NSIS installer)
npm run build:win

# macOS (DMG)
npm run build:mac

# Linux (AppImage + deb)
npm run build:linux

# Build for all platforms
npm run build:all
```

Installers will be created in the `dist/` directory.

## ⚙️ Configuration

### First Launch

On first launch, the app will:
1. Appear in your system tray
2. Register the global hotkey (`Ctrl/Cmd + Shift + M`)
3. Check connection to the backend API
4. Load default settings

### Settings Panel

Access settings through:
- System tray menu → "Settings"
- App window → Settings icon (⚙️)

#### Available Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Backend API URL** | URL of your Macrocomm backend | `http://localhost:8000` |
| **Global Hotkey** | Keyboard shortcut to toggle window | `CommandOrControl+Shift+M` |
| **Always on Top** | Keep window above other applications | `true` |
| **Auto-start on Boot** | Launch app when system starts | `true` |
| **Offline Mode** | Use cached conversations when offline | `false` |

### Configuration File

Settings are stored in a persistent configuration file:

- **Windows**: `%APPDATA%/macrocomm-desktop/config.json`
- **macOS**: `~/Library/Application Support/macrocomm-desktop/config.json`
- **Linux**: `~/.config/macrocomm-desktop/config.json`

## 🎮 Usage

### Opening the App

Three ways to open the assistant:

1. **Global Hotkey**: Press `Ctrl/Cmd + Shift + M` from anywhere
2. **System Tray**: Double-click the tray icon
3. **Tray Menu**: Right-click tray → "Show Assistant"

### Quick Search

Access instant search:
1. Right-click tray icon → "Quick Search"
2. Or press global hotkey and click the search bar
3. Type your question and press Enter

### Chat Interface

**Keyboard Shortcuts**:
- `Enter` - Send message
- `Shift + Enter` - New line in message
- `Ctrl/Cmd + Shift + M` - Toggle window visibility
- `Esc` - Close settings panel

**Quick Action Buttons**:
- 📋 Company Policies
- 💰 Expense Reports
- 🏖️ Vacation Policy

### Hiding the Window

The app never fully closes - it minimizes to the system tray:
- Click the minimize button (—)
- Press the global hotkey while window is visible
- Close the window (X button)

To fully quit:
- Right-click tray icon → "Quit"
- Or use keyboard shortcut: `Ctrl/Cmd + Q`

## 🏗️ Architecture

### Process Structure

The app uses Electron's multi-process architecture:

```
┌─────────────────────────────────────────┐
│         Main Process (main.js)          │
│  - System tray management               │
│  - Global hotkey registration           │
│  - Window management                    │
│  - IPC handlers                         │
│  - Settings persistence                 │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼─────────┐
│ Preload Script │   │ Renderer Process │
│ (preload.js)   │   │  (renderer.js)   │
│                │   │                  │
│ - Security     │   │ - UI logic       │
│   bridge       │   │ - API calls      │
│ - Context      │   │ - Message        │
│   isolation    │   │   handling       │
└────────────────┘   └──────────────────┘
```

### File Structure

```
desktop-app/
├── src/
│   ├── main.js          # Main process (system integration)
│   ├── preload.js       # Security bridge
│   ├── renderer.js      # Renderer process (UI logic)
│   ├── index.html       # App UI structure
│   └── styles.css       # App styling
├── assets/
│   └── icons/           # App and tray icons
├── package.json         # Dependencies and build config
└── README.md           # This file
```

### Communication Flow

```
User Action → Renderer Process → IPC → Main Process
                    ↓
              Backend API
            (http://localhost:8000)
                    ↓
          Response → UI Update
```

## 🔒 Security

### Security Features

- **Context Isolation**: Renderer process isolated from Node.js
- **No Node Integration**: Direct Node.js access disabled in renderer
- **Preload Script**: Controlled API exposure via contextBridge
- **HTTPS Support**: Configurable for secure backend connections
- **Local Storage**: Sensitive data stays on device
- **No Telemetry**: Zero data collection or tracking

### Data Storage

All data is stored locally:

| Data Type | Location | Purpose |
|-----------|----------|---------|
| Settings | electron-store | Persistent configuration |
| Conversations | localStorage | Cached messages (last 100) |
| Session State | Memory | Current conversation context |

## 🐛 Troubleshooting

### App won't start

**Check Node.js version**:
```bash
node --version  # Should be 16.x or later
```

**Reinstall dependencies**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Global hotkey not working

- Check if another app is using the same hotkey
- Try changing the hotkey in settings
- On Linux, may require accessibility permissions

### Cannot connect to backend

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check API URL in settings matches your backend
3. Look for firewall blocking connections
4. Check backend logs for errors

### Tray icon not appearing

**Linux**: Some desktop environments require additional packages:
```bash
# Ubuntu/Debian
sudo apt-get install libappindicator3-1

# Fedora
sudo dnf install libappindicator-gtk3
```

### App uses too much memory

- Clear cached conversations (delete localStorage)
- Disable offline mode if not needed
- Restart the app periodically
- Check for memory leaks in backend API

## 🔧 Development

### Project Structure

```javascript
// Main Process (main.js)
- Window management
- Tray creation
- Hotkey registration
- IPC handlers
- Auto-start configuration

// Preload Script (preload.js)
- Expose limited API to renderer
- Security bridge

// Renderer Process (renderer.js)
- UI event handling
- Backend API communication
- Message rendering
- Local caching
```

### Debug Mode

Launch with dev tools:
```bash
npm run dev
# Or manually:
electron . --dev
```

This opens Chrome DevTools for debugging renderer process.

### Adding Features

1. **UI Changes**: Modify `index.html` and `styles.css`
2. **Business Logic**: Update `renderer.js`
3. **System Integration**: Modify `main.js`
4. **Security Bridge**: Update `preload.js` (carefully!)

### Building for Distribution

```bash
# Test build locally
npm run build:win   # or build:mac, build:linux

# Test installer
cd dist/
# Run the generated installer
```

## 📦 Distribution

### Installer Types

| Platform | Format | Output |
|----------|--------|--------|
| Windows | NSIS | `Macrocomm-Setup-1.0.0.exe` |
| macOS | DMG | `Macrocomm-1.0.0.dmg` |
| Linux | AppImage | `Macrocomm-1.0.0.AppImage` |
| Linux | Debian | `macrocomm_1.0.0_amd64.deb` |

### Auto-Update Support

To enable auto-updates, configure electron-builder with a release server:

```json
{
  "publish": {
    "provider": "github",
    "owner": "your-org",
    "repo": "macrocomm"
  }
}
```

## 🤝 Contributing

### Setting Up Development Environment

1. Fork and clone the repository
2. Install dependencies: `npm install`
3. Generate icons: `cd assets/icons && ./generate-icons.sh`
4. Start development: `npm run dev`
5. Make changes and test thoroughly
6. Build for your platform: `npm run build:win` (or mac/linux)

### Code Style

- Use 4 spaces for indentation
- Add JSDoc comments for functions
- Follow existing naming conventions
- Test on multiple platforms if possible

## 📄 License

MIT License - See main repository LICENSE file

## 🙋 Support

### Getting Help

- **Documentation**: See main project README
- **Issues**: Report bugs on GitHub Issues
- **Backend Setup**: Refer to backend API documentation

### Common Questions

**Q: Can I use a remote backend?**
A: Yes! Change the API URL in settings to your backend URL (e.g., `https://api.company.com`)

**Q: How much disk space does it use?**
A: ~100MB for the app, plus cached conversations (typically < 10MB)

**Q: Does it work without internet?**
A: With offline mode enabled, it can display cached conversations, but cannot answer new questions without backend connectivity.

**Q: Can I customize the UI colors?**
A: Yes, edit `src/styles.css` and rebuild the app.

## 🗺️ Roadmap

Future enhancements planned:
- [ ] Voice input support
- [ ] Multi-language support
- [ ] Customizable themes
- [ ] Plugin system for integrations
- [ ] Rich message formatting (markdown, code highlighting)
- [ ] File attachment support
- [ ] Conversation export (PDF, TXT)

---

**Built with ❤️ using Electron** | [Main Project](../README.md) | [Backend API Docs](../docs/API.md)
