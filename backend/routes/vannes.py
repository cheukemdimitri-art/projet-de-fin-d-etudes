# backend/routes/vannes.py
from fastapi import APIRouter, HTTPException
from database import get_connexion
from vanne_service import mettre_a_jour_statut_vanne, envoyer_commande_vanne

router = APIRouter()

# ── GET /api/vannes — Liste toutes les électrovannes ─────────────────────────
@router.get("/api/vannes")
def get_vannes():
    conn = get_connexion()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, nom, zone_id, capteur_id, statut, mode, derniere_action
        FROM electrovannes
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "total": len(rows),
        "vannes": [
            {
                "id":              r[0],
                "nom":             r[1],
                "zone_id":         r[2],
                "capteur_id":      r[3],
                "statut":          r[4],
                "mode":            r[5],
                "derniere_action": str(r[6]),
            }
            for r in rows
        ]
    }

# ── POST /api/vannes/{id}/fermer — Fermeture manuelle ─────────────────────────
@router.post("/api/vannes/{vanne_id}/fermer")
def fermer_vanne(vanne_id: str, zone_id: str, utilisateur: str = "OPERATEUR"):
    succes_mqtt = envoyer_commande_vanne(zone_id, "FERMER")
    succes_bd   = mettre_a_jour_statut_vanne(vanne_id, "FERMEE", actionneur=utilisateur)

    if succes_bd:
        return {"message": "Vanne fermée avec succès", "vanne_id": vanne_id}
    raise HTTPException(status_code=500, detail="Erreur fermeture vanne")

# ── POST /api/vannes/{id}/ouvrir — Réouverture manuelle ───────────────────────
@router.post("/api/vannes/{vanne_id}/ouvrir")
def ouvrir_vanne(vanne_id: str, zone_id: str, utilisateur: str = "OPERATEUR"):
    succes_mqtt = envoyer_commande_vanne(zone_id, "OUVRIR")
    succes_bd   = mettre_a_jour_statut_vanne(vanne_id, "OUVERTE", actionneur=utilisateur)

    if succes_bd:
        return {"message": "Vanne ouverte avec succès", "vanne_id": vanne_id}
    raise HTTPException(status_code=500, detail="Erreur ouverture vanne")

# ── POST /api/vannes/{id}/mode — Changer AUTO/MANUEL ──────────────────────────
@router.post("/api/vannes/{vanne_id}/mode")
def changer_mode_vanne(vanne_id: str, nouveau_mode: str):
    if nouveau_mode not in ["AUTO", "MANUEL"]:
        raise HTTPException(status_code=400, detail="Mode invalide (AUTO ou MANUEL)")

    conn = get_connexion()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE electrovannes SET mode = %s WHERE id = %s
    """, (nouveau_mode, vanne_id))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": f"Mode changé en {nouveau_mode}", "vanne_id": vanne_id}