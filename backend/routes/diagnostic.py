import os
import hashlib
from fastapi import APIRouter, Header, HTTPException
from email_service import envoyer_email_alerte, obtenir_destinataires_email

router = APIRouter()


@router.post("/api/diagnostic/email-test")
def envoyer_email_test(x_email_test_token: str = Header(None)):
    token_attendu = os.getenv("EMAIL_TEST_TOKEN", "")
    if not token_attendu or x_email_test_token != token_attendu:
        raise HTTPException(status_code=403, detail="Token diagnostic invalide")

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
