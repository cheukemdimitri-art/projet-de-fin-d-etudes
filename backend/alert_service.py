# backend/alert_service.py
import uuid
from datetime import datetime
from database import get_connexion
from vanne_service import fermer_vanne_automatique
from audit_service import journaliser
from email_service import envoyer_email_alerte
from push_service import envoyer_push_alerte

# ── Évaluer le niveau d'alerte ────────────────────────────────────────────────
def evaluer_niveau(valeur, seuil_warning, seuil_danger, seuil_critique):
    if valeur >= seuil_critique:
        return "CRITIQUE"
    elif valeur >= seuil_danger:
        return "DANGER"
    elif valeur >= seuil_warning:
        return "WARNING"
    else:
        return "NORMAL"

# ── Créer une alerte directement avec psycopg2 ────────────────────────────────
def creer_alerte(capteur_id, niveau, message):
    conn = None
    try:
        conn = get_connexion()
        cur  = conn.cursor()

        # Vérifier si alerte active existe déjà
        cur.execute("""
            SELECT id FROM alertes
            WHERE capteur_id = %s AND acquittee = false
            LIMIT 1
        """, (capteur_id,))

        existante = cur.fetchone()
        if existante:
            print(f"⚠️ Alerte déjà active pour {capteur_id}")
            cur.close()
            conn.close()
            return None

        # Créer nouvelle alerte
        alerte_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO alertes (id, niveau, message, capteur_id, acquittee, date_detection)
            VALUES (%s, %s, %s, %s, false, %s)
        """, (alerte_id, niveau, message, capteur_id, datetime.utcnow()))

        conn.commit()
        cur.close()
        print(f"🚨 Alerte créée : {niveau} pour {capteur_id}")
        journaliser("CREER_ALERTE", "capteur", capteur_id, "SYSTEME", {"alerte_id": alerte_id, "niveau": niveau})
        envoyer_email_alerte(niveau, message, capteur_id, alerte_id=alerte_id)
        envoyer_push_alerte(niveau, message, capteur_id, alerte_id=alerte_id)
        return alerte_id

    except Exception as e:
        print(f"❌ Erreur création alerte : {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

# ── Vérifier et déclencher les alertes ───────────────────────────────────────
# ── Vérifier et déclencher les alertes ───────────────────────────────────────
def verifier_et_alerter(donnees: dict):
    capteurs    = donnees.get("capteurs", {})
    device_id   = donnees.get("device_id", "INCONNU")
    mq2_ppm     = capteurs.get("mq2_ppm",        0)
    mq7_ppm     = capteurs.get("mq7_ppm",        0)
    niveau_cuve = capteurs.get("niveau_cuve_cm", 100)
    fuite_sol   = capteurs.get("fuite_sol",      False)

    alertes = []

    # ── Vérifier MQ-2 (GPL) ──────────────────────────────────────────────────
    niveau_mq2 = evaluer_niveau(mq2_ppm, 1500, 2500, 3500)
    print(f"📊 MQ-2 : {mq2_ppm} ppm → {niveau_mq2}")
    if niveau_mq2 != "NORMAL":
        id_alerte = creer_alerte(
            "CAP_A1", niveau_mq2,
            f"Concentration GPL : {mq2_ppm} ppm"
        )
        if id_alerte:
            alertes.append({
                "id":         id_alerte,
                "niveau":     niveau_mq2,
                "capteur_id": "CAP_A1"
            })

    # ── Vérifier MQ-7 (CO) ───────────────────────────────────────────────────
    niveau_mq7 = evaluer_niveau(mq7_ppm, 800, 1500, 2000)
    print(f"📊 MQ-7 : {mq7_ppm} ppm → {niveau_mq7}")
    if niveau_mq7 != "NORMAL":
        id_alerte = creer_alerte(
            "CAP_A2", niveau_mq7,
            f"Concentration CO : {mq7_ppm} ppm"
        )
        if id_alerte:
            alertes.append({
                "id":         id_alerte,
                "niveau":     niveau_mq7,
                "capteur_id": "CAP_A2"
            })

    # ── Vérifier fuite sol (câble de fuite liquide) ──────────────────────────
    if fuite_sol:
        print(f"🚨 FUITE LIQUIDE AU SOL DETECTEE !")
        id_alerte = creer_alerte(
            "CAP_B2", "DANGER",
            "Fuite liquide detectee au sol - Intervention immediate requise"
        )
        if id_alerte:
            alertes.append({
                "id":         id_alerte,
                "niveau":     "DANGER",
                "capteur_id": "CAP_B2"
            })

            # Fermer la vanne liquide automatiquement
            fermer_vanne_automatique("CAP_B2", "ZONE_B")

    # ── Vérifier niveau cuve (HC-SR04) ───────────────────────────────────────
    niveau_cuve_alerte = evaluer_niveau(
        100 - niveau_cuve, 20, 40, 60
    )
    print(f"📊 Niveau cuve : {niveau_cuve} cm → {niveau_cuve_alerte}")
    if niveau_cuve_alerte != "NORMAL":
        id_alerte = creer_alerte(
            "CAP_B1", niveau_cuve_alerte,
            f"Niveau cuve bas : {niveau_cuve} cm - Possible fuite"
        )
        if id_alerte:
            alertes.append({
                "id":         id_alerte,
                "niveau":     niveau_cuve_alerte,
                "capteur_id": "CAP_B1"
            })

            # Fermer la vanne liquide si DANGER ou CRITIQUE
            if niveau_cuve_alerte in ["DANGER", "CRITIQUE"]:
                fermer_vanne_automatique("CAP_B1", "ZONE_B")

    return alertes
