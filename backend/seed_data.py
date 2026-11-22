
import random
from datetime import datetime, timedelta
from decimal import Decimal

from backend import database
from backend.config import DEMO_PASSWORD
from backend.security import hacher_mot_de_passe

# =====================================================
# CONFIGURATION
# =====================================================

random.seed(2026)

MARQUEUR = "[TEST]"

PRENOMS = [
    "Mohamed", "Ahmed", "Youssef", "Amine",
    "Sami", "Oussama", "Khalil", "Fares",
    "Mariem", "Amira", "Ines", "Fatma",
    "Nour", "Rania", "Sarra", "Aya",
    "Meriem", "Hiba", "Yasmine", "Eya"
]

NOMS = [
    "Ben Salah", "Trabelsi", "Gharbi", "Ben Amor",
    "Mansouri", "Jaziri", "Bouazizi", "Khelifi",
    "Haddad", "Mejri", "Chaabane", "Dridi",
    "Saidi", "Ayari", "Bouzid", "Hamdi"
]

SPECIALITES = [
    "Cardiologue",
    "Généraliste",
    "Dermatologue",
    "Pédiatre",
    "Neurologue",
    "Gynécologue"
]


def date_texte(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def nom_arabe():
    return f"{random.choice(PRENOMS)} {random.choice(NOMS)}"


def ajouter_si_absent(db, modele, filtre, objet):
    """Ajoute un objet seulement s'il n'existe pas déjà."""
    existe = db.query(modele).filter(filtre).first()

    if existe:
        return existe, False

    db.add(objet)
    db.flush()
    return objet, True


# =====================================================
# 1. UTILISATEURS ET PATIENTS DE DEMONSTRATION
# =====================================================

# Comptes affichés dans l'onglet « Accès Rapide Démo » de frontend/app.py.
# Ils doivent exister en base : l'accès démo passe par la vraie route /login.
COMPTES_DEMO = [
    {"email": "admin@clinique.com", "role": "admin", "nom_complet": "Administrateur Central"},
    {"email": "dr.martin@clinique.com", "role": "medecin", "nom_complet": "Dr. Martin",
     "specialite": "Cardiologue", "bureau": "Bureau 101", "telephone": "73680101"},
    {"email": "secretaire@clinique.com", "role": "secretaire", "nom_complet": "Sophie Secrétaire"},
    {"email": "jean.dupont@email.com", "role": "patient", "nom_complet": "Jean Dupont",
     "telephone": "22123456"},
]


def creer_comptes_demo(db):
    """Crée les comptes de démonstration (mot de passe : CLINIQUE_DEMO_PASSWORD)."""
    medecin_demo, patient_demo = None, None

    for compte in COMPTES_DEMO:
        user = db.query(database.Utilisateur).filter_by(email=compte["email"]).first()
        if not user:
            user = database.Utilisateur(
                mot_de_passe=hacher_mot_de_passe(DEMO_PASSWORD), **compte
            )
            db.add(user)
            db.flush()

        if user.role == "medecin":
            medecin_demo = user
        elif user.role == "patient":
            patient = db.query(database.Patient).filter_by(id_utilisateur=user.id).first()
            if not patient:
                patient = database.Patient(
                    id_utilisateur=user.id,
                    date_naissance="1972-04-15",
                    telephone=user.telephone or "20000000",
                    antecedents=f"{MARQUEUR} Hypertension familiale",
                )
                db.add(patient)
                db.flush()
            patient_demo = patient

    return medecin_demo, patient_demo


def creer_utilisateurs_patients(db):
    medecin_demo, patient_demo = creer_comptes_demo(db)
    medecins = [medecin_demo]
    patients = [patient_demo]

    # Deux médecins fictifs avec des noms tunisiens
    for i in range(1, 3):
        email = f"medecin.test.arabe{i}@clinique.com"

        user = db.query(database.Utilisateur).filter_by(
            email=email
        ).first()

        if not user:
            user = database.Utilisateur(
                email=email,
                mot_de_passe=hacher_mot_de_passe("TestClinique2026!"),
                role="medecin",
                nom_complet="Dr. " + nom_arabe(),
                specialite=random.choice(SPECIALITES),
                bureau=f"Salle TEST-{100 + i}",
                telephone=f"20{random.randint(100000, 999999)}"
            )
            db.add(user)
            db.flush()

        medecins.append(user)

    # Huit patients fictifs avec des noms tunisiens
    for i in range(1, 9):
        email = f"patient.test.arabe{i}@clinique.com"

        user = db.query(database.Utilisateur).filter_by(
            email=email
        ).first()

        if not user:
            user = database.Utilisateur(
                email=email,
                mot_de_passe=hacher_mot_de_passe("TestClinique2026!"),
                role="patient",
                nom_complet=nom_arabe(),
                telephone=f"21{random.randint(100000, 999999)}"
            )
            db.add(user)
            db.flush()

        patient = db.query(database.Patient).filter_by(
            id_utilisateur=user.id
        ).first()

        if not patient:
            annee = random.randint(1960, 2002)
            mois = random.randint(1, 12)
            jour = random.randint(1, 28)

            patient = database.Patient(
                id_utilisateur=user.id,
                date_naissance=f"{annee}-{mois:02d}-{jour:02d}",
                telephone=user.telephone or "20000000",
                antecedents=f"{MARQUEUR} Dossier fictif de démonstration"
            )
            db.add(patient)
            db.flush()

        patients.append(patient)

    db.flush()
    return medecins, patients


# =====================================================
# 2. RENDEZ-VOUS DE DEMONSTRATION
# =====================================================

def creer_rendez_vous(db, medecins, patients):
    rendez_vous = db.query(database.RendezVous).filter(
        database.RendezVous.motif.like(f"%{MARQUEUR}%")
    ).all()

    if rendez_vous:
        return rendez_vous

    motifs = [
        f"{MARQUEUR} Consultation de démonstration",
        f"{MARQUEUR} Suivi fictif",
        f"{MARQUEUR} Visite de contrôle simulée",
        f"{MARQUEUR} Bilan de démonstration"
    ]

    for i in range(16):
        medecin = random.choice(medecins)
        patient = random.choice(patients)

        date_rdv = datetime.now() + timedelta(
            days=random.randint(-75, 45),
            hours=random.randint(8, 16)
        )

        rdv = database.RendezVous(
            id_patient=patient.id,
            id_medecin=medecin.id,
            date_heure=date_texte(date_rdv),
            statut=random.choice([
                "en_attente", "confirmé", "confirmé"
            ]),
            motif=random.choice(motifs),
            salle=medecin.bureau,
            type_consultation=random.choice([
                "Première visite", "Suivi"
            ])
        )

        db.add(rdv)

    db.flush()

    return db.query(database.RendezVous).filter(
        database.RendezVous.motif.like(f"%{MARQUEUR}%")
    ).all()


# =====================================================
# 2b. HISTORIQUE DE PREDICTIONS IA (DEMO)
# =====================================================

def creer_predictions(db, medecins, patients):
    """Historique fictif pour alimenter les tableaux de bord sans Spark."""
    import json

    deja = db.query(database.Prediction).filter(
        database.Prediction.constantes.like('%"demo": true%')
    ).first()
    if deja:
        return

    for patient in patients[:3]:
        for k in range(5):
            date = datetime.now() - timedelta(days=30 * (5 - k))
            systolic = random.randint(118, 165)
            glucose = round(random.uniform(4.8, 8.5), 1)
            constantes = {
                "maladie": "hypertension", "age": 54, "gender": "M",
                "systolic_bp": systolic, "glucose": glucose,
                "heart_rate": random.randint(62, 95), "demo": True,
            }
            proba = min(0.95, max(0.05, (systolic - 110) / 70))
            db.add(database.Prediction(
                id_patient=patient.id,
                id_medecin=medecins[0].id,
                maladie="hypertension",
                probabilite=round(proba, 3),
                date_prediction=date_texte(date),
                constantes=json.dumps(constantes),
            ))
    db.flush()


# =====================================================
# 3. CONSULTATIONS ET MESURES
# =====================================================

def creer_consultations_mesures(db, medecins, patients):
    consultations = db.query(database.Consultation).filter(
        database.Consultation.diagnostic.like(f"%{MARQUEUR}%")
    ).all()

    if not consultations:
        for i in range(18):
            patient = random.choice(patients)
            medecin = random.choice(medecins)

            consultation = database.Consultation(
                id_patient=patient.id,
                id_medecin=medecin.id,
                diagnostic=f"{MARQUEUR} Consultation fictive de démonstration {i + 1}",
                traitement=f"{MARQUEUR} Aucun traitement réel - donnée de test",
                date_consultation=date_texte(
                    datetime.now() - timedelta(days=random.randint(1, 90))
                )
            )

            db.add(consultation)

        db.flush()

        consultations = db.query(database.Consultation).filter(
            database.Consultation.diagnostic.like(f"%{MARQUEUR}%")
        ).all()

    for consultation in consultations:
        existe = db.query(database.MesureConstante).filter(
            database.MesureConstante.id_consultation == consultation.id
        ).first()

        if not existe:
            mesure = database.MesureConstante(
                id_patient=consultation.id_patient,
                id_consultation=consultation.id,
                tension_systolique=random.randint(110, 135),
                tension_diastolique=random.randint(70, 88),
                frequence_cardiaque=random.randint(65, 95),
                temperature=round(random.uniform(36.2, 37.2), 1),
                saturation_oxygene=random.randint(96, 100),
                poids=round(random.uniform(55, 90), 1),
                taille=round(random.uniform(155, 190), 1),
                date_mesure=datetime.now() - timedelta(
                    days=random.randint(1, 90)
                )
            )
            db.add(mesure)

    db.flush()

    # Analyses fictives clairement marquées
    parametres = [
        ("Hématologie", "Paramètre A", "unité A"),
        ("Biochimie", "Paramètre B", "unité B"),
        ("Analyse générale", "Paramètre C", "unité C")
    ]

    for patient in patients:
        existe = db.query(database.AnalyseLaboratoire).filter(
            database.AnalyseLaboratoire.id_patient == patient.id,
            database.AnalyseLaboratoire.type_analyse.like(
                f"%{MARQUEUR}%"
            )
        ).first()

        if not existe:
            for type_analyse, parametre, unite in parametres:
                analyse = database.AnalyseLaboratoire(
                    id_patient=patient.id,
                    id_consultation=None,
                    type_analyse=f"{MARQUEUR} {type_analyse}",
                    nom_parametre=parametre,
                    resultat=round(random.uniform(10, 90), 2),
                    resultat_texte=f"{MARQUEUR} Résultat fictif",
                    unite=unite,
                    valeur_reference_min=None,
                    valeur_reference_max=None,
                    date_analyse=datetime.now() - timedelta(
                        days=random.randint(1, 60)
                    ),
                    statut="terminee"
                )
                db.add(analyse)

    db.flush()


# =====================================================
# 4. PHARMACIE ET MOUVEMENTS DE STOCK
# =====================================================

def creer_pharmacie(db, medecin):
    noms_medicaments = [
        "Paracetamol Demo",
        "Vitamine Demo",
        "Solution Demo",
        "Comprime Demo",
        "Sirop Demo",
        "Produit Medical Demo",
        "Gel Demo",
        "Materiel Demo"
    ]

    medicaments = []

    for nom in noms_medicaments:
        nom_complet = f"{MARQUEUR} {nom}"

        medicament = db.query(database.Medicament).filter_by(
            nom=nom_complet
        ).first()

        if not medicament:
            medicament = database.Medicament(
                nom=nom_complet,
                categorie="Démonstration",
                laboratoire="Laboratoire fictif",
                forme="Unité de démonstration",
                dosage="Non applicable",
                stock_actuel=30,
                seuil_alerte=5,
                prix_unitaire=Decimal("10.00"),
                date_peremption=datetime.now() + timedelta(days=365)
            )
            db.add(medicament)
            db.flush()

            mouvement = database.MouvementStock(
                id_medicament=medicament.id,
                id_utilisateur=medecin.id,
                type_mouvement="entree",
                quantite=30,
                motif=f"{MARQUEUR} Stock initial fictif"
            )
            db.add(mouvement)

        medicaments.append(medicament)

    db.flush()
    return medicaments


# =====================================================
# 5. SERVICES, SALLES ET LITS
# =====================================================

def creer_infrastructure(db, medecins):
    noms_services = [
        "Cardiologie",
        "Médecine générale",
        "Pédiatrie"
    ]

    services = []

    for nom in noms_services:
        nom_test = f"{MARQUEUR} {nom}"

        service = db.query(database.ServiceMedical).filter_by(
            nom=nom_test
        ).first()

        if not service:
            service = database.ServiceMedical(
                nom=nom_test,
                description=f"{MARQUEUR} Service fictif pour les tests",
                responsable_id=medecins[0].id,
                capacite=20,
                statut="actif"
            )
            db.add(service)
            db.flush()

        services.append(service)

        # Deux salles par service
        for i in range(1, 3):
            nom_salle = f"{MARQUEUR} Salle {i}"

            salle = db.query(database.SalleMedicale).filter_by(
                id_service=service.id,
                nom=nom_salle
            ).first()

            if not salle:
                salle = database.SalleMedicale(
                    id_service=service.id,
                    nom=nom_salle,
                    type_salle="Démonstration",
                    capacite=2,
                    statut="disponible"
                )
                db.add(salle)
                db.flush()

            # Deux lits par salle
            for j in range(1, 3):
                numero = f"TEST-{i}-{j}"

                lit = db.query(database.Lit).filter_by(
                    id_salle=salle.id,
                    numero=numero
                ).first()

                if not lit:
                    lit = database.Lit(
                        id_salle=salle.id,
                        numero=numero,
                        type_lit="Standard",
                        statut="disponible"
                    )
                    db.add(lit)

    db.flush()
    return services


# =====================================================
# 6. HOSPITALISATIONS FICTIVES
# =====================================================

def creer_hospitalisations(db, medecins, patients, services):
    deja_creees = db.query(database.Hospitalisation).filter(
        database.Hospitalisation.motif.like(f"%{MARQUEUR}%")
    ).count()

    if deja_creees:
        return

    lits = db.query(database.Lit).filter(
        database.Lit.numero.like("TEST-%")
    ).all()

    for i in range(min(5, len(patients), len(lits))):
        date_entree = datetime.now() - timedelta(days=random.randint(5, 30))
        date_sortie = date_entree + timedelta(days=random.randint(1, 4))

        hospitalisation = database.Hospitalisation(
            id_patient=patients[i].id,
            id_medecin=medecins[i % len(medecins)].id,
            id_service=services[i % len(services)].id,
            id_lit=lits[i].id,
            date_entree=date_entree,
            date_sortie=date_sortie,
            motif=f"{MARQUEUR} Hospitalisation fictive de démonstration",
            statut="terminee"
        )

        db.add(hospitalisation)

    db.flush()


# =====================================================
# 7. SATISFACTION PATIENT
# =====================================================

def creer_satisfaction(db, patients, rendez_vous):
    deja_creees = db.query(database.SatisfactionPatient).filter(
        database.SatisfactionPatient.commentaire.like(
            f"%{MARQUEUR}%"
        )
    ).count()

    if deja_creees:
        return

    for i in range(min(12, len(patients), len(rendez_vous))):
        evaluation = database.SatisfactionPatient(
            id_patient=rendez_vous[i].id_patient,
            id_rendez_vous=rendez_vous[i].id,
            note=random.randint(3, 5),
            commentaire=f"{MARQUEUR} Avis fictif de démonstration",
            date_evaluation=datetime.now() - timedelta(
                days=random.randint(1, 60)
            )
        )

        db.add(evaluation)

    db.flush()


# =====================================================
# 8. FACTURES ET PAIEMENTS
# =====================================================

def creer_factures_paiements(db, rendez_vous):
    for rdv in rendez_vous[:8]:
        facture = db.query(database.Facture).filter_by(
            id_rendez_vous=rdv.id
        ).first()

        if not facture:
            facture = database.Facture(
                id_rendez_vous=rdv.id,
                montant=100.00,
                statut_paiement="payee",
                date_emission=date_texte(datetime.now())
            )
            db.add(facture)
            db.flush()

        paiement = db.query(database.Paiement).filter_by(
            id_facture=facture.id
        ).first()

        if not paiement and facture.montant and facture.montant > 0:
            paiement = database.Paiement(
                id_facture=facture.id,
                montant=Decimal(str(facture.montant)),
                mode_paiement=random.choice([
                    "especes", "carte", "virement"
                ]),
                date_paiement=datetime.now() - timedelta(
                    days=random.randint(1, 30)
                ),
                reference=f"TEST-{facture.id}",
                statut="valide"
            )
            db.add(paiement)

    db.flush()


# =====================================================
# 9. DEPENSES
# =====================================================

def creer_depenses(db, medecin):
    deja_creees = db.query(database.Depense).filter(
        database.Depense.description.like(f"%{MARQUEUR}%")
    ).count()

    if deja_creees:
        return

    categories = [
        "Électricité",
        "Matériel",
        "Maintenance",
        "Nettoyage",
        "Fournitures",
        "Informatique"
    ]

    for i in range(18):
        depense = database.Depense(
            categorie=random.choice(categories),
            description=f"{MARQUEUR} Dépense fictive de démonstration",
            montant=Decimal(str(random.randint(50, 800))),
            date_depense=datetime.now() - timedelta(
                days=random.randint(1, 180)
            ),
            id_utilisateur=medecin.id
        )

        db.add(depense)

    db.flush()


# =====================================================
# 10. JOURNAL D'ACTIVITE
# =====================================================

def creer_journal(db, medecins, patients):
    deja_crees = db.query(database.JournalActivite).filter(
        database.JournalActivite.description.like(f"%{MARQUEUR}%")
    ).count()

    if deja_crees:
        return

    activites = [
        ("Création", "Patients"),
        ("Consultation", "Dossier médical"),
        ("Modification", "Rendez-vous"),
        ("Ajout", "Pharmacie"),
        ("Évaluation", "Satisfaction"),
        ("Paiement", "Finance"),
        ("Ajout", "Laboratoire")
    ]

    for i in range(25):
        action, module = random.choice(activites)

        journal = database.JournalActivite(
            id_utilisateur=medecins[i % len(medecins)].id,
            action=action,
            module=module,
            description=f"{MARQUEUR} Activité fictive de démonstration",
            date_action=datetime.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 12)
            ),
            statut="succes"
        )

        db.add(journal)

    db.flush()


