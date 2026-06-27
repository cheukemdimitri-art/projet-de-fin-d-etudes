# backend/scheduler_service.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from rapport_service import generer_rapport_mensuel

scheduler = BackgroundScheduler()


def tache_rapport_mensuel():
    print("Generation automatique du rapport mensuel...")
    chemin = generer_rapport_mensuel()
    if chemin:
        print(f"Rapport genere automatiquement : {chemin}")


def demarrer_planificateur():
    scheduler.add_job(
        tache_rapport_mensuel,
        CronTrigger(day=1, hour=8, minute=0),
        id="rapport_mensuel",
        name="Rapport Mensuel PDF",
        replace_existing=True
    )

    scheduler.start()
    print("Planificateur demarre !")
    print("   -> Rapport mensuel : 1er de chaque mois a 8h00")