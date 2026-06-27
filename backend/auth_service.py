# backend/auth_service.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from database import get_connexion
# Configuration JWT
SECRET_KEY = "pfe-detection-fuites-iut-bandjoun-2024-cle-secrete"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 1440

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
