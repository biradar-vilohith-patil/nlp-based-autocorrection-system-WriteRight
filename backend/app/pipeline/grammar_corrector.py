"""
app/pipeline/grammar_corrector.py
───────────────────────────────────
Grammar correction using the vennify/t5-base-grammar-correction model.

The model expects input prefixed with "grammar: " and returns a
grammatically corrected sequence.  We process sentence-by-sentence to
stay within the model's max token length and improve throughput.
"""

from __future__ import annotations

import re
from loguru import logger

from app.config import Settings
from app.utils.text_utils import count_word_diffs


# ── Style prompts for the refinement stage ────────────────────────────────────
_STYLE_PROMPTS: dict[str, str] = {
    "professional": (
        "Rewrite the following text in a clear, professional tone while "
        "preserving its exact meaning. Do not add new information:\n\n"
    ),
    "casual": (
        "Rewrite the following text in a friendly, conversational tone "
        "while keeping the same meaning:\n\n"
    ),
    "academic": (
        "Rewrite the following text in a formal academic style, using precise "
        "vocabulary and preserving all factual content:\n\n"
    ),
    "concise": (
        "Rewrite the following text as concisely as possible while retaining "
        "all key information and meaning:\n\n"
    ),
}


class GrammarCorrector:
    def __init__(self, settings: Settings, tokenizer, model):
        self._settings = settings
        self._tokenizer = tokenizer
        self._model = model

    # ── Grammar correction ────────────────────────────────────────────────────

    def correct(self, sentence: str) -> dict[str, object]:
        """
        Correct grammar in a single sentence.
        Returns {"corrected": str, "fixes": int}.
        """
        if not self._tokenizer or not self._model:
            return {"corrected": sentence, "fixes": 0}

        sentence = sentence.strip()
        if not sentence:
            return {"corrected": sentence, "fixes": 0}

        try:
            prompt = self._settings.model_prefix + sentence
            inputs = self._tokenizer.encode(
                prompt,
                return_tensors="pt",
                max_length=self._settings.max_input_length,
                truncation=True,
            )
            outputs = self._model.generate(
                inputs,
                max_length=self._settings.max_output_length,
                num_beams=4,
                early_stopping=True,
            )
            corrected = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            fixes = count_word_diffs(sentence, corrected)
            return {"corrected": corrected, "fixes": fixes}
        except Exception as e:
            logger.error(f"T5 grammar correction error: {e}")
            return {"corrected": sentence, "fixes": 0}

    # ── Refinement ────────────────────────────────────────────────────────────

    def refine(self, text: str, style: str = "professional") -> dict[str, object]:
        """
        Generate a fluent rewrite preserving meaning.
        Operates on the full text (not sentence-by-sentence) for coherence.
        """
        if not self._tokenizer or not self._model:
            return {
                "refined": text,
                "improvements": ["T5 model not loaded — no refinement applied."],
            }

        style_prefix = _STYLE_PROMPTS.get(style, _STYLE_PROMPTS["professional"])

        try:
            prompt = "grammar: " + style_prefix + text
            inputs = self._tokenizer.encode(
                prompt,
                return_tensors="pt",
                max_length=self._settings.max_input_length,
                truncation=True,
            )
            outputs = self._model.generate(
                inputs,
                max_length=self._settings.max_output_length,
                num_beams=5,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )
            refined = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

            improvements = self._detect_improvements(text, refined)
            return {"refined": refined, "improvements": improvements}
        except Exception as e:
            logger.error(f"T5 refinement error: {e}")
            return {"refined": text, "improvements": [f"Refinement error: {e}"]}

    @staticmethod
    def _detect_improvements(original: str, refined: str) -> list[str]:
        """Produce a short human-readable list of what changed."""
        improvements: list[str] = []

        orig_words = original.split()
        ref_words = refined.split()

        if len(ref_words) < len(orig_words) * 0.9:
            improvements.append("Condensed verbose phrasing for clarity.")
        if len(ref_words) > len(orig_words) * 1.1:
            improvements.append("Expanded phrases for improved readability.")

        # Check sentence count
        orig_sents = re.split(r"[.!?]+", original)
        ref_sents = re.split(r"[.!?]+", refined)
        if len(ref_sents) != len(orig_sents):
            improvements.append("Restructured sentences for better flow.")

        # Check for passive → active voice heuristic
        passive_re = re.compile(r"\bwas\s+\w+ed\b|\bwere\s+\w+ed\b", re.I)
        if passive_re.search(original) and not passive_re.search(refined):
            improvements.append("Converted passive constructions to active voice.")

        if not improvements:
            improvements.append("Improved word choice and sentence cohesion.")

        return improvements[:3]
