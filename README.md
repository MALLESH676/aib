# TrustShield 🛡️
## AI-Powered Trust & Safety Platform

Multi-agent fraud detection platform for e-commerce marketplaces.

## Architecture

```
Browser (React + Vite)
    ↓ REST
FastAPI Backend
    ↓
TrustCoordinator (async parallel)
    ├── RiskAgent      (XGBoost + rules)
    ├── AuthAgent      (rules + price anomaly + image heuristics)  
    └── ReviewAgent    (sentence-transformers + NetworkX)
    ↓
RiskFusionEngine (confidence-weighted)
    ↓
PolicyEngine (deterministic)
    ↓
ALLOW / REVIEW / HOLD → AuditLog → DB
```

## Quick Start

### Backend
```bash
cd backend
python -m pip install -r requirements.txt
python main.py
# API at http://localhost:8000
# Docs at http://localhost:8000/api/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

## Demo Scenarios

Hit `POST /api/v1/demo/B` to trigger the Fraud Ring scenario (primary demo).

| Scenario | Type | Expected | Risk | Auth | Review |
|----------|------|----------|------|------|--------|
| A | Legitimate | ALLOW | 8 | 5 | 7 |
| B | Fraud Ring | HOLD | 87 | 94 | 96 |
| C | Ambiguous | REVIEW | 64 | 71 | 68 |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite 5 + TypeScript |
| Backend | FastAPI + Python 3.12 |
| Database | SQLite (async via aiosqlite) |
| Risk ML | XGBoost (trained on 2000 synthetic samples) |
| Review NLP | sentence-transformers (all-MiniLM-L6-v2) |
| Graph Analysis | NetworkX |
| ORM | SQLAlchemy 2.0 async |

## Environment

Copy `backend/.env.example` to `backend/.env`.
Set `LLM_MODEL=template` for offline mode (no API key required).
Set `LLM_MODEL=gemini/gemini-2.0-flash` + `GEMINI_API_KEY=...` for AI explanations.
