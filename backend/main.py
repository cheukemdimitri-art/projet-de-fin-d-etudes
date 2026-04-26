# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Création de l'application ─────────────────────────────────────────────────
app = FastAPI(
    title="API Détection Fuites",
    description="Système de détection de fuites gaz et liquides — IUT FV Bandjoun",
    version="1.0.0"
)

# ── Autoriser React et Flutter à appeler l'API (CORS) ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Endpoint de test — Semaine 1 ──────────────────────────────────────────────
@app.get("/api/test")
def test():
    return {
        "status": "ok",
        "message": "API opérationnelle",
        "equipe": "IUT FV Bandjoun — PFE 2024-2025"
    }

# ── Endpoint racine ───────────────────────────────────────────────────────────
@app.get("/")
def racine():
    return {"message": "Bienvenue sur l'API de détection de fuites"}