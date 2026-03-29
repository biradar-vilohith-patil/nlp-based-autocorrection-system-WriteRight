"""
app/models/model_loader.py
───────────────────────────
Loads and caches:
  • spaCy en_core_web_sm  — for tokenisation, POS tagging, NER
  • HuggingFace T5        — for grammar correction / refinement

Both are loaded once at startup and injected into the pipeline.
"""

from __future__ import annotations

from loguru import logger
from app.config import Settings


class ModelLoader:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._nlp = None
        self._tokenizer = None
        self._model = None

    def load(self) -> tuple:
        """
        Returns (nlp, tokenizer, t5_model).
        Any component that fails to load returns None for that slot.
        """
        nlp       = self._load_spacy()
        tokenizer, model = self._load_t5()
        return nlp, tokenizer, model

    # ── spaCy ─────────────────────────────────────────────────────────────────

    def _load_spacy(self):
        try:
            import spacy
            logger.info(f"Loading spaCy model: {self._settings.spacy_model}")
            nlp = spacy.load(
                self._settings.spacy_model,
                # Only load the components we need — faster startup
                disable=["ner"] if self._settings.skip_spell_for_proper_nouns else [],
            )
            logger.info("spaCy loaded successfully.")
            self._nlp = nlp
            return nlp
        except OSError:
            logger.warning(
                f"spaCy model '{self._settings.spacy_model}' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            return None
        except ImportError:
            logger.warning("spaCy not installed.")
            return None
        except Exception as e:
            logger.error(f"spaCy load error: {e}")
            return None

    # ── T5 Transformer ────────────────────────────────────────────────────────

    def _load_t5(self) -> tuple:
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            model_name = self._settings.model_name
            device     = self._settings.model_device

            logger.info(f"Loading T5 model: {model_name} on {device}")

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            if device == "cuda":
                try:
                    model = model.to("cuda")
                    logger.info("T5 moved to CUDA.")
                except Exception:
                    logger.warning("CUDA unavailable, using CPU.")

            model.eval()   # inference mode — disables dropout
            logger.info("T5 model loaded successfully.")
            self._tokenizer = tokenizer
            self._model = model
            return tokenizer, model

        except ImportError:
            logger.warning(
                "transformers / torch not installed — grammar correction disabled."
            )
            return None, None
        except Exception as e:
            logger.error(f"T5 load error: {e}")
            return None, None
