"""Assistant IA de la clinique (fournisseur gratuit, API compatible OpenAI).

Fournisseurs pris en charge (variable ASSISTANT_PROVIDER) :
- groq    (défaut) : gratuit sans carte bancaire — clé sur https://console.groq.com/keys
- gemini           : offre gratuite Google AI Studio — clé sur https://aistudio.google.com/apikey
- openrouter       : modèles « :free » — clé sur https://openrouter.ai/keys
- ollama           : modèle local, 100 % gratuit et hors-ligne, aucune clé

L'assistant répond en s'appuyant sur des OUTILS en lecture seule qui
interrogent la base. Chaque outil est filtré selon le rôle de l'utilisateur :
un patient ne voit que ses propres données, seul l'admin voit les finances.
"""

import json
import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend import database

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-120b",
        "key_env": "GROQ_API_KEY",
        "label": "Groq",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-flash-latest",
        "key_env": "GEMINI_API_KEY",
        "label": "Google Gemini",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-oss-120b:free",
        "key_env": "OPENROUTER_API_KEY",
        "label": "OpenRouter",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1",
        "key_env": None,
        "label": "Ollama (local)",
    },
}

MAX_TOOL_ROUNDS = 6
MAX_HISTORY = 12


def configuration() -> dict:
    """Fournisseur, modèle et clé lus depuis l'environnement / le fichier .env."""
    provider = os.getenv("ASSISTANT_PROVIDER", "groq").strip().lower()
    preset = PROVIDERS.get(provider, PROVIDERS["groq"])
    key = os.getenv("ASSISTANT_API_KEY") or (os.getenv(preset["key_env"]) if preset["key_env"] else None)
    if provider == "ollama":
        key = key or "ollama"  # Ollama n'exige pas de clé, le SDK veut une valeur
    return {
        "provider": provider if provider in PROVIDERS else "groq",
        "label": preset["label"],
        "base_url": os.getenv("ASSISTANT_BASE_URL", preset["base_url"]),
        "model": os.getenv("ASSISTANT_MODEL", preset["model"]),
        "api_key": key,
    }


# ======================================================================
# OUTILS (lecture seule, filtrés par rôle)
# ======================================================================

def _nom(db: Session, user_id):
    u = db.query(database.Utilisateur).filter(database.Utilisateur.id == user_id).first()
    return u.nom_complet if u else "Inconnu"


def _patient_de_utilisateur(db: Session, user_id):
    return db.query(database.Patient).filter(database.Patient.id_utilisateur == user_id).first()


def outil_statistiques_clinique(db: Session, ctx: dict, **_):
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    rdvs = db.query(database.RendezVous).all()
    lits = db.query(database.Lit).all()
    return {
        "patients": db.query(database.Patient).count(),
        "medecins": db.query(database.Utilisateur).filter(database.Utilisateur.role == "medecin").count(),
        "rendez_vous_total": len(rdvs),
        "rendez_vous_aujourd_hui": sum(1 for r in rdvs if (r.date_heure or "").startswith(aujourd_hui)),
        "rendez_vous_en_attente": sum(1 for r in rdvs if r.statut == "en_attente"),
        "lits_total": len(lits),
        "lits_disponibles": sum(1 for l in lits if l.statut == "disponible"),
        "hospitalisations_en_cours": db.query(database.Hospitalisation)
        .filter(database.Hospitalisation.statut == "en_cours").count(),
    }


def outil_lister_rendez_vous(db: Session, ctx: dict, date: str = None, jours: int = 7, statut: str = None, **_):
    q = db.query(database.RendezVous)
    role, uid = ctx["role"], ctx["user_id"]
    if role == "medecin":
        q = q.filter(database.RendezVous.id_medecin == uid)
    elif role == "patient":
        patient = _patient_de_utilisateur(db, uid)
        if not patient:
            return {"erreur": "Dossier patient introuvable."}
        q = q.filter(database.RendezVous.id_patient == patient.id)
    if statut:
        q = q.filter(database.RendezVous.statut == statut)

    rdvs = q.all()
    if date:
        rdvs = [r for r in rdvs if (r.date_heure or "").startswith(date)]
    else:
        debut = datetime.now()
        fin = debut + timedelta(days=max(1, min(int(jours or 7), 90)))
        rdvs = [r for r in rdvs if r.date_heure and debut.strftime("%Y-%m-%d") <= r.date_heure[:10] <= fin.strftime("%Y-%m-%d")]

    rdvs.sort(key=lambda r: r.date_heure or "")
    resultat = []
    for r in rdvs[:30]:
        patient = db.query(database.Patient).filter(database.Patient.id == r.id_patient).first()
        resultat.append({
            "id": r.id, "date_heure": r.date_heure, "statut": r.statut, "motif": r.motif, "salle": r.salle,
            "patient": _nom(db, patient.id_utilisateur) if patient else "Inconnu",
            "medecin": _nom(db, r.id_medecin),
        })
    return {"nombre": len(rdvs), "rendez_vous": resultat}


