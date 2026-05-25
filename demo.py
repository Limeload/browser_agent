#!/usr/bin/env python3
"""
Quick demo: shows intent parsing results for a set of example commands
without requiring a running server or API keys.
"""

import json
import asyncio
import os

DEMO_COMMANDS = [
    "Go to google.com",
    "Click the search button",
    "Type hello world in the search box",
    "Take a screenshot",
    "Wait 5 seconds",
    "Scroll down",
    "Delete my account",
    "Post this tweet",
]


def local_parse(text: str) -> dict:
    """Minimal rule-based parser for offline demo."""
    t = text.lower()
    if "go to" in t or "navigate" in t:
        return {"action_type": "navigate", "reversibility": "reversible", "requires_confirmation": False}
    if "click" in t:
        return {"action_type": "click", "reversibility": "reversible", "requires_confirmation": False}
    if "type" in t:
        return {"action_type": "type", "reversibility": "reversible", "requires_confirmation": False}
    if "screenshot" in t or "capture" in t:
        return {"action_type": "screenshot", "reversibility": "read", "requires_confirmation": False}
    if "wait" in t or "pause" in t:
        return {"action_type": "wait", "reversibility": "read", "requires_confirmation": False}
    if "scroll" in t:
        return {"action_type": "scroll", "reversibility": "reversible", "requires_confirmation": False}
    if "delete" in t or "post" in t or "send" in t or "submit" in t:
        return {"action_type": "click", "reversibility": "irreversible", "requires_confirmation": True}
    return {"action_type": "unknown", "reversibility": "reversible", "requires_confirmation": False}


async def claude_parse(text: str) -> dict | None:
    """Live parse via Claude API (requires ANTHROPIC_API_KEY)."""
    try:
        from backend.intent_parser import parse_transcript
        intent = await parse_transcript(text)
        return intent.model_dump()
    except Exception as exc:
        print(f"  [Claude API unavailable: {exc}]")
        return None


def demo_intent_parsing():
    print("\nIntent Parsing Demo")
    print("===================")
    use_api = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"Mode: {'Claude API' if use_api else 'local rule-based (set ANTHROPIC_API_KEY for Claude)'}\n")

    for cmd in DEMO_COMMANDS:
        print(f"Command: {cmd!r}")
        if use_api:
            result = asyncio.run(claude_parse(cmd)) or local_parse(cmd)
        else:
            result = local_parse(cmd)
        print(f"  action_type          : {result.get('action_type')}")
        print(f"  reversibility        : {result.get('reversibility')}")
        print(f"  requires_confirmation: {result.get('requires_confirmation')}")
        if result.get("description"):
            print(f"  description          : {result.get('description')}")
        print()


def main():
    print("Voice Browser Agent — Demo")
    print("==========================")
    demo_intent_parsing()

    print("To start the full application:")
    print("  ./start.sh")
    print("")
    print("To run the intent parser test suite:")
    print("  ANTHROPIC_API_KEY=sk-... pytest tests/test_parse.py -v")
    print("")
    print("API endpoints (server running):")
    print("  POST http://localhost:8000/parse        — text intent parse")
    print("  POST http://localhost:8000/parse/audio  — Whisper + intent parse")
    print("  GET  http://localhost:8000/health       — health check")
    print("  WS   ws://localhost:8000/ws             — browser automation channel")


if __name__ == "__main__":
    main()
