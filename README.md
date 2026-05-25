# Voice Browser Agent

A voice-controlled browser automation agent. Speak a command — the agent transcribes it with Whisper, parses the intent with Claude, and executes it in a real browser via Playwright.

## Architecture

```
Microphone  ->  Whisper (speech-to-text)
            ->  Claude claude-sonnet-4-6 (intent parsing / TaskIntent schema)
            ->  FastAPI backend (POST /parse, WebSocket /ws)
            ->  Playwright (browser automation)
            ->  React + Vite frontend (voice panel, intent panel, browser panel)
```

## Stack

| Layer | Technology |
|---|---|
| Voice input | Web Speech API (browser) or OpenAI Whisper-1 (audio file upload) |
| Intent parser | Claude claude-sonnet-4-6 via Anthropic SDK — forced `tool_use` for structured output |
| API layer | FastAPI + uvicorn |
| Browser automation | Playwright (Chromium) |
| Real-time channel | WebSocket (`/ws`) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (only needed for `/parse/audio`)

### Setup

```bash
git clone https://github.com/Limeload/browser_agent.git
cd browser_agent

# Copy and fill in your keys
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
playwright install chromium
npm install
```

### Run

```bash
# Option 1 — automated
./start.sh

# Option 2 — manual (two terminals)
python3 -m uvicorn backend.main:app --reload --port 8000
npm run dev
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## API reference

### `POST /parse`

Parse a text transcript into a structured `TaskIntent`.

```json
// Request
{ "transcript": "Go to github.com" }

// Response
{
  "action_type": "navigate",
  "reversibility": "reversible",
  "requires_confirmation": false,
  "confidence": 0.97,
  "target": "https://github.com",
  "value": null,
  "steps": [],
  "ambiguity_flags": [],
  "description": "Navigate to https://github.com",
  "raw_transcript": "Go to github.com"
}
```

`reversibility` values:
- `read` — no state change (screenshot, extract, wait)
- `reversible` — can navigate away (click, type, navigate, scroll)
- `irreversible` — permanent (delete, submit payment, post, send email)

`requires_confirmation` is always `true` when `reversibility` is `irreversible` — this is the HITL gate.

### `POST /parse/audio`

Multipart upload of a WAV/MP3/M4A/OGG file. Transcribes with Whisper-1, then parses. Returns the same `TaskIntent` schema with `raw_transcript` populated from Whisper output.

### `WebSocket /ws`

Browser automation control channel. Send JSON messages:

| `type` | Payload | Response |
|---|---|---|
| `connect-browser` | `{ url }` | `browser-status` |
| `disconnect-browser` | `{ sessionId }` | `browser-status` |
| `execute-command` | `{ sessionId, command }` | `command-result` |
| `take-screenshot` | `{ sessionId }` | `screenshot-result` (base64 PNG) |

### `GET /health`

Returns server status, active browser session count, and WebSocket connection count.

## Intent schema (`TaskIntent`)

```python
action_type: Literal["navigate", "click", "type", "scroll", "wait",
                     "screenshot", "extract", "form_submit",
                     "back", "forward", "refresh", "multi_step", "unknown"]
reversibility: Literal["read", "reversible", "irreversible"]
requires_confirmation: bool
confidence: float  # 0.0 – 1.0
target: str | None
value: str | None
steps: list[TaskStep]       # populated when action_type == "multi_step"
ambiguity_flags: list[str]  # non-empty when command is unclear
description: str
raw_transcript: str
```

## Test suite

28 utterances covering simple commands, multi-step, irreversible actions, ambiguous input, and edge cases. Asserts >= 90% accuracy against the live Claude API.

```bash
# Offline (rule-based mock, no API key needed)
pytest tests/ --mock

# Live API
ANTHROPIC_API_KEY=sk-... pytest tests/ -v

# Accuracy benchmark only
ANTHROPIC_API_KEY=sk-... pytest tests/test_parse.py::test_accuracy_benchmark -s
```

## Project structure

```
browser_agent/
├── backend/
│   ├── main.py               # FastAPI app — /parse, /parse/audio, /ws, /health
│   ├── intent_parser.py      # TaskIntent schema + Claude tool-use parser
│   ├── voice_pipeline.py     # Whisper-1 transcription
│   ├── browser_automation.py # Playwright session management
│   └── websocket_manager.py  # WebSocket connection pool
├── src/
│   ├── components/           # React components
│   ├── hooks/                # useVoiceRecognition, useSocket, useTTS
│   ├── types/                # TypeScript interfaces
│   └── App.tsx
├── tests/
│   ├── conftest.py           # --mock flag, skip logic
│   └── test_parse.py         # 28-utterance accuracy benchmark
├── .env.example
├── requirements.txt
├── pytest.ini
└── start.sh
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