def outil_rechercher_patients(db: Session, ctx: dict, nom: str = "", **_):
    q = db.query(database.Patient, database.Utilisateur).join(
        database.Utilisateur, database.Utilisateur.id == database.Patient.id_utilisateur)
    if nom:
        q = q.filter(database.Utilisateur.nom_complet.ilike(f"%{nom}%"))
    return {"patients": [
        {"id_patient": p.id, "nom": u.nom_complet, "telephone": p.telephone, "date_naissance": p.date_naissance}
        for p, u in q.limit(20).all()
    ]}


def outil_dossier_patient(db: Session, ctx: dict, patient_id: int = None, **_):
    if ctx["role"] == "patient":  # un patient ne lit que SON dossier
        patient = _patient_de_utilisateur(db, ctx["user_id"])
    else:
        patient = db.query(database.Patient).filter(database.Patient.id == patient_id).first()
    if not patient:
        return {"erreur": "Patient introuvable."}

    consultations = db.query(database.Consultation).filter(database.Consultation.id_patient == patient.id) \
        .order_by(database.Consultation.date_consultation.desc()).limit(5).all()
    ordonnances = db.query(database.Ordonnance).filter(database.Ordonnance.id_patient == patient.id) \
        .order_by(database.Ordonnance.date_prescription.desc()).limit(5).all()
    predictions = db.query(database.Prediction).filter(database.Prediction.id_patient == patient.id) \
        .order_by(database.Prediction.date_prediction.desc()).limit(5).all()
    mesures = db.query(database.MesureConstante).filter(database.MesureConstante.id_patient == patient.id) \
        .order_by(database.MesureConstante.date_mesure.desc()).limit(5).all()
    return {
        "patient": {"id": patient.id, "nom": _nom(db, patient.id_utilisateur),
                    "date_naissance": patient.date_naissance, "antecedents": patient.antecedents},
        "consultations": [{"date": c.date_consultation, "diagnostic": c.diagnostic, "traitement": c.traitement}
                          for c in consultations],
        "ordonnances": [{"date": o.date_prescription, "medicaments": o.medicaments, "posologie": o.posologie}
                        for o in ordonnances],
        "predictions_ia": [{"date": p.date_prediction, "maladie": p.maladie, "probabilite": round(p.probabilite, 3)}
                           for p in predictions],
        "constantes": [{"date": str(m.date_mesure), "tension": f"{m.tension_systolique}/{m.tension_diastolique}",
                        "frequence_cardiaque": m.frequence_cardiaque, "temperature": m.temperature,
                        "saturation_o2": m.saturation_oxygene} for m in mesures],
    }


def outil_alertes_pharmacie(db: Session, ctx: dict, **_):
    meds = db.query(database.Medicament).all()
    alertes = [m for m in meds if (m.stock_actuel or 0) <= (m.seuil_alerte or 0)]
    limite = datetime.now() + timedelta(days=60)
    perimes = [m for m in meds if m.date_peremption and m.date_peremption <= limite]
    return {
        "stock_faible": [{"nom": m.nom, "stock": m.stock_actuel, "seuil": m.seuil_alerte} for m in alertes],
        "peremption_sous_60_jours": [{"nom": m.nom, "date": str(m.date_peremption)[:10]} for m in perimes],
        "total_medicaments": len(meds),
    }


