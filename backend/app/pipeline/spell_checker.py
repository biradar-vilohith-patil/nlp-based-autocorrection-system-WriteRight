"""
app/pipeline/spell_checker.py
──────────────────────────────
Spell correction using SymSpell (edit-distance 1–2).

SymSpell is chosen for its O(1) average lookup speed via a pre-built
frequency dictionary and delete-neighbourhood indexing.
"""

from __future__ import annotations

import re
from pathlib import Path
from loguru import logger

from app.config import Settings

try:
    from symspellpy import SymSpell, Verbosity
    SYMSPELL_AVAILABLE = True
except ImportError:
    SYMSPELL_AVAILABLE = False
    logger.warning("symspellpy not installed — spell checking disabled.")


# Tokens we never attempt to correct
_SKIP_PATTERNS = re.compile(
    r"""
    ^https?://      |   # URLs
    ^www\.          |   # bare URLs
    \d              |   # contains digit
    ^[A-Z]{2,}$    |   # abbreviations / acronyms (ALL CAPS)
    ^[A-Z][a-z]+[A-Z]  # camelCase / PascalCase (proper nouns)
    """,
    re.VERBOSE,
)


class SpellChecker:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._sym: "SymSpell | None" = None

    # ── Loading ───────────────────────────────────────────────────────────────

    def load(self) -> bool:
        if not SYMSPELL_AVAILABLE:
            return False

        self._sym = SymSpell(
            max_dictionary_edit_distance=self._settings.spell_max_edit_distance,
            prefix_length=self._settings.spell_prefix_length,
        )

        dict_path = Path(self._settings.spell_dict_path)

        if dict_path.exists() and dict_path.stat().st_size > 0:
            # Load custom dictionary (word\tfrequency per line)
            ok = self._sym.load_dictionary(
                str(dict_path),
                term_index=0,
                count_index=1,
                separator="\t",
            )
            logger.info(f"SymSpell loaded custom dict: {dict_path} ({ok})")
        else:
            # Fall back to SymSpell's bundled frequency dictionary
            try:
                import pkg_resources
                freq_dict = pkg_resources.resource_filename(
                    "symspellpy", "frequency_dictionary_en_82_765.txt"
                )
                self._sym.load_dictionary(freq_dict, term_index=0, count_index=1)
                logger.info("SymSpell loaded bundled frequency dictionary.")
            except Exception as e:
                logger.error(f"Could not load any spell dictionary: {e}")
                return False

        return True

    # ── Correction ────────────────────────────────────────────────────────────

    def correct(self, text: str) -> dict[str, object]:
        """
        Tokenise text word-by-word, look up each token in SymSpell,
        replace if a closer match exists. Preserves surrounding punctuation.
        """
        if not self._sym:
            return {"corrected": text, "fixes": 0}

        # Split while capturing whitespace so we can reconstruct exactly
        tokens = re.split(r"(\s+)", text)
        fixes = 0
        out_tokens: list[str] = []

        for token in tokens:
            if re.match(r"^\s+$", token):
                out_tokens.append(token)
                continue

            corrected_token = self._correct_token(token)
            if corrected_token.lower() != token.lower():
                fixes += 1
            out_tokens.append(corrected_token)

        return {"corrected": "".join(out_tokens), "fixes": fixes}

    def _correct_token(self, token: str) -> str:
        """Strip punctuation, correct core word, reattach punctuation."""
        # Strip leading/trailing punctuation
        m = re.match(r"^([^a-zA-Z']*)([a-zA-Z']+)([^a-zA-Z']*)$", token)
        if not m:
            return token

        pre, word, post = m.group(1), m.group(2), m.group(3)

        # Skip short words, patterns we don't touch
        if (
            len(word) <= self._settings.min_word_length_for_spell
            or _SKIP_PATTERNS.match(token)
        ):
            return token

        suggestions = self._sym.lookup(
            word.lower(),
            Verbosity.CLOSEST,
            max_edit_distance=self._settings.spell_max_edit_distance,
            include_unknown=True,
        )

        if not suggestions:
            return token

        best = suggestions[0].term

        # Preserve original capitalisation
        if word.isupper():
            best = best.upper()
        elif word[0].isupper():
            best = best.capitalize()

        return pre + best + post
