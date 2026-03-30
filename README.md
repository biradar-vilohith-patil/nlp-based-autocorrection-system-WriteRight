---
title: WriteRight NLP Backend
sdk: docker
app_port: 7860
---


# ✦ WriteRight — NLP Auto-Corrector

> Context-aware spelling & grammar correction powered by spaCy, SymSpell, and a T5 transformer.

---

## Project Structure

```
writeright/
├── frontend/    # React + Vite + Tailwind CSS
└── backend/     # FastAPI + spaCy + SymSpell + HuggingFace T5
```

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be live at **http://localhost:5173**  
API docs at **http://localhost:8000/docs**

---

## Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | React 18, Vite, Tailwind CSS            |
| Backend   | FastAPI, Python 3.10+                   |
| NLP       | spaCy (`en_core_web_sm`)                |
| Spelling  | SymSpell (`symspellpy`)                 |
| Grammar   | HuggingFace T5 (`vennify/t5-base-grammar-correction`) |
| Homophones| Custom JSON resolver                    |

---

## Pipeline Flow

```
User Input
    │
    ▼
Text Preprocessing  (spaCy tokenisation + normalisation)
    │
    ▼
Spell Correction    (SymSpell — edit-distance lookup)
    │
    ▼
Homophone Resolution (context-aware e.g. their/there/they're)
    │
    ▼
Grammar Correction  (T5 sequence-to-sequence model)
    │
    ▼
Scoring & Diff      (confidence + change summary)
    │
    ▼
Corrected Output ──► Optional Refinement (rephrase with same meaning)
```

---

## Environment Variables

Create `backend/.env`:

```env
MODEL_NAME=vennify/t5-base-grammar-correction
MAX_INPUT_LENGTH=512
SPELL_DICT_PATH=app/resources/dictionary.txt
HOMOPHONE_PATH=app/resources/homophones.json
ALLOWED_ORIGINS=http://localhost:5173
```
