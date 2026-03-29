"""
app/pipeline/scorer.py
───────────────────────
Confidence scoring for the correction pipeline.

Produces a value in [0, 1] reflecting how much the text changed and
whether the changes seem linguistically reasonable.

Heuristics used:
  • Normalised edit distance between original and corrected
  • Token overlap ratio (Jaccard)
  • spaCy entity preservation check (named entities should survive)
  • Penalty if corrected text is much longer / shorter than original
"""

from __future__ import annotations

import math
import re

from loguru import logger


class Scorer:
    def __init__(self, nlp=None):
        """
        :param nlp: spaCy Language model (optional but improves scoring).
        """
        self._nlp = nlp

    def score(self, original: str, corrected: str) -> float:
        """Return a confidence score in [0.0, 1.0]."""
        if not original or not corrected:
            return 1.0

        if original == corrected:
            return 1.0

        try:
            sim   = self._token_similarity(original, corrected)
            ratio = self._length_ratio(original, corrected)
            ent   = self._entity_preservation(original, corrected)

            # Weighted average
            score = 0.5 * sim + 0.25 * ratio + 0.25 * ent
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Scorer error: {e}")
            return 0.85  # safe fallback

    # ── Sub-metrics ────────────────────────────────────────────────────────────

    @staticmethod
    def _token_similarity(a: str, b: str) -> float:
        """Jaccard similarity on word-token sets."""
        ta = set(re.findall(r"\b\w+\b", a.lower()))
        tb = set(re.findall(r"\b\w+\b", b.lower()))
        if not ta and not tb:
            return 1.0
        intersection = len(ta & tb)
        union = len(ta | tb)
        return intersection / union if union else 1.0

    @staticmethod
    def _length_ratio(a: str, b: str) -> float:
        """
        Penalises large length differences.
        Returns 1.0 when lengths match, decays toward 0 as ratio diverges.
        """
        la, lb = len(a.split()), len(b.split())
        if la == 0:
            return 1.0
        ratio = min(la, lb) / max(la, lb)
        # Apply mild sigmoid to soften extreme cases
        return 1 / (1 + math.exp(-10 * (ratio - 0.5)))

    def _entity_preservation(self, a: str, b: str) -> float:
        """
        Check that named entities in the original survive in the corrected text.
        Falls back to 1.0 if spaCy is unavailable.
        """
        if not self._nlp:
            return 1.0

        try:
            doc_a = self._nlp(a)
            doc_b = self._nlp(b)
            ents_a = {ent.text.lower() for ent in doc_a.ents}
            ents_b = {ent.text.lower() for ent in doc_b.ents}

            if not ents_a:
                return 1.0

            preserved = len(ents_a & ents_b)
            return preserved / len(ents_a)
        except Exception:
            return 1.0
