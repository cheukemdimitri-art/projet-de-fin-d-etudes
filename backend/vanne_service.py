# backend/vanne_service.py
from datetime import datetime
from database import get_connexion
import paho.mqtt.publish as publish

MQTT_BROKER = "localhost"
MQTT_PORT   = 1883

# ── Récupérer la vanne liée à un capteur ──────────────────────────────────────
def obtenir_vanne_par_capteur(capteur_id):
    conn = None
    try:
        conn = get_connexion()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, nom, statut, mode FROM electrovannes
            WHERE capteur_id = %s
        """, (capteur_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            return {"id": row[0], "nom": row[1], "statut": row[2], "mode": row[3]}
        return None
    except Exception as e:
        print(f"❌ Erreur lecture vanne : {e}")
        return None
    finally:
        if conn:
            conn.close()

# ── Changer le statut d'une vanne en BD ──────────────────────────────────────
def mettre_a_jour_statut_vanne(vanne_id, nouveau_statut, actionneur="SYSTEME"):
    conn = None
    try:
        conn = get_connexion()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE electrovannes
            SET statut = %s, derniere_action = %s, actionneur = %s
            WHERE id = %s
        """, (nouveau_statut, datetime.utcnow(), actionneur, vanne_id))
        conn.commit()
        cur.close()
        print(f"🔧 Vanne {vanne_id} → {nouveau_statut} (par {actionneur})")
        return True
    except Exception as e:
        print(f"❌ Erreur mise à jour vanne : {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# ── Envoyer la commande physique via MQTT à l'ESP32 ───────────────────────────
def envoyer_commande_vanne(zone_id, commande):
    """
    commande : "FERMER" ou "OUVRIR"
    """
    try:
        topic = f"lab/{zone_id.lower()}/commande_vanne"
        publish.single(topic, commande, hostname=MQTT_BROKER, port=MQTT_PORT)
        print(f"📡 Commande envoyée à l'ESP32 : {topic} → {commande}")
        return True
    except Exception as e:
        print(f"❌ Erreur envoi commande MQTT : {e}")
        return False

# ── Fermer automatiquement la vanne lors d'une alerte critique ───────────────
def fermer_vanne_automatique(capteur_id, zone_id):
    vanne = obtenir_vanne_par_capteur(capteur_id)

    if not vanne:
        print(f"⚠️ Aucune vanne associée au capteur {capteur_id}")
        return False

    if vanne["mode"] != "AUTO":
        print(f"⚠️ Vanne {vanne['id']} en mode MANUEL, fermeture auto désactivée")
        return False

    if vanne["statut"] == "FERMEE":
        print(f"⚠️ Vanne {vanne['id']} déjà fermée")
        return True

    # Envoyer la commande physique
    envoyer_commande_vanne(zone_id, "FERMER")

    # Mettre à jour la base de données
    mettre_a_jour_statut_vanne(vanne["id"], "FERMEE", actionneur="SYSTEME")

    print(f"🚨 Vanne {vanne['id']} fermée automatiquement (alerte critique)")
    return True