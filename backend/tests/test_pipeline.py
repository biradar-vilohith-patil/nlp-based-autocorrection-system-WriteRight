"""
tests/test_pipeline.py
───────────────────────
Unit + integration tests for the WriteRight NLP pipeline.
Run with: pytest tests/ -v
"""

import pytest
import sys
import os

# Make sure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.text_utils import (
    normalise_whitespace,
    split_into_sentences,
    build_word_diffs,
    count_word_diffs,
)
from app.pipeline.homophone_resolver import HomophoneResolver
from app.config import Settings


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def homophone_resolver(settings):
    resolver = HomophoneResolver(settings)
    resolver.load()
    return resolver


# ── text_utils tests ──────────────────────────────────────────────────────────

class TestNormaliseWhitespace:
    def test_collapses_spaces(self):
        assert normalise_whitespace("hello   world") == "hello world"

    def test_strips_leading_trailing(self):
        assert normalise_whitespace("  hello  ") == "hello"

    def test_collapses_tabs(self):
        assert normalise_whitespace("hello\t\tworld") == "hello world"

    def test_preserves_single_newlines(self):
        result = normalise_whitespace("line one\nline two")
        assert "line one" in result and "line two" in result

    def test_collapses_triple_newlines(self):
        result = normalise_whitespace("a\n\n\n\nb")
        assert "\n\n\n" not in result

    def test_empty_string(self):
        assert normalise_whitespace("") == ""

    def test_only_whitespace(self):
        assert normalise_whitespace("   \t  ") == ""


class TestSplitIntoSentences:
    def test_single_sentence(self):
        sentences = split_into_sentences("Hello world.")
        assert len(sentences) == 1

    def test_two_sentences(self):
        sentences = split_into_sentences("Hello world. My name is Alice.")
        assert len(sentences) == 2

    def test_question_marks(self):
        sentences = split_into_sentences("How are you? I am fine.")
        assert len(sentences) == 2

    def test_exclamation(self):
        sentences = split_into_sentences("Watch out! There is a bug.")
        assert len(sentences) == 2

    def test_no_punctuation(self):
        sentences = split_into_sentences("a simple sentence without end")
        assert len(sentences) >= 1

    def test_empty_string(self):
        sentences = split_into_sentences("")
        assert sentences == []


class TestBuildWordDiffs:
    def test_no_changes(self):
        diffs = build_word_diffs("hello world", "hello world", "spell")
        assert len(diffs) == 0

    def test_single_substitution(self):
        diffs = build_word_diffs("helo world", "hello world", "spell")
        # Should detect the change
        assert len(diffs) >= 1

    def test_diff_type_preserved(self):
        diffs = build_word_diffs("I goes home", "I go home", "grammar")
        for d in diffs:
            assert d["type"] == "grammar"

    def test_insertion(self):
        diffs = build_word_diffs("I very happy", "I am very happy", "grammar")
        assert len(diffs) >= 1


class TestCountWordDiffs:
    def test_identical(self):
        assert count_word_diffs("hello world", "hello world") == 0

    def test_one_change(self):
        assert count_word_diffs("helo world", "hello world") == 1

    def test_length_difference(self):
        result = count_word_diffs("one two three", "one two three four")
        assert result >= 1

    def test_empty(self):
        assert count_word_diffs("", "") == 0


# ── Homophone resolver tests ─────────────────────────────────────────────────

class TestHomophoneResolver:
    def test_your_going(self, homophone_resolver):
        result = homophone_resolver.resolve("your going to love this")
        assert "you're" in result["corrected"]
        assert result["fixes"] >= 1

    def test_their_is(self, homophone_resolver):
        result = homophone_resolver.resolve("their is a problem")
        assert "there" in result["corrected"].lower()

    def test_more_then(self, homophone_resolver):
        result = homophone_resolver.resolve("This is more then enough")
        assert "than" in result["corrected"]

    def test_no_false_positive(self, homophone_resolver):
        clean = "There is a cat in their house."
        result = homophone_resolver.resolve(clean)
        # Should not mangle correctly used their/there
        assert result["corrected"] == clean or result["fixes"] == 0

    def test_will_loose(self, homophone_resolver):
        result = homophone_resolver.resolve("Don't loose your keys")
        assert "lose" in result["corrected"]


# ── Config tests ──────────────────────────────────────────────────────────────

class TestSettings:
    def test_defaults_exist(self, settings):
        assert settings.app_name
        assert settings.app_version
        assert settings.max_input_length > 0

    def test_model_name_set(self, settings):
        assert "t5" in settings.model_name.lower()

    def test_spell_edit_distance(self, settings):
        assert 1 <= settings.spell_max_edit_distance <= 3


# ── API integration tests (requires running server) ──────────────────────────

@pytest.mark.asyncio
class TestAPIIntegration:
    """
    These tests hit the actual API. Skip them if the server isn't running.
    Run with: pytest tests/ -v -m integration
    """

    @pytest.mark.integration
    async def test_health_endpoint(self):
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

    @pytest.mark.integration
    async def test_correct_endpoint(self):
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            resp = await client.post(
                "/api/correct",
                json={"text": "She dont know wher she goed yesterday."},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "corrected" in data
            assert data["corrected"] != data["original"]

    @pytest.mark.integration
    async def test_refine_endpoint(self):
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            resp = await client.post(
                "/api/refine",
                json={"text": "The meeting was attended by the team.", "style": "professional"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "refined" in data
            assert "improvements" in data

    @pytest.mark.integration
    async def test_empty_text_rejected(self):
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            resp = await client.post("/api/correct", json={"text": "  "})
            assert resp.status_code == 422

    @pytest.mark.integration
    async def test_stats_endpoint(self):
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            resp = await client.get("/api/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert "total_requests" in data
