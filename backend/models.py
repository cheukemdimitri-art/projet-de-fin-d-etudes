# backend/models.py
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func
from database import Base

# ── Table Zone ────────────────────────────────────────────────────────────────
class Zone(Base):
    __tablename__ = "zones"

    id            = Column(String, primary_key=True)
    nom           = Column(String, nullable=False)
    description   = Column(String)
    superficie    = Column(Float)
    coord_x       = Column(Float, default=0)
    coord_y       = Column(Float, default=0)
    date_creation = Column(DateTime, server_default=func.now())

# ── Table Capteur ─────────────────────────────────────────────────────────────
class Capteur(Base):
    __tablename__ = "capteurs"

    id                = Column(String, primary_key=True)
    nom               = Column(String, nullable=False)
    type              = Column(String, nullable=False)
    zone_id           = Column(String, ForeignKey("zones.id"))
    actif             = Column(Boolean, default=True)
    seuil_warning     = Column(Float, default=1500)
    seuil_danger      = Column(Float, default=2500)
    seuil_critique    = Column(Float, default=3500)
    derniere_valeur   = Column(Float, default=0)
    date_installation = Column(DateTime, server_default=func.now())

# ── Table Alerte ──────────────────────────────────────────────────────────────
class Alerte(Base):
    __tablename__ = "alertes"

    id                = Column(String, primary_key=True)
    niveau            = Column(String, nullable=False)
    message           = Column(String)
    capteur_id        = Column(String, ForeignKey("capteurs.id"))
    acquittee         = Column(Boolean, default=False)
    commentaire       = Column(String)
    date_detection    = Column(DateTime, server_default=func.now())
    date_acquittement = Column(DateTime)

# ── Table Utilisateur ─────────────────────────────────────────────────────────
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id            = Column(String, primary_key=True)
    nom           = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    mot_de_passe  = Column(String, nullable=False)
    role          = Column(String, default="OPERATEUR")
    actif         = Column(Boolean, default=True)
    date_creation = Column(DateTime, server_default=func.now())
    # ── Table Electrovanne ────────────────────────────────────────────────────────
class Electrovanne(Base):
    __tablename__ = "electrovannes"

    id              = Column(String, primary_key=True)
    nom             = Column(String, nullable=False)
    zone_id         = Column(String, ForeignKey("zones.id"))
    capteur_id      = Column(String, ForeignKey("capteurs.id"))
    statut          = Column(String, default="OUVERTE")
    mode            = Column(String, default="AUTO")
    derniere_action = Column(DateTime, server_default=func.now())
    actionneur      = Column(String)


class MesureCapteur(Base):
    __tablename__ = "mesures_capteurs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    capteur_id  = Column(String, ForeignKey("capteurs.id"), index=True)
    gaz_ppm     = Column(Float, default=0)
    temp_c      = Column(Float, default=0)
    hum         = Column(Float, default=0)
    fuite_sol   = Column(Boolean, default=False)
    niveau      = Column(String, default="NORMAL")
    source      = Column(String, default="MQTT")
    date_mesure = Column(DateTime, server_default=func.now(), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur = Column(String, default="SYSTEME", index=True)
    action      = Column(String, nullable=False, index=True)
    cible_type  = Column(String, default="")
    cible_id    = Column(String, default="", index=True)
    details     = Column(Text)
    date_action = Column(DateTime, server_default=func.now(), index=True)


class PushToken(Base):
    __tablename__ = "push_tokens"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id      = Column(String, ForeignKey("utilisateurs.id"), index=True)
    token               = Column(Text, unique=True, nullable=False)
    plateforme          = Column(String, default="android")
    actif               = Column(Boolean, default=True, index=True)
    date_enregistrement = Column(DateTime, server_default=func.now())
    derniere_activite   = Column(DateTime, server_default=func.now(), onupdate=func.now())
