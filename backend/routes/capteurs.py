# backend/routes/capteurs.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Capteur

router = APIRouter()

# ── GET /api/capteurs — Liste tous les capteurs ───────────────────────────────
@router.get("/api/capteurs")
def get_capteurs(db: Session = Depends(get_db)):
    capteurs = db.query(Capteur).all()
    return {
        "total": len(capteurs),
        "capteurs": [
            {
                "id":             c.id,
                "nom":            c.nom,
                "type":           c.type,
                "zone_id":        c.zone_id,
                "actif":          c.actif,
                "seuil_warning":  c.seuil_warning,
                "seuil_danger":   c.seuil_danger,
                "derniere_valeur":c.derniere_valeur,
            }
            for c in capteurs
        ]
    }

# ── GET /api/capteurs/{id} — Détail d'un capteur ─────────────────────────────
@router.get("/api/capteurs/{capteur_id}")
def get_capteur(capteur_id: str, db: Session = Depends(get_db)):
    capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
    if not capteur:
        return {"erreur": "Capteur non trouvé"}
    return capteur