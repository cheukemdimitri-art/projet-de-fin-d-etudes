from datetime import datetime, timedelta
from database import SessionLocal
from models import Capteur, MesureCapteur


def enregistrer_mesure(capteur_id, gaz_ppm=0, temp_c=0, hum=0, fuite_sol=False, niveau="NORMAL", source="MQTT"):
    db = SessionLocal()
    try:
        mesure = MesureCapteur(
            capteur_id=capteur_id,
            gaz_ppm=float(gaz_ppm or 0),
            temp_c=float(temp_c or 0),
            hum=float(hum or 0),
            fuite_sol=bool(fuite_sol),
            niveau=niveau or "NORMAL",
            source=source,
        )
        db.add(mesure)

        capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        if capteur:
            if capteur.type in ["GAZ_GPL", "GAZ_CO"]:
                capteur.derniere_valeur = float(gaz_ppm or 0)
            elif capteur.type == "TEMPERATURE":
                capteur.derniere_valeur = float(temp_c or 0)
            elif capteur.type == "LIQUIDE_SOL":
                capteur.derniere_valeur = 1 if fuite_sol else 0

        db.commit()
        return {"id": mesure.id, "capteur_id": capteur_id}
    except Exception as e:
        print(f"Erreur enregistrement mesure {capteur_id}: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def dernieres_mesures_par_capteur():
    db = SessionLocal()
    try:
        rows = {}
        mesures = (
            db.query(MesureCapteur)
            .order_by(MesureCapteur.date_mesure.desc())
            .limit(1000)
            .all()
        )
        for mesure in mesures:
            if mesure.capteur_id not in rows:
                rows[mesure.capteur_id] = mesure.date_mesure
        return rows
    finally:
        db.close()


def capteurs_muets(minutes=10):
    db = SessionLocal()
    try:
        limite = datetime.utcnow() - timedelta(minutes=minutes)
        dernieres = dernieres_mesures_par_capteur()
        capteurs = db.query(Capteur).filter(Capteur.actif == True).all()
        muets = []
        for capteur in capteurs:
            derniere = dernieres.get(capteur.id)
            if not derniere or derniere < limite:
                muets.append({
                    "id": capteur.id,
                    "nom": capteur.nom,
                    "type": capteur.type,
                    "zone_id": capteur.zone_id,
                    "derniere_mesure": str(derniere) if derniere else None,
                })
        return muets
    finally:
        db.close()
