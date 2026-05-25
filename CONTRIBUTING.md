# Contributing

Thanks for your interest in contributing to Voice Browser Agent.

## Getting started

1. Fork the repository and clone your fork.
2. Create a virtual environment and install Python dependencies:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Install Node.js dependencies:
   ```bash
   npm install
   ```
4. Copy `.env.example` to `.env` and add your API keys.

## Running tests

```bash
# Offline (no API key required)
pytest tests/ --mock

# Against the real Claude API
ANTHROPIC_API_KEY=sk-... pytest tests/ -v
```

## Workflow

- Branch off `main`: `git checkout -b feature/your-feature`
- Write or update tests for any new behaviour.
- Run `npm run type-check` and `pytest tests/ --mock` before opening a PR.
- Keep commits focused; one logical change per commit.
- Open a pull request against `main` with a clear description of what and why.

## Code style

- Python: follow PEP 8; 4-space indent; no trailing whitespace.
- TypeScript: follow the existing ESLint config (`npm run lint`).
- No emojis in source code, shell scripts, or documentation.
- Comments only where the _why_ is non-obvious.

## Reporting issues

Open an issue on GitHub with:
- A minimal reproduction (command or test case).
- Expected vs. actual behaviour.
- Python/Node versions and OS.
