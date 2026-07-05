# backend/routes/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth_service import (
    authentifier_utilisateur,
    creer_token,
    obtenir_ou_creer_utilisateur_google,
    verifier_token_google,
)

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str


class GoogleRegisterRequest(BaseModel):
    id_token: str

# ── POST /auth/login ──────────────────────────────────────────────────────────
@router.post("/auth/login")
def login(donnees: LoginRequest):
    utilisateur = authentifier_utilisateur(donnees.email, donnees.mot_de_passe)

    if not utilisateur:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = creer_token(utilisateur["id"], utilisateur["email"], utilisateur["role"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "utilisateur": {
            "id": utilisateur["id"],
            "nom": utilisateur["nom"],
            "email": utilisateur["email"],
            "role": utilisateur["role"]
        }
    }


@router.post("/auth/register/google")
def register_google(donnees: GoogleRegisterRequest):
    try:
        profil_google = verifier_token_google(donnees.id_token)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not profil_google:
        raise HTTPException(status_code=401, detail="Verification Google invalide")

    utilisateur = obtenir_ou_creer_utilisateur_google(
        profil_google["email"],
        profil_google["nom"],
    )

    if not utilisateur:
        raise HTTPException(status_code=500, detail="Erreur creation utilisateur")

    token = creer_token(utilisateur["id"], utilisateur["email"], utilisateur["role"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "utilisateur": {
            "id": utilisateur["id"],
            "nom": utilisateur["nom"],
            "email": utilisateur["email"],
            "role": utilisateur["role"],
        },
    }
