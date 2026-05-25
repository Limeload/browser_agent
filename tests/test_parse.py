"""
Voice pipeline intent-parsing test suite.

Tests call parse_transcript() directly (real Claude API) and validate the
returned TaskIntent against expected action_type, reversibility, and
requires_confirmation.  The final accuracy benchmark asserts ≥ 90 %.

Run:
    ANTHROPIC_API_KEY=sk-... pytest tests/test_parse.py -v
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

import pytest

import backend.intent_parser as _parser
from backend.intent_parser import TaskIntent

# Use module-level reference so conftest mock patching takes effect
parse_transcript = _parser.parse_transcript

# ---------------------------------------------------------------------------
# Test-case schema
# ---------------------------------------------------------------------------


@dataclass
class Case:
    id: str
    utterance: str
    valid_action_types: list[str]          # any of these is a correct parse
    expected_reversibility: str            # exact match required
    expected_requires_confirmation: bool
    expect_ambiguity: bool = False         # True → ambiguity_flags must be non-empty
    notes: str = ""


# ---------------------------------------------------------------------------
# 28 test utterances covering every category
# ---------------------------------------------------------------------------

TEST_CASES: list[Case] = [
    # ── Simple navigation ──────────────────────────────────────────────────
    Case(
        id="navigate_go_to",
        utterance="Go to google.com",
        valid_action_types=["navigate"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="navigate_keyword",
        utterance="Navigate to amazon.com",
        valid_action_types=["navigate"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="navigate_back",
        utterance="Go back",
        valid_action_types=["back", "navigate"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="navigate_refresh",
        utterance="Refresh the page",
        valid_action_types=["refresh", "navigate"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    # ── Click / submit ─────────────────────────────────────────────────────
    Case(
        id="click_button",
        utterance="Click the search button",
        valid_action_types=["click"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="click_submit",
        utterance="Click the submit button",
        valid_action_types=["click", "form_submit"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
        notes="submitting a neutral form is still reversible (can navigate away)",
    ),
    Case(
        id="click_link",
        utterance="Click on the first link in the results",
        valid_action_types=["click"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    # ── Type ───────────────────────────────────────────────────────────────
    Case(
        id="type_simple",
        utterance="Type hello world in the search box",
        valid_action_types=["type"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="type_email",
        utterance="Enter my email address john@example.com in the email field",
        valid_action_types=["type"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    # ── Scroll ─────────────────────────────────────────────────────────────
    Case(
        id="scroll_down",
        utterance="Scroll down",
        valid_action_types=["scroll"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="scroll_top",
        utterance="Scroll to the top of the page",
        valid_action_types=["scroll"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    # ── Read-only ──────────────────────────────────────────────────────────
    Case(
        id="wait_seconds",
        utterance="Wait 3 seconds",
        valid_action_types=["wait"],
        expected_reversibility="read",
        expected_requires_confirmation=False,
    ),
    Case(
        id="screenshot",
        utterance="Take a screenshot",
        valid_action_types=["screenshot"],
        expected_reversibility="read",
        expected_requires_confirmation=False,
    ),
    Case(
        id="extract_price",
        utterance="What is the price of this item?",
        valid_action_types=["extract"],
        expected_reversibility="read",
        expected_requires_confirmation=False,
    ),
    Case(
        id="extract_title",
        utterance="Read me the article title",
        valid_action_types=["extract"],
        expected_reversibility="read",
        expected_requires_confirmation=False,
    ),
    Case(
        id="extract_products",
        utterance="Extract all product names from this page",
        valid_action_types=["extract"],
        expected_reversibility="read",
        expected_requires_confirmation=False,
    ),
    # ── Multi-step ─────────────────────────────────────────────────────────
    Case(
        id="multi_shop",
        utterance="Go to amazon.com, search for headphones, and click the first result",
        valid_action_types=["multi_step"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    Case(
        id="multi_sequential",
        utterance="First go to google.com then search for cats",
        valid_action_types=["multi_step"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
    ),
    # ── Irreversible — HITL required ───────────────────────────────────────
    Case(
        id="irreversible_delete_account",
        utterance="Delete my account",
        valid_action_types=["click", "form_submit", "navigate", "unknown"],
        expected_reversibility="irreversible",
        expected_requires_confirmation=True,
    ),
    Case(
        id="irreversible_payment",
        utterance="Submit my payment of fifty dollars",
        valid_action_types=["form_submit", "click"],
        expected_reversibility="irreversible",
        expected_requires_confirmation=True,
    ),
    Case(
        id="irreversible_tweet",
        utterance="Post this tweet",
        valid_action_types=["click", "form_submit"],
        expected_reversibility="irreversible",
        expected_requires_confirmation=True,
    ),
    Case(
        id="irreversible_send_email",
        utterance="Send the email",
        valid_action_types=["click", "form_submit"],
        expected_reversibility="irreversible",
        expected_requires_confirmation=True,
    ),
    Case(
        id="irreversible_confirm_purchase",
        utterance="Confirm the purchase",
        valid_action_types=["click", "form_submit"],
        expected_reversibility="irreversible",
        expected_requires_confirmation=True,
    ),
    # ── Ambiguous ──────────────────────────────────────────────────────────
    Case(
        id="ambiguous_click_it",
        utterance="Click it",
        valid_action_types=["click", "unknown"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
        expect_ambiguity=True,
        notes="Target is a pronoun with no referent",
    ),
    Case(
        id="ambiguous_go_there",
        utterance="Go there",
        valid_action_types=["navigate", "unknown"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
        expect_ambiguity=True,
        notes="No URL or location specified",
    ),
    Case(
        id="ambiguous_delete_bare",
        utterance="Delete",
        valid_action_types=["click", "form_submit", "unknown"],
        expected_reversibility="irreversible",
        expected_requires_confirmation=True,
        expect_ambiguity=True,
        notes="Single-word destructive command with no target",
    ),
    # ── Edge cases ─────────────────────────────────────────────────────────
    Case(
        id="edge_stutter",
        utterance="um... click the... uh... search button",
        valid_action_types=["click"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
        notes="Whisper output with filler words should still parse correctly",
    ),
    Case(
        id="edge_caps",
        utterance="CLICK THE BIG RED BUTTON NOW",
        valid_action_types=["click"],
        expected_reversibility="reversible",
        expected_requires_confirmation=False,
        notes="All-caps emphasis must not confuse the parser",
    ),
]

# Sanity check at import time
assert len(TEST_CASES) >= 20, f"Expected ≥20 test cases, got {len(TEST_CASES)}"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def evaluate(case: Case, intent: TaskIntent) -> tuple[bool, str]:
    """Return (passed, reason).  All three fields must match."""
    if intent.action_type not in case.valid_action_types:
        return False, (
            f"action_type={intent.action_type!r} not in {case.valid_action_types}"
        )
    if intent.reversibility != case.expected_reversibility:
        return False, (
            f"reversibility={intent.reversibility!r} "
            f"!= {case.expected_reversibility!r}"
        )
    if intent.requires_confirmation != case.expected_requires_confirmation:
        return False, (
            f"requires_confirmation={intent.requires_confirmation} "
            f"!= {case.expected_requires_confirmation}"
        )
    if case.expect_ambiguity and not intent.ambiguity_flags:
        return False, "expected non-empty ambiguity_flags but got []"
    return True, "ok"


# ---------------------------------------------------------------------------
# Parametrised unit tests (one API call per case; good for -k filtering)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("case", TEST_CASES, ids=[c.id for c in TEST_CASES])
async def test_parse_utterance(case: Case):
    intent = await _parser.parse_transcript(case.utterance)

    # Basic schema validation
    assert intent.raw_transcript == case.utterance
    assert 0.0 <= intent.confidence <= 1.0
    assert intent.action_type in (
        "navigate", "click", "type", "scroll", "wait",
        "screenshot", "extract", "form_submit",
        "back", "forward", "refresh", "multi_step", "unknown",
    ), f"Unexpected action_type: {intent.action_type}"

    passed, reason = evaluate(case, intent)
    assert passed, (
        f"\nUtterance : {case.utterance!r}\n"
        f"Failure   : {reason}\n"
        f"Intent    : action={intent.action_type!r}, "
        f"rev={intent.reversibility!r}, "
        f"confirm={intent.requires_confirmation}, "
        f"flags={intent.ambiguity_flags}\n"
        f"Notes     : {case.notes}"
    )


# ---------------------------------------------------------------------------
# Accuracy benchmark — runs all cases, asserts ≥ 90 %
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_accuracy_benchmark():
    """
    Run all 28 utterances concurrently and assert overall accuracy ≥ 90 %.
    This is the primary deliverable metric for Week 1.
    """

    async def _run(case: Case) -> tuple[Case, TaskIntent | None, str]:
        try:
            intent = await _parser.parse_transcript(case.utterance)
            return case, intent, ""
        except Exception as exc:  # noqa: BLE001
            return case, None, str(exc)

    results = await asyncio.gather(*[_run(c) for c in TEST_CASES])

    passed_count = 0
    failures: list[str] = []

    for case, intent, err in results:
        if intent is None:
            failures.append(f"  ✗  [{case.id}] ERROR: {err}")
            continue
        ok, reason = evaluate(case, intent)
        if ok:
            passed_count += 1
            print(f"  ✓  [{case.id}] {case.utterance[:60]}")
        else:
            failures.append(
                f"  ✗  [{case.id}] {case.utterance[:60]}\n"
                f"         {reason}"
            )

    total = len(TEST_CASES)
    accuracy = passed_count / total

    print(f"\n{'='*60}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f)
    print(f"\nAccuracy: {passed_count}/{total} = {accuracy:.1%}")
    print(f"{'='*60}\n")

    assert accuracy >= 0.90, (
        f"Accuracy {accuracy:.1%} is below the 90% threshold "
        f"({passed_count}/{total} passed)"
    )
