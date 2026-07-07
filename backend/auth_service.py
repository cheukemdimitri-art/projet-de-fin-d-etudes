# backend/auth_service.py
from datetime import datetime, timedelta
import json
import os
import urllib.parse
import urllib.request
import uuid
from jose import JWTError, jwt
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_connexion
# Configuration JWT
SECRET_KEY = "pfe-detection-fuites-iut-bandjoun-2024-cle-secrete"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 1440
DEFAULT_GOOGLE_CLIENT_ID = "430510354808-2v3nmcdu2hi64rgo220le8uala3caftp.apps.googleusercontent.com"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") or DEFAULT_GOOGLE_CLIENT_ID


def _mot_de_passe_valide(mot_de_passe: str, valeur_stockee: str) -> bool:
    if not valeur_stockee:
        return False
    if valeur_stockee.startswith(("scrypt:", "pbkdf2:", "argon2:")):
        return check_password_hash(valeur_stockee, mot_de_passe)
    return mot_de_passe == valeur_stockee

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
            SELECT id, nom, email, role, actif
            FROM utilisateurs
            WHERE email = %s
        """, (email,))
        row = cur.fetchone()

        if row:
            cur.close()
            if not row[4]:
                return None
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


def creer_utilisateur_email(nom: str, email: str, mot_de_passe: str):
    conn = None
    try:
        nom = (nom or "").strip()
        email = (email or "").strip().lower()
        mot_de_passe = mot_de_passe or ""

        if len(nom) < 2 or "@" not in email or len(mot_de_passe) < 6:
            return None, "Nom, email ou mot de passe invalide"

        conn = get_connexion()
        cur = conn.cursor()
        cur.execute("SELECT id FROM utilisateurs WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            return None, "Un compte existe deja avec cet email"

        utilisateur_id = str(uuid.uuid4())
        role = "OPERATEUR"
        mot_de_passe_hash = generate_password_hash(mot_de_passe)
        cur.execute("""
            INSERT INTO utilisateurs (id, nom, email, mot_de_passe, role, actif)
            VALUES (%s, %s, %s, %s, %s, true)
        """, (utilisateur_id, nom, email, mot_de_passe_hash, role))

        conn.commit()
        cur.close()

        return {
            "id": utilisateur_id,
            "nom": nom,
            "email": email,
            "role": role,
        }, None

    except Exception as e:
        print(f"Erreur creation utilisateur email : {e}")
        if conn:
            conn.rollback()
        return None, "Erreur creation utilisateur"
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
            SELECT id, nom, email, mot_de_passe, role, actif
            FROM utilisateurs
            WHERE email = %s
        """, (email,))
        row = cur.fetchone()
        cur.close()

        if not row:
            print(f"Aucun utilisateur trouve pour {email}")
            return None

        utilisateur_id, nom, email_bd, mdp_stocke, role, actif = row

        if not actif:
            print(f"Utilisateur inactif : {email}")
            return None

        if _mot_de_passe_valide(mot_de_passe, mdp_stocke):
            return {"id": utilisateur_id, "nom": nom, "email": email_bd, "role": role}

        print(f"Mot de passe incorrect pour {email}")
        return None

    except Exception as e:
        print(f"Erreur authentification : {e}")
        return None
    finally:
        if conn:
            conn.close()
