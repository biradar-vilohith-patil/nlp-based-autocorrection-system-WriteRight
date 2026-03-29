"""
app/api/routes.py
─────────────────
All REST endpoints for the WriteRight API.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field, field_validator
from loguru import logger
import time

from app.config import get_settings

router = APIRouter()
settings = get_settings()


# ── Request / Response schemas ────────────────────────────────────────────────

class CorrectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096, description="Raw input text")
    run_spell: bool = Field(True, description="Run spell-correction stage")
    run_grammar: bool = Field(True, description="Run grammar-correction stage")
    run_homophones: bool = Field(True, description="Run homophone-resolution stage")

    @field_validator("text")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be blank")
        return v


class DiffEntry(BaseModel):
    original: str
    corrected: str
    type: str          # "spell" | "grammar" | "homophone"
    position: int


class CorrectionResponse(BaseModel):
    original: str
    corrected: str
    spell_fixed: int
    grammar_fixed: int
    homophone_fixed: int
    confidence: float
    diffs: list[DiffEntry]
    processing_ms: float


class RefineRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
    style: str = Field("professional", description="professional | casual | academic | concise")

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        allowed = {"professional", "casual", "academic", "concise"}
        if v not in allowed:
            raise ValueError(f"style must be one of {allowed}")
        return v


class RefineResponse(BaseModel):
    original: str
    refined: str
    improvements: list[str]
    processing_ms: float


class HealthResponse(BaseModel):
    status: str
    spacy_loaded: bool
    symspell_loaded: bool
    t5_loaded: bool
    version: str


class StatsResponse(BaseModel):
    total_requests: int
    total_words_processed: int
    avg_spell_fixes_per_request: float
    avg_grammar_fixes_per_request: float
    avg_processing_ms: float


# ── In-memory stats accumulator ────────────────────────────────────────────────
_stats = {
    "requests": 0,
    "words": 0,
    "spell_fixes": 0,
    "grammar_fixes": 0,
    "processing_ms": 0.0,
}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(request: Request):
    """Returns liveness + model readiness."""
    proc = request.app.state.processor
    return HealthResponse(
        status="ok",
        spacy_loaded=proc.spacy_ready,
        symspell_loaded=proc.symspell_ready,
        t5_loaded=proc.t5_ready,
        version=settings.app_version,
    )


@router.get("/stats", response_model=StatsResponse, tags=["System"])
async def get_stats():
    """Aggregate pipeline stats since last restart."""
    n = max(_stats["requests"], 1)
    return StatsResponse(
        total_requests=_stats["requests"],
        total_words_processed=_stats["words"],
        avg_spell_fixes_per_request=round(_stats["spell_fixes"] / n, 2),
        avg_grammar_fixes_per_request=round(_stats["grammar_fixes"] / n, 2),
        avg_processing_ms=round(_stats["processing_ms"] / n, 1),
    )


@router.post("/correct", response_model=CorrectionResponse, tags=["NLP"])
async def correct_text(body: CorrectionRequest, request: Request):
    """
    Full correction pipeline:
      1. Text pre-processing (spaCy tokenisation)
      2. Spell correction (SymSpell)
      3. Homophone resolution (context-aware JSON rules)
      4. Grammar correction (T5 transformer)
      5. Confidence scoring + diff generation
    """
    proc = request.app.state.processor
    t0 = time.perf_counter()

    try:
        result = await proc.correct(
            text=body.text,
            run_spell=body.run_spell,
            run_grammar=body.run_grammar,
            run_homophones=body.run_homophones,
        )
    except Exception as e:
        logger.error(f"/correct error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Update stats
    word_count = len(body.text.split())
    _stats["requests"] += 1
    _stats["words"] += word_count
    _stats["spell_fixes"] += result["spell_fixed"]
    _stats["grammar_fixes"] += result["grammar_fixed"]
    _stats["processing_ms"] += elapsed_ms

    return CorrectionResponse(
        original=body.text,
        corrected=result["corrected"],
        spell_fixed=result["spell_fixed"],
        grammar_fixed=result["grammar_fixed"],
        homophone_fixed=result["homophone_fixed"],
        confidence=result["confidence"],
        diffs=[DiffEntry(**d) for d in result["diffs"]],
        processing_ms=round(elapsed_ms, 1),
    )


@router.post("/refine", response_model=RefineResponse, tags=["NLP"])
async def refine_text(body: RefineRequest, request: Request):
    """
    Takes already-corrected text and generates a polished rewrite
    with the same meaning but improved fluency, style, and coherence.
    """
    proc = request.app.state.processor
    t0 = time.perf_counter()

    try:
        result = await proc.refine(text=body.text, style=body.style)
    except Exception as e:
        logger.error(f"/refine error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return RefineResponse(
        original=body.text,
        refined=result["refined"],
        improvements=result["improvements"],
        processing_ms=round(elapsed_ms, 1),
    )
