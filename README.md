# Voice Browser Agent

A sophisticated voice-enabled browser automation agent built with **React TypeScript** frontend and **Python FastAPI** backend. This application combines cutting-edge voice recognition with browser automation capabilities, similar to advanced AI assistants but focused on web automation tasks.

## 🏗️ Architecture

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI + WebSocket + Playwright
- **Communication**: Native WebSocket for real-time communication
- **Browser Automation**: Playwright for professional browser control

## ✨ Features

### 🎤 Voice Control
- **Real-time Speech Recognition**: Uses Web Speech API for live transcription
- **Intent Parsing**: Advanced natural language processing to understand commands
- **Command Structure Display**: Visual representation of parsed commands
- **Confidence Meter**: Real-time confidence scoring for voice input

### 🌐 Browser Automation
- **Playwright Integration**: Professional browser automation with headless Chrome
- **Multi-Command Support**: Navigate, click, type, scroll, wait, and screenshot commands
- **Live Status Monitoring**: Real-time connection status and session management
- **Screenshot Capture**: Automatic screenshot capture with results display

### 📊 Live Monitoring
- **Execution Logging**: Comprehensive logging system with timestamps
- **Performance Metrics**: Command success rate and execution statistics
- **Session Timer**: Real-time session duration tracking
- **Status Indicators**: Visual indicators for connection and recording status

### 🔊 Audio Feedback
- **Text-to-Speech**: Built-in TTS system for command confirmation
- **Visual Feedback**: Modern notification system for user feedback
- **Audio Cues**: Sound feedback for different system states

### 💾 Session Management
- **Save Sessions**: Export complete session data including commands and logs
- **Load Sessions**: Import and restore previous sessions
- **Export Logs**: Export execution logs in JSON format
- **Data Persistence**: Maintain session state across browser refreshes

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd browser_agent

# Run the startup script (installs dependencies and starts both services)
./start.sh
```

### Option 2: Manual Setup

#### 1. Install Dependencies
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies
npm install
```

#### 2. Build Frontend
```bash
npm run build
```

#### 3. Start Services
```bash
# Terminal 1: Start Python backend
python3 -m backend.main

# Terminal 2: Start React frontend (development)
npm run dev
```

#### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 Usage

### Getting Started
1. **Connect to Browser**: Enter a target URL and click "Connect Browser"
2. **Start Voice Control**: Click "Start Voice Control" to begin voice recognition
3. **Give Commands**: Speak naturally to control the browser

### Voice Commands

The system understands natural language commands:

#### Navigation
- "Go to google.com"
- "Navigate to example.com"
- "Visit github.com"

#### Interaction
- "Click the button"
- "Press the submit button"
- "Type hello world"
- "Enter my email address"
- "Scroll down"
- "Scroll up"

#### Capture
- "Take a screenshot"
- "Capture the page"
- "Take a picture"

#### Timing
- "Wait 5 seconds"
- "Pause for 2 minutes"

## 🛠️ Development

### Project Structure
```
browser_agent/
├── src/                    # React TypeScript frontend
│   ├── components/         # React components
│   ├── hooks/             # Custom React hooks
│   ├── types/             # TypeScript type definitions
│   └── App.tsx            # Main React app
├── backend/               # Python FastAPI backend
│   ├── main.py            # FastAPI application
│   ├── models.py          # Pydantic models
│   ├── websocket_manager.py # WebSocket handling
│   └── browser_automation.py # Playwright automation
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
└── start.sh              # Startup script
```

### Available Scripts

#### Frontend (React)
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run type-check   # TypeScript type checking
npm run lint         # ESLint code linting
```

#### Backend (Python)
```bash
python3 -m backend.main    # Start FastAPI server
uvicorn backend.main:app  # Alternative start command
```

### API Endpoints

#### HTTP Endpoints
- `GET /` - Serve React application
- `GET /health` - Health check with session count
- `GET /api/sessions` - List active sessions
- `DELETE /api/sessions/{id}` - Close specific session

#### WebSocket Events
- `connect-browser` - Initialize browser session
- `disconnect-browser` - Close browser session
- `execute-command` - Execute automation command
- `take-screenshot` - Capture screenshot

## 🔧 Configuration

### Configuration
The application uses default settings. No environment variables are required for basic operation.

### Browser Settings
The application uses Playwright with Chromium. Browser settings can be modified in `backend/browser_automation.py`:

```python
self.browser = await self.playwright.chromium.launch(
    headless=True,  # Set to False for debugging
    args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        # ... other args
    ]
)
```

## 🌐 Browser Compatibility

### Voice Recognition
- **Chrome/Chromium**: Full support ✅
- **Firefox**: Limited support ⚠️
- **Safari**: Limited support ⚠️
- **Edge**: Full support ✅

### Required Permissions
- Microphone access for voice recognition
- Camera access (if using visual features)

## 🐛 Troubleshooting

### Common Issues

1. **Voice Recognition Not Working**
   - Ensure microphone permissions are granted
   - Use HTTPS in production (required for Web Speech API)
   - Check browser compatibility

2. **Browser Connection Failed**
   - Verify Playwright installation: `pip3 install playwright`
   - Install browser binaries: `playwright install chromium`
   - Check system dependencies

3. **Commands Not Executing**
   - Verify WebSocket connection status
   - Check browser session is active
   - Review backend logs for errors

4. **Build Issues**
   - Ensure Node.js 16+ is installed
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### Debug Mode

Enable debug logging by setting environment variables:
```bash
export LOG_LEVEL=debug
python3 -m backend.main
```

## 📦 Dependencies

### Python Dependencies
- **FastAPI**: Modern web framework
- **Playwright**: Browser automation
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### Node.js Dependencies
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Lucide React**: Icons

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright** for excellent browser automation
- **FastAPI** for the modern Python web framework
- **React** for the powerful frontend framework
- **Web Speech API** for voice recognition capabilities

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review backend logs
- Open an issue on GitHub

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Advanced command chaining
- [ ] Custom command training
- [ ] Mobile app integration
- [ ] Cloud deployment options
- [ ] Advanced analytics dashboard
- [ ] Voice command history
- [ ] Custom browser profiles
- [ ] Integration with CI/CD pipelines# browser_agent
