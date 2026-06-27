# backend/rapport_service.py
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Table, TableStyle, HRFlowable
from database import SessionLocal
from models import Alerte, Capteur, Zone


def generer_rapport_mensuel():
    db = SessionLocal()
    try:
        maintenant = datetime.utcnow()
        debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = maintenant

        print(f"Generation rapport : {debut_mois} a {fin_mois}")

        alertes = db.query(Alerte).filter(
            Alerte.date_detection >= debut_mois,
            Alerte.date_detection <= fin_mois
        ).all()

        capteurs = db.query(Capteur).all()
        zones = db.query(Zone).all()

        total_alertes = len(alertes)
        alertes_warning = len([a for a in alertes if a.niveau == "WARNING"])
        alertes_danger = len([a for a in alertes if a.niveau == "DANGER"])
        alertes_critique = len([a for a in alertes if a.niveau == "CRITIQUE"])
        alertes_acquit = len([a for a in alertes if a.acquittee])
        taux_acquit = (alertes_acquit / total_alertes * 100) if total_alertes > 0 else 100

        nom_fichier = f"rapport_mensuel_{maintenant.strftime('%Y_%m')}.pdf"
        chemin = os.path.join(os.getcwd(), nom_fichier)

        doc = SimpleDocTemplate(chemin, pagesize=A4,
                                 topMargin=2*cm, bottomMargin=2*cm,
                                 leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        contenu = []

        titre_style = ParagraphStyle(
            "titre", parent=styles["Title"], fontSize=20,
            textColor=colors.HexColor("#1F3864"), spaceAfter=10,
        )
        sous_titre_style = ParagraphStyle(
            "sous_titre", parent=styles["Heading2"], fontSize=14,
            textColor=colors.HexColor("#2E75B6"), spaceBefore=15, spaceAfter=8,
        )

        contenu.append(Paragraph("RAPPORT MENSUEL DE SURVEILLANCE", titre_style))
        contenu.append(Paragraph("Systeme de Detection et Alertes de Fuites", sous_titre_style))
        contenu.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E75B6")))
        contenu.append(Spacer(1, 0.5*cm))

        contenu.append(Paragraph("Informations Generales", sous_titre_style))
        info_data = [
            ["Etablissement", "IUT Fotso Victor de Bandjoun"],
            ["Periode", f"{debut_mois.strftime('%d/%m/%Y')} au {fin_mois.strftime('%d/%m/%Y')}"],
            ["Date generation", maintenant.strftime("%d/%m/%Y a %H:%M")],
            ["Nombre de zones", str(len(zones))],
            ["Nombre de capteurs", str(len(capteurs))],
        ]
        tableau_info = Table(info_data, colWidths=[6*cm, 11*cm])
        tableau_info.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D6E4F0")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        contenu.append(tableau_info)
        contenu.append(Spacer(1, 0.5*cm))

        contenu.append(Paragraph("Statistiques des Alertes", sous_titre_style))
        stats_data = [
            ["Indicateur", "Valeur"],
            ["Total alertes", str(total_alertes)],
            ["Alertes WARNING", str(alertes_warning)],
            ["Alertes DANGER", str(alertes_danger)],
            ["Alertes CRITIQUE", str(alertes_critique)],
            ["Alertes acquittees", str(alertes_acquit)],
            ["Taux d'acquittement", f"{taux_acquit:.1f}%"],
        ]
        tableau_stats = Table(stats_data, colWidths=[8*cm, 9*cm])
        tableau_stats.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        contenu.append(tableau_stats)
        contenu.append(Spacer(1, 0.5*cm))

        contenu.append(Paragraph("Etat des Capteurs", sous_titre_style))
        capteurs_data = [["ID", "Nom", "Type", "Zone", "Statut"]]
        for c in capteurs:
            capteurs_data.append([
                c.id, c.nom, c.type, c.zone_id or "-",
                "Actif" if c.actif else "Inactif",
            ])
        tableau_capteurs = Table(capteurs_data, colWidths=[3*cm, 4*cm, 3.5*cm, 3.5*cm, 3*cm])
        tableau_capteurs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#375623")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        contenu.append(tableau_capteurs)
        contenu.append(Spacer(1, 0.5*cm))

        contenu.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E75B6")))
        contenu.append(Spacer(1, 0.3*cm))

        if alertes_critique == 0 and alertes_danger == 0:
            conclusion = "Le systeme a fonctionne normalement ce mois."
            couleur_conc = colors.HexColor("#375623")
        elif alertes_critique > 0:
            conclusion = "Des alertes critiques ont ete detectees. Revision recommandee."
            couleur_conc = colors.red
        else:
            conclusion = "Des alertes ont ete detectees. Surveillance renforcee conseillee."
            couleur_conc = colors.orange

        conc_style = ParagraphStyle(
            "conclusion", parent=styles["Normal"], fontSize=11,
            textColor=couleur_conc, fontName="Helvetica-Bold",
        )
        contenu.append(Paragraph(conclusion, conc_style))

        doc.build(contenu)
        print(f"Rapport PDF genere : {nom_fichier}")
        return chemin

    except Exception as e:
        print(f"Erreur generation rapport : {e}")
        return None
    finally:
        db.close()


def generer_rapport_incident(alerte_id: str):
    db = SessionLocal()
    try:
        alerte = db.query(Alerte).filter(Alerte.id == alerte_id).first()

        if not alerte:
            print(f"Alerte {alerte_id} non trouvee")
            return None

        capteur = db.query(Capteur).filter(Capteur.id == alerte.capteur_id).first()

        nom_fichier = f"rapport_incident_{alerte_id[:8]}.pdf"
        chemin = os.path.join(os.getcwd(), nom_fichier)

        doc = SimpleDocTemplate(chemin, pagesize=A4,
                                 topMargin=2*cm, bottomMargin=2*cm,
                                 leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        contenu = []

        titre_style = ParagraphStyle("titre", parent=styles["Title"], fontSize=18,
                                      textColor=colors.HexColor("#C00000"))

        contenu.append(Paragraph("RAPPORT D'INCIDENT", titre_style))
        contenu.append(Spacer(1, 0.5*cm))

        details = [
            ["Niveau d'alerte", alerte.niveau],
            ["Capteur concerne", f"{capteur.nom if capteur else alerte.capteur_id}"],
            ["Message", alerte.message or "-"],
            ["Date de detection", str(alerte.date_detection)],
            ["Acquittee", "Oui" if alerte.acquittee else "Non"],
            ["Commentaire operateur", alerte.commentaire or "-"],
            ["Date d'acquittement", str(alerte.date_acquittement) if alerte.date_acquittement else "-"],
        ]
        tableau = Table(details, colWidths=[6*cm, 11*cm])
        tableau.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D6E4F0")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        contenu.append(tableau)

        doc.build(contenu)
        print(f"Rapport d'incident genere : {nom_fichier}")
        return chemin

    except Exception as e:
        print(f"Erreur generation rapport incident : {e}")
        return None
    finally:
        db.close()