def outil_resume_financier(db: Session, ctx: dict, **_):
    factures = db.query(database.Facture).all()
    depenses = db.query(database.Depense).all()
    total_facture = sum(float(f.montant or 0) for f in factures)
    encaisse = sum(float(f.montant or 0) for f in factures if f.statut_paiement in ("payé", "payee", "payée"))
    total_depenses = sum(float(d.montant or 0) for d in depenses)
    return {
        "devise": "TND", "factures": len(factures), "montant_facture": round(total_facture, 2),
        "montant_encaisse": round(encaisse, 2), "impayes": round(total_facture - encaisse, 2),
        "depenses": round(total_depenses, 2), "solde": round(encaisse - total_depenses, 2),
    }


def outil_disponibilite_lits(db: Session, ctx: dict, **_):
    resultat = []
    for s in db.query(database.ServiceMedical).all():
        lits = [l for salle in s.salles for l in salle.lits]
        resultat.append({"service": s.nom, "lits": len(lits),
                         "disponibles": sum(1 for l in lits if l.statut == "disponible")})
    return {"services": resultat}


def outil_liste_medecins(db: Session, ctx: dict, specialite: str = None, **_):
    q = db.query(database.Utilisateur).filter(database.Utilisateur.role == "medecin")
    if specialite:
        q = q.filter(database.Utilisateur.specialite.ilike(f"%{specialite}%"))
    return {"medecins": [{"id": m.id, "nom": m.nom_complet, "specialite": m.specialite, "bureau": m.bureau}
                         for m in q.all()]}


TOUS = {"admin", "medecin", "secretaire", "patient"}
PERSONNEL = {"admin", "medecin", "secretaire"}

# nom -> (fonction, rôles autorisés, description, paramètres JSON Schema)
OUTILS = {
    "statistiques_clinique": (outil_statistiques_clinique, PERSONNEL,
        "Chiffres clés de la clinique : patients, rendez-vous du jour, lits, hospitalisations.", {}),
    "lister_rendez_vous": (outil_lister_rendez_vous, TOUS,
        "Liste les rendez-vous (ceux du médecin ou du patient connecté le cas échéant). "
        "Par défaut : les 7 prochains jours.",
        {"date": {"type": "string", "description": "Jour précis AAAA-MM-JJ (optionnel)"},
         "jours": {"type": "integer", "description": "Nombre de jours à venir si pas de date (défaut 7)"},
         "statut": {"type": "string", "enum": ["en_attente", "confirmé", "terminé", "annulé"]}}),
    "rechercher_patients": (outil_rechercher_patients, PERSONNEL,
        "Recherche des patients par nom (renvoie leur identifiant).",
        {"nom": {"type": "string", "description": "Nom ou partie du nom"}}),
    "dossier_patient": (outil_dossier_patient, {"admin", "medecin", "patient"},
        "Résumé du dossier médical : antécédents, consultations, ordonnances, prédictions IA, constantes.",
        {"patient_id": {"type": "integer", "description": "Identifiant du patient (ignoré pour un patient connecté)"}}),
    "alertes_pharmacie": (outil_alertes_pharmacie, {"admin", "medecin"},
        "Médicaments en stock faible ou proches de la péremption.", {}),
    "resume_financier": (outil_resume_financier, {"admin"},
        "Synthèse financière : facturé, encaissé, impayés, dépenses, solde.", {}),
    "disponibilite_lits": (outil_disponibilite_lits, PERSONNEL,
        "Lits disponibles par service médical.", {}),
    "liste_medecins": (outil_liste_medecins, TOUS,
        "Annuaire des médecins, filtrable par spécialité.",
        {"specialite": {"type": "string"}}),
}


def _definitions_outils(role: str):
    return [
        {"type": "function", "function": {
            "name": nom, "description": desc,
            "parameters": {"type": "object", "properties": params, "required": []},
        }}
        for nom, (_, roles, desc, params) in OUTILS.items() if role in roles
    ]


def _executer_outil(db: Session, ctx: dict, nom: str, arguments: str):
    if nom not in OUTILS or ctx["role"] not in OUTILS[nom][1]:
        return {"erreur": f"Outil « {nom} » non autorisé pour le rôle {ctx['role']}."}
    try:
        args = json.loads(arguments or "{}")
        if not isinstance(args, dict):
            args = {}
    except json.JSONDecodeError:
        return {"erreur": "Arguments JSON invalides."}
    try:
        return OUTILS[nom][0](db, ctx, **args)
    except Exception as e:  # un outil défaillant ne doit pas casser la conversation
        return {"erreur": f"Échec de l'outil : {e}"}


