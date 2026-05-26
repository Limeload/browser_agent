import os
import pytest

from backend.intent_parser import TaskIntent


def pytest_addoption(parser):
    parser.addoption(
        "--mock",
        action="store_true",
        default=False,
        help="Replace Claude API calls with a rule-based stub (no API key needed)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests that call live APIs")


def pytest_collection_modifyitems(config, items):
    # Skip parse tests if ANTHROPIC_API_KEY is absent AND --mock was not passed.
    # Other test modules (test_hitl, test_perception, test_guard) run without a key.
    if not os.environ.get("ANTHROPIC_API_KEY") and not config.getoption("--mock"):
        skip = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set (use --mock for offline testing)")
        for item in items:
            if item.fspath.basename == "test_parse.py":
                item.add_marker(skip)


# ---------------------------------------------------------------------------
# Mock parse_transcript — injected via monkeypatching when --mock is active
# ---------------------------------------------------------------------------

_MOCK_RULES: list[tuple[list[str], dict]] = [
    (["go to", "navigate to", "open "], dict(action_type="navigate", reversibility="reversible", requires_confirmation=False, confidence=0.95, description="Navigate to URL", steps=[], ambiguity_flags=[])),
    (["go back"], dict(action_type="back", reversibility="reversible", requires_confirmation=False, confidence=0.95, description="Go back", steps=[], ambiguity_flags=[])),
    (["refresh"], dict(action_type="refresh", reversibility="reversible", requires_confirmation=False, confidence=0.9, description="Refresh page", steps=[], ambiguity_flags=[])),
    # More-specific click patterns must come before the bare "click" catch-all
    (["click it"], dict(action_type="click", reversibility="reversible", requires_confirmation=False, confidence=0.4, description="Click ambiguous target", steps=[], ambiguity_flags=["Target is unclear — 'it' has no referent"])),
    (["click the", "click on", "click submit", "click"], dict(action_type="click", reversibility="reversible", requires_confirmation=False, confidence=0.9, description="Click element", steps=[], ambiguity_flags=[])),
    (["type ", "enter my"], dict(action_type="type", reversibility="reversible", requires_confirmation=False, confidence=0.9, description="Type text", steps=[], ambiguity_flags=[])),
    (["scroll"], dict(action_type="scroll", reversibility="reversible", requires_confirmation=False, confidence=0.95, description="Scroll page", steps=[], ambiguity_flags=[])),
    (["wait "], dict(action_type="wait", reversibility="read", requires_confirmation=False, confidence=0.95, description="Wait", steps=[], ambiguity_flags=[])),
    (["screenshot", "take a screen"], dict(action_type="screenshot", reversibility="read", requires_confirmation=False, confidence=0.95, description="Screenshot", steps=[], ambiguity_flags=[])),
    (["price", "what is", "extract", "read me"], dict(action_type="extract", reversibility="read", requires_confirmation=False, confidence=0.85, description="Extract content", steps=[], ambiguity_flags=[])),
    (["delete my account", "delete my"], dict(action_type="click", reversibility="irreversible", requires_confirmation=True, confidence=0.9, description="Delete account", steps=[], ambiguity_flags=[])),
    (["submit my payment", "confirm the purchase", "post this", "send the email"], dict(action_type="form_submit", reversibility="irreversible", requires_confirmation=True, confidence=0.9, description="Irreversible action", steps=[], ambiguity_flags=[])),
    (["go there"], dict(action_type="navigate", reversibility="reversible", requires_confirmation=False, confidence=0.4, description="Navigate to unknown", steps=[], ambiguity_flags=["No URL specified"])),
    (["delete"], dict(action_type="unknown", reversibility="irreversible", requires_confirmation=True, confidence=0.4, description="Ambiguous delete", steps=[], ambiguity_flags=["No target specified"])),
    # multi-step heuristic: contains comma or "then"
]


def _mock_parse(transcript: str) -> TaskIntent:
    t = transcript.lower()

    # Multi-step heuristic
    if ("," in t and any(kw in t for kw in ["go to", "search", "click"])) or " then " in t:
        return TaskIntent(
            action_type="multi_step",
            reversibility="reversible",
            requires_confirmation=False,
            confidence=0.85,
            description="Multi-step task",
            raw_transcript=transcript,
            steps=[],
            ambiguity_flags=[],
        )

    for keywords, fields in _MOCK_RULES:
        if any(kw in t for kw in keywords):
            return TaskIntent(raw_transcript=transcript, **fields)

    return TaskIntent(
        action_type="unknown",
        reversibility="reversible",
        requires_confirmation=False,
        confidence=0.3,
        description="Unknown command",
        raw_transcript=transcript,
        steps=[],
        ambiguity_flags=["Could not determine intent"],
    )


@pytest.fixture(autouse=True)
def maybe_mock_parser(request, monkeypatch):
    if request.config.getoption("--mock"):
        import backend.intent_parser as parser_mod

        async def _async_mock(transcript: str) -> TaskIntent:
            return _mock_parse(transcript)

        # Patch the module attribute that test_parse.py calls through (_parser.parse_transcript)
        monkeypatch.setattr(parser_mod, "parse_transcript", _async_mock)
