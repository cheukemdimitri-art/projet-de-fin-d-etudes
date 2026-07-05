# backend/auth_service.py
from datetime import datetime, timedelta
import json
import os
import urllib.parse
import urllib.request
import uuid
from jose import JWTError, jwt
from database import get_connexion
# Configuration JWT
SECRET_KEY = "pfe-detection-fuites-iut-bandjoun-2024-cle-secrete"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 1440
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Creer un token JWT
def creer_token(utilisateur_id: str, email: str, role: str) -> str:
    expiration = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    payload = {
        "sub": utilisateur_id,
        "email": email,
        "role": role,
        "exp": expiration
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Verifier et decoder un token
def verifier_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verifier_token_google(id_token: str):
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID non configure")

    params = urllib.parse.urlencode({"id_token": id_token})
    url = f"https://oauth2.googleapis.com/tokeninfo?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Erreur verification Google : {e}")
        return None

    if payload.get("aud") != GOOGLE_CLIENT_ID:
        print("Token Google refuse : audience invalide")
        return None

    if payload.get("email_verified") not in ["true", True]:
        print("Token Google refuse : email non verifie")
        return None

    email = payload.get("email")
    if not email:
        return None

    return {
        "email": email,
        "nom": payload.get("name") or email.split("@")[0],
    }


def obtenir_ou_creer_utilisateur_google(email: str, nom: str):
    conn = None
    try:
        conn = get_connexion()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nom, email, role
            FROM utilisateurs
            WHERE email = %s
        """, (email,))
        row = cur.fetchone()

        if row:
            cur.close()
            return {"id": row[0], "nom": row[1], "email": row[2], "role": row[3]}

        utilisateur_id = str(uuid.uuid4())
        role = "OPERATEUR"
        cur.execute("""
            INSERT INTO utilisateurs (id, nom, email, mot_de_passe, role, actif)
            VALUES (%s, %s, %s, %s, %s, true)
        """, (utilisateur_id, nom, email, "GOOGLE_AUTH", role))

        conn.commit()
        cur.close()

        return {
            "id": utilisateur_id,
            "nom": nom,
            "email": email,
            "role": role,
        }

    except Exception as e:
        print(f"Erreur creation utilisateur Google : {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

# Authentifier un utilisateur (email + mot de passe en clair pour le moment)
def authentifier_utilisateur(email: str, mot_de_passe: str):
    conn = None
    try:
        conn = get_connexion()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nom, email, mot_de_passe, role
            FROM utilisateurs
            WHERE email = %s
        """, (email,))
        row = cur.fetchone()
        cur.close()

        if not row:
            print(f"Aucun utilisateur trouve pour {email}")
            return None

        utilisateur_id, nom, email_bd, mdp_stocke, role = row

        # Comparaison simple (mot de passe en clair)
        if mot_de_passe == mdp_stocke:
            return {"id": utilisateur_id, "nom": nom, "email": email_bd, "role": role}

        print(f"Mot de passe incorrect pour {email}")
        return None

    except Exception as e:
        print(f"Erreur authentification : {e}")
        return None
    finally:
        if conn:
            conn.close()
