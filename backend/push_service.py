import json
import os

from database import get_connexion

_firebase_ready = False


def _init_firebase():
    global _firebase_ready
    if _firebase_ready:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _firebase_ready = True
            return True

        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if service_account_json:
            info = json.loads(service_account_json)
            cred = credentials.Certificate(info)
        elif credentials_path:
            cred = credentials.Certificate(credentials_path)
        else:
            print("FCM non configure: FIREBASE_SERVICE_ACCOUNT_JSON ou FIREBASE_CREDENTIALS_PATH manquant")
            return False

        firebase_admin.initialize_app(cred)
        _firebase_ready = True
        return True
    except Exception as exc:
        print(f"Erreur initialisation FCM: {exc}")
        return False


def _tokens_actifs():
    conn = None
    try:
        conn = get_connexion()
        cur = conn.cursor()
        cur.execute("SELECT token FROM push_tokens WHERE actif = true")
        tokens = [row[0] for row in cur.fetchall()]
        cur.close()
        return tokens
    except Exception as exc:
        print(f"Erreur lecture tokens FCM: {exc}")
        return []
    finally:
        if conn:
            conn.close()


def envoyer_push_alerte(niveau, message, capteur_id, alerte_id=None):
    if not _init_firebase():
        return {"sent": 0, "failed": 0, "configured": False}

    tokens = _tokens_actifs()
    if not tokens:
        return {"sent": 0, "failed": 0, "configured": True}

    from firebase_admin import messaging

    title = f"PURECONTROL - Alerte {niveau}"
    body = message or f"Capteur {capteur_id}: intervention requise."
    data = {
        "type": "ALERTE_CAPTEUR",
        "title": title,
        "body": body,
        "niveau": str(niveau or ""),
        "capteur_id": str(capteur_id or ""),
        "alerte_id": str(alerte_id or ""),
        "persistent": "true" if niveau in ["DANGER", "CRITIQUE"] else "false",
    }

    message_fcm = messaging.MulticastMessage(
        tokens=tokens,
        data=data,
        android=messaging.AndroidConfig(
            priority="high",
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message_fcm)
        _desactiver_tokens_invalides(tokens, response.responses)
        print(f"FCM envoye: {response.success_count} ok, {response.failure_count} echec")
        return {
            "sent": response.success_count,
            "failed": response.failure_count,
            "configured": True,
        }
    except Exception as exc:
        print(f"Erreur envoi FCM: {exc}")
        return {"sent": 0, "failed": len(tokens), "configured": True}


def _desactiver_tokens_invalides(tokens, responses):
    invalides = []
    for token, response in zip(tokens, responses):
        if response.success:
            continue
        code = getattr(response.exception, "code", "")
        if code in {"registration-token-not-registered", "invalid-registration-token"}:
            invalides.append(token)

    if not invalides:
        return

    conn = None
    try:
        conn = get_connexion()
        cur = conn.cursor()
        cur.execute(
            "UPDATE push_tokens SET actif = false WHERE token = ANY(%s)",
            (invalides,),
        )
        conn.commit()
        cur.close()
    except Exception as exc:
        print(f"Erreur desactivation tokens FCM: {exc}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
