# backend/mqtt_client.py
import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv
from influx_service import ecrire_mesure
from alert_service import verifier_et_alerter
from email_service import envoyer_email_alerte

load_dotenv()

BROKER = os.getenv("MQTT_BROKER", "10.221.69.218")
PORT   = int(os.getenv("MQTT_PORT", 1883))
TOPIC  = os.getenv("MQTT_TOPIC",  "lab/zone_a/capteurs")

def on_message(client, userdata, msg):
    try:
        donnees = json.loads(msg.payload.decode())
        device_id = donnees.get("capteur_id", "INCONNU")
        print(f"\nMessage recu de : {device_id}")

        mq2_ppm     = donnees.get("gaz_ppm", 0)
        mq7_ppm     = 0
        niveau_cuve = 100
        fuite_sol   = donnees.get("fuite_sol", False)

        # Reconstruire le format interne attendu par le reste du backend
        donnees_normalisees = {
            "device_id": device_id,
            "capteurs": {
                "mq2_ppm": mq2_ppm,
                "mq7_ppm": mq7_ppm,
                "niveau_cuve_cm": niveau_cuve,
                "fuite_sol": fuite_sol
            }
        }

        # 1. Sauvegarder dans InfluxDB
        ecrire_mesure(device_id, mq2_ppm, mq7_ppm, niveau_cuve, fuite_sol)

        # 2. Verifier et creer les alertes
        alertes = verifier_et_alerter(donnees_normalisees)

        # 3. Envoyer email pour chaque alerte
        for alerte in alertes:
            if alerte["niveau"] in ["WARNING", "DANGER", "CRITIQUE"]:
                envoyer_email_alerte(
                    alerte["niveau"],
                    f"Alerte {alerte['niveau']} capteur {alerte['capteur_id']}",
                    alerte["capteur_id"]
                )

        print("-" * 40)

    except Exception as e:
        print(f"Erreur : {e}")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connecte au broker MQTT")
        client.subscribe(TOPIC)
        print(f"Abonne au topic : {TOPIC}")
    else:
        print(f"Connexion echouee : code {reason_code}")

def demarrer_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    demarrer_client()