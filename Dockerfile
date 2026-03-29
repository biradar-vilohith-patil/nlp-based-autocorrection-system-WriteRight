# Dockerfile  — must be at the repo root
FROM python:3.10-slim

# System dependencies (needed for tokenizers native Rust extension)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only torch FIRST to reduce image size by ~2 GB
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Create non-root user (HF Spaces security requirement)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model at BUILD time so it doesn't delay startup
RUN python -m spacy download en_core_web_sm

# Copy application source code
COPY app/ ./app/

# Switch to non-root user
USER appuser

# HF Spaces REQUIRES port 7860 — do not change this
EXPOSE 7860

# Launch FastAPI on port 7860
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--workers", "1"]
