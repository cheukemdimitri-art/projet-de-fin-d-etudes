import json
from database import SessionLocal
from models import AuditLog


def journaliser(action, cible_type="", cible_id="", utilisateur="SYSTEME", details=None):
    db = SessionLocal()
    try:
        audit = AuditLog(
            utilisateur=utilisateur or "SYSTEME",
            action=action,
            cible_type=cible_type or "",
            cible_id=cible_id or "",
            details=json.dumps(details or {}, ensure_ascii=False),
        )
        db.add(audit)
        db.commit()
        return audit.id
    except Exception as e:
        print(f"Erreur audit {action}: {e}")
        db.rollback()
        return None
    finally:
        db.close()
