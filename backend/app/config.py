"""
app/config.py
─────────────
Centralised settings loaded from environment / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    app_name: str = "WriteRight NLP API"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── CORS ─────────────────────────────────────────────
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ── Model ─────────────────────────────────────────────
    # vennify/t5-base-grammar-correction is a lightweight T5
    # fine-tuned specifically for grammar error correction.
    model_name: str = "vennify/t5-base-grammar-correction"
    model_prefix: str = "grammar: "
    max_input_length: int = 512
    max_output_length: int = 512
    model_device: str = "cpu"          # "cuda" if GPU available

    # ── Spell checker ─────────────────────────────────────
    spell_dict_path: str = str(BASE_DIR / "resources" / "dictionary.txt")
    spell_max_edit_distance: int = 2
    spell_prefix_length: int = 7

    # ── Homophones ────────────────────────────────────────
    homophone_path: str = str(BASE_DIR / "resources" / "homophones.json")

    # ── Pipeline ─────────────────────────────────────────
    spacy_model: str = "en_core_web_sm"
    min_word_length_for_spell: int = 2   # skip very short tokens
    skip_spell_for_proper_nouns: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
