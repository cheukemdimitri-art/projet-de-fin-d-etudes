# backend/mqtt_client.py
import paho.mqtt.client as mqtt
import json
import os
import ssl
import threading
from dotenv import load_dotenv
from influx_service import ecrire_mesure
from alert_service import verifier_et_alerter
from mesure_service import enregistrer_mesure
from audit_service import journaliser

load_dotenv()

BROKER    = os.getenv("MQTT_BROKER",   "localhost")
PORT      = int(os.getenv("MQTT_PORT", 8883))
TOPIC     = os.getenv("MQTT_TOPIC",    "iut/bandjoun/capteur/json")
MQTT_USER = os.getenv("MQTT_USER",     "")
MQTT_PASS = os.getenv("MQTT_PASSWORD", "")

gestionnaire_ws = None

def set_gestionnaire(g):
    global gestionnaire_ws
    gestionnaire_ws = g

def on_message(client, userdata, msg):
    try:
        donnees   = json.loads(msg.payload.decode())
        device_id = donnees.get("capteur_id", "INCONNU")
        print(f"\n📨 Message recu de : {device_id}")

        mq2_ppm     = donnees.get("gaz_ppm",   0)
        mq7_ppm     = 0
        niveau_cuve = 100
        fuite_sol   = donnees.get("fuite_sol", False)
        temp_c      = donnees.get("temp_c",    0)
        hum         = donnees.get("hum",       0)
        niveau      = donnees.get("niveau",    "NORMAL")

        donnees_normalisees = {
            "device_id": device_id,
            "capteurs": {
                "mq2_ppm":        mq2_ppm,
                "mq7_ppm":        mq7_ppm,
                "niveau_cuve_cm": niveau_cuve,
                "fuite_sol":      fuite_sol
            }
        }

        ecrire_mesure(device_id, mq2_ppm, mq7_ppm, niveau_cuve, fuite_sol)
        enregistrer_mesure(device_id, mq2_ppm, temp_c, hum, fuite_sol, niveau, source="MQTT")

        if gestionnaire_ws:
            import asyncio
            payload_ws = {
                "type":       "mesure",
                "capteur_id": device_id,
                "gaz_ppm":    mq2_ppm,
                "temp_c":     temp_c,
                "hum":        hum,
                "fuite_sol":  fuite_sol,
                "niveau":     niveau
            }
            asyncio.run(gestionnaire_ws.diffuser(payload_ws))

        alertes = verifier_et_alerter(donnees_normalisees)
        if alertes:
            journaliser(
                "ALERTE_MQTT",
                "capteur",
                device_id,
                "SYSTEME",
                {"niveau": niveau, "alertes": alertes},
            )
            if gestionnaire_ws:
                import asyncio
                asyncio.run(gestionnaire_ws.diffuser({
                    "type": "alerte",
                    "source": "MQTT",
                    "alertes": alertes,
                    "niveau": max((a.get("niveau", "NORMAL") for a in alertes), key=lambda n: ["NORMAL", "WARNING", "DANGER", "CRITIQUE"].index(n) if n in ["NORMAL", "WARNING", "DANGER", "CRITIQUE"] else 0),
                }))

        print("-" * 40)

    except Exception as e:
        print(f"❌ Erreur on_message : {e}")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connecte au broker MQTT HiveMQ")
        client.subscribe(TOPIC)
        print(f"📡 Abonne au topic : {TOPIC}")
    else:
        print(f"❌ Connexion MQTT echouee : code {reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"⚠️ Deconnecte du broker MQTT (code {reason_code})")

def demarrer_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    if PORT == 8883:
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

def demarrer_client_thread(gestionnaire):
    set_gestionnaire(gestionnaire)
    thread = threading.Thread(target=demarrer_client, daemon=True)
    thread.start()
    print("🔄 Client MQTT démarré en arrière-plan")