SYSTEM_PROMPT = """Tu es l'assistant IA de la Clinique Santé+ (Mahdia, Tunisie).
Utilisateur connecté : {nom} — rôle : {role}. Date du jour : {date}.

Règles :
- Réponds en français (ou dans la langue de l'utilisateur), de façon concise et structurée.
- Pour toute question sur les données de la clinique, utilise les outils : n'invente jamais
  de chiffres, de noms ni de rendez-vous. Si un outil ne renvoie rien, dis-le.
- Tu peux aussi aider à rédiger (courriers, comptes rendus, rappels) et expliquer l'application.
- Tu n'es pas médecin : pour toute question de santé, donne des informations générales
  et recommande de consulter un professionnel. Les probabilités IA ne sont pas un diagnostic.
- Montants en TND. Les données marquées [TEST] sont fictives."""


def discuter(db: Session, messages: list, user_id: int, role: str) -> dict:
    """Envoie la conversation au modèle, exécute les outils demandés, renvoie la réponse."""
    cfg = configuration()
    if not cfg["api_key"]:
        return {"erreur": "non_configure", "message": (
            "Assistant non configuré : ajoutez une clé API gratuite dans le fichier .env "
            "(par ex. GROQ_API_KEY=...) puis redémarrez l'API. Voir le README.")}

    from openai import OpenAI, APIConnectionError, APIStatusError, AuthenticationError, \
        NotFoundError, RateLimitError

    ctx = {"user_id": user_id, "role": role}
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"], timeout=60, max_retries=1)
    conversation = [{"role": "system", "content": SYSTEM_PROMPT.format(
        nom=_nom(db, user_id), role=role, date=datetime.now().strftime("%A %d/%m/%Y"))}]
    for m in messages[-MAX_HISTORY:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            conversation.append({"role": m["role"], "content": str(m["content"])[:4000]})

    outils = _definitions_outils(role)
    outils_utilises = []
    try:
        for _ in range(MAX_TOOL_ROUNDS):
            reponse = client.chat.completions.create(
                model=cfg["model"], messages=conversation, tools=outils or None,
                tool_choice="auto" if outils else None, temperature=0.2, max_tokens=1500,
            )
            message = reponse.choices[0].message
            appels = message.tool_calls or []
            if not appels:
                return {"reponse": message.content or "", "outils": outils_utilises,
                        "modele": f"{cfg['label']} · {cfg['model']}"}

            conversation.append({
                "role": "assistant", "content": message.content or "",
                "tool_calls": [{"id": a.id, "type": "function",
                                "function": {"name": a.function.name, "arguments": a.function.arguments}}
                               for a in appels],
            })
            for appel in appels:
                outils_utilises.append(appel.function.name)
                resultat = _executer_outil(db, ctx, appel.function.name, appel.function.arguments)
                conversation.append({"role": "tool", "tool_call_id": appel.id,
                                     "content": json.dumps(resultat, ensure_ascii=False, default=str)})
        return {"reponse": "Je n'ai pas pu terminer : trop d'appels d'outils. Reformulez la question.",
                "outils": outils_utilises}
    except AuthenticationError:
        return {"erreur": "auth", "message": "Clé API refusée par le fournisseur : vérifiez-la dans .env."}
    except RateLimitError:
        return {"erreur": "quota", "message": "Quota gratuit atteint chez le fournisseur : réessayez dans une minute."}
    except NotFoundError:
        return {"erreur": "modele", "message": (
            f"Modèle « {cfg['model']} » introuvable chez {cfg['label']} : choisissez-en un autre "
            "avec ASSISTANT_MODEL dans .env.")}
    except APIConnectionError:
        return {"erreur": "connexion", "message": f"Impossible de joindre {cfg['label']} ({cfg['base_url']})."}
    except APIStatusError as e:
        return {"erreur": "api", "message": f"Erreur du fournisseur ({e.status_code}) : {str(e)[:300]}"}
