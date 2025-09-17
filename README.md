# Voice-Enabled Browser Agent

A comprehensive AI-powered browser automation system that captures voice input, parses it into structured intents, and executes browser automation via Browserbase + Playwright, with centralized logging and monitoring.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Executor      │
│   (React/TS)    │◄──►│   (Python)      │◄──►│   (Node.js)     │
│                 │    │                 │    │                 │
│ • Audio Capture │    │ • STT Service   │    │ • Browserbase   │
│ • VAD & Chunking│    │ • Intent Parser │    │ • Playwright    │
│ • UI Dashboard  │    │ • Planner       │    │ • Automation    │
│ • TTS Playback  │    │ • Archive       │    │ • Screenshots   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Monitoring    │
                    │                 │
                    │ • Prometheus    │
                    │ • Grafana       │
                    │ • Elasticsearch │
                    │ • Redis         │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Docker and Docker Compose
- OpenAI API key (for intent parsing)
- STT provider API key (Whisper/Deepgram/Google)

### 1. Clone and Install

```bash
git clone <repository-url>
cd browser_agent
npm run install:all
```

### 2. Environment Setup

```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

### 3. Start Monitoring Stack

```bash
cd monitoring
docker-compose up -d
```

### 4. Start Services

```bash
# Start all services
npm run dev

# Or start individually:
npm run dev:backend    # Python FastAPI backend
npm run dev:frontend   # React frontend
npm run dev:executor   # Node.js browser executor
```

### 5. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Browser Executor**: http://localhost:3001
- **Grafana**: http://localhost:3001 (admin/admin)
- **Kibana**: http://localhost:5601
- **Prometheus**: http://localhost:9090

## 📋 Features

### 🎤 Voice Processing
- **Audio Capture**: Web Audio API with noise reduction
- **Voice Activity Detection**: Automatic speech detection
- **Audio Chunking**: Real-time audio streaming
- **Multiple STT Providers**: Whisper, Deepgram, Google STT

### 🧠 AI Intent Parsing
- **GPT-4o Integration**: Advanced intent understanding
- **Deterministic Validation**: Rule-based validation layer
- **Context Management**: Session-aware processing
- **Workflow Chaining**: Multi-step action sequences

### 🌐 Browser Automation
- **Playwright Integration**: Robust browser control
- **Resilient Selectors**: Multiple selector strategies
- **Screenshot Capture**: Visual execution tracking
- **Error Recovery**: Automatic retry mechanisms

### 📊 Monitoring & Observability
- **Structured Logging**: JSON-formatted logs
- **Metrics Collection**: Prometheus integration
- **Real-time Dashboards**: Grafana visualization
- **Log Aggregation**: Elasticsearch + Kibana

### 💾 Data Management
- **Session Archival**: Complete session storage
- **Export Capabilities**: JSON, CSV, HTML formats
- **Cloud Storage**: S3/GCS integration
- **Data Privacy**: Configurable retention policies

## 🛠️ Development

### Project Structure

```
browser_agent/
├── frontend/          # React/Next.js frontend
│   ├── app/           # Next.js app directory
│   ├── components/    # React components
│   ├── services/      # WebSocket & API services
│   └── store/         # Zustand state management
├── backend/           # Python FastAPI backend
│   ├── services/      # Core business logic
│   ├── models/        # Pydantic schemas
│   └── main.py        # FastAPI application
├── executor/          # Node.js browser executor
│   ├── src/          # TypeScript source
│   ├── services/     # Browser automation
│   └── routes/       # API endpoints
├── monitoring/        # Observability stack
│   ├── docker-compose.yml
│   ├── prometheus.yml
│   └── grafana/       # Dashboards & configs
└── README.md
```

### Available Scripts

```bash
# Development
npm run dev                    # Start all services
npm run dev:frontend          # Frontend only
npm run dev:backend           # Backend only
npm run dev:executor          # Executor only

# Production
npm run build                 # Build frontend
npm run start                 # Start production services

# Utilities
npm run install:all           # Install all dependencies
```

### API Endpoints

#### Backend (Port 8000)
- `GET /health` - Health check
- `GET /api/sessions` - List sessions
- `POST /api/export/{session_id}` - Export session
- `WebSocket /ws/{session_id}` - Real-time communication

#### Executor (Port 3001)
- `GET /health` - Health check
- `POST /api/execute` - Execute browser actions
- `GET /api/execution/{session_id}/status` - Execution status
- `POST /api/execution/{session_id}/cancel` - Cancel execution

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# STT Provider
STT_PROVIDER=whisper  # whisper, deepgram, google
OPENAI_API_KEY=your_key_here

# Monitoring
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200

# Cloud Storage
AWS_ACCESS_KEY_ID=your_key
S3_BUCKET_NAME=voice-agent-archive
```

### STT Provider Setup

#### Whisper (Default)
```bash
STT_PROVIDER=whisper
WHISPER_MODEL_SIZE=base  # tiny, base, small, medium, large
```

#### Deepgram
```bash
STT_PROVIDER=deepgram
DEEPGRAM_API_KEY=your_deepgram_key
```

#### Google Speech-to-Text
```bash
STT_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## 📈 Monitoring

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin):

- **Voice Agent Overview**: System metrics and performance
- **Request Rate**: API call frequency
- **Error Rate**: Error tracking and alerting
- **Response Time**: Latency monitoring
- **Active Sessions**: Concurrent user tracking

### Log Analysis

Access Kibana at http://localhost:5601:

- **Structured Logs**: JSON-formatted log entries
- **Service Filtering**: Filter by service (backend, executor, frontend)
- **Session Tracking**: Follow complete user sessions
- **Error Analysis**: Detailed error investigation

### Metrics

Prometheus metrics available at http://localhost:9090:

- `voice_agent_requests_total` - Total requests
- `voice_agent_request_duration_seconds` - Request latency
- `voice_agent_errors_total` - Error count
- `voice_agent_active_sessions` - Active sessions
- `voice_agent_stt_processing_seconds` - STT processing time
- `voice_agent_intent_parsing_seconds` - Intent parsing time
- `voice_agent_execution_seconds` - Browser execution time

## 🎯 Usage Examples

### Basic Voice Commands

```
"Go to google.com"
"Search for machine learning tutorials"
"Click on the login button"
"Fill the email field with john@example.com"
"Scroll down"
"Take a screenshot"
"Extract all links from this page"
```

### Advanced Workflows

The system supports complex multi-step workflows:

```
"Fill out the contact form with my details"
→ Navigate to form page
→ Fill name field
→ Fill email field
→ Fill message field
→ Submit form
→ Take screenshot
```

## 🔒 Security Considerations

- **API Key Management**: Store keys in environment variables
- **CORS Configuration**: Restrict origins in production
- **Input Validation**: All inputs are validated and sanitized
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **Session Management**: Secure session handling
- **Data Privacy**: Configurable data retention policies

## 🚀 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

The system is designed for cloud deployment:

- **Backend**: Deploy to AWS ECS, Google Cloud Run, or Azure Container Instances
- **Frontend**: Deploy to Vercel, Netlify, or AWS S3 + CloudFront
- **Executor**: Deploy to AWS Lambda, Google Cloud Functions, or Azure Functions
- **Monitoring**: Use managed services (AWS CloudWatch, Google Cloud Monitoring)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Advanced workflow templates
- [ ] Mobile app integration
- [ ] Enterprise SSO integration
- [ ] Advanced analytics and reporting
- [ ] Custom voice model training
- [ ] Browser extension support