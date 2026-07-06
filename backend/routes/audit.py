import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import AuditLog
from security import obtenir_utilisateur_courant, verifier_role_admin

router = APIRouter()


@router.get("/api/audit")
def get_audit(
    limite: int = 100,
    db: Session = Depends(get_db),
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    verifier_role_admin(utilisateur)
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.date_action.desc())
        .limit(max(1, min(limite, 500)))
        .all()
    )
    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "utilisateur": log.utilisateur,
                "action": log.action,
                "cible_type": log.cible_type,
                "cible_id": log.cible_id,
                "details": json.loads(log.details or "{}"),
                "date_action": str(log.date_action),
            }
            for log in logs
        ],
    }
