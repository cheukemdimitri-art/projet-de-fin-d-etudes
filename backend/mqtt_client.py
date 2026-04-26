# backend/mqtt_client.py

import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

BROKER  = os.getenv("MQTT_BROKER", "localhost")
PORT    = int(os.getenv("MQTT_PORT", 1883))
TOPIC   = os.getenv("MQTT_TOPIC", "lab/zone_a/capteurs")

# ── Fonction appelée quand on reçoit un message MQTT ──────────────────────────
def on_message(client, userdata, msg):
    try:
        # Décoder le message JSON reçu
        donnees = json.loads(msg.payload.decode())
        print(f"✅ Message reçu sur {msg.topic} :")
        print(f"   Device  : {donnees.get('device_id')}")
        print(f"   MQ2 ppm : {donnees.get('mq2_ppm')}")
        print(f"   Alerte  : {donnees.get('niveau_alerte')}")
        print("-" * 40)
    except Exception as e:
        print(f"❌ Erreur décodage message : {e}")

# ── Fonction appelée quand on se connecte au broker ───────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connecté au broker MQTT ({BROKER}:{PORT})")
        # S'abonner au topic après connexion
        client.subscribe(TOPIC)
        print(f"📡 Abonné au topic : {TOPIC}")
    else:
        print(f"❌ Connexion échouée, code erreur : {rc}")

# ── Démarrer le client MQTT ───────────────────────────────────────────────────
def demarrer_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔄 Connexion au broker {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, keepalive=60)

    # Boucle infinie — écoute en permanence les messages
    client.loop_forever()

if __name__ == "__main__":
    demarrer_client()