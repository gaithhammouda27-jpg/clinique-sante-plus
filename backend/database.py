from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    ForeignKey, DateTime, Boolean, Text, Numeric,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

from backend.config import DATABASE_URL

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    mot_de_passe = Column(String)
    role = Column(String)
    nom_complet = Column(String)
    specialite = Column(String, nullable=True)
    bureau = Column(String, nullable=True)
    telephone = Column(String, nullable=True)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id"))
    date_naissance = Column(String)
    telephone = Column(String)
    antecedents = Column(String)

class RendezVous(Base):
    __tablename__ = "rendez_vous"
    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"))
    id_medecin = Column(Integer, ForeignKey("utilisateurs.id"))
    date_heure = Column(String)
    statut = Column(String, default="en_attente")
    motif = Column(String, nullable=True)
    salle = Column(String, nullable=True)
    type_consultation = Column(String, default="Première visite")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"))
    id_medecin = Column(Integer, ForeignKey("utilisateurs.id"))
    maladie = Column(String)  # "hypertension", "diabete"
    probabilite = Column(Float)
    date_prediction = Column(String)
    constantes = Column(String)

class Ordonnance(Base):
    __tablename__ = "ordonnances"
    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"))
    id_medecin = Column(Integer, ForeignKey("utilisateurs.id"))
    medicaments = Column(String)
    posologie = Column(String)
    instructions = Column(String, nullable=True)
    date_prescription = Column(String)

class Facture(Base):
    __tablename__ = "factures"
    id = Column(Integer, primary_key=True, index=True)
    id_rendez_vous = Column(Integer, ForeignKey("rendez_vous.id"))
    montant = Column(Float)
    statut_paiement = Column(String, default="en_attente")
    date_emission = Column(String)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"))
    id_medecin = Column(Integer, ForeignKey("utilisateurs.id"))
    nom_fichier = Column(String)
    type_fichier = Column(String)
    chemin_stockage = Column(String)
    date_ajout = Column(String)
    description = Column(String, nullable=True)

class Consultation(Base):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"))
    id_medecin = Column(Integer, ForeignKey("utilisateurs.id"))
    diagnostic = Column(String)
    traitement = Column(String)
    date_consultation = Column(String)
# ==========================================
# NOUVEAUX MODELES : MODULE MEDICAL
# ==========================================

class MesureConstante(Base):
    __tablename__ = "mesures_constantes"

    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"), nullable=False)
    id_consultation = Column(Integer, ForeignKey("consultations.id"), nullable=True)

    tension_systolique = Column(Float, nullable=True)
    tension_diastolique = Column(Float, nullable=True)
    frequence_cardiaque = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    saturation_oxygene = Column(Float, nullable=True)
    poids = Column(Float, nullable=True)
    taille = Column(Float, nullable=True)

    date_mesure = Column(DateTime, default=datetime.now, nullable=False)

    patient = relationship("Patient")
    consultation = relationship("Consultation")


class AnalyseLaboratoire(Base):
    __tablename__ = "analyses_laboratoire"

    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"), nullable=False)
    id_consultation = Column(Integer, ForeignKey("consultations.id"), nullable=True)

    type_analyse = Column(String, nullable=False)
    nom_parametre = Column(String, nullable=False)
    resultat = Column(Float, nullable=True)
    resultat_texte = Column(Text, nullable=True)
    unite = Column(String, nullable=True)
    valeur_reference_min = Column(Float, nullable=True)
    valeur_reference_max = Column(Float, nullable=True)

    date_analyse = Column(DateTime, default=datetime.now)
    statut = Column(String, default="en_attente")

    patient = relationship("Patient")
    consultation = relationship("Consultation")


class Hospitalisation(Base):
    __tablename__ = "hospitalisations"

    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"), nullable=False)
    id_medecin = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    id_service = Column(Integer, ForeignKey("services_medicaux.id"), nullable=False)
    id_lit = Column(Integer, ForeignKey("lits.id"), nullable=True)

    date_entree = Column(DateTime, default=datetime.now, nullable=False)
    date_sortie = Column(DateTime, nullable=True)
    motif = Column(Text)
    statut = Column(String, default="en_cours")

    patient = relationship("Patient")
    medecin = relationship("Utilisateur")


class SatisfactionPatient(Base):
    __tablename__ = "satisfaction_patients"

    id = Column(Integer, primary_key=True, index=True)
    id_patient = Column(Integer, ForeignKey("patients.id"), nullable=False)
    id_rendez_vous = Column(Integer, ForeignKey("rendez_vous.id"), nullable=True)

    note = Column(Integer, nullable=False)
    commentaire = Column(Text, nullable=True)
    date_evaluation = Column(DateTime, default=datetime.now)

    __table_args__ = (
        CheckConstraint("note >= 1 AND note <= 5", name="check_note_satisfaction"),
    )

    patient = relationship("Patient")
    rendez_vous = relationship("RendezVous")
  # ==========================================
# NOUVEAUX MODELES : PHARMACIE
# ==========================================

