import os
import hashlib
import uuid
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from werkzeug.security import generate_password_hash
from audit_service import journaliser
from database import get_connexion
from email_service import envoyer_email_alerte, obtenir_destinataires_email

router = APIRouter()


class AdminBootstrapRequest(BaseModel):
    nom: str = "Administrateur PURECONTROL"
    email: str
    mot_de_passe: str


def _verifier_token_diagnostic(x_email_test_token: str):
    token_attendu = os.getenv("EMAIL_TEST_TOKEN", "")
    if not token_attendu or x_email_test_token != token_attendu:
        raise HTTPException(status_code=403, detail="Token diagnostic invalide")


@router.post("/api/diagnostic/email-test")
def envoyer_email_test(x_email_test_token: str = Header(None)):
    _verifier_token_diagnostic(x_email_test_token)

    destinataires = obtenir_destinataires_email()
    ok = envoyer_email_alerte(
        "WARNING",
        "Test SendGrid depuis Render - PURECONTROL",
        "DIAGNOSTIC_RENDER",
    )
    key = os.getenv("SENDGRID_API_KEY", "")
    return {
        "ok": ok,
        "destinataires": len(destinataires),
        "sendgrid_key_present": bool(key),
        "sendgrid_key_fingerprint": hashlib.sha256(key.encode("utf-8")).hexdigest()[:12] if key else "",
        "message": "Email de test envoye" if ok else "Email de test non envoye",
    }


@router.post("/api/diagnostic/admin-bootstrap")
def bootstrap_admin(donnees: AdminBootstrapRequest, x_email_test_token: str = Header(None)):
    _verifier_token_diagnostic(x_email_test_token)

    nom = (donnees.nom or "Administrateur PURECONTROL").strip()
    email = (donnees.email or "").strip().lower()
    mot_de_passe = donnees.mot_de_passe or ""
    if len(nom) < 2 or "@" not in email or len(mot_de_passe) < 8:
        raise HTTPException(status_code=400, detail="Nom, email ou mot de passe invalide")

    conn = None
    try:
        conn = get_connexion()
        cur = conn.cursor()
        mot_de_passe_hash = generate_password_hash(mot_de_passe)
        cur.execute("SELECT id FROM utilisateurs WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            utilisateur_id = row[0]
            cur.execute(
                """
                UPDATE utilisateurs
                SET nom = %s, mot_de_passe = %s, role = 'ADMIN', actif = true
                WHERE id = %s
                """,
                (nom, mot_de_passe_hash, utilisateur_id),
            )
            action = "PROMOUVOIR_ADMIN"
        else:
            utilisateur_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO utilisateurs (id, nom, email, mot_de_passe, role, actif)
                VALUES (%s, %s, %s, %s, 'ADMIN', true)
                """,
                (utilisateur_id, nom, email, mot_de_passe_hash),
            )
            action = "CREER_ADMIN"

        conn.commit()
        cur.close()
        journaliser(action, "utilisateur", utilisateur_id, "SYSTEME", {"email": email})
        return {"ok": True, "id": utilisateur_id, "email": email, "role": "ADMIN", "action": action}

    except Exception as e:
        print(f"Erreur bootstrap admin : {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Bootstrap admin impossible")
    finally:
        if conn:
            conn.close()
