from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import PushToken
from security import obtenir_utilisateur_courant

router = APIRouter()


class PushTokenRequest(BaseModel):
    token: str
    plateforme: str = "android"


@router.post("/api/push/register")
def register_push_token(
    donnees: PushTokenRequest,
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    existing = db.query(PushToken).filter(PushToken.token == donnees.token).first()
    if existing:
        existing.utilisateur_id = utilisateur.get("sub")
        existing.plateforme = donnees.plateforme
        existing.actif = True
    else:
        db.add(PushToken(
            utilisateur_id=utilisateur.get("sub"),
            token=donnees.token,
            plateforme=donnees.plateforme,
            actif=True,
        ))
    db.commit()
    return {"message": "Token push enregistre"}


@router.post("/api/push/unregister")
def unregister_push_token(
    donnees: PushTokenRequest,
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    existing = db.query(PushToken).filter(PushToken.token == donnees.token).first()
    if existing:
        existing.actif = False
        db.commit()
    return {"message": "Token push desactive"}
