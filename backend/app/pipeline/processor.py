"""
app/pipeline/processor.py
──────────────────────────
Orchestrates the full NLP correction pipeline:
  Pre-process → Spell → Homophones → Grammar → Score → Diff
"""

from __future__ import annotations

import asyncio
from loguru import logger

from app.config import Settings
from app.pipeline.spell_checker import SpellChecker
from app.pipeline.homophone_resolver import HomophoneResolver
from app.pipeline.grammar_corrector import GrammarCorrector
from app.pipeline.scorer import Scorer
from app.models.model_loader import ModelLoader
from app.utils.text_utils import (
    split_into_sentences,
    normalise_whitespace,
    build_word_diffs,
)


class NLPProcessor:
    """
    Central pipeline orchestrator. Holds references to all sub-modules and
    coordinates them for each correction / refinement request.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

        # Status flags — set to True once each module loads successfully
        self.spacy_ready: bool = False
        self.symspell_ready: bool = False
        self.t5_ready: bool = False

        self._spell_checker: SpellChecker | None = None
        self._homophone_resolver: HomophoneResolver | None = None
        self._grammar_corrector: GrammarCorrector | None = None
        self._scorer: Scorer | None = None
        self._model_loader: ModelLoader | None = None

    # ── Initialisation ────────────────────────────────────────────────────────

    async def initialise(self) -> None:
        """Load all models/resources. Called once at startup."""
        logger.info("Initialising NLP pipeline…")

        # Run heavy model loads in a thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_all)

        logger.info(
            f"Pipeline ready | spaCy={self.spacy_ready} "
            f"SymSpell={self.symspell_ready} T5={self.t5_ready}"
        )

    def _load_all(self) -> None:
        s = self._settings

        # 1. Model loader (spaCy + T5)
        self._model_loader = ModelLoader(s)
        nlp, tokenizer, t5_model = self._model_loader.load()

        if nlp:
            self.spacy_ready = True

        # 2. Spell checker
        self._spell_checker = SpellChecker(s)
        if self._spell_checker.load():
            self.symspell_ready = True

        # 3. Homophone resolver
        self._homophone_resolver = HomophoneResolver(s)
        self._homophone_resolver.load()

        # 4. Grammar corrector
        self._grammar_corrector = GrammarCorrector(s, tokenizer, t5_model)
        if tokenizer and t5_model:
            self.t5_ready = True

        # 5. Scorer
        self._scorer = Scorer(nlp)

    # ── Correction pipeline ───────────────────────────────────────────────────

    async def correct(
        self,
        text: str,
        run_spell: bool = True,
        run_grammar: bool = True,
        run_homophones: bool = True,
    ) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._correct_sync,
            text,
            run_spell,
            run_grammar,
            run_homophones,
        )

    def _correct_sync(
        self,
        text: str,
        run_spell: bool,
        run_grammar: bool,
        run_homophones: bool,
    ) -> dict:
        original = text
        spell_fixed = 0
        grammar_fixed = 0
        homophone_fixed = 0
        all_diffs: list[dict] = []

        # ── Stage 1: Normalise whitespace ─────────────────────────────────────
        current = normalise_whitespace(text)

        # ── Stage 2: Spell correction ─────────────────────────────────────────
        if run_spell and self._spell_checker and self.symspell_ready:
            spell_result = self._spell_checker.correct(current)
            if spell_result["corrected"] != current:
                diffs = build_word_diffs(current, spell_result["corrected"], "spell")
                all_diffs.extend(diffs)
                spell_fixed = spell_result["fixes"]
                current = spell_result["corrected"]
                logger.debug(f"Spell: {spell_fixed} fixes")

        # ── Stage 3: Homophone resolution ─────────────────────────────────────
        if run_homophones and self._homophone_resolver:
            hom_result = self._homophone_resolver.resolve(current)
            if hom_result["corrected"] != current:
                diffs = build_word_diffs(current, hom_result["corrected"], "homophone")
                all_diffs.extend(diffs)
                homophone_fixed = hom_result["fixes"]
                current = hom_result["corrected"]
                logger.debug(f"Homophones: {homophone_fixed} fixes")

        # ── Stage 4: Grammar correction (sentence by sentence) ────────────────
        if run_grammar and self._grammar_corrector:
            sentences = split_into_sentences(current)
            corrected_sentences: list[str] = []
            for sent in sentences:
                gram_result = self._grammar_corrector.correct(sent)
                corrected_sentences.append(gram_result["corrected"])
                grammar_fixed += gram_result["fixes"]

            grammar_text = " ".join(corrected_sentences)
            if grammar_text != current:
                diffs = build_word_diffs(current, grammar_text, "grammar")
                all_diffs.extend(diffs)
                current = grammar_text
                logger.debug(f"Grammar: {grammar_fixed} fixes")

        # ── Stage 5: Confidence score ─────────────────────────────────────────
        confidence = 1.0
        if self._scorer:
            confidence = self._scorer.score(original, current)

        return {
            "corrected": current,
            "spell_fixed": spell_fixed,
            "grammar_fixed": grammar_fixed,
            "homophone_fixed": homophone_fixed,
            "confidence": round(confidence, 3),
            "diffs": all_diffs,
        }

    # ── Refinement pipeline ───────────────────────────────────────────────────

    async def refine(self, text: str, style: str = "professional") -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._refine_sync, text, style)

    def _refine_sync(self, text: str, style: str) -> dict:
        if self._grammar_corrector:
            return self._grammar_corrector.refine(text, style)

        # Fallback: return text unchanged if model not loaded
        return {
            "refined": text,
            "improvements": ["Grammar model not loaded; no refinement applied."],
        }
