# 🤖 AI Resume Analyzer API

A production-ready REST API built with **FastAPI** that accepts a PDF resume and returns a structured AI-powered analysis — including key skills, strengths, weaknesses, suggestions, and a quality score.

> **Demo Mode:** Currently runs with mock AI responses — no API key required.  
> To enable real AI analysis, see the [Switching to Live AI](#switching-to-live-ai) section below.

---

## 📐 Architecture Overview

```
HTTP Request
     │
     ▼
┌─────────────────────────────┐
│   FastAPI App  (main.py)    │  ← CORS, global error handler, lifespan
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Routes Layer (routes.py)  │  ← HTTP ↔ Python mapping, status codes
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Service Layer             │  ← Business logic, validation, orchestration
│   (resume_service.py)       │
└──────┬──────────────┬───────┘
       │              │
       ▼              ▼
┌──────────────┐  ┌───────────────────────────┐
│ pdf_parser   │  │  LLM (Gemini / OpenAI)    │
│ (PyMuPDF)    │  │  pluggable — see README   │
└──────────────┘  └───────────────────────────┘
              ▼
┌─────────────────────────────┐
│  Pydantic Models/Schemas    │  ← Typed, validated response
└─────────────────────────────┘
```

### REST Constraints followed

| Constraint | How it's implemented |
|---|---|
| **Client-Server** | No HTML/frontend — pure JSON API |
| **Stateless** | No sessions; every request is self-contained |
| **Cacheable** | `/health` cacheable for 30s |
| **Uniform Interface** | Resource-based URLs, standard HTTP verbs |
| **Layered System** | routes → services → utils → LLM |

---

## 📁 Project Structure

```
ai-resume-analyzer/
├── app/
│   ├── main.py                 ← FastAPI app factory, middleware, lifespan
│   ├── api/
│   │   └── routes.py           ← HTTP route definitions (thin adapter)
│   ├── services/
│   │   └── resume_service.py   ← Business logic, LLM orchestration
│   ├── models/
│   │   └── schemas.py          ← Pydantic request/response models
│   ├── core/
│   │   └── config.py           ← Env-based settings (BaseSettings)
│   └── utils/
│       └── pdf_parser.py       ← PDF text extraction (PyMuPDF)
├── requirements.txt
├── .env.example
├── vercel.json
└── README.md
```

---

## 🚀 Local Setup

### Step 1 — Create virtual environment

```bash
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

### Step 4 — Open Swagger UI

Visit **http://localhost:8000/docs**

---

## 🧪 Testing the API

### curl

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Analyze a resume
curl -X POST http://localhost:8000/api/v1/resumes/analyze \
     -F "file=@/path/to/resume.pdf"
```

### Postman
1. POST → `http://localhost:8000/api/v1/resumes/analyze`
2. Body → form-data → key: `file`, type: File
3. Upload PDF → Send

---

## 🔌 Switching to Live AI

### Option 1 — Gemini

1. Get free API key: https://aistudio.google.com/app/apikey
2. Install package:
```bash
   pip install google-genai
```
3. Add to `.env`:
```
   GEMINI_API_KEY=your-key-here
```
4. In `config.py` — uncomment Gemini section
5. In `resume_service.py` — comment out Demo block, uncomment Gemini block

### Option 2 — OpenAI

1. Get API key: https://platform.openai.com/api-keys
2. Install package:
```bash
   pip install openai
```
3. Add to `.env`:
```
   OPENAI_API_KEY=sk-your-key-here
```
4. In `config.py` — uncomment OpenAI section
5. In `resume_service.py` — comment out Demo block, uncomment OpenAI block

---

## 📋 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/api/v1/health` | Liveness check |
| POST | `/api/v1/resumes/analyze` | Upload PDF, get analysis |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc docs |

---

## ☁️ Deployment

### Render (recommended)

1. Push to GitHub
2. New Web Service → connect repo
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Deploy ✅ (no env vars needed for demo mode)

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 🛡️ Security Notes

- No API keys needed in demo mode
- File size capped at 5 MB
- PDF text truncated to 12,000 chars before LLM call
- No stack traces exposed to clients
- CORS open (`*`) by default — restrict in production