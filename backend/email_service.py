# backend/email_service.py
import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

SENDGRID_KEY = os.getenv("SENDGRID_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")


def envoyer_email_alerte(niveau, message, capteur_id):
    if not SENDGRID_KEY:
        print("SENDGRID_API_KEY manquante dans .env")
        return False

    try:
        couleurs = {
            "WARNING": "#FFA500",
            "DANGER": "#FF4500",
            "CRITIQUE": "#FF0000",
        }
        couleur = couleurs.get(niveau, "#000000")

        contenu_html = f"""
        <div style="font-family: Arial; padding: 20px;">
            <h2 style="color: {couleur};">
                ALERTE {niveau} - Systeme de Detection de Fuites
            </h2>
            <hr>
            <p><strong>Capteur :</strong> {capteur_id}</p>
            <p><strong>Niveau :</strong>
                <span style="color: {couleur}; font-weight: bold;">{niveau}</span>
            </p>
            <p><strong>Message :</strong> {message}</p>
            <hr>
            <p style="color: gray; font-size: 12px;">
                IUT Fotso Victor de Bandjoun - Systeme PFE 2024-2025
            </p>
        </div>
        """

        mail = Mail(
            from_email=EMAIL_FROM,
            to_emails=EMAIL_TO,
            subject=f"ALERTE {niveau} - Capteur {capteur_id}",
            html_content=contenu_html
        )

        sg = SendGridAPIClient(SENDGRID_KEY)
        response = sg.send(mail)

        print(f"Email envoye ! Code : {response.status_code}")
        return True

    except Exception as e:
        print(f"Erreur envoi email : {e}")
        return False