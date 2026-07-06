# backend/routes/alertes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Alerte, Capteur
from fastapi import Depends
from security import obtenir_utilisateur_courant
from fastapi.responses import FileResponse
from rapport_service import generer_rapport_mensuel, generer_rapport_incident
from qrcode_service import generer_qrcode_capteur
from audit_service import journaliser
from mesure_service import capteurs_muets
router = APIRouter()

# ── GET /api/alertes — Liste toutes les alertes ───────────────────────────────
@router.get("/api/alertes")
def get_alertes(db: Session = Depends(get_db)):
    alertes = db.query(Alerte).order_by(
        Alerte.date_detection.desc()
    ).all()
    return {
        "total": len(alertes),
        "alertes": [
            {
                "id":             a.id,
                "niveau":         a.niveau,
                "message":        a.message,
                "capteur_id":     a.capteur_id,
                "acquittee":      a.acquittee,
                "commentaire":    a.commentaire,
                "date_detection": str(a.date_detection),
            }
            for a in alertes
        ]
    }

# ── GET /api/alertes/actives — Alertes non acquittées ────────────────────────
@router.get("/api/alertes/actives")
def get_alertes_actives(db: Session = Depends(get_db)):
    alertes = db.query(Alerte).filter(
        Alerte.acquittee == False
    ).all()
    return {
        "total": len(alertes),
        "alertes": [
            {
                "id":             a.id,
                "niveau":         a.niveau,
                "message":        a.message,
                "capteur_id":     a.capteur_id,
                "date_detection": str(a.date_detection),
            }
            for a in alertes
        ]
    }

# ── POST /api/alertes/{id}/acquitter ─────────────────────────────────────────
@router.post("/api/alertes/{alerte_id}/acquitter")
def acquitter_alerte(
    alerte_id: str,
    commentaire: str = "Alerte traitee",
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant)
):
    alerte = db.query(Alerte).filter(Alerte.id == alerte_id).first()

    if not alerte:
        raise HTTPException(status_code=404, detail="Alerte non trouvee")

    if alerte.acquittee:
        return {"message": "Alerte déjà acquittée", "alerte_id": alerte_id}

    alerte.acquittee         = True
    alerte.commentaire       = commentaire
    alerte.date_acquittement = datetime.utcnow()

    db.commit()
    journaliser(
        "ACQUITTER_ALERTE",
        "alerte",
        alerte_id,
        utilisateur.get("email", "INCONNU"),
        {"commentaire": commentaire, "capteur_id": alerte.capteur_id},
    )

    print(f"✅ Alerte {alerte_id} acquittée")
    return {
        "message":    "Alerte acquittée avec succès",
        "alerte_id":  alerte_id,
        "commentaire": commentaire
    }

# ── GET /api/dashboard/stats ──────────────────────────────────────────────────
@router.get("/api/dashboard/stats")
def get_stats(db: Session = Depends(get_db)):
    total_capteurs        = db.query(Capteur).count()
    capteurs_actifs       = db.query(Capteur).filter(Capteur.actif == True).count()
    total_alertes         = db.query(Alerte).count()
    alertes_actives       = db.query(Alerte).filter(Alerte.acquittee == False).count()
    alertes_critiques     = db.query(Alerte).filter(
        Alerte.niveau == "CRITIQUE",
        Alerte.acquittee == False
    ).count()
    muets = capteurs_muets(10)

    return {
        "capteurs": {
            "total":  total_capteurs,
            "actifs": capteurs_actifs,
            "muets": len(muets),
        },
        "alertes": {
            "total":    total_alertes,
            "actives":  alertes_actives,
            "critiques": alertes_critiques,
        },
        "maintenance": {
            "capteurs_muets": len(muets),
        },
        "statut_global": "DANGER" if alertes_critiques > 0
                         else "WARNING" if alertes_actives > 0
                         else "NORMAL"
    }
@router.get("/api/rapports/generer")
def generer_rapport():
    chemin = generer_rapport_mensuel()
    if chemin:
        return FileResponse(
            chemin,
            media_type="application/pdf",
            filename="rapport_mensuel.pdf"
        )
    raise HTTPException(status_code=500, detail="Erreur generation rapport")


@router.get("/api/alertes/{alerte_id}/rapport")
def rapport_incident(alerte_id: str):
    chemin = generer_rapport_incident(alerte_id)
    if chemin:
        return FileResponse(
            chemin,
            media_type="application/pdf",
            filename=f"rapport_incident_{alerte_id[:8]}.pdf"
        )
    raise HTTPException(status_code=404, detail="Alerte non trouvee ou erreur generation")
