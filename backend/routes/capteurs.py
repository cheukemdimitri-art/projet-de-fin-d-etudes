# backend/routes/capteurs.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Capteur
from fastapi.responses import FileResponse
from qrcode_service import generer_qrcode_capteur

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
@router.get("/api/capteurs/{capteur_id}/qrcode")
def get_qrcode(capteur_id: str):
    chemin = generer_qrcode_capteur(capteur_id)
    if chemin:
        return FileResponse(
            chemin,
            media_type="image/png",
            filename=f"qr_{capteur_id}.png"
        )
    raise HTTPException(status_code=404, detail="QR Code non genere")