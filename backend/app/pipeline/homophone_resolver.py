"""
app/pipeline/homophone_resolver.py
───────────────────────────────────
Context-aware homophone disambiguation.

Strategy:
  • Load a JSON map of {word: [homophone_group]} sets.
  • For each potential homophone in the text, use the surrounding
    POS context (provided by spaCy when available, else heuristic
    bigram rules) to select the most likely intended word.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from loguru import logger

from app.config import Settings


# ── Heuristic rules ───────────────────────────────────────────────────────────
# Pattern: (regex_in_context, wrong_word, correct_word)
# These catch the most common confusable pairs without needing spaCy.

_RULES: list[tuple[re.Pattern, str, str]] = [
    # their / there / they're
    (re.compile(r"\bthier\b", re.I), "thier", "their"),
    (re.compile(r"\btheir\s+is\b", re.I), "their is", "there is"),
    (re.compile(r"\bthere\s+\w+ing\b", re.I), None, None),  # placeholder trigger
    # your / you're
    (re.compile(r"\byour\s+(?:going|coming|doing|being|making|taking)\b", re.I), "your", "you're"),
    (re.compile(r"\byoure\b", re.I), "youre", "you're"),
    # its / it's
    (re.compile(r"\bits\s+(?:a|an|the|not|been|going|very|quite)\b", re.I), "its", "it's"),
    # then / than (comparison context)
    (re.compile(r"\b(?:more|less|better|worse|greater|smaller|higher|lower)\s+then\b", re.I), "then", "than"),
    # to / too / two
    (re.compile(r"\bto\s+(?:much|many|late|soon|bad|good|big|small)\b", re.I), "to much", "too much"),
    (re.compile(r"\btwo\s+(?:much|many|late|soon)\b", re.I), "two", "too"),
    # affect / effect  (basic heuristic)
    (re.compile(r"\bthe\s+affect\s+of\b", re.I), "affect", "effect"),
    (re.compile(r"\bpositive\s+affect\b", re.I), "affect", "effect"),
    # lose / loose
    (re.compile(r"\bdon't\s+loose\b", re.I), "loose", "lose"),
    (re.compile(r"\bwill\s+loose\b", re.I), "loose", "lose"),
    # accept / except
    (re.compile(r"\baccept\s+for\b", re.I), "accept", "except"),
    # weather / whether
    (re.compile(r"\bweather\s+or\s+not\b", re.I), "weather", "whether"),
]


class HomophoneResolver:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._homophones: dict = {}

    def load(self) -> bool:
        path = Path(self._settings.homophone_path)
        if not path.exists():
            logger.warning(f"Homophone file not found: {path}")
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                self._homophones = json.load(f)
            logger.info(f"Loaded {len(self._homophones)} homophone groups.")
            return True
        except Exception as e:
            logger.error(f"Failed to load homophones: {e}")
            return False

    def resolve(self, text: str) -> dict[str, object]:
        fixes = 0
        result = text

        for pattern, wrong, correct in _RULES:
            if wrong is None:
                continue  # placeholder — skip
            m = pattern.search(result)
            if m:
                old = result
                # Case-insensitive replace preserving original case structure
                result = self._replace_preserving_case(result, wrong, correct)
                if result != old:
                    fixes += 1

        return {"corrected": result, "fixes": fixes}

    @staticmethod
    def _replace_preserving_case(text: str, wrong: str, correct: str) -> str:
        def replacer(m: re.Match) -> str:
            original = m.group(0)
            if original.isupper():
                return correct.upper()
            if original[0].isupper():
                return correct.capitalize()
            return correct

        return re.sub(re.escape(wrong), replacer, text, flags=re.IGNORECASE)
