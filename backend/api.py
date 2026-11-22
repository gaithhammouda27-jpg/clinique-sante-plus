from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import shutil
import os
import uuid
import json
from fastapi.responses import FileResponse
from collections import Counter
from decimal import Decimal
from sqlalchemy import func
from typing import Optional

from backend import database
from backend.config import UPLOAD_DIR as _UPLOAD_DIR
from backend.security import hacher_mot_de_passe, verifier_mot_de_passe

# ==========================================
# 1. INITIALISATION
# ==========================================
app = FastAPI(title="API Clinique", version="1.1")

# Crée les tables manquantes au démarrage (ne supprime rien)
database.Base.metadata.create_all(bind=database.engine)


def utilisateur_public(user):
    """Représentation d'un utilisateur SANS le hachage du mot de passe."""
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "nom_complet": user.nom_complet,
        "specialite": user.specialite,
        "bureau": user.bureau,
        "telephone": user.telephone,
    }

# Dépendance pour la session de base de données
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. MODÈLES PYDANTIC
# ==========================================
class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str

class UtilisateurCreate(BaseModel):
    email: str
    mot_de_passe: str
    role: str
    nom_complet: str
    specialite: str = None
    bureau: str = None
    telephone: str = None

class PatientCreate(BaseModel):
    id_utilisateur: int
    date_naissance: str
    telephone: str
    antecedents: str

class PatientUpdate(BaseModel):
    nom_complet: str = None
    email: str = None
    telephone: str = None
    antecedents: str = None

class RendezVousCreate(BaseModel):
    id_patient: int
    id_medecin: int
    date_heure: str
    motif: str = None
    salle: str = None
    type_consultation: str = "Première visite"

class RendezVousUpdate(BaseModel):
    id_medecin: int = None
    date_heure: str = None
    salle: str = None
    motif: str = None
    statut: str = None

class StatutUpdate(BaseModel):
    statut: str

class NouveauPatientComplet(BaseModel):
    nom_complet: str
    email: str
    mot_de_passe: str
    date_naissance: str
    telephone: str
    antecedents: Optional[str] = None

class FactureCreate(BaseModel):
    id_rendez_vous: int
    montant: float

class PaiementUpdate(BaseModel):
    statut_paiement: str

class OrdonnanceCreate(BaseModel):
    id_patient: int
    id_medecin: int
    medicaments: str
    posologie: str
    instructions: str = None

class ConsultationCreate(BaseModel):
    id_patient: int
    id_medecin: int
    diagnostic: str
    traitement: str = None

class MesureConstanteCreate(BaseModel):
    id_patient: int
    id_consultation: int = None
    tension_systolique: float = None
    tension_diastolique: float = None
    frequence_cardiaque: float = None
    temperature: float = None
    saturation_oxygene: float = None
    poids: float = None
    taille: float = None


class AnalyseLaboratoireCreate(BaseModel):
    id_patient: int
    id_consultation: int = None
    type_analyse: str
    nom_parametre: str
    resultat: float = None
    resultat_texte: str = None
    unite: str = None
    valeur_reference_min: float = None
    valeur_reference_max: float = None

# NOUVEAU : Modèle générique pour l'IA
class DonneesMedicales(BaseModel):
    maladie: str
    age: int
    gender: str = None
    systolic_bp: int = None
    glucose: float = None
    heart_rate: int = None
    bmi: float = None
    blood_pressure: int = None
    id_patient: int
    id_medecin: int

class HospitalisationCreate(BaseModel):
    id_patient: int
    id_medecin: int
    id_service: int
    id_lit: int = None
    motif: str = None
class SatisfactionPatientCreate(BaseModel):
    id_patient: int
    id_rendez_vous: int = None
    note: int
    commentaire: str = None

class MedicamentCreate(BaseModel):
    nom: str
    categorie: str = None
    laboratoire: str = None
    forme: str = None
    dosage: str = None
    stock_actuel: int = 0
    seuil_alerte: int = 5
    prix_unitaire: float = 0

class MouvementStockCreate(BaseModel):
    id_medicament: int
    id_utilisateur: int = None
    type_mouvement: str
    quantite: int
    motif: str = None

class LigneOrdonnanceCreate(BaseModel):
    id_ordonnance: int
    id_medicament: int
    quantite: int
    posologie: str
    duree_jours: int = None

class PaiementCreate(BaseModel):
    id_facture: int
    montant: float
    mode_paiement: str
    reference: str = None

class DepenseCreate(BaseModel):
    categorie: str
    description: str = None
    montant: float
    id_utilisateur: int = None
class ServiceMedicalCreate(BaseModel):
    nom: str
    description: str = None
    responsable_id: int = None
    capacite: int = 0


class SalleMedicaleCreate(BaseModel):
    id_service: int
    nom: str
    type_salle: str = None
    capacite: int = 1


class LitCreate(BaseModel):
    id_salle: int
    numero: str
    type_lit: str = None

class JournalActiviteCreate(BaseModel):
    id_utilisateur: int = None
    action: str
    module: str
    description: str = None
    statut: str = "succes"
class SalleMedicaleUpdate(BaseModel):
    nom: Optional[str] = None
    id_service: Optional[int] = None
    type_salle: Optional[str] = None
    capacite: Optional[int] = None
    statut: Optional[str] = None


class LitUpdate(BaseModel):
    id_salle: Optional[int] = None
    numero: Optional[str] = None
    type_lit: Optional[str] = None
    statut: Optional[str] = None

# ==========================================
# 3. ROUTES DE BASE
# ==========================================
@app.get("/")
def read_root():
    return {"message": "Bienvenue dans l'API de la Clinique"}

