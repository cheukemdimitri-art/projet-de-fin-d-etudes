# backend/security.py
from fastapi import Header, HTTPException
from auth_service import verifier_token

def obtenir_utilisateur_courant(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")

    token = authorization.replace("Bearer ", "")
    payload = verifier_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    return payload

def verifier_role_admin(utilisateur=None):
    if utilisateur and utilisateur.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return utilisateur