# backend/qrcode_service.py
import os
import qrcode
from database import SessionLocal
from models import Capteur

DEFAULT_PUBLIC_BASE_URL = "https://projet-de-fin-d-etudes.onrender.com"
PUBLIC_BASE_URL = (
    os.getenv("PUBLIC_BASE_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
    or DEFAULT_PUBLIC_BASE_URL
).rstrip("/")


def generer_qrcode_capteur(capteur_id: str):
    try:
        url = f"{PUBLIC_BASE_URL}/api/capteurs/{capteur_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#1F3864", back_color="white")

        dossier = "qrcodes"
        os.makedirs(dossier, exist_ok=True)
        chemin = f"{dossier}/qr_{capteur_id}.png"
        img.save(chemin)

        print(f"QR Code genere : {chemin} -> {url}")
        return chemin

    except Exception as e:
        print(f"Erreur QR Code : {e}")
        return None


def generer_tous_qrcodes():
    db = SessionLocal()
    try:
        capteurs = db.query(Capteur).all()
        chemins = []

        for capteur in capteurs:
            chemin = generer_qrcode_capteur(capteur.id)
            if chemin:
                chemins.append(chemin)

        print(f"{len(chemins)} QR Codes generes dans le dossier 'qrcodes/'")
        return chemins

    finally:
        db.close()
