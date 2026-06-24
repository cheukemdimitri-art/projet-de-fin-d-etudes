# backend/database.py
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ── Paramètres de connexion ───────────────────────────────────────────────────
DB_PARAMS = {
    "host":     "localhost",
    "port":     5432,
    "user":     "postgres",
    "password": "1234",
    "dbname":   "detection_fuites",
}

POSTGRES_URL = (
    f"postgresql://{DB_PARAMS['user']}:"
    f"{DB_PARAMS['password']}@"
    f"{DB_PARAMS['host']}:"
    f"{DB_PARAMS['port']}/"
    f"{DB_PARAMS['dbname']}"
)

print("URL PostgreSQL :", POSTGRES_URL)

# ── SQLAlchemy pour les modèles ───────────────────────────────────────────────
engine       = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Connexion directe psycopg2 (contourne le problème encodage) ───────────────
def get_connexion():
    conn = psycopg2.connect(
        host=DB_PARAMS["host"],
        port=DB_PARAMS["port"],
        user=DB_PARAMS["user"],
        password=DB_PARAMS["password"],
        dbname=DB_PARAMS["dbname"],
        options="-c client_encoding=UTF8"
    )
    return conn