from fastapi import APIRouter, Depends, HTTPException
from database import get_connexion
from vanne_service import mettre_a_jour_statut_vanne, envoyer_commande_vanne
from security import obtenir_utilisateur_courant
from audit_service import journaliser

router = APIRouter()


@router.get("/api/vannes")
def get_vannes():
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nom, zone_id, capteur_id, statut, mode, derniere_action, actionneur
        FROM electrovannes
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "total": len(rows),
        "vannes": [
            {
                "id": r[0],
                "nom": r[1],
                "zone_id": r[2],
                "capteur_id": r[3],
                "statut": r[4],
                "mode": r[5],
                "derniere_action": str(r[6]) if r[6] else None,
                "actionneur": r[7],
            }
            for r in rows
        ],
    }


@router.post("/api/vannes/{vanne_id}/fermer")
def fermer_vanne(
    vanne_id: str,
    zone_id: str,
    utilisateur_courant=Depends(obtenir_utilisateur_courant),
):
    utilisateur = utilisateur_courant.get("email", "INCONNU")
    succes_mqtt = envoyer_commande_vanne(zone_id, "FERMER")
    succes_bd = mettre_a_jour_statut_vanne(vanne_id, "FERMEE", actionneur=utilisateur)

    if succes_bd:
        journaliser("FERMER_VANNE", "vanne", vanne_id, utilisateur, {"zone_id": zone_id, "mqtt": succes_mqtt})
        return {"message": "Vanne fermee avec succes", "vanne_id": vanne_id, "mqtt": succes_mqtt}
    raise HTTPException(status_code=500, detail="Erreur fermeture vanne")


@router.post("/api/vannes/{vanne_id}/ouvrir")
def ouvrir_vanne(
    vanne_id: str,
    zone_id: str,
    utilisateur_courant=Depends(obtenir_utilisateur_courant),
):
    utilisateur = utilisateur_courant.get("email", "INCONNU")
    succes_mqtt = envoyer_commande_vanne(zone_id, "OUVRIR")
    succes_bd = mettre_a_jour_statut_vanne(vanne_id, "OUVERTE", actionneur=utilisateur)

    if succes_bd:
        journaliser("OUVRIR_VANNE", "vanne", vanne_id, utilisateur, {"zone_id": zone_id, "mqtt": succes_mqtt})
        return {"message": "Vanne ouverte avec succes", "vanne_id": vanne_id, "mqtt": succes_mqtt}
    raise HTTPException(status_code=500, detail="Erreur ouverture vanne")


@router.post("/api/vannes/{vanne_id}/mode")
def changer_mode_vanne(
    vanne_id: str,
    nouveau_mode: str,
    utilisateur_courant=Depends(obtenir_utilisateur_courant),
):
    if nouveau_mode not in ["AUTO", "MANUEL"]:
        raise HTTPException(status_code=400, detail="Mode invalide (AUTO ou MANUEL)")

    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("UPDATE electrovannes SET mode = %s WHERE id = %s", (nouveau_mode, vanne_id))
    if cur.rowcount == 0:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Vanne non trouvee")
    conn.commit()
    cur.close()
    conn.close()

    journaliser(
        "CHANGER_MODE_VANNE",
        "vanne",
        vanne_id,
        utilisateur_courant.get("email", "INCONNU"),
        {"nouveau_mode": nouveau_mode},
    )
    return {"message": f"Mode change en {nouveau_mode}", "vanne_id": vanne_id}
