from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Zone

router = APIRouter()

@router.get("/api/zones")
def get_zones(db: Session = Depends(get_db)):
    zones = db.query(Zone).all()
    return {
        "total": len(zones),
        "zones": [
            {
                "id": z.id,
                "nom": z.nom,
                "description": z.description,
                "superficie": z.superficie,
            }
            for z in zones
        ]
    }