# backend/mqtt_client.py
import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv
from influx_service import ecrire_mesure

load_dotenv()

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT   = int(os.getenv("MQTT_PORT", 1883))
TOPIC  = os.getenv("MQTT_TOPIC",  "lab/zone_a/capteurs")

# ── Réception d'un message MQTT ───────────────────────────────────────────────
def on_message(client, userdata, msg):
    try:
        donnees = json.loads(msg.payload.decode())
        print(f"✅ Message reçu : {donnees}")

        # Extraire les valeurs
        device_id   = donnees.get("device_id",  "INCONNU")
        capteurs    = donnees.get("capteurs",    {})
        mq2_ppm     = capteurs.get("mq2_ppm",   0)
        mq7_ppm     = capteurs.get("mq7_ppm",   0)
        niveau_cuve = capteurs.get("niveau_cuve_cm", 0)
        fuite_sol   = capteurs.get("fuite_sol", False)

        # Sauvegarder dans InfluxDB
        ecrire_mesure(device_id, mq2_ppm, mq7_ppm, niveau_cuve, fuite_sol)

        print("-" * 40)

    except Exception as e:
        print(f"❌ Erreur traitement message : {e}")

# ── Connexion au broker ───────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connecté au broker MQTT")
        client.subscribe(TOPIC)
        print(f"📡 Abonné au topic : {TOPIC}")
    else:
        print(f"❌ Connexion échouée : code {rc}")

# ── Démarrer le client ────────────────────────────────────────────────────────
def demarrer_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    demarrer_client()