# =====================================================
# FONCTION PRINCIPALE
# =====================================================

def generer_donnees():
    print("\n======================================")
    print(" CLINIQUE SANTE+ - DONNEES DE TEST")
    print("======================================")

    # Crée uniquement les tables manquantes.
    # Ne supprime aucune table ni aucune donnée.
    database.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()

    try:
        medecins, patients = creer_utilisateurs_patients(db)

        rendez_vous = creer_rendez_vous(
            db, medecins, patients
        )

        creer_predictions(db, medecins, patients)

        creer_consultations_mesures(
            db, medecins, patients
        )

        creer_pharmacie(db, medecins[0])

        services = creer_infrastructure(
            db, medecins
        )

        creer_hospitalisations(
            db, medecins, patients, services
        )

        creer_satisfaction(
            db, patients, rendez_vous
        )

        creer_factures_paiements(
            db, rendez_vous
        )

        creer_depenses(db, medecins[0])

        creer_journal(db, medecins, patients)

        db.commit()

        print("\n✅ DONNEES DE TEST AJOUTEES")
        print("--------------------------------------")
        print("Médecins de démonstration :", len(medecins))
        print("Patients de démonstration :", len(patients))
        print("Rendez-vous de test :", len(rendez_vous))
        print("Consultations, mesures et analyses : OK")
        print("Pharmacie et mouvements : OK")
        print("Services, salles et lits : OK")
        print("Hospitalisations : OK")
        print("Satisfaction : OK")
        print("Factures et paiements : OK")
        print("Dépenses : OK")
        print("Journal d'activité : OK")
        print("--------------------------------------")
        print("Les données fictives portent le marqueur [TEST].")
        print("Comptes démo (mot de passe :", DEMO_PASSWORD + ") :")
        for compte in COMPTES_DEMO:
            print(f"  - {compte['role']:<10} {compte['email']}")
        print("Aucune donnée existante n'a été supprimée.")

    except Exception as erreur:
        db.rollback()
        print("\n❌ ERREUR : aucune modification non validée")
        print(str(erreur))
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generer_donnees()
