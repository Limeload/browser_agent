# Voice-Enabled Browser Agent Usage Guide

This guide provides detailed instructions on how to use the Voice-Enabled Browser Agent system.

## 🎯 Getting Started

### 1. Initial Setup

```bash
# Run the setup script
./setup.sh

# Or manually:
npm run install:all
cp env.example .env
# Edit .env with your API keys
```

### 2. Start Services

```bash
# Start all services
npm run dev

# Or start individually:
npm run dev:backend    # Python FastAPI (port 8000)
npm run dev:frontend   # React frontend (port 3000)
npm run dev:executor   # Browser executor (port 3001)
```

### 3. Access the Application

Open your browser and go to http://localhost:3000

## 🎤 Voice Commands

### Basic Navigation
```
"Go to google.com"
"Navigate to https://example.com"
"Open facebook.com"
"Visit the login page"
```

### Search Commands
```
"Search for machine learning tutorials"
"Find information about Python programming"
"Look up the weather today"
"Google 'best restaurants near me'"
```

### Form Interactions
```
"Fill the email field with john@example.com"
"Enter my password in the password field"
"Type 'Hello World' in the message box"
"Input my name in the name field"
```

### Click Actions
```
"Click the login button"
"Press the submit button"
"Tap on the menu icon"
"Select the first option"
```

### Scrolling
```
"Scroll down"
"Scroll up"
"Scroll to the bottom"
"Scroll to the top"
```

### Data Extraction
```
"Extract all links from this page"
"Get the text from the main content"
"Copy the page title"
"Find all images on this page"
```

### Screenshots
```
"Take a screenshot"
"Capture this page"
"Save the current view"
```

## 🔧 Advanced Usage

### Multi-Step Workflows

The system supports complex workflows that chain multiple actions:

```
"Fill out the contact form"
→ Navigate to contact page
→ Fill name field
→ Fill email field
→ Fill message field
→ Submit form
→ Take screenshot
```

### Context-Aware Commands

The system maintains context across commands:

```
"Go to the shopping cart"
"Add this item to cart"
"Proceed to checkout"
"Enter my shipping address"
```

### Error Recovery

If an action fails, the system will:
1. Retry the action (up to 3 times)
2. Try alternative selectors
3. Report the error with details
4. Continue with remaining actions

## 📊 Monitoring and Logs

### Real-Time Monitoring

Access the monitoring dashboard at http://localhost:3001:

- **System Health**: Service status and health checks
- **Performance Metrics**: Response times, error rates, throughput
- **Active Sessions**: Current user sessions
- **Resource Usage**: CPU, memory, and network usage

### Log Analysis

Access Kibana at http://localhost:5601:

- **Structured Logs**: JSON-formatted log entries
- **Service Filtering**: Filter by service (backend, executor, frontend)
- **Session Tracking**: Follow complete user sessions
- **Error Analysis**: Detailed error investigation

### Metrics Dashboard

Access Prometheus at http://localhost:9090:

- **Request Rate**: API calls per second
- **Error Rate**: Error frequency
- **Response Time**: Latency percentiles
- **Active Sessions**: Concurrent users
- **Processing Times**: STT, intent parsing, execution times

## 💾 Session Management

### Viewing Sessions

1. Go to the "Sessions" tab in the frontend
2. View all available sessions
3. Click on a session to see details
4. Export session data

### Exporting Data

Sessions can be exported in multiple formats:

- **JSON**: Complete session data with metadata
- **CSV**: Tabular format for analysis
- **HTML**: Human-readable report

### Session Data Includes

- Audio transcripts with confidence scores
- Parsed intents and entities
- Executed browser actions
- Screenshots captured
- Performance metrics
- Error logs

## 🛠️ Configuration

### STT Provider Configuration

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

### Intent Parsing Configuration

The system uses OpenAI GPT-4o for intent parsing. Configure with:

```bash
OPENAI_API_KEY=your_openai_api_key
```

### Monitoring Configuration

```bash
# Redis for caching
REDIS_URL=redis://localhost:6379

# Elasticsearch for logs
ELASTICSEARCH_URL=http://localhost:9200

# Prometheus metrics
METRICS_PORT=9090
```

## 🔒 Security Best Practices

### API Key Management

- Store API keys in environment variables
- Never commit keys to version control
- Use different keys for development and production
- Rotate keys regularly

### Network Security

- Use HTTPS in production
- Configure CORS properly
- Implement rate limiting
- Use secure WebSocket connections

### Data Privacy

- Configure data retention policies
- Encrypt sensitive data
- Implement access controls
- Regular security audits

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3
```

### Cloud Deployment

#### AWS
- **ECS**: Container orchestration
- **S3**: File storage
- **CloudWatch**: Monitoring
- **ElastiCache**: Redis caching

#### Google Cloud
- **Cloud Run**: Serverless containers
- **Cloud Storage**: File storage
- **Cloud Monitoring**: Metrics
- **Memorystore**: Redis caching

#### Azure
- **Container Instances**: Container hosting
- **Blob Storage**: File storage
- **Application Insights**: Monitoring
- **Redis Cache**: Caching

## 🐛 Troubleshooting

### Common Issues

#### Audio Not Captured
- Check microphone permissions
- Verify browser supports Web Audio API
- Check audio device settings

#### STT Not Working
- Verify API key is correct
- Check network connectivity
- Review STT provider quotas

#### Browser Actions Failing
- Check if target website is accessible
- Verify selectors are correct
- Review browser console for errors

#### High Latency
- Check network connectivity
- Monitor system resources
- Review service logs

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true npm run dev
```

### Log Analysis

Check logs in Kibana or use command line:

```bash
# Backend logs
docker-compose logs backend

# Executor logs
docker-compose logs executor

# Frontend logs
docker-compose logs frontend
```

## 📈 Performance Optimization

### Frontend Optimization

- Use audio compression
- Implement connection pooling
- Cache frequently used data
- Optimize bundle size

### Backend Optimization

- Use connection pooling
- Implement caching strategies
- Optimize database queries
- Use async processing

### Executor Optimization

- Reuse browser instances
- Implement action batching
- Use efficient selectors
- Optimize screenshot capture

## 🔮 Advanced Features

### Custom Workflows

Create custom workflow templates:

```python
# In backend/services/planner.py
custom_workflow = {
    "ecommerce_checkout": [
        {"action_type": "navigate", "url": "{product_url}"},
        {"action_type": "click", "selector": "button[data-testid='add-to-cart']"},
        {"action_type": "click", "selector": "a[href*='cart']"},
        {"action_type": "click", "selector": "button[data-testid='checkout']"}
    ]
}
```

### Custom Intent Types

Add new intent types:

```python
# In backend/models/schemas.py
class IntentType(str, Enum):
    CUSTOM_ACTION = "custom_action"
    # ... existing types
```

### Custom Monitoring

Add custom metrics:

```python
# In backend/services/monitoring.py
await monitoring_service.record_metric(
    "custom_metric",
    value,
    {"tag": "value"}
)
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Health Checks**: http://localhost:8000/health
- **Metrics**: http://localhost:9090
- **Logs**: http://localhost:5601
- **Dashboard**: http://localhost:3001

## 🆘 Support

- **GitHub Issues**: Create issues for bugs or feature requests
- **Documentation**: Check README.md and inline code comments
- **Community**: Use GitHub Discussions for questions
- **Email**: Contact the development team for enterprise support
