"""Tests for the selective perception engine (Week 3)."""

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.perception import TFIDFScorer, count_tokens, filter_tree


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------

def test_count_tokens_empty():
    assert count_tokens("") == 1  # max(1, 0)


def test_count_tokens_four_chars():
    assert count_tokens("abcd") == 1


def test_count_tokens_approximation():
    text = "a" * 400
    assert count_tokens(text) == 100


# ---------------------------------------------------------------------------
# TFIDFScorer
# ---------------------------------------------------------------------------

class TestTFIDFScorer:
    def test_fit_builds_idf(self):
        scorer = TFIDFScorer()
        docs = ["click the button", "navigate to google", "type in the search box"]
        scorer.fit(docs)
        assert "click" in scorer._idf
        assert "the" in scorer._idf
        # "the" appears in 2 of 3 docs → lower IDF than "click" (1 of 3)
        assert scorer._idf["the"] < scorer._idf["click"]

    def test_score_returns_zero_for_empty_document(self):
        scorer = TFIDFScorer()
        scorer.fit(["click button", "search box"])
        assert scorer.score("click", "") == 0.0

    def test_score_higher_for_relevant_doc(self):
        scorer = TFIDFScorer()
        docs = [
            "click the submit button",
            "navigate to amazon homepage",
            "extract product prices from page",
        ]
        scorer.fit(docs)
        query = "click button"
        score_click = scorer.score(query, docs[0])
        score_nav = scorer.score(query, docs[1])
        score_extract = scorer.score(query, docs[2])
        assert score_click > score_nav
        assert score_click > score_extract

    def test_tokenize_lowercases(self):
        tokens = TFIDFScorer._tokenize("Click THE Button")
        assert tokens == ["click", "the", "button"]

    def test_tokenize_strips_punctuation(self):
        tokens = TFIDFScorer._tokenize("hello, world!")
        assert tokens == ["hello", "world"]

    def test_idf_formula(self):
        scorer = TFIDFScorer()
        scorer.fit(["a b", "b c", "c d"])
        # "b" appears in 2 of 3 → IDF = log(4/3) + 1
        expected = math.log(4 / 3) + 1.0
        assert abs(scorer._idf["b"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# filter_tree (integration-style, mocking Playwright)
# ---------------------------------------------------------------------------

def _make_page_mock(node_texts: list[str]):
    """Return a mock Playwright Page whose accessibility snapshot yields node_texts."""
    snapshot = {
        "role": "RootWebArea",
        "name": "page",
        "children": [
            {"role": "button", "name": text, "children": []}
            for text in node_texts
        ],
    }
    page = MagicMock()
    page.accessibility = MagicMock()
    page.accessibility.snapshot = AsyncMock(return_value=snapshot)
    return page


async def test_filter_tree_returns_all_when_within_budget():
    texts = ["Click me", "Search box", "Submit form"]
    page = _make_page_mock(texts)
    nodes, before, after = await filter_tree(page, "click button", token_budget=10_000)
    # _flatten includes the root node too, so >= 3 children + root
    assert len(nodes) >= 3
    node_texts = {n["text"] for n in nodes}
    assert {"Click me", "Search box", "Submit form"}.issubset(node_texts)
    assert before == after  # no filtering needed


async def test_filter_tree_reduces_tokens_when_over_budget():
    # Create 200 nodes of 40 chars each = 200 * 10 tokens = 2000 total
    # Budget = 50 → must filter heavily
    texts = [f"Node number {i:04d} with some filler text here" for i in range(200)]
    page = _make_page_mock(texts)
    nodes, before, after = await filter_tree(page, "Node 0001", token_budget=50)
    assert after <= 50
    assert before > 50


async def test_filter_tree_token_reduction_target():
    """Verify >=70% token reduction when page has 300 nodes."""
    texts = [f"Random page element content block number {i}" for i in range(300)]
    page = _make_page_mock(texts)
    _, before, after = await filter_tree(page, "login form username", token_budget=500)
    if before > 500:
        reduction = (before - after) / before
        assert reduction >= 0.70, f"Expected >=70% reduction, got {reduction:.1%}"


async def test_filter_tree_empty_page():
    page = MagicMock()
    page.accessibility = MagicMock()
    page.accessibility.snapshot = AsyncMock(return_value=None)
    nodes, before, after = await filter_tree(page, "anything")
    assert nodes == []
    assert before == 0
    assert after == 0


async def test_filter_tree_prefers_relevant_nodes():
    texts = [
        "Username input field",
        "Password input field",
        "Random unrelated footer text",
        "Copyright notice at the bottom",
        "Login submit button",
    ]
    page = _make_page_mock(texts)
    nodes, _, _ = await filter_tree(page, "login username password", token_budget=20)
    node_texts = [n["text"] for n in nodes]
    assert any("Username" in t or "Password" in t or "Login" in t for t in node_texts)
