# backend/routes/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth_service import authentifier_utilisateur, creer_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str

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