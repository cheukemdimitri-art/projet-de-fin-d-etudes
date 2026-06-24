# backend/email_service.py
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO   = os.getenv("EMAIL_TO", "")

def envoyer_email_alerte(niveau, message, capteur_id):
    """
    Email simulé - SendGrid sera activé après vérification
    de l'email expéditeur sur app.sendgrid.com
    """
    print(f"")
    print(f"📧 ═══════ EMAIL ALERTE ═══════")
    print(f"   De      : {EMAIL_FROM}")
    print(f"   A       : {EMAIL_TO}")
    print(f"   Sujet   : ALERTE {niveau} - Capteur {capteur_id}")
    print(f"   Message : {message}")
    print(f"📧 ══════════════════════════")
    return True