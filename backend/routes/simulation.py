from fastapi import APIRouter, Depends
from pydantic import BaseModel
from alert_service import verifier_et_alerter
from audit_service import journaliser
from mesure_service import enregistrer_mesure
from security import obtenir_utilisateur_courant

router = APIRouter()


class SimulationMesureRequest(BaseModel):
    capteur_id: str = "CAP_A1"
    gaz_ppm: float = 2800
    temp_c: float = 28
    hum: float = 60
    fuite_sol: bool = False
    niveau: str = "DANGER"


@router.post("/api/simulation/mesure")
async def simuler_mesure(
    donnees: SimulationMesureRequest,
    utilisateur=Depends(obtenir_utilisateur_courant),
):
    mesure = enregistrer_mesure(
        donnees.capteur_id,
        donnees.gaz_ppm,
        donnees.temp_c,
        donnees.hum,
        donnees.fuite_sol,
        donnees.niveau,
        source="SIMULATION",
    )

    normalise = {
        "device_id": donnees.capteur_id,
        "capteurs": {
            "mq2_ppm": donnees.gaz_ppm,
            "mq7_ppm": 0,
            "niveau_cuve_cm": 100,
            "fuite_sol": donnees.fuite_sol,
        },
    }
    alertes = verifier_et_alerter(normalise)

    try:
        from main import gestionnaire
        await gestionnaire.diffuser({
            "type": "mesure",
            "capteur_id": donnees.capteur_id,
            "gaz_ppm": donnees.gaz_ppm,
            "temp_c": donnees.temp_c,
            "hum": donnees.hum,
            "fuite_sol": donnees.fuite_sol,
            "niveau": donnees.niveau,
            "source": "SIMULATION",
        })
    except Exception as e:
        print(f"Simulation WebSocket non diffusee : {e}")

    journaliser(
        "SIMULER_MESURE",
        "capteur",
        donnees.capteur_id,
        utilisateur.get("email", "INCONNU"),
        {"mesure_id": mesure.get("id") if mesure else None, "alertes": alertes, **donnees.model_dump()},
    )
    return {"message": "Mesure simulee", "mesure_id": mesure.get("id") if mesure else None, "alertes": alertes}
