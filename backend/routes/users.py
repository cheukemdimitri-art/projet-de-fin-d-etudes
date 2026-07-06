from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Utilisateur
from security import obtenir_utilisateur_courant, verifier_role_admin
from audit_service import journaliser

router = APIRouter()


class UpdateUtilisateurRequest(BaseModel):
    role: str | None = None
    actif: bool | None = None


@router.get("/api/users")
def get_users(
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    verifier_role_admin(utilisateur)
    users = db.query(Utilisateur).order_by(Utilisateur.date_creation.desc()).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "nom": u.nom,
                "email": u.email,
                "role": u.role,
                "actif": u.actif,
                "date_creation": str(u.date_creation),
            }
            for u in users
        ],
    }


@router.patch("/api/users/{user_id}")
def update_user(
    user_id: str,
    donnees: UpdateUtilisateurRequest,
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    verifier_role_admin(utilisateur)
    cible = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    if donnees.role is not None:
        if donnees.role not in ["ADMIN", "OPERATEUR", "LECTEUR"]:
            raise HTTPException(status_code=400, detail="Role invalide")
        cible.role = donnees.role
    if donnees.actif is not None:
        cible.actif = donnees.actif

    db.commit()
    journaliser(
        "MODIFIER_UTILISATEUR",
        "utilisateur",
        user_id,
        utilisateur.get("email", "INCONNU"),
        donnees.model_dump(exclude_none=True),
    )
    return {"message": "Utilisateur mis a jour", "user_id": user_id}
