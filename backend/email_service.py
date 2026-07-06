# backend/email_service.py
import os
import re
from html import escape
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from database import get_connexion

load_dotenv()

SENDGRID_KEY = os.getenv("SENDGRID_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_ROLES = os.getenv("EMAIL_ALERT_ROLES", "ADMIN,OPERATEUR")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _split_emails(value):
    return [email.strip() for email in value.replace(";", ",").split(",") if email.strip()]


def _email_valide(email):
    return bool(EMAIL_REGEX.match(email or ""))


def _destinataires_utilisateurs():
    roles = [role.strip().upper() for role in EMAIL_ROLES.split(",") if role.strip()]
    if not roles:
        return []

    conn = None
    try:
        conn = get_connexion()
        cur = conn.cursor()
        placeholders = ",".join(["%s"] * len(roles))
        cur.execute(
            f"""
            SELECT email
            FROM utilisateurs
            WHERE actif = true
              AND upper(role) IN ({placeholders})
            """,
            roles,
        )
        emails = [row[0] for row in cur.fetchall() if row and row[0]]
        cur.close()
        return emails
    except Exception as e:
        print(f"Erreur lecture destinataires email : {e}")
        return []
    finally:
        if conn:
            conn.close()


def obtenir_destinataires_email():
    emails = _split_emails(EMAIL_TO)
    emails.extend(_destinataires_utilisateurs())
    invalides = sorted(set(email for email in emails if email and not _email_valide(email)))
    if invalides:
        print(f"Destinataires email ignores car invalides : {', '.join(invalides)}")
    return sorted(set(email for email in emails if _email_valide(email)))


def envoyer_email_alerte(niveau, message, capteur_id, alerte_id=None):
    if not SENDGRID_KEY:
        print("SENDGRID_API_KEY manquante dans .env")
        return False
    if not EMAIL_FROM:
        print("EMAIL_FROM manquant dans .env")
        return False
    if not _email_valide(EMAIL_FROM):
        print(f"EMAIL_FROM invalide : {EMAIL_FROM}")
        return False

    destinataires = obtenir_destinataires_email()
    if not destinataires:
        print("Aucun destinataire email configure")
        return False

    try:
        couleurs = {
            "WARNING": "#FFA500",
            "DANGER": "#FF4500",
            "CRITIQUE": "#FF0000",
        }
        couleur = couleurs.get(niveau, "#000000")
        niveau_html = escape(str(niveau))
        capteur_html = escape(str(capteur_id))
        message_html = escape(str(message))
        alerte_html = escape(str(alerte_id or ""))

        contenu_html = f"""
        <div style="font-family: Arial; padding: 20px;">
            <h2 style="color: {couleur};">
                ALERTE {niveau_html} - Systeme de Detection de Fuites
            </h2>
            <hr>
            <p><strong>Capteur :</strong> {capteur_html}</p>
            <p><strong>Niveau :</strong>
                <span style="color: {couleur}; font-weight: bold;">{niveau_html}</span>
            </p>
            <p><strong>Message :</strong> {message_html}</p>
            {f"<p><strong>Alerte ID :</strong> {alerte_html}</p>" if alerte_id else ""}
            <hr>
            <p style="color: gray; font-size: 12px;">
                IUT Fotso Victor de Bandjoun - Systeme PFE 2024-2025
            </p>
        </div>
        """

        mail = Mail(
            from_email=EMAIL_FROM,
            to_emails=destinataires,
            subject=f"ALERTE {niveau} - Capteur {capteur_id}",
            html_content=contenu_html
        )

        sg = SendGridAPIClient(SENDGRID_KEY)
        response = sg.send(mail)

        print(f"Email envoye a {len(destinataires)} destinataire(s) ! Code : {response.status_code}")
        return True

    except Exception as e:
        print(f"Erreur envoi email : {e}")
        if hasattr(e, "body"):
            print(f"Detail SendGrid : {e.body}")
        return False
