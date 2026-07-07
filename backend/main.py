# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from models import Zone, Capteur, Alerte, Utilisateur
from routes.capteurs import router as capteurs_router
from routes.zones import router as zones_router
from routes.alertes import router as alertes_router
from routes.vannes import router as vannes_router
from routes.auth import router as auth_router
from routes.audit import router as audit_router
from routes.users import router as users_router
from routes.simulation import router as simulation_router
from routes.diagnostic import router as diagnostic_router
from scheduler_service import demarrer_planificateur
from qrcode_service import generer_tous_qrcodes
import json
from mqtt_client import demarrer_client_thread 
from fastapi import Response
# ── Créer les tables ──────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Detection Fuites",
    description="IUT FV Bandjoun — PFE 2024-2025",
    version="3.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Gestionnaire de connexions WebSocket ──────────────────────────────────────
class GestionnaireConnexions:
    def __init__(self):
        self.connexions_actives = []

    async def connecter(self, websocket: WebSocket):
        await websocket.accept()
        self.connexions_actives.append(websocket)
        print(f"✅ Nouveau client WebSocket connecté. Total : {len(self.connexions_actives)}")

    def deconnecter(self, websocket: WebSocket):
        self.connexions_actives.remove(websocket)
        print(f"❌ Client WebSocket déconnecté. Total : {len(self.connexions_actives)}")

    async def diffuser(self, message: dict):
        for connexion in self.connexions_actives:
            try:
                await connexion.send_json(message)
            except Exception:
                pass

gestionnaire = GestionnaireConnexions()

# ── Endpoint WebSocket ────────────────────────────────────────────────────────
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await gestionnaire.connecter(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        gestionnaire.deconnecter(websocket)

# ── Inclure les routes ────────────────────────────────────────────────────────
app.include_router(capteurs_router)
app.include_router(zones_router)
app.include_router(alertes_router)
app.include_router(vannes_router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(users_router)
app.include_router(simulation_router)
app.include_router(diagnostic_router)

# ── Endpoints de base ─────────────────────────────────────────────────────────
@app.get("/")
def racine():
    return {"message": "API Detection Fuites operationnelle"}

@app.get("/api/test")
def test():
    return {
        "status": "ok",
        "message": "API operationnelle",
        "version": "3.0.0",
        "clients_connectes": len(gestionnaire.connexions_actives)
    }
@app.on_event("startup")
async def startup_event():
    demarrer_planificateur()
    generer_tous_qrcodes()
    demarrer_client_thread(gestionnaire)  # ← AJOUTER cette ligne
    print("✅ Tous les services démarrés !")
@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "healthy"}
