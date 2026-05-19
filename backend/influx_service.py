# backend/influx_service.py
import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()

URL    = os.getenv("INFLUXDB_URL",    "http://localhost:8086")
TOKEN  = os.getenv("INFLUXDB_TOKEN",  "")
ORG    = os.getenv("INFLUXDB_ORG",    "iut-bandjoun")
BUCKET = os.getenv("INFLUXDB_BUCKET", "capteur-fuites")

client    = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

def ecrire_mesure(device_id, mq2_ppm, mq7_ppm, niveau_cuve, fuite_sol):
    try:
        point = (
            Point("mesure_capteur")
            .tag("device_id", device_id)
            .field("mq2_ppm",      float(mq2_ppm))
            .field("mq7_ppm",      float(mq7_ppm))
            .field("niveau_cuve",  float(niveau_cuve))
            # ⚠️ Convertir booléen en entier (0 ou 1)
            .field("fuite_sol",    int(bool(fuite_sol)))
            .time(datetime.utcnow())
        )
        write_api.write(bucket=BUCKET, org=ORG, record=point)
        print(f"✅ Mesure écrite dans InfluxDB : {device_id}")

    except Exception as e:
        print(f"❌ Erreur écriture InfluxDB : {e}")