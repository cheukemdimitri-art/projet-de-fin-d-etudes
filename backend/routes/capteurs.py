from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Capteur, MesureCapteur
from qrcode_service import generer_qrcode_capteur
from security import obtenir_utilisateur_courant
from audit_service import journaliser
from mesure_service import capteurs_muets

router = APIRouter()


class SeuilsCapteurRequest(BaseModel):
    seuil_warning: float
    seuil_danger: float
    seuil_critique: float


@router.get("/api/capteurs")
def get_capteurs(db: Session = Depends(get_db)):
    capteurs = db.query(Capteur).all()
    return {
        "total": len(capteurs),
        "capteurs": [
            {
                "id": c.id,
                "nom": c.nom,
                "type": c.type,
                "zone_id": c.zone_id,
                "actif": c.actif,
                "seuil_warning": c.seuil_warning,
                "seuil_danger": c.seuil_danger,
                "seuil_critique": c.seuil_critique,
                "derniere_valeur": c.derniere_valeur,
            }
            for c in capteurs
        ],
    }


@router.get("/api/capteurs/maintenance")
def get_capteurs_maintenance(minutes: int = 10):
    return {
        "fenetre_minutes": minutes,
        "capteurs_muets": capteurs_muets(minutes),
    }


@router.get("/api/capteurs/{capteur_id}")
def get_capteur(capteur_id: str, db: Session = Depends(get_db)):
    capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
    if not capteur:
        raise HTTPException(status_code=404, detail="Capteur non trouve")
    return capteur


@router.get("/api/capteurs/{capteur_id}/historique")
def get_historique_capteur(
    capteur_id: str,
    heures: int = 24,
    limite: int = 200,
    db: Session = Depends(get_db),
):
    capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
    if not capteur:
        raise HTTPException(status_code=404, detail="Capteur non trouve")

    depuis = datetime.utcnow() - timedelta(hours=max(1, min(heures, 24 * 30)))
    mesures = (
        db.query(MesureCapteur)
        .filter(MesureCapteur.capteur_id == capteur_id, MesureCapteur.date_mesure >= depuis)
        .order_by(MesureCapteur.date_mesure.desc())
        .limit(max(1, min(limite, 1000)))
        .all()
    )
    mesures = list(reversed(mesures))
    return {
        "capteur_id": capteur_id,
        "heures": heures,
        "points": [
            {
                "date_mesure": str(m.date_mesure),
                "gaz_ppm": m.gaz_ppm,
                "temp_c": m.temp_c,
                "hum": m.hum,
                "fuite_sol": m.fuite_sol,
                "niveau": m.niveau,
                "source": m.source,
            }
            for m in mesures
        ],
    }


@router.patch("/api/capteurs/{capteur_id}/seuils")
def modifier_seuils_capteur(
    capteur_id: str,
    donnees: SeuilsCapteurRequest,
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    if not (donnees.seuil_warning < donnees.seuil_danger < donnees.seuil_critique):
        raise HTTPException(status_code=400, detail="Les seuils doivent respecter warning < danger < critique")

    capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
    if not capteur:
        raise HTTPException(status_code=404, detail="Capteur non trouve")

    capteur.seuil_warning = donnees.seuil_warning
    capteur.seuil_danger = donnees.seuil_danger
    capteur.seuil_critique = donnees.seuil_critique
    db.commit()

    journaliser(
        "MODIFIER_SEUILS_CAPTEUR",
        "capteur",
        capteur_id,
        utilisateur.get("email", "INCONNU"),
        donnees.model_dump(),
    )
    return {"message": "Seuils mis a jour", "capteur_id": capteur_id}


@router.get("/api/capteurs/{capteur_id}/qrcode")
def get_qrcode(capteur_id: str):
    chemin = generer_qrcode_capteur(capteur_id)
    if chemin:
        return FileResponse(chemin, media_type="image/png", filename=f"qr_{capteur_id}.png")
    raise HTTPException(status_code=404, detail="QR Code non genere")
