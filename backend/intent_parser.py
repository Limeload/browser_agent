import os
from typing import Optional, Literal
import anthropic
from pydantic import BaseModel, Field

ActionType = Literal[
    "navigate", "click", "type", "scroll", "wait",
    "screenshot", "extract", "form_submit",
    "back", "forward", "refresh", "multi_step", "unknown",
]
Reversibility = Literal["read", "reversible", "irreversible"]


class TaskStep(BaseModel):
    action_type: ActionType
    target: Optional[str] = None
    value: Optional[str] = None
    reversibility: Reversibility
    description: str


class TaskIntent(BaseModel):
    action_type: ActionType
    target: Optional[str] = None
    value: Optional[str] = None
    reversibility: Reversibility
    requires_confirmation: bool
    confidence: float = Field(ge=0.0, le=1.0)
    steps: list[TaskStep] = []
    ambiguity_flags: list[str] = []
    raw_transcript: str
    description: str


_PARSE_TOOL = {
    "name": "parse_task_intent",
    "description": "Parse a voice command into a structured TaskIntent for browser automation",
    "input_schema": {
        "type": "object",
        "required": [
            "action_type", "reversibility",
            "requires_confirmation", "confidence", "description",
        ],
        "properties": {
            "action_type": {
                "type": "string",
                "enum": [
                    "navigate", "click", "type", "scroll", "wait",
                    "screenshot", "extract", "form_submit",
                    "back", "forward", "refresh", "multi_step", "unknown",
                ],
                "description": "Primary browser action to perform",
            },
            "target": {
                "type": "string",
                "description": "CSS selector, URL, or element description. Omit if ambiguous.",
            },
            "value": {
                "type": "string",
                "description": "Text to type, URL, or other value parameter",
            },
            "reversibility": {
                "type": "string",
                "enum": ["read", "reversible", "irreversible"],
                "description": (
                    "read=no state change (screenshot/extract/wait), "
                    "reversible=can navigate away (navigate/click/type/scroll), "
                    "irreversible=permanent (delete/payment/post/send/confirm-purchase)"
                ),
            },
            "requires_confirmation": {
                "type": "boolean",
                "description": "Must be true for all irreversible actions",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Parse confidence score",
            },
            "steps": {
                "type": "array",
                "description": "Individual steps for multi_step actions (populate when action_type=multi_step)",
                "items": {
                    "type": "object",
                    "required": ["action_type", "reversibility", "description"],
                    "properties": {
                        "action_type": {"type": "string"},
                        "target": {"type": "string"},
                        "value": {"type": "string"},
                        "reversibility": {
                            "type": "string",
                            "enum": ["read", "reversible", "irreversible"],
                        },
                        "description": {"type": "string"},
                    },
                },
            },
            "ambiguity_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ambiguities or missing information (unclear target, vague action, etc.)",
            },
            "description": {
                "type": "string",
                "description": "Human-readable summary of what will happen",
            },
        },
    },
}

_SYSTEM_PROMPT = """\
You are a browser automation intent parser. Convert voice commands into structured task intents.

Action types:
  navigate    — go to a URL
  click       — click an element or button
  type        — type text into an input field
  scroll      — scroll the page (up/down/left/right)
  wait        — pause for a duration
  screenshot  — capture screenshot (read-only)
  extract     — read/extract content from page (read-only)
  form_submit — submit a form
  back        — browser back button
  forward     — browser forward button
  refresh     — reload the page
  multi_step  — two or more sequential actions; populate `steps`
  unknown     — cannot determine intent

Reversibility rules (strictly apply these):
  read         — zero state change: screenshot, extract, wait
  reversible   — can navigate away or undo: navigate, click, type, scroll, back, forward, refresh
  irreversible — PERMANENT actions: delete anything, submit payment, post/publish content,
                 send email/message, confirm/complete a purchase, upload files, share data

IMPORTANT:
- Always set requires_confirmation=true when reversibility=irreversible.
- Add ambiguity_flags entries when: target is unclear ("it", "there"), action is vague,
  the command is a single word with no context, or multiple interpretations exist.
- For multi_step, break into individual steps in `steps[]`.
- For stuttered/filler words (um, uh, er), ignore them and parse the intent.
"""

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


async def parse_transcript(transcript: str) -> TaskIntent:
    """Parse a text transcript into a TaskIntent using Claude structured output."""
    client = _get_client()

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        tools=[_PARSE_TOOL],
        tool_choice={"type": "tool", "name": "parse_task_intent"},
        messages=[{"role": "user", "content": f'Parse this voice command: "{transcript}"'}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "parse_task_intent":
            data = block.input
            data["raw_transcript"] = transcript
            # Ensure required list fields are always present
            data.setdefault("steps", [])
            data.setdefault("ambiguity_flags", [])
            return TaskIntent(**data)

    # Tool call was forced so this path should not be reached
    return TaskIntent(
        action_type="unknown",
        reversibility="reversible",
        requires_confirmation=False,
        confidence=0.0,
        raw_transcript=transcript,
        description="Failed to parse command",
        ambiguity_flags=["Parser did not return structured output"],
    )
