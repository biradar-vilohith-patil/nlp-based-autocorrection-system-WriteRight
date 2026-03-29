# WriteRight — Backend

FastAPI backend exposing the NLP correction pipeline.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Running

```bash
# Development (auto-reload)
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## API Endpoints

| Method | Path               | Description                      |
|--------|--------------------|----------------------------------|
| POST   | `/api/correct`     | Spell + grammar correction       |
| POST   | `/api/refine`      | Rephrase while preserving meaning|
| GET    | `/api/health`      | Health check + model status      |
| GET    | `/api/stats`       | Pipeline metrics                 |

## Running Tests

```bash
pytest tests/ -v
```