class Medicament(Base):
    __tablename__ = "medicaments"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False, index=True)
    categorie = Column(String, nullable=True)
    laboratoire = Column(String, nullable=True)
    forme = Column(String, nullable=True)
    dosage = Column(String, nullable=True)

    stock_actuel = Column(Integer, default=0, nullable=False)
    seuil_alerte = Column(Integer, default=5, nullable=False)
    prix_unitaire = Column(Numeric(10, 2), default=0)

    date_peremption = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("stock_actuel >= 0", name="check_stock_positif"),
        CheckConstraint("seuil_alerte >= 0", name="check_seuil_positif"),
    )


class LigneOrdonnance(Base):
    __tablename__ = "lignes_ordonnance"

    id = Column(Integer, primary_key=True, index=True)
    id_ordonnance = Column(Integer, ForeignKey("ordonnances.id"), nullable=False)
    id_medicament = Column(Integer, ForeignKey("medicaments.id"), nullable=False)

    quantite = Column(Integer, nullable=False)
    posologie = Column(Text, nullable=False)
    duree_jours = Column(Integer, nullable=True)

    ordonnance = relationship("Ordonnance")
    medicament = relationship("Medicament")

    __table_args__ = (
        UniqueConstraint(
            "id_ordonnance",
            "id_medicament",
            name="unique_medicament_ordonnance"
        ),
        CheckConstraint("quantite > 0", name="check_quantite_positive"),
    )


class MouvementStock(Base):
    __tablename__ = "mouvements_stock"

    id = Column(Integer, primary_key=True, index=True)
    id_medicament = Column(Integer, ForeignKey("medicaments.id"), nullable=False)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)

    type_mouvement = Column(String, nullable=False)
    quantite = Column(Integer, nullable=False)
    date_mouvement = Column(DateTime, default=datetime.now)

    motif = Column(String, nullable=True)

    medicament = relationship("Medicament")
    utilisateur = relationship("Utilisateur")

    __table_args__ = (
        CheckConstraint("quantite > 0", name="check_mouvement_quantite"),
        CheckConstraint(
            "type_mouvement IN ('entree', 'sortie', 'ajustement')",
            name="check_type_mouvement"
        ),
    )  

# ==========================================
# NOUVEAUX MODELES : INFRASTRUCTURE
# ==========================================

class ServiceMedical(Base):
    __tablename__ = "services_medicaux"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    responsable_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    capacite = Column(Integer, default=0)
    statut = Column(String, default="actif")

    responsable = relationship("Utilisateur")


class SalleMedicale(Base):
    __tablename__ = "salles_medicales"

    id = Column(Integer, primary_key=True, index=True)
    id_service = Column(Integer, ForeignKey("services_medicaux.id"), nullable=False)

    nom = Column(String, nullable=False)
    type_salle = Column(String, nullable=True)
    capacite = Column(Integer, default=1)
    statut = Column(String, default="disponible")

    service = relationship("ServiceMedical", backref="salles")

    __table_args__ = (
        UniqueConstraint("id_service", "nom", name="unique_salle_service"),
    )


class Lit(Base):
    __tablename__ = "lits"

    id = Column(Integer, primary_key=True, index=True)
    id_salle = Column(Integer, ForeignKey("salles_medicales.id"), nullable=False)

    numero = Column(String, nullable=False)
    type_lit = Column(String, nullable=True)
    statut = Column(String, default="disponible")

    salle = relationship("SalleMedicale", backref="lits")

    __table_args__ = (
        UniqueConstraint("id_salle", "numero", name="unique_lit_salle"),
    )

    # ==========================================
# NOUVEAUX MODELES : FINANCE
# ==========================================

class Paiement(Base):
    __tablename__ = "paiements"

    id = Column(Integer, primary_key=True, index=True)
    id_facture = Column(Integer, ForeignKey("factures.id"), nullable=False)

    montant = Column(Numeric(10, 2), nullable=False)
    mode_paiement = Column(String, nullable=False)
    date_paiement = Column(DateTime, default=datetime.now)

    reference = Column(String, nullable=True)
    statut = Column(String, default="valide")

    facture = relationship("Facture")

    __table_args__ = (
        CheckConstraint("montant > 0", name="check_paiement_positif"),
    )


class Depense(Base):
    __tablename__ = "depenses"

    id = Column(Integer, primary_key=True, index=True)

    categorie = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    montant = Column(Numeric(10, 2), nullable=False)

    date_depense = Column(DateTime, default=datetime.now)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)

    utilisateur = relationship("Utilisateur")

    __table_args__ = (
        CheckConstraint("montant > 0", name="check_depense_positive"),
    )

# ==========================================
# NOUVEAU MODELE : JOURNAL D'ACTIVITE
# ==========================================

class JournalActivite(Base):
    __tablename__ = "journal_activite"

    id = Column(Integer, primary_key=True, index=True)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)

    action = Column(String, nullable=False)
    module = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    date_action = Column(DateTime, default=datetime.now)
    statut = Column(String, default="succes")

    utilisateur = relationship("Utilisateur")

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Base de données et tables créées avec succès !")

if __name__ == "__main__":
    init_db()