# ==========================================
# 4. AUTHENTIFICATION
# ==========================================
@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(database.Utilisateur).filter(database.Utilisateur.email == data.email).first()
    
    if not user or not verifier_mot_de_passe(data.mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    return {
        "id": user.id,
        "email": user.email,
        "nom_complet": user.nom_complet,
        "role": user.role
    }

# ==========================================
# 5. GESTION DES UTILISATEURS
# ==========================================
@app.get("/utilisateurs/")
def lire_utilisateurs(db: Session = Depends(get_db)):
    utilisateurs = db.query(
        database.Utilisateur.id,
        database.Utilisateur.nom_complet,
        database.Utilisateur.email,
        database.Utilisateur.role,
        database.Utilisateur.specialite,
        database.Utilisateur.bureau,
        database.Utilisateur.telephone
    ).all()

    return [
        {
            "id": u.id,
            "nom_complet": u.nom_complet,
            "email": u.email,
            "role": u.role,
            "specialite": u.specialite,
            "bureau": u.bureau,
            "telephone": u.telephone
        }
        for u in utilisateurs
    ]

@app.post("/utilisateurs/")
def creer_utilisateur(user: UtilisateurCreate, db: Session = Depends(get_db)):
    if db.query(database.Utilisateur).filter(database.Utilisateur.email == user.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    mdp_hache = hacher_mot_de_passe(user.mot_de_passe)
    
    nouvel_utilisateur = database.Utilisateur(
        email=user.email, mot_de_passe=mdp_hache, role=user.role,
        nom_complet=user.nom_complet, specialite=user.specialite,
        bureau=user.bureau, telephone=user.telephone
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    return {"message": "Utilisateur créé", "id": nouvel_utilisateur.id}

@app.get("/utilisateurs/par-email/{email}")
def lire_utilisateur_par_email(email: str, db: Session = Depends(get_db)):
    user = db.query(database.Utilisateur).filter(database.Utilisateur.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return utilisateur_public(user)

@app.get("/medecins/")
def lire_medecins(db: Session = Depends(get_db)):
    medecins = db.query(database.Utilisateur).filter(database.Utilisateur.role == "medecin").all()
    return [utilisateur_public(m) for m in medecins]

# ==========================================
# 6. GESTION DES PATIENTS
# ==========================================
@app.post("/patients/")
def creer_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    user = db.query(database.Utilisateur).filter(database.Utilisateur.id == patient.id_utilisateur).first()
    if not user or user.role != "patient":
        raise HTTPException(status_code=400, detail="Utilisateur invalide ou rôle incorrect")
    
    nouveau_patient = database.Patient(
        id_utilisateur=patient.id_utilisateur, date_naissance=patient.date_naissance,
        telephone=patient.telephone, antecedents=patient.antecedents
    )
    db.add(nouveau_patient)
    db.commit()
    db.refresh(nouveau_patient)
    return {"message": "Patient créé avec succès", "id": nouveau_patient.id}

@app.get("/patients/")
def lire_patients(db: Session = Depends(get_db)):
    patients = db.query(database.Patient).all()
    resultat = []
    for p in patients:
        user = db.query(database.Utilisateur).filter(database.Utilisateur.id == p.id_utilisateur).first()
        resultat.append({
            "id": p.id,
            "nom_complet": user.nom_complet if user else "Inconnu",
            "telephone": p.telephone,
            "date_naissance": p.date_naissance,
            "antecedents": p.antecedents
        })
    return resultat

@app.get("/patients/details/{patient_id}")
def lire_details_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(database.Patient).filter(database.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    user = db.query(database.Utilisateur).filter(database.Utilisateur.id == patient.id_utilisateur).first()
    return {
        "id": patient.id, "id_utilisateur": patient.id_utilisateur,
        "nom_complet": user.nom_complet if user else "Inconnu",
        "email": user.email if user else "Inconnu",
        "telephone": patient.telephone, "date_naissance": patient.date_naissance,
        "antecedents": patient.antecedents
    }

@app.put("/patients/{patient_id}/modifier")
def modifier_patient(patient_id: int, data: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(database.Patient).filter(database.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    user = db.query(database.Utilisateur).filter(database.Utilisateur.id == patient.id_utilisateur).first()
    if data.nom_complet and user: user.nom_complet = data.nom_complet
    if data.email and user: user.email = data.email
    if data.telephone: patient.telephone = data.telephone
    if data.antecedents is not None: patient.antecedents = data.antecedents
    db.commit()
    return {"message": "Dossier patient mis à jour"}

@app.get("/patients/par-email/{email}")
def lire_patient_par_email(email: str, db: Session = Depends(get_db)):
    user = db.query(database.Utilisateur).filter(database.Utilisateur.email == email).first()
    if not user or user.role != "patient":
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    patient = db.query(database.Patient).filter(database.Patient.id_utilisateur == user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Dossier patient non trouvé")
    return {"id_patient": patient.id, "nom_complet": user.nom_complet}

# ==========================================
# 7. GESTION DES RENDEZ-VOUS
# ==========================================
@app.post("/rendezvous/")
def creer_rendez_vous(rdv: RendezVousCreate, db: Session = Depends(get_db)):
    if not db.query(database.Patient).filter(database.Patient.id == rdv.id_patient).first():
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    
    medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == rdv.id_medecin).first()
    if not medecin or medecin.role != "medecin":
        raise HTTPException(status_code=400, detail="Médecin invalide")

    try:
        date_str = datetime.fromisoformat(rdv.date_heure).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide")

    # Vérification des conflits
    conflit_medecin = db.query(database.RendezVous).filter(
        database.RendezVous.id_medecin == rdv.id_medecin,
        database.RendezVous.date_heure == date_str,
        database.RendezVous.statut != "annulé"
    ).first()
    if conflit_medecin:
        raise HTTPException(status_code=400, detail=f"Le médecin est déjà occupé à cette heure (RDV n°{conflit_medecin.id}).")

    conflit_patient = db.query(database.RendezVous).filter(
        database.RendezVous.id_patient == rdv.id_patient,
        database.RendezVous.date_heure == date_str,
        database.RendezVous.statut != "annulé"
    ).first()
    if conflit_patient:
        raise HTTPException(status_code=400, detail="Le patient a déjà un rendez-vous à cette heure.")

    nouveau_rdv = database.RendezVous(
        id_patient=rdv.id_patient, id_medecin=rdv.id_medecin, date_heure=date_str,
        statut="en_attente", motif=rdv.motif, salle=rdv.salle, type_consultation=rdv.type_consultation
    )
    db.add(nouveau_rdv)
    db.commit()
    db.refresh(nouveau_rdv)
    return {"message": "Rendez-vous créé", "id": nouveau_rdv.id}

@app.get("/rendezvous/")
def lire_rendez_vous(db: Session = Depends(get_db)):
    return db.query(database.RendezVous).all()

@app.get("/patients/{patient_id}/rendezvous")
def lire_rendez_vous_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(database.Patient).filter(database.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    
    rdvs = db.query(database.RendezVous).filter(database.RendezVous.id_patient == patient_id).all()
    resultat = []
    for rdv in rdvs:
        medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == rdv.id_medecin).first()
        resultat.append({
            "id": rdv.id, "date_heure": rdv.date_heure, "statut": rdv.statut,
            "medecin": medecin.nom_complet if medecin else "Inconnu",
            "motif": rdv.motif, "salle": rdv.salle, "type_consultation": rdv.type_consultation
        })
    return resultat

@app.get("/medecins/{medecin_id}/rendezvous")
def lire_rendez_vous_medecin(medecin_id: int, db: Session = Depends(get_db)):
    medecin = db.query(database.Utilisateur).filter(
        database.Utilisateur.id == medecin_id, 
        database.Utilisateur.role == "medecin"
    ).first()
    if not medecin:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")
    
    rdvs = db.query(database.RendezVous).filter(database.RendezVous.id_medecin == medecin_id).all()
    resultat = []
    for rdv in rdvs:
        patient_user = db.query(database.Utilisateur).join(
            database.Patient, database.Patient.id_utilisateur == database.Utilisateur.id
        ).filter(database.Patient.id == rdv.id_patient).first()
        resultat.append({
            "id": rdv.id, "date_heure": rdv.date_heure, "statut": rdv.statut,
            "patient_nom": patient_user.nom_complet if patient_user else "Inconnu",
            "motif": rdv.motif, "salle": rdv.salle
        })
    return resultat

@app.put("/rendezvous/{rdv_id}/statut")
def modifier_statut_rdv(rdv_id: int, data: StatutUpdate, db: Session = Depends(get_db)):
    rdv = db.query(database.RendezVous).filter(database.RendezVous.id == rdv_id).first()
    if not rdv:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    rdv.statut = data.statut
    db.commit()
    return {"message": f"Statut mis à jour : {rdv.statut}"}

@app.put("/rendezvous/{rdv_id}/modifier")
def modifier_rendez_vous(rdv_id: int, data: RendezVousUpdate, db: Session = Depends(get_db)):
    rdv = db.query(database.RendezVous).filter(database.RendezVous.id == rdv_id).first()
    if not rdv:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    if data.id_medecin is not None:
        medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == data.id_medecin, database.Utilisateur.role == "medecin").first()
        if not medecin:
            raise HTTPException(status_code=400, detail="Médecin invalide")
        rdv.id_medecin = data.id_medecin
    if data.date_heure is not None:
        try:
            date_obj = datetime.fromisoformat(data.date_heure)
            rdv.date_heure = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide")
    if data.salle is not None: rdv.salle = data.salle
    if data.motif is not None: rdv.motif = data.motif
    if data.statut is not None: rdv.statut = data.statut
    db.commit()
    return {"message": "Rendez-vous modifié", "rdv": rdv}

# ==========================================
# 8. GESTION DES SECRÉTAIRES / ADMIN
# ==========================================
@app.post("/secretaire/creer-patient")
def creer_patient_complet(data: NouveauPatientComplet, db: Session = Depends(get_db)):
    if db.query(database.Utilisateur).filter(database.Utilisateur.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    mdp_hache = hacher_mot_de_passe(data.mot_de_passe)
    
    nouvel_user = database.Utilisateur(
        email=data.email, mot_de_passe=mdp_hache, 
        role="patient", nom_complet=data.nom_complet
    )
    db.add(nouvel_user)
    db.commit()
    db.refresh(nouvel_user)

    nouveau_dossier = database.Patient(
        id_utilisateur=nouvel_user.id, date_naissance=data.date_naissance,
        telephone=data.telephone,
        antecedents=(data.antecedents or "").strip() or "Aucun"
    )
    db.add(nouveau_dossier)
    db.commit()
    db.refresh(nouveau_dossier)
    return {"message": "Patient et compte créés avec succès", "id": nouveau_dossier.id}

# ==========================================
# 9. IA (DIAGNOSTIC MULTI-MALADIES)
# ==========================================

@app.post("/ia/predire")
def lancer_prediction(data: DonneesMedicales, db: Session = Depends(get_db)):
    try:
        try:
            from backend.ia_service import predire_maladie
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Module IA indisponible (PySpark/Java non installés ?) : {e}",
            )

        resultat = predire_maladie(data.maladie, data.dict())

        if not isinstance(resultat, dict):
            raise HTTPException(status_code=500, detail="Résultat IA invalide")

        if "erreur" in resultat:
            raise HTTPException(status_code=400, detail=resultat["erreur"])

        probabilite = float(resultat["probabilite"])

        # Seuil technique à valider avant toute interprétation médicale
        risque_eleve = probabilite >= 0.5

        # Préparation des constantes
        constantes = data.dict(exclude={"id_patient"})

        # Création de la prédiction
        nouvelle_prediction = database.Prediction(
            id_patient=data.id_patient,
            id_medecin=data.id_medecin,  # À remplacer par la vraie variable
            maladie=data.maladie,
            probabilite=probabilite,
            date_prediction=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            constantes=json.dumps(constantes)
        )

        db.add(nouvelle_prediction)
        db.commit()
        db.refresh(nouvelle_prediction)

        return {
            "id": nouvelle_prediction.id,
            "maladie": data.maladie,
            "probabilite": probabilite,
            "risque_eleve": risque_eleve,
            "date": nouvelle_prediction.date_prediction
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Erreur API : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 10. GESTION DES ORDONNANCES
# ==========================================
@app.post("/ordonnances/")
def creer_ordonnance(ordonnance: OrdonnanceCreate, db: Session = Depends(get_db)):
    if not db.query(database.Patient).filter(database.Patient.id == ordonnance.id_patient).first():
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    
    medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == ordonnance.id_medecin).first()
    if not medecin or medecin.role != "medecin":
        raise HTTPException(status_code=400, detail="Médecin invalide")
    
    nouvelle_ordonnance = database.Ordonnance(
        id_patient=ordonnance.id_patient, id_medecin=ordonnance.id_medecin,
        medicaments=ordonnance.medicaments, posologie=ordonnance.posologie,
        instructions=ordonnance.instructions,
        date_prescription=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(nouvelle_ordonnance)
    db.commit()
    db.refresh(nouvelle_ordonnance)
    return {"message": "Ordonnance créée", "id": nouvelle_ordonnance.id}

@app.get("/patients/{patient_id}/ordonnances")
def lire_ordonnances_patient(patient_id: int, db: Session = Depends(get_db)):
    if not db.query(database.Patient).filter(database.Patient.id == patient_id).first():
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    
    ordonnances = db.query(database.Ordonnance).filter(
        database.Ordonnance.id_patient == patient_id
    ).order_by(database.Ordonnance.date_prescription.desc()).all()
    
    resultat = []
    for o in ordonnances:
        medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == o.id_medecin).first()
        resultat.append({
            "id": o.id, "date": o.date_prescription,
            "medecin": medecin.nom_complet if medecin else "Inconnu",
            "medicaments": o.medicaments, "posologie": o.posologie,
            "instructions": o.instructions
        })
    return resultat

# ==========================================
# 11. GESTION DES DOCUMENTS
# ==========================================
UPLOAD_DIR = str(_UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/patients/{patient_id}/documents")
async def ajouter_document(
    patient_id: int, id_medecin: int, description: str = None,
    fichier: UploadFile = File(...), db: Session = Depends(get_db)
):
    if not db.query(database.Patient).filter(database.Patient.id == patient_id).first():
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    extension = fichier.filename.split(".")[-1].lower()
    if extension not in ["jpg", "jpeg", "png", "pdf"]:
        raise HTTPException(status_code=400, detail="Format non supporté (JPG, PNG, PDF uniquement)")

    nom_unique = f"{uuid.uuid4()}.{extension}"
    chemin_complet = os.path.join(UPLOAD_DIR, nom_unique)

    with open(chemin_complet, "wb") as buffer:
        shutil.copyfileobj(fichier.file, buffer)

    type_fichier = "pdf" if extension == "pdf" else "image"

    nouveau_doc = database.Document(
        id_patient=patient_id, id_medecin=id_medecin,
        nom_fichier=fichier.filename, type_fichier=type_fichier,
        chemin_stockage=chemin_complet,
        date_ajout=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description=description
    )
    db.add(nouveau_doc)
    db.commit()
    db.refresh(nouveau_doc)
    return {"message": "Document ajouté", "id": nouveau_doc.id}

@app.get("/patients/{patient_id}/documents")
def lire_documents_patient(patient_id: int, db: Session = Depends(get_db)):
    documents = db.query(database.Document).filter(database.Document.id_patient == patient_id).all()
    resultat = []
    for doc in documents:
        medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == doc.id_medecin).first()
        resultat.append({
            "id": doc.id, "nom_fichier": doc.nom_fichier, "type_fichier": doc.type_fichier,
            "chemin_stockage": doc.chemin_stockage, "date_ajout": doc.date_ajout,
            "description": doc.description, "medecin": medecin.nom_complet if medecin else "Inconnu"
        })
    return resultat

# ==========================================
# 12. GESTION DES CONSULTATIONS
# ==========================================
@app.post("/consultations/")
def creer_consultation(data: ConsultationCreate, db: Session = Depends(get_db)):
    if not db.query(database.Patient).filter(database.Patient.id == data.id_patient).first():
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    
    nouvelle_consultation = database.Consultation(
        id_patient=data.id_patient, id_medecin=data.id_medecin,
        diagnostic=data.diagnostic, traitement=data.traitement,
        date_consultation=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(nouvelle_consultation)
    db.commit()
    db.refresh(nouvelle_consultation)
    return {"message": "Consultation enregistrée", "id": nouvelle_consultation.id}

@app.get("/patients/{patient_id}/consultations")
def lire_consultations_patient(patient_id: int, db: Session = Depends(get_db)):
    consultations = db.query(database.Consultation).filter(
        database.Consultation.id_patient == patient_id
    ).order_by(database.Consultation.date_consultation.desc()).all()
    
    resultat = []
    for c in consultations:
        medecin = db.query(database.Utilisateur).filter(database.Utilisateur.id == c.id_medecin).first()
        resultat.append({
            "id": c.id, "date": c.date_consultation,
            "medecin": medecin.nom_complet if medecin else "Inconnu",
            "diagnostic": c.diagnostic, "traitement": c.traitement
        })
    return resultat

# ==========================================
# 13. DOSSIER MÉDICAL COMPLET
# ==========================================
@app.get("/patients/{patient_id}/dossier-complet")
def lire_dossier_complet(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(database.Patient).filter(database.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    
    user = db.query(database.Utilisateur).filter(database.Utilisateur.id == patient.id_utilisateur).first()
    
    # Ordonnances
    ordonnances = db.query(database.Ordonnance).filter(database.Ordonnance.id_patient == patient_id).order_by(database.Ordonnance.date_prescription.desc()).all()
    ordonnances_list = []
    for o in ordonnances:
        med = db.query(database.Utilisateur).filter(database.Utilisateur.id == o.id_medecin).first()
        ordonnances_list.append({
            "id": o.id, "date": o.date_prescription, "medecin": med.nom_complet if med else "Inconnu",
            "medicaments": o.medicaments, "posologie": o.posologie, "instructions": o.instructions
        })

    # Documents
    documents = db.query(database.Document).filter(database.Document.id_patient == patient_id).order_by(database.Document.date_ajout.desc()).all()
    documents_list = []
    for d in documents:
        med = db.query(database.Utilisateur).filter(database.Utilisateur.id == d.id_medecin).first()
        documents_list.append({
            "id": d.id, "nom_fichier": d.nom_fichier, "type_fichier": d.type_fichier,
            "chemin_stockage": d.chemin_stockage, "date_ajout": d.date_ajout,
            "description": d.description, "medecin": med.nom_complet if med else "Inconnu"
        })

    # Prédictions
    predictions = db.query(database.Prediction).filter(database.Prediction.id_patient == patient_id).order_by(database.Prediction.date_prediction.asc()).all()
    predictions_list = []
    for p in predictions:
           # Dans la boucle des prédictions
        predictions_list.append({
        "id": p.id, 
        "date": p.date_prediction, 
        "probabilite": p.probabilite,
        "maladie": p.maladie,  # <-- Assurez-vous que c'est bien là
        "constantes": p.constantes
    })

    # Rendez-vous
    rdvs = db.query(database.RendezVous).filter(database.RendezVous.id_patient == patient_id).order_by(database.RendezVous.date_heure.desc()).all()
    rdvs_list = []
    for r in rdvs:
        med = db.query(database.Utilisateur).filter(database.Utilisateur.id == r.id_medecin).first()
        rdvs_list.append({
            "id": r.id, "date": r.date_heure, "statut": r.statut,
            "medecin": med.nom_complet if med else "Inconnu", "motif": r.motif
        })

    # Consultations
    consultations = db.query(database.Consultation).filter(database.Consultation.id_patient == patient_id).order_by(database.Consultation.date_consultation.desc()).all()
    consultations_list = []
    for c in consultations:
        med = db.query(database.Utilisateur).filter(database.Utilisateur.id == c.id_medecin).first()
        consultations_list.append({
            "id": c.id, "date": c.date_consultation,
            "medecin": med.nom_complet if med else "Inconnu",
            "diagnostic": c.diagnostic, "traitement": c.traitement
        })

    return {
        "patient": {
            "id": patient.id, "nom_complet": user.nom_complet if user else "Inconnu",
            "email": user.email if user else "Inconnu",
            "telephone": patient.telephone, "date_naissance": patient.date_naissance,
            "antecedents": patient.antecedents
        },
        "ordonnances": ordonnances_list,
        "documents": documents_list,
        "predictions": predictions_list,
        "rendez_vous": rdvs_list,
        "consultations": consultations_list
    }

# ==========================================
# 14. GESTION DES FACTURES
# ==========================================
@app.post("/factures/")
def creer_facture(facture: FactureCreate, db: Session = Depends(get_db)):
    rdv = db.query(database.RendezVous).filter(database.RendezVous.id == facture.id_rendez_vous).first()
    if not rdv:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    nouvelle_facture = database.Facture(
        id_rendez_vous=facture.id_rendez_vous, montant=facture.montant,
        date_emission=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(nouvelle_facture)
    db.commit()
    db.refresh(nouvelle_facture)
    return {"message": "Facture créée", "id": nouvelle_facture.id}

@app.get("/factures/")
def lire_factures(db: Session = Depends(get_db)):
    return db.query(database.Facture).all()

@app.put("/factures/{facture_id}/statut")
def modifier_statut_facture(facture_id: int, data: PaiementUpdate, db: Session = Depends(get_db)):
    facture = db.query(database.Facture).filter(database.Facture.id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    facture.statut_paiement = data.statut_paiement
    db.commit()
    return {"message": f"Statut mis à jour : {facture.statut_paiement}"}

# ==========================================
# 15. ANNUAIRE MÉDECINS
# ==========================================
@app.get("/medecins/annuaire")
def lire_annuaire_medecins(db: Session = Depends(get_db)):
    medecins = db.query(database.Utilisateur).filter(database.Utilisateur.role == "medecin").all()
    resultat = []
    for med in medecins:
        rdvs = db.query(database.RendezVous).filter(database.RendezVous.id_medecin == med.id).all()
        patients_du_medecin = []
        rdvs_details = []
        for rdv in rdvs:
            patient_user = db.query(database.Utilisateur).join(
                database.Patient, database.Patient.id_utilisateur == database.Utilisateur.id
            ).filter(database.Patient.id == rdv.id_patient).first()
            nom_patient = patient_user.nom_complet if patient_user else "Inconnu"
            rdvs_details.append({"date": rdv.date_heure, "patient": nom_patient, "motif": rdv.motif})
            if nom_patient not in patients_du_medecin:
                patients_du_medecin.append(nom_patient)
        resultat.append({
            "id": med.id, "nom_complet": med.nom_complet, "email": med.email,
            "telephone": med.telephone or "Non renseigné",
            "specialite": med.specialite or "Généraliste",
            "bureau": med.bureau or "Non assigné",
            "nombre_patients": len(patients_du_medecin),
            "liste_patients": patients_du_medecin,
            "rendez_vous": rdvs_details
        })
    return resultat

# Télécharger un document
@app.get("/documents/{document_id}/telecharger")
def telecharger_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(database.Document).filter(
        database.Document.id == document_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    if not os.path.isfile(doc.chemin_stockage):
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    return FileResponse(
        path=doc.chemin_stockage,
        filename=doc.nom_fichier
    )


# Modifier la description d'un document
@app.put("/documents/{document_id}")
def modifier_document(
    document_id: int,
    description: str = None,
    db: Session = Depends(get_db)
):
    doc = db.query(database.Document).filter(
        database.Document.id == document_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    doc.description = description
    db.commit()

    return {"message": "Description modifiée"}


# Supprimer un document
@app.delete("/documents/{document_id}")
def supprimer_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(database.Document).filter(
        database.Document.id == document_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    chemin = doc.chemin_stockage

    db.delete(doc)
    db.commit()

    if chemin and os.path.isfile(chemin):
        os.remove(chemin)

    return {"message": "Document supprimé"}

@app.put("/consultations/{consultation_id}")
def modifier_consultation(
    consultation_id: int,
    diagnostic: str,
    traitement: str,
    db: Session = Depends(get_db)
):
    consultation = db.query(database.Consultation).filter(
        database.Consultation.id == consultation_id
    ).first()

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")

    consultation.diagnostic = diagnostic
    consultation.traitement = traitement

    db.commit()

    return {"message": "Consultation modifiée"}


@app.delete("/consultations/{consultation_id}")
def supprimer_consultation(
    consultation_id: int,
    db: Session = Depends(get_db)
):
    consultation = db.query(database.Consultation).filter(
        database.Consultation.id == consultation_id
    ).first()

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")

    db.delete(consultation)
    db.commit()

    return {"message": "Consultation supprimée"}
@app.delete("/ordonnances/{ordonnance_id}")
def supprimer_ordonnance(
    ordonnance_id: int,
    db: Session = Depends(get_db)
):
    ordonnance = db.query(database.Ordonnance).filter(
        database.Ordonnance.id == ordonnance_id
    ).first()

    if not ordonnance:
        raise HTTPException(
            status_code=404,
            detail="Ordonnance non trouvée"
        )

    db.delete(ordonnance)
    db.commit()

    return {"message": "Ordonnance supprimée"}
@app.put("/ordonnances/{ordonnance_id}")
def modifier_ordonnance(
    ordonnance_id: int,
    medicaments: str,
    posologie: str,
    instructions: str = None,
    db: Session = Depends(get_db)
):
    ordonnance = db.query(database.Ordonnance).filter(
        database.Ordonnance.id == ordonnance_id
    ).first()

    if not ordonnance:
        raise HTTPException(
            status_code=404,
            detail="Ordonnance non trouvée"
        )

    ordonnance.medicaments = medicaments
    ordonnance.posologie = posologie
    ordonnance.instructions = instructions


    db.commit()
    db.refresh(ordonnance)

    return {"message": "Ordonnance modifiée", "id": ordonnance.id}

# ==========================================
# 16. MESURES DES CONSTANTES
# ==========================================

@app.post("/mesures-constantes/")
def creer_mesure_constante(
    data: MesureConstanteCreate,
    db: Session = Depends(get_db)
):
    patient = db.query(database.Patient).filter(
        database.Patient.id == data.id_patient
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    if data.id_consultation is not None:
        consultation = db.query(database.Consultation).filter(
            database.Consultation.id == data.id_consultation,
            database.Consultation.id_patient == data.id_patient
        ).first()

        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation non trouvée")

    mesure = database.MesureConstante(**data.dict())

    db.add(mesure)
    db.commit()
    db.refresh(mesure)

    return {
        "message": "Mesure enregistrée",
        "id": mesure.id,
        "date_mesure": mesure.date_mesure
    }


@app.get("/patients/{patient_id}/mesures-constantes")
def lire_mesures_constantes(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.query(database.Patient).filter(
        database.Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    mesures = db.query(database.MesureConstante).filter(
        database.MesureConstante.id_patient == patient_id
    ).order_by(database.MesureConstante.date_mesure.desc()).all()

    return [
        {
            "id": m.id,
            "id_consultation": m.id_consultation,
            "tension_systolique": m.tension_systolique,
            "tension_diastolique": m.tension_diastolique,
            "frequence_cardiaque": m.frequence_cardiaque,
            "temperature": m.temperature,
            "saturation_oxygene": m.saturation_oxygene,
            "poids": m.poids,
            "taille": m.taille,
            "date_mesure": m.date_mesure
        }
        for m in mesures
    ]

# ==========================================
# 17. ANALYSES DE LABORATOIRE
# ==========================================

@app.post("/analyses-laboratoire/")
def creer_analyse_laboratoire(
    data: AnalyseLaboratoireCreate,
    db: Session = Depends(get_db)
):
    patient = db.query(database.Patient).filter(
        database.Patient.id == data.id_patient
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    if data.id_consultation is not None:
        consultation = db.query(database.Consultation).filter(
            database.Consultation.id == data.id_consultation,
            database.Consultation.id_patient == data.id_patient
        ).first()

        if not consultation:
            raise HTTPException(
                status_code=404,
                detail="Consultation non trouvée pour ce patient"
            )

    analyse = database.AnalyseLaboratoire(
        **data.dict(),
        date_analyse=datetime.now(),
        statut="terminee"
    )

    try:
        db.add(analyse)
        db.commit()
        db.refresh(analyse)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement de l'analyse"
        )

    return {
        "message": "Analyse enregistrée avec succès",
        "id": analyse.id,
        "date_analyse": analyse.date_analyse,
        "statut": analyse.statut
    }


@app.get("/patients/{patient_id}/analyses-laboratoire")
def lire_analyses_laboratoire(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.query(database.Patient).filter(
        database.Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    analyses = db.query(database.AnalyseLaboratoire).filter(
        database.AnalyseLaboratoire.id_patient == patient_id
    ).order_by(
        database.AnalyseLaboratoire.date_analyse.desc()
    ).all()

    return [
        {
            "id": a.id,
            "id_consultation": a.id_consultation,
            "type_analyse": a.type_analyse,
            "nom_parametre": a.nom_parametre,
            "resultat": a.resultat,
            "resultat_texte": a.resultat_texte,
            "unite": a.unite,
            "valeur_reference_min": a.valeur_reference_min,
            "valeur_reference_max": a.valeur_reference_max,
            "date_analyse": a.date_analyse,
            "statut": a.statut
        }
        for a in analyses
    ]
# ==========================================
# 18. GESTION DES HOSPITALISATIONS
# ==========================================

@app.post("/hospitalisations/")
def creer_hospitalisation(
    data: HospitalisationCreate,
    db: Session = Depends(get_db)
):
    patient = db.query(database.Patient).filter(
        database.Patient.id == data.id_patient
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    medecin = db.query(database.Utilisateur).filter(
        database.Utilisateur.id == data.id_medecin,
        database.Utilisateur.role == "medecin"
    ).first()

    if not medecin:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")

    service = db.query(database.ServiceMedical).filter(
        database.ServiceMedical.id == data.id_service
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service médical non trouvé")

    if data.id_lit is not None:
        lit = db.query(database.Lit).filter(
            database.Lit.id == data.id_lit
        ).first()

        if not lit:
            raise HTTPException(status_code=404, detail="Lit non trouvé")

        if lit.statut != "disponible":
            raise HTTPException(status_code=409, detail="Ce lit n'est pas disponible")

        salle = db.query(database.SalleMedicale).filter(
            database.SalleMedicale.id == lit.id_salle
        ).first()

        if not salle or salle.id_service != data.id_service:
            raise HTTPException(
                status_code=400,
                detail="Le lit ne correspond pas au service sélectionné"
            )

    hospitalisation = database.Hospitalisation(
        **data.dict(),
        date_entree=datetime.now(),
        statut="en_cours"
    )

    try:
        db.add(hospitalisation)

        if data.id_lit is not None:
            lit.statut = "occupe"

        db.commit()
        db.refresh(hospitalisation)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la création de l'hospitalisation"
        )

    return {
        "message": "Hospitalisation créée avec succès",
        "id": hospitalisation.id,
        "statut": hospitalisation.statut,
        "date_entree": hospitalisation.date_entree
    }


@app.get("/hospitalisations/")
def lister_hospitalisations(
    db: Session = Depends(get_db)
):
    hospitalisations = db.query(database.Hospitalisation).order_by(
        database.Hospitalisation.date_entree.desc()
    ).all()

    return [
        {
            "id": h.id,
            "id_patient": h.id_patient,
            "id_medecin": h.id_medecin,
            "id_service": h.id_service,
            "id_lit": h.id_lit,
            "date_entree": h.date_entree,
            "date_sortie": h.date_sortie,
            "motif": h.motif,
            "statut": h.statut
        }
        for h in hospitalisations
    ]


@app.get("/patients/{patient_id}/hospitalisations")
def hospitalisations_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.query(database.Patient).filter(
        database.Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    hospitalisations = db.query(database.Hospitalisation).filter(
        database.Hospitalisation.id_patient == patient_id
    ).order_by(
        database.Hospitalisation.date_entree.desc()
    ).all()

    return [
        {
            "id": h.id,
            "id_medecin": h.id_medecin,
            "id_service": h.id_service,
            "id_lit": h.id_lit,
            "date_entree": h.date_entree,
            "date_sortie": h.date_sortie,
            "motif": h.motif,
            "statut": h.statut
        }
        for h in hospitalisations
    ]


@app.patch("/hospitalisations/{hospitalisation_id}/sortie")
def terminer_hospitalisation(
    hospitalisation_id: int,
    db: Session = Depends(get_db)
):
    hospitalisation = db.query(database.Hospitalisation).filter(
        database.Hospitalisation.id == hospitalisation_id
    ).first()

    if not hospitalisation:
        raise HTTPException(
            status_code=404,
            detail="Hospitalisation non trouvée"
        )

    if hospitalisation.statut != "en_cours":
        raise HTTPException(
            status_code=409,
            detail="Cette hospitalisation est déjà terminée"
        )

    try:
        hospitalisation.date_sortie = datetime.now()
        hospitalisation.statut = "terminee"

        if hospitalisation.id_lit is not None:
            lit = db.query(database.Lit).filter(
                database.Lit.id == hospitalisation.id_lit
            ).first()

            if lit:
                lit.statut = "disponible"

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la sortie du patient"
        )

    return {
        "message": "Hospitalisation terminée avec succès",
        "id": hospitalisation.id,
        "statut": hospitalisation.statut,
        "date_sortie": hospitalisation.date_sortie
    }
# ==========================================
# 19. SATISFACTION DES PATIENTS
# ==========================================

@app.post("/satisfaction/")
def creer_satisfaction(
    data: SatisfactionPatientCreate,
    db: Session = Depends(get_db)
):
    if data.note < 1 or data.note > 5:
        raise HTTPException(
            status_code=400,
            detail="La note doit être comprise entre 1 et 5"
        )

    patient = db.query(database.Patient).filter(
        database.Patient.id == data.id_patient
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")

    if data.id_rendez_vous is not None:
        rendez_vous = db.query(database.RendezVous).filter(
            database.RendezVous.id == data.id_rendez_vous,
            database.RendezVous.id_patient == data.id_patient
        ).first()

        if not rendez_vous:
            raise HTTPException(
                status_code=404,
                detail="Rendez-vous non trouvé pour ce patient"
            )

    satisfaction = database.SatisfactionPatient(
        **data.dict(),
        date_evaluation=datetime.now()
    )

    try:
        db.add(satisfaction)
        db.commit()
        db.refresh(satisfaction)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement"
        )

    return {
        "message": "Évaluation enregistrée avec succès",
        "id": satisfaction.id,
        "note": satisfaction.note,
        "date_evaluation": satisfaction.date_evaluation
    }


@app.get("/satisfaction/")
def lister_satisfactions(
    db: Session = Depends(get_db)
):
    evaluations = db.query(database.SatisfactionPatient).order_by(
        database.SatisfactionPatient.date_evaluation.desc()
    ).all()

    return [
        {
            "id": e.id,
            "id_patient": e.id_patient,
            "id_rendez_vous": e.id_rendez_vous,
            "note": e.note,
            "commentaire": e.commentaire,
            "date_evaluation": e.date_evaluation
        }
        for e in evaluations
    ]


@app.get("/satisfaction/statistiques")
def statistiques_satisfaction(
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    resultat = db.query(
        func.count(database.SatisfactionPatient.id),
        func.avg(database.SatisfactionPatient.note)
    ).first()

    total = resultat[0] or 0
    moyenne = round(float(resultat[1] or 0), 2)

    repartition = db.query(
        database.SatisfactionPatient.note,
        func.count(database.SatisfactionPatient.id)
    ).group_by(
        database.SatisfactionPatient.note
    ).order_by(
        database.SatisfactionPatient.note
    ).all()

    return {
        "nombre_evaluations": total,
        "note_moyenne": moyenne,
        "repartition": [
            {"note": note, "nombre": nombre}
            for note, nombre in repartition
        ]
    }
# ==========================================
# 20. GESTION DES MÉDICAMENTS
# ==========================================

@app.post("/medicaments/")
def creer_medicament(
    data: MedicamentCreate,
    db: Session = Depends(get_db)
):
    if data.stock_actuel < 0 or data.seuil_alerte < 0:
        raise HTTPException(
            status_code=400,
            detail="Le stock et le seuil doivent être positifs"
        )

    if data.prix_unitaire < 0:
        raise HTTPException(
            status_code=400,
            detail="Le prix ne peut pas être négatif"
        )

    medicament = database.Medicament(**data.dict())

    try:
        db.add(medicament)
        db.commit()
        db.refresh(medicament)

        if data.stock_actuel > 0:
            mouvement = database.MouvementStock(
                id_medicament=medicament.id,
                type_mouvement="entree",
                quantite=data.stock_actuel,
                motif="Stock initial"
            )
            db.add(mouvement)
            db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la création du médicament"
        )

    return {
        "message": "Médicament ajouté avec succès",
        "id": medicament.id,
        "nom": medicament.nom,
        "stock_actuel": medicament.stock_actuel
    }


@app.get("/medicaments/")
def lister_medicaments(
    db: Session = Depends(get_db)
):
    medicaments = db.query(database.Medicament).order_by(
        database.Medicament.nom
    ).all()

    return [
        {
            "id": m.id,
            "nom": m.nom,
            "categorie": m.categorie,
            "laboratoire": m.laboratoire,
            "forme": m.forme,
            "dosage": m.dosage,
            "stock_actuel": m.stock_actuel,
            "seuil_alerte": m.seuil_alerte,
            "prix_unitaire": float(m.prix_unitaire or 0),
            "date_peremption": m.date_peremption
        }
        for m in medicaments
    ]


@app.get("/medicaments/alertes")
def alertes_stock(
    db: Session = Depends(get_db)
):
    medicaments = db.query(database.Medicament).filter(
        database.Medicament.stock_actuel <=
        database.Medicament.seuil_alerte
    ).order_by(
        database.Medicament.stock_actuel
    ).all()

    return [
        {
            "id": m.id,
            "nom": m.nom,
            "stock_actuel": m.stock_actuel,
            "seuil_alerte": m.seuil_alerte,
            "alerte": "Rupture" if m.stock_actuel == 0 else "Stock faible"
        }
        for m in medicaments
    ]


@app.get("/medicaments/statistiques")
def statistiques_medicaments(
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    total = db.query(func.count(database.Medicament.id)).scalar() or 0

    stock_total = db.query(
        func.sum(database.Medicament.stock_actuel)
    ).scalar() or 0

    valeur_stock = db.query(
        func.sum(
            database.Medicament.stock_actuel *
            database.Medicament.prix_unitaire
        )
    ).scalar() or 0

    alertes = db.query(database.Medicament).filter(
        database.Medicament.stock_actuel <=
        database.Medicament.seuil_alerte
    ).count()

    return {
        "nombre_medicaments": total,
        "quantite_totale": int(stock_total),
        "valeur_stock": round(float(valeur_stock), 2),
        "nombre_alertes": alertes
    }
# ==========================================
# 21. MOUVEMENTS DE STOCK
# ==========================================

@app.post("/mouvements-stock/")
def creer_mouvement_stock(
    data: MouvementStockCreate,
    db: Session = Depends(get_db)
):
    if data.quantite <= 0:
        raise HTTPException(
            status_code=400,
            detail="La quantité doit être supérieure à zéro"
        )

    if data.type_mouvement not in ["entree", "sortie", "ajustement"]:
        raise HTTPException(
            status_code=400,
            detail="Type invalide : entree, sortie ou ajustement"
        )

    medicament = db.query(database.Medicament).filter(
        database.Medicament.id == data.id_medicament
    ).with_for_update().first()

    if not medicament:
        raise HTTPException(status_code=404, detail="Médicament non trouvé")

    if data.id_utilisateur is not None:
        utilisateur = db.query(database.Utilisateur).filter(
            database.Utilisateur.id == data.id_utilisateur
        ).first()

        if not utilisateur:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    ancien_stock = medicament.stock_actuel

    if data.type_mouvement == "entree":
        nouveau_stock = ancien_stock + data.quantite

    elif data.type_mouvement == "sortie":
        nouveau_stock = ancien_stock - data.quantite

        if nouveau_stock < 0:
            raise HTTPException(
                status_code=400,
                detail="Stock insuffisant"
            )

    else:
        # Ajustement : la quantité représente le nouveau stock total.
        nouveau_stock = data.quantite

    mouvement = database.MouvementStock(
        id_medicament=data.id_medicament,
        id_utilisateur=data.id_utilisateur,
        type_mouvement=data.type_mouvement,
        quantite=data.quantite,
        motif=data.motif
    )

    try:
        medicament.stock_actuel = nouveau_stock
        db.add(mouvement)
        db.commit()
        db.refresh(mouvement)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement du mouvement"
        )

    return {
        "message": "Mouvement enregistré avec succès",
        "id_mouvement": mouvement.id,
        "ancien_stock": ancien_stock,
        "nouveau_stock": nouveau_stock,
        "type_mouvement": data.type_mouvement
    }


@app.get("/mouvements-stock/")
def lister_mouvements_stock(
    db: Session = Depends(get_db)
):
    mouvements = db.query(database.MouvementStock).order_by(
        database.MouvementStock.date_mouvement.desc()
    ).all()

    return [
        {
            "id": m.id,
            "id_medicament": m.id_medicament,
            "id_utilisateur": m.id_utilisateur,
            "type_mouvement": m.type_mouvement,
            "quantite": m.quantite,
            "date_mouvement": m.date_mouvement,
            "motif": m.motif
        }
        for m in mouvements
    ]


@app.get("/medicaments/{medicament_id}/mouvements")
def historique_medicament(
    medicament_id: int,
    db: Session = Depends(get_db)
):
    medicament = db.query(database.Medicament).filter(
        database.Medicament.id == medicament_id
    ).first()

    if not medicament:
        raise HTTPException(status_code=404, detail="Médicament non trouvé")

    mouvements = db.query(database.MouvementStock).filter(
        database.MouvementStock.id_medicament == medicament_id
    ).order_by(
        database.MouvementStock.date_mouvement.desc()
    ).all()

    return [
        {
            "id": m.id,
            "type_mouvement": m.type_mouvement,
            "quantite": m.quantite,
            "date_mouvement": m.date_mouvement,
            "motif": m.motif
        }
        for m in mouvements
    ]
# ==========================================
# 22. LIGNES D'ORDONNANCE
# ==========================================

@app.post("/lignes-ordonnance/")
def creer_ligne_ordonnance(
    data: LigneOrdonnanceCreate,
    db: Session = Depends(get_db)
):
    if data.quantite <= 0:
        raise HTTPException(
            status_code=400,
            detail="La quantité doit être supérieure à zéro"
        )

    if data.duree_jours is not None and data.duree_jours <= 0:
        raise HTTPException(
            status_code=400,
            detail="La durée doit être supérieure à zéro"
        )

    ordonnance = db.query(database.Ordonnance).filter(
        database.Ordonnance.id == data.id_ordonnance
    ).first()

    if not ordonnance:
        raise HTTPException(status_code=404, detail="Ordonnance non trouvée")

    medicament = db.query(database.Medicament).filter(
        database.Medicament.id == data.id_medicament
    ).first()

    if not medicament:
        raise HTTPException(status_code=404, detail="Médicament non trouvé")

    ligne_existante = db.query(database.LigneOrdonnance).filter(
        database.LigneOrdonnance.id_ordonnance == data.id_ordonnance,
        database.LigneOrdonnance.id_medicament == data.id_medicament
    ).first()

    if ligne_existante:
        raise HTTPException(
            status_code=409,
            detail="Ce médicament existe déjà dans cette ordonnance"
        )

    ligne = database.LigneOrdonnance(**data.dict())

    try:
        db.add(ligne)
        db.commit()
        db.refresh(ligne)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'ajout du médicament à l'ordonnance"
        )

    return {
        "message": "Médicament ajouté à l'ordonnance",
        "id": ligne.id,
        "id_ordonnance": ligne.id_ordonnance,
        "id_medicament": ligne.id_medicament
    }


@app.get("/ordonnances/{ordonnance_id}/lignes")
def lire_lignes_ordonnance(
    ordonnance_id: int,
    db: Session = Depends(get_db)
):
    ordonnance = db.query(database.Ordonnance).filter(
        database.Ordonnance.id == ordonnance_id
    ).first()

    if not ordonnance:
        raise HTTPException(status_code=404, detail="Ordonnance non trouvée")

    lignes = db.query(database.LigneOrdonnance).filter(
        database.LigneOrdonnance.id_ordonnance == ordonnance_id
    ).all()

    return [
        {
            "id": ligne.id,
            "id_medicament": ligne.id_medicament,
            "nom_medicament": ligne.medicament.nom,
            "dosage": ligne.medicament.dosage,
            "quantite": ligne.quantite,
            "posologie": ligne.posologie,
            "duree_jours": ligne.duree_jours
        }
        for ligne in lignes
    ]


@app.delete("/lignes-ordonnance/{ligne_id}")
def supprimer_ligne_ordonnance(
    ligne_id: int,
    db: Session = Depends(get_db)
):
    ligne = db.query(database.LigneOrdonnance).filter(
        database.LigneOrdonnance.id == ligne_id
    ).first()

    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")

    try:
        db.delete(ligne)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression"
        )

    return {"message": "Ligne d'ordonnance supprimée"}
# ==========================================
# 23. GESTION DES PAIEMENTS
# ==========================================

@app.post("/paiements/")
def creer_paiement(
    data: PaiementCreate,
    db: Session = Depends(get_db)
):
    if data.montant <= 0:
        raise HTTPException(
            status_code=400,
            detail="Le montant doit être supérieur à zéro"
        )

    facture = db.query(database.Facture).filter(
        database.Facture.id == data.id_facture
    ).first()

    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    paiements_valides = db.query(database.Paiement).filter(
        database.Paiement.id_facture == data.id_facture,
        database.Paiement.statut == "valide"
    ).all()

    montant_deja_paye = sum(float(p.montant) for p in paiements_valides)
    montant_restant = float(facture.montant) - montant_deja_paye

    if data.montant > montant_restant:
        raise HTTPException(
            status_code=400,
            detail=f"Paiement supérieur au montant restant ({montant_restant:.2f})"
        )

    paiement = database.Paiement(
        **data.dict(),
        date_paiement=datetime.now(),
        statut="valide"
    )

    try:
        db.add(paiement)
        db.flush()

        nouveau_total = montant_deja_paye + data.montant

        if nouveau_total >= float(facture.montant):
            facture.statut_paiement = "paye"
        elif nouveau_total > 0:
            facture.statut_paiement = "partiellement_paye"

        db.commit()
        db.refresh(paiement)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement du paiement"
        )

    return {
        "message": "Paiement enregistré avec succès",
        "id_paiement": paiement.id,
        "montant_paye": data.montant,
        "total_paye": round(nouveau_total, 2),
        "reste_a_payer": round(
            float(facture.montant) - nouveau_total, 2
        ),
        "statut_facture": facture.statut_paiement
    }


@app.get("/paiements/")
def lister_paiements(
    db: Session = Depends(get_db)
):
    paiements = db.query(database.Paiement).order_by(
        database.Paiement.date_paiement.desc()
    ).all()

    return [
        {
            "id": p.id,
            "id_facture": p.id_facture,
            "montant": float(p.montant),
            "mode_paiement": p.mode_paiement,
            "date_paiement": p.date_paiement,
            "reference": p.reference,
            "statut": p.statut
        }
        for p in paiements
    ]


@app.get("/factures/{facture_id}/paiements")
def paiements_facture(
    facture_id: int,
    db: Session = Depends(get_db)
):
    facture = db.query(database.Facture).filter(
        database.Facture.id == facture_id
    ).first()

    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    paiements = db.query(database.Paiement).filter(
        database.Paiement.id_facture == facture_id
    ).order_by(
        database.Paiement.date_paiement.desc()
    ).all()

    total_paye = sum(
        float(p.montant)
        for p in paiements
        if p.statut == "valide"
    )

    return {
        "id_facture": facture_id,
        "montant_facture": float(facture.montant),
        "total_paye": round(total_paye, 2),
        "reste_a_payer": round(
            max(0, float(facture.montant) - total_paye), 2
        ),
        "paiements": [
            {
                "id": p.id,
                "montant": float(p.montant),
                "mode_paiement": p.mode_paiement,
                "date_paiement": p.date_paiement,
                "statut": p.statut
            }
            for p in paiements
        ]
    }
# ==========================================
# 24. GESTION DES DEPENSES
# ==========================================

@app.post("/depenses/")
def creer_depense(
    data: DepenseCreate,
    db: Session = Depends(get_db)
):
    if data.montant <= 0:
        raise HTTPException(
            status_code=400,
            detail="Le montant doit être supérieur à zéro"
        )

    if not data.categorie.strip():
        raise HTTPException(
            status_code=400,
            detail="La catégorie est obligatoire"
        )

    if data.id_utilisateur is not None:
        utilisateur = db.query(database.Utilisateur).filter(
            database.Utilisateur.id == data.id_utilisateur
        ).first()

        if not utilisateur:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur non trouvé"
            )

    depense = database.Depense(
        categorie=data.categorie.strip(),
        description=data.description,
        montant=data.montant,
        id_utilisateur=data.id_utilisateur,
        date_depense=datetime.now()
    )

    try:
        db.add(depense)
        db.commit()
        db.refresh(depense)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement de la dépense"
        )

    return {
        "message": "Dépense enregistrée avec succès",
        "id": depense.id,
        "categorie": depense.categorie,
        "montant": float(depense.montant),
        "date_depense": depense.date_depense
    }


@app.get("/depenses/")
def lister_depenses(
    db: Session = Depends(get_db)
):
    depenses = db.query(database.Depense).order_by(
        database.Depense.date_depense.desc()
    ).all()

    return [
        {
            "id": d.id,
            "categorie": d.categorie,
            "description": d.description,
            "montant": float(d.montant),
            "date_depense": d.date_depense,
            "id_utilisateur": d.id_utilisateur
        }
        for d in depenses
    ]


@app.get("/depenses/statistiques")
def statistiques_depenses(
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    total = db.query(
        func.sum(database.Depense.montant)
    ).scalar() or 0

    repartition = db.query(
        database.Depense.categorie,
        func.sum(database.Depense.montant)
    ).group_by(
        database.Depense.categorie
    ).all()

    return {
        "total_depenses": round(float(total), 2),
        "repartition": [
            {
                "categorie": categorie,
                "montant": round(float(montant), 2)
            }
            for categorie, montant in repartition
        ]
    }
# ==========================================
# 25. SERVICES MEDICAUX
# ==========================================

@app.post("/services-medicaux/")
def creer_service(
    data: ServiceMedicalCreate,
    db: Session = Depends(get_db)
):
    if data.capacite < 0:
        raise HTTPException(status_code=400, detail="Capacité invalide")

    if not data.nom.strip():
        raise HTTPException(status_code=400, detail="Nom obligatoire")

    if data.responsable_id is not None:
        responsable = db.query(database.Utilisateur).filter(
            database.Utilisateur.id == data.responsable_id
        ).first()

        if not responsable:
            raise HTTPException(status_code=404, detail="Responsable non trouvé")

    service = database.ServiceMedical(**data.dict())

    try:
        db.add(service)
        db.commit()
        db.refresh(service)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer le service")

    return {"message": "Service créé", "id": service.id, "nom": service.nom}


@app.get("/services-medicaux/")
def lister_services(db: Session = Depends(get_db)):
    services = db.query(database.ServiceMedical).all()

    return [
        {
            "id": s.id,
            "nom": s.nom,
            "description": s.description,
            "responsable_id": s.responsable_id,
            "capacite": s.capacite,
            "statut": s.statut
        }
        for s in services
    ]


# ==========================================
# 26. SALLES MEDICALES
# ==========================================

@app.post("/salles-medicales/")
def creer_salle(
    data: SalleMedicaleCreate,
    db: Session = Depends(get_db)
):
    if data.capacite <= 0:
        raise HTTPException(status_code=400, detail="Capacité invalide")

    service = db.query(database.ServiceMedical).filter(
        database.ServiceMedical.id == data.id_service
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service non trouvé")

    salle = database.SalleMedicale(**data.dict())

    try:
        db.add(salle)
        db.commit()
        db.refresh(salle)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer la salle")

    return {"message": "Salle créée", "id": salle.id, "nom": salle.nom}


@app.get("/salles-medicales/")
def lister_salles(db: Session = Depends(get_db)):
    salles = db.query(database.SalleMedicale).all()

    return [
        {
            "id": s.id,
            "id_service": s.id_service,
            "nom": s.nom,
            "type_salle": s.type_salle,
            "capacite": s.capacite,
            "statut": s.statut
        }
        for s in salles
    ]


# ==========================================
# 27. LITS
# ==========================================

@app.post("/lits/")
def creer_lit(
    data: LitCreate,
    db: Session = Depends(get_db)
):
    salle = db.query(database.SalleMedicale).filter(
        database.SalleMedicale.id == data.id_salle
    ).first()

    if not salle:
        raise HTTPException(status_code=404, detail="Salle non trouvée")

    lit = database.Lit(**data.dict())

    try:
        db.add(lit)
        db.commit()
        db.refresh(lit)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de créer le lit")

    return {
        "message": "Lit créé",
        "id": lit.id,
        "numero": lit.numero,
        "statut": lit.statut
    }


@app.get("/lits/")
def lister_lits(db: Session = Depends(get_db)):
    lits = db.query(database.Lit).all()

    return [
        {
            "id": l.id,
            "id_salle": l.id_salle,
            "numero": l.numero,
            "type_lit": l.type_lit,
            "statut": l.statut
        }
        for l in lits
    ]


# ==========================================
# 28. STATISTIQUES D'OCCUPATION
# ==========================================

@app.get("/infrastructure/statistiques")
def statistiques_infrastructure(
    db: Session = Depends(get_db)
):
    total_services = db.query(database.ServiceMedical).count()
    total_salles = db.query(database.SalleMedicale).count()
    total_lits = db.query(database.Lit).count()

    lits_occupes = db.query(database.Lit).filter(
        database.Lit.statut == "occupe"
    ).count()

    lits_disponibles = db.query(database.Lit).filter(
        database.Lit.statut == "disponible"
    ).count()

    taux = (
        round((lits_occupes / total_lits) * 100, 2)
        if total_lits > 0 else 0
    )

    return {
        "nombre_services": total_services,
        "nombre_salles": total_salles,
        "nombre_lits": total_lits,
        "lits_occupes": lits_occupes,
        "lits_disponibles": lits_disponibles,
        "taux_occupation": taux
    }
# ==========================================
# 29. JOURNAL D'ACTIVITE
# ==========================================

@app.post("/journal-activite/")
def creer_journal_activite(
    data: JournalActiviteCreate,
    db: Session = Depends(get_db)
):
    if not data.action.strip() or not data.module.strip():
        raise HTTPException(
            status_code=400,
            detail="L'action et le module sont obligatoires"
        )

    if data.statut not in ["succes", "echec"]:
        raise HTTPException(
            status_code=400,
            detail="Statut invalide : succes ou echec"
        )

    if data.id_utilisateur is not None:
        utilisateur = db.query(database.Utilisateur).filter(
            database.Utilisateur.id == data.id_utilisateur
        ).first()

        if not utilisateur:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur non trouvé"
            )

    journal = database.JournalActivite(
        **data.dict(),
        date_action=datetime.now()
    )

    try:
        db.add(journal)
        db.commit()
        db.refresh(journal)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement de l'activité"
        )

    return {
        "message": "Activité enregistrée",
        "id": journal.id,
        "date_action": journal.date_action
    }


@app.get("/journal-activite/")
def lister_journal_activite(
    db: Session = Depends(get_db)
):
    activites = db.query(database.JournalActivite).order_by(
        database.JournalActivite.date_action.desc()
    ).limit(500).all()

    return [
        {
            "id": a.id,
            "id_utilisateur": a.id_utilisateur,
            "action": a.action,
            "module": a.module,
            "description": a.description,
            "date_action": a.date_action,
            "statut": a.statut
        }
        for a in activites
    ]


@app.get("/journal-activite/statistiques")
def statistiques_journal_activite(
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    total = db.query(
        func.count(database.JournalActivite.id)
    ).scalar() or 0

    par_module = db.query(
        database.JournalActivite.module,
        func.count(database.JournalActivite.id)
    ).group_by(
        database.JournalActivite.module
    ).all()

    par_statut = db.query(
        database.JournalActivite.statut,
        func.count(database.JournalActivite.id)
    ).group_by(
        database.JournalActivite.statut
    ).all()

    return {
        "total_activites": total,
        "par_module": [
            {"module": module, "nombre": nombre}
            for module, nombre in par_module
        ],
        "par_statut": [
            {"statut": statut, "nombre": nombre}
            for statut, nombre in par_statut
        ]
    }
# ============================================================
# ANALYTICS - TABLEAU DE BORD GLOBAL
# ============================================================

def _analytics_parse_date(value):
    """
    Convertit une date String ou DateTime en datetime.
    Retourne None si la date est absente ou invalide.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M:%S",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except (ValueError, TypeError):
            continue

    return None


def _analytics_monthly_count(rows, date_attribute):
    """
    Compte les enregistrements par mois.
    Fonctionne avec les colonnes String et DateTime.
    """
    counts = Counter()

    for row in rows:
        parsed_date = _analytics_parse_date(
            getattr(row, date_attribute, None)
        )

        if parsed_date:
            month = parsed_date.strftime("%Y-%m")
            counts[month] += 1

    return [
        {"mois": month, "total": counts[month]}
        for month in sorted(counts)
    ]


def _analytics_monthly_sum(rows, date_attribute, amount_attribute):
    """
    Calcule une somme financière par mois.
    """
    totals = {}

    for row in rows:
        parsed_date = _analytics_parse_date(
            getattr(row, date_attribute, None)
        )

        if not parsed_date:
            continue

        month = parsed_date.strftime("%Y-%m")
        amount = getattr(row, amount_attribute, 0) or 0

        try:
            amount = float(amount)
        except (ValueError, TypeError):
            amount = 0.0

        totals[month] = totals.get(month, 0.0) + amount

    return [
        {"mois": month, "montant": round(totals[month], 2)}
        for month in sorted(totals)
    ]


def _analytics_status_distribution(rows, attribute):
    """
    Renvoie le nombre d'enregistrements par statut.
    """
    counts = Counter()

    for row in rows:
        status = getattr(row, attribute, None) or "non_defini"
        counts[str(status)] += 1

    return [
        {"statut": status, "total": total}
        for status, total in counts.items()
    ]


@app.get("/analytics/dashboard")
def analytics_dashboard(db: Session = Depends(get_db)):

    # --------------------------------------------------------
    # 1. Récupération des données
    # --------------------------------------------------------

    patients = db.query(database.Patient).all()
    rendez_vous = db.query(database.RendezVous).all()
    consultations = db.query(database.Consultation).all()
    factures = db.query(database.Facture).all()
    paiements = db.query(database.Paiement).all()
    depenses = db.query(database.Depense).all()
    medicaments = db.query(database.Medicament).all()
    mouvements = db.query(database.MouvementStock).all()
    hospitalisations = db.query(database.Hospitalisation).all()
    lits = db.query(database.Lit).all()
    satisfaction = db.query(database.SatisfactionPatient).all()
    journal = db.query(database.JournalActivite).all()

    # --------------------------------------------------------
    # 2. PATIENTS
    # --------------------------------------------------------

    total_patients = len(patients)

    # --------------------------------------------------------
    # 3. RENDEZ-VOUS
    # --------------------------------------------------------

    rendez_vous_par_statut = _analytics_status_distribution(
        rendez_vous, "statut"
    )

    rendez_vous_par_mois = _analytics_monthly_count(
        rendez_vous, "date_heure"
    )

    # --------------------------------------------------------
    # 4. CONSULTATIONS PAR MEDECIN
    # --------------------------------------------------------

    consultations_par_medecin = (
        db.query(
            database.Utilisateur.nom_complet,
            database.Utilisateur.specialite,
            func.count(database.Consultation.id)
        )
        .join(
            database.Consultation,
            database.Consultation.id_medecin == database.Utilisateur.id
        )
        .group_by(
            database.Utilisateur.id,
            database.Utilisateur.nom_complet,
            database.Utilisateur.specialite
        )
        .all()
    )

    consultations_medecins = [
        {
            "medecin": nom or "Non renseigné",
            "specialite": specialite or "Non renseignée",
            "total": total
        }
        for nom, specialite, total in consultations_par_medecin
    ]

    consultations_par_mois = _analytics_monthly_count(
        consultations, "date_consultation"
    )

    # --------------------------------------------------------
    # 5. FINANCES
    # --------------------------------------------------------

    montant_factures = sum(
        float(f.montant or 0)
        for f in factures
    )

    paiements_valides = [
        p for p in paiements
        if str(p.statut or "").strip().lower() == "valide"
    ]

    montant_encaisse = sum(
        float(p.montant or 0)
        for p in paiements_valides
    )

    montant_depenses = sum(
        float(d.montant or 0)
        for d in depenses
    )

    solde_net = montant_encaisse - montant_depenses

    paiements_par_mois = _analytics_monthly_sum(
        paiements_valides, "date_paiement", "montant"
    )

    depenses_par_mois = _analytics_monthly_sum(
        depenses, "date_depense", "montant"
    )

    depenses_par_categorie = Counter()

    for depense in depenses:
        categorie = depense.categorie or "Non classée"
        depenses_par_categorie[categorie] += float(
            depense.montant or 0
        )

    repartition_depenses = [
        {
            "categorie": categorie,
            "montant": round(montant, 2)
        }
        for categorie, montant in depenses_par_categorie.items()
    ]

    # --------------------------------------------------------
    # 6. PHARMACIE
    # --------------------------------------------------------

    total_medicaments = len(medicaments)

    stock_total = sum(
        int(m.stock_actuel or 0)
        for m in medicaments
    )

    medicaments_en_alerte = [
        {
            "id": m.id,
            "nom": m.nom,
            "stock": m.stock_actuel,
            "seuil": m.seuil_alerte
        }
        for m in medicaments
        if (m.stock_actuel or 0) <= (m.seuil_alerte or 0)
    ]

    mouvements_par_type = Counter(
        str(m.type_mouvement or "non_defini")
        for m in mouvements
    )

    repartition_mouvements = [
        {"type": type_mouvement, "total": total}
        for type_mouvement, total in mouvements_par_type.items()
    ]

    # --------------------------------------------------------
    # 7. HOSPITALISATIONS ET LITS
    # --------------------------------------------------------

    hospitalisations_en_cours = sum(
        1 for h in hospitalisations
        if str(h.statut or "").strip().lower() == "en_cours"
    )

    lits_par_statut = _analytics_status_distribution(
        lits, "statut"
    )

    lits_occupes = sum(
        1 for lit in lits
        if str(lit.statut or "").strip().lower()
        in ("occupe", "occupé")
    )

    lits_disponibles = sum(
        1 for lit in lits
        if str(lit.statut or "").strip().lower()
        in ("disponible", "libre")
    )

    total_lits = len(lits)

    taux_occupation = (
        round((lits_occupes / total_lits) * 100, 2)
        if total_lits > 0 else 0
    )

    # --------------------------------------------------------
    # 8. SATISFACTION
    # --------------------------------------------------------

    notes = [
        int(s.note)
        for s in satisfaction
        if s.note is not None
    ]

    note_moyenne = (
        round(sum(notes) / len(notes), 2)
        if notes else 0
    )

    distribution_satisfaction = [
        {
            "note": note,
            "total": notes.count(note)
        }
        for note in range(1, 6)
    ]

    # --------------------------------------------------------
    # 9. JOURNAL D'ACTIVITE
    # --------------------------------------------------------

    activites_par_module = Counter(
        str(j.module or "Non défini")
        for j in journal
    )

    activites_par_action = Counter(
        str(j.action or "Non définie")
        for j in journal
    )

    repartition_modules = [
        {"module": module, "total": total}
        for module, total in activites_par_module.items()
    ]

    repartition_actions = [
        {"action": action, "total": total}
        for action, total in activites_par_action.items()
    ]

    # --------------------------------------------------------
    # 10. REPONSE GLOBALE
    # --------------------------------------------------------

    return {
        "indicateurs": {
            "total_patients": total_patients,
            "total_rendez_vous": len(rendez_vous),
            "total_consultations": len(consultations),
            "total_factures": len(factures),
            "montant_factures": round(montant_factures, 2),
            "montant_encaisse": round(montant_encaisse, 2),
            "total_depenses": round(montant_depenses, 2),
            "solde_net": round(solde_net, 2),
            "total_medicaments": total_medicaments,
            "stock_total": stock_total,
            "medicaments_en_alerte": len(medicaments_en_alerte),
            "hospitalisations_en_cours": hospitalisations_en_cours,
            "total_lits": total_lits,
            "lits_occupes": lits_occupes,
            "lits_disponibles": lits_disponibles,
            "taux_occupation": taux_occupation,
            "note_satisfaction_moyenne": note_moyenne,
            "total_evaluations": len(notes),
            "total_activites": len(journal)
        },

        "rendez_vous": {
            "par_statut": rendez_vous_par_statut,
            "par_mois": rendez_vous_par_mois
        },

        "consultations": {
            "par_medecin": consultations_medecins,
            "par_mois": consultations_par_mois
        },

        "finance": {
            "paiements_par_mois": paiements_par_mois,
            "depenses_par_mois": depenses_par_mois,
            "depenses_par_categorie": repartition_depenses
        },

        "pharmacie": {
            "medicaments_en_alerte": medicaments_en_alerte,
            "mouvements_par_type": repartition_mouvements
        },

        "hospitalisations": {
            "lits_par_statut": lits_par_statut
        },

        "satisfaction": {
            "distribution": distribution_satisfaction
        },

        "activite": {
            "par_module": repartition_modules,
            "par_action": repartition_actions
        }
    }
# ==========================================================
# MODIFICATION ET SUPPRESSION DES SALLES
# ==========================================================

@app.put("/salles-medicales/{salle_id}")
def modifier_salle(
    salle_id: int,
    donnees: SalleMedicaleUpdate,
    db: Session = Depends(get_db)
):
    salle = db.query(database.SalleMedicale).filter(
        database.SalleMedicale.id == salle_id
    ).first()

    if not salle:
        raise HTTPException(404, "Salle introuvable")

    modifications = donnees.dict(exclude_unset=True)

    if "capacite" in modifications:
        if modifications["capacite"] is None or modifications["capacite"] <= 0:
            raise HTTPException(400, "Capacité invalide")

        nombre_lits = db.query(database.Lit).filter(
            database.Lit.id_salle == salle_id
        ).count()

        if modifications["capacite"] < nombre_lits:
            raise HTTPException(
                400,
                f"La capacité ne peut pas être inférieure au nombre de lits ({nombre_lits})"
            )

    if "id_service" in modifications:
        service = db.query(database.ServiceMedical).filter(
            database.ServiceMedical.id == modifications["id_service"]
        ).first()

        if not service:
            raise HTTPException(404, "Service introuvable")

    for champ, valeur in modifications.items():
        setattr(salle, champ, valeur)

    try:
        db.commit()
        db.refresh(salle)
        return {"message": "Salle modifiée avec succès", "id": salle.id}
    except Exception:
        db.rollback()
        raise HTTPException(400, "Erreur lors de la modification")


@app.delete("/salles-medicales/{salle_id}")
def supprimer_salle(
    salle_id: int,
    db: Session = Depends(get_db)
):
    salle = db.query(database.SalleMedicale).filter(
        database.SalleMedicale.id == salle_id
    ).first()

    if not salle:
        raise HTTPException(404, "Salle introuvable")

    nombre_lits = db.query(database.Lit).filter(
        database.Lit.id_salle == salle_id
    ).count()

    if nombre_lits > 0:
        raise HTTPException(
            400,
            "Impossible de supprimer cette salle : elle contient encore des lits."
        )

    db.delete(salle)

    try:
        db.commit()
        return {"message": "Salle supprimée avec succès"}
    except Exception:
        db.rollback()
        raise HTTPException(400, "Erreur lors de la suppression")
    # ==========================================================
# MODIFICATION ET SUPPRESSION DES LITS
# ==========================================================

@app.put("/lits/{lit_id}")
def modifier_lit(
    lit_id: int,
    donnees: LitUpdate,
    db: Session = Depends(get_db)
):
    lit = db.query(database.Lit).filter(
        database.Lit.id == lit_id
    ).first()

    if not lit:
        raise HTTPException(404, "Lit introuvable")

    modifications = donnees.dict(exclude_unset=True)

    hospitalisation_active = db.query(
        database.Hospitalisation
    ).filter(
        database.Hospitalisation.id_lit == lit_id,
        database.Hospitalisation.statut == "en_cours"
    ).first()

    if hospitalisation_active:
        if "id_salle" in modifications or modifications.get("statut") != "occupe":
            raise HTTPException(
                400,
                "Ce lit est associé à une hospitalisation en cours."
            )

    if "id_salle" in modifications:
        salle = db.query(database.SalleMedicale).filter(
            database.SalleMedicale.id == modifications["id_salle"]
        ).first()

        if not salle:
            raise HTTPException(404, "Salle de destination introuvable")

        nombre_lits = db.query(database.Lit).filter(
            database.Lit.id_salle == salle.id,
            database.Lit.id != lit_id
        ).count()

        if nombre_lits >= salle.capacite:
            raise HTTPException(400, "La salle a atteint sa capacité maximale")

    statuts_valides = ["disponible", "occupe", "maintenance"]

    if "statut" in modifications:
        if modifications["statut"] not in statuts_valides:
            raise HTTPException(400, "Statut du lit invalide")

        if modifications["statut"] != lit.statut:
            if hospitalisation_active:
                raise HTTPException(
                    400,
                    "Impossible de changer le statut d'un lit associé à une hospitalisation en cours."
                )

    for champ, valeur in modifications.items():
        setattr(lit, champ, valeur)

    try:
        db.commit()
        db.refresh(lit)
        return {"message": "Lit modifié avec succès", "id": lit.id}
    except Exception:
        db.rollback()
        raise HTTPException(400, "Erreur lors de la modification")


@app.delete("/lits/{lit_id}")
def supprimer_lit(
    lit_id: int,
    db: Session = Depends(get_db)
):
    lit = db.query(database.Lit).filter(
        database.Lit.id == lit_id
    ).first()

    if not lit:
        raise HTTPException(404, "Lit introuvable")

    if lit.statut == "occupe":
        raise HTTPException(400, "Impossible de supprimer un lit occupé")

    hospitalisation_active = db.query(
        database.Hospitalisation
    ).filter(
        database.Hospitalisation.id_lit == lit_id,
        database.Hospitalisation.statut == "en_cours"
    ).first()

    if hospitalisation_active:
        raise HTTPException(
            400,
            "Ce lit est associé à une hospitalisation en cours."
        )

    db.delete(lit)

    try:
        db.commit()
        return {"message": "Lit supprimé avec succès"}
    except Exception:
        db.rollback()
        raise HTTPException(400, "Erreur lors de la suppression")