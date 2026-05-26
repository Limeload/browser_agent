"""
GuardLayer injection firewall — Week 4.

Stage 1 — regex (fast, deterministic): catches the 6 known 2025 attack patterns.
Stage 2 — semantic (HuggingFace zero-shot, lazy-loaded): catches novel variants
          that slip past regex.  Falls back silently if transformers is not installed.

All detections are logged to PostgreSQL via backend.database (best-effort).
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AttackType(str, Enum):
    HASH_JACK = "hash_jack"
    SPOILER_TAG = "spoiler_tag"
    URL_FRAGMENT = "url_fragment"
    ROLE_ESCALATION = "role_escalation"
    INDIRECT_INJECTION = "indirect_injection"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"


@dataclass
class Detection:
    attack_type: AttackType
    confidence: float
    matched_text: str
    source: str  # "regex" | "semantic"


# ---------------------------------------------------------------------------
# Regex pattern library — one or more patterns per attack type
# First match per type wins
# ---------------------------------------------------------------------------

REGEX_PATTERNS: dict[AttackType, list[re.Pattern]] = {
    AttackType.HASH_JACK: [
        re.compile(
            r"#.*?(?:ignore|forget|disregard|override).{0,60}(?:instruction|command|rule|system)",
            re.I | re.S,
        ),
        re.compile(r'href=["\']#[^"\']*(?:inject|exec|eval|script|ignore)', re.I),
    ],
    AttackType.SPOILER_TAG: [
        re.compile(
            r"<details[^>]*>.*?<summary[^>]*>.*?</summary>.*?"
            r"(?:ignore|system\s+prompt|you\s+are\s+now|new\s+instruction)",
            re.I | re.S,
        ),
        re.compile(
            r"<!--.*?(?:ignore\s+previous|new\s+instruction|you\s+are\s+now|system\s+prompt).*?-->",
            re.I | re.S,
        ),
    ],
    AttackType.URL_FRAGMENT: [
        re.compile(
            r"[?#&].*?(?:ignore|forget|override|system.prompt|instruction|new.role|jailbreak)\s*=",
            re.I,
        ),
        re.compile(
            r"(?:url|href|src|navigate)\s*=.*?[#?&].*?(?:ignore|system|inject|instruction)",
            re.I,
        ),
    ],
    AttackType.ROLE_ESCALATION: [
        re.compile(
            r"(?:ignore|forget|disregard|override)\s+(?:all\s+)?(?:previous|prior|your|the)?\s*"
            r"(?:instructions?|rules?|constraints?|guidelines?|prompts?)",
            re.I,
        ),
        re.compile(
            r"you\s+are\s+(?:now\s+)?(?:a\s+)?(?:new|different|unrestricted|jailbroken|DAN|free)",
            re.I,
        ),
        re.compile(
            r"(?:act|behave|pretend)\s+as\s+(?:if\s+)?(?:you\s+(?:have\s+no|are\s+not)|an?\s+AI\s+without)",
            re.I,
        ),
        re.compile(
            r"(?:new\s+)?system\s+prompt\s*[:=]\s*(?:you\s+are|ignore|forget)",
            re.I,
        ),
    ],
    AttackType.INDIRECT_INJECTION: [
        re.compile(
            r"(?:font.size\s*:\s*0|color\s*:\s*white|visibility\s*:\s*hidden|display\s*:\s*none)",
            re.I,
        ),
        re.compile(
            r"(?:aria-hidden\s*=\s*[\"']true|opacity\s*:\s*0)"
            r"[^>]{0,200}(?:instruction|ignore|system)",
            re.I | re.S,
        ),
        re.compile(
            r"(?:dear\s+(?:AI|assistant|claude|gpt|llm)|to\s+the\s+(?:AI|agent|assistant|LLM))"
            r"[\s:,]+(?:please\s+)?(?:ignore|disregard|forget|override)",
            re.I,
        ),
    ],
    AttackType.SYSTEM_PROMPT_LEAK: [
        re.compile(
            r"(?:print|output|reveal|show|tell\s+me|what\s+(?:is|are))\s+"
            r"(?:your|the)?\s*(?:system\s+prompt|initial\s+instructions?|base\s+prompt|original\s+prompt)",
            re.I,
        ),
        re.compile(
            r"(?:repeat|copy|paste|quote|reproduce)\s+"
            r"(?:your|the)?\s*(?:system|initial|original|full)\s+"
            r"(?:prompt|instructions?|message|context)",
            re.I,
        ),
        re.compile(r"(?:leak|exfiltrate|extract)\s+(?:your\s+)?(?:system\s+)?prompt", re.I),
    ],
}

# ---------------------------------------------------------------------------
# Semantic classifier (lazy, optional)
# ---------------------------------------------------------------------------

_clf = None  # None = not yet attempted; False = attempted but unavailable

_SEMANTIC_LABELS = [
    "prompt injection attack",
    "role escalation attempt",
    "system prompt extraction",
    "benign web content",
]


def _get_clf():
    global _clf
    if _clf is None:
        try:
            from transformers import pipeline  # type: ignore

            _clf = pipeline(
                "zero-shot-classification",
                model="typeform/distilbart-mnli-12-3",
                device=-1,
            )
            logger.info("Semantic classifier loaded")
        except Exception as exc:
            logger.info("Semantic classifier unavailable (%s) — regex-only mode", exc)
            _clf = False
    return _clf if _clf is not False else None


def _semantic_detect(text: str, threshold: float = 0.75) -> Optional[Detection]:
    clf = _get_clf()
    if clf is None:
        return None
    try:
        result = clf(text[:512], _SEMANTIC_LABELS, multi_label=False)
        label: str = result["labels"][0]
        score: float = result["scores"][0]
        if label != "benign web content" and score >= threshold:
            return Detection(
                attack_type=AttackType.ROLE_ESCALATION,
                confidence=score,
                matched_text=text[:120],
                source="semantic",
            )
    except Exception as exc:
        logger.debug("Semantic classifier error: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan(text: str) -> list[Detection]:
    """
    Scan *text* for injection attacks.
    Returns a list of Detection objects (empty list = clean).
    """
    detections: list[Detection] = []
    for attack_type, patterns in REGEX_PATTERNS.items():
        for pattern in patterns:
            m = pattern.search(text)
            if m:
                detections.append(
                    Detection(
                        attack_type=attack_type,
                        confidence=1.0,
                        matched_text=m.group(0)[:200],
                        source="regex",
                    )
                )
                break  # one detection per attack type

    if not detections:
        sem = _semantic_detect(text)
        if sem:
            detections.append(sem)

    return detections


def is_clean(text: str) -> bool:
    return len(scan(text)) == 0


async def scan_and_log(text: str, page_url: str = "") -> list[Detection]:
    """Scan and persist any detections to the database (best-effort)."""
    detections = scan(text)
    if detections:
        try:
            from backend.database import log_detection

            for d in detections:
                await log_detection(
                    attack_type=d.attack_type.value,
                    confidence=d.confidence,
                    source=d.source,
                    matched_text=d.matched_text,
                    page_url=page_url,
                    raw_text=text[:500],
                )
        except Exception as exc:
            logger.debug("Detection logging failed: %s", exc)
    return detections
