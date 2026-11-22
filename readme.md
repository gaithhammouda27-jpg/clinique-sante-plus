# 🏥 Clinique Santé+ — Système d'Information Hospitalier avec Intelligence Artificielle

## 📝 Description
Ce projet est un **Système d'Information Hospitalier (SIH)** complet intégrant un module d'**Intelligence Artificielle** pour l'aide au diagnostic de l'hypertension. Il permet la gestion des patients, des médecins, des rendez-vous, et offre une prédiction du risque en temps réel via **Apache Spark**.

## ✨ Fonctionnalités principales
- **Authentification sécurisée** : Connexion centralisée sur la base de données avec gestion des rôles (Admin, Médecin, Secrétaire, Patient).
- **Espace Secrétariat** : Création de patients, prise de rendez-vous, modification, annuaire des médecins.
- **Espace Médecin** : Planning des rendez-vous, aide au diagnostic par IA (Spark MLlib), historique des prédictions.
- **Espace Patient** : Consultation de ses rendez-vous et de son historique de santé.
- **IA Prédictive** : Modèle Random Forest entraîné sur 1000 patients avec 15% de bruit pour simuler la réalité médicale.

## 🏗️ Architecture
- **Frontend** : Streamlit (interfaces interactives).
- **Backend** : FastAPI (API REST, gestion des rôles, logique métier).
- **Base de données** : SQLite (via SQLAlchemy).
- **Intelligence Artificielle** : Apache Spark MLlib (Random Forest).

## 🚀 Installation et Lancement

### Prérequis
- Python 3.13
- Java 17 (pour Spark)
- Hadoop (winutils.exe configuré sous Windows)

### Étapes
1. **Cloner le projet** (ou le télécharger).
2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt

 3.  Initialiser la base de données 
        bash
    python database.py
    4. Lancer l'API (Backend) :

        bash
        uvicorn api:app --reload
        5. Lancer l'interface (Frontend) (dans un autre terminal) :

        bash
        streamlit run app.py

    Performance du Modèle
Algorithme : Random Forest (Spark MLlib).

AUC (Aire sous la courbe ROC) : ~0.78.

Données d'entraînement : 1000 patients (15% de bruit ajouté)


---

### 📋 Fichier `requirements.txt` (Bonus)
Pour que le `README` soit complet, assurez-vous d'avoir aussi ce fichier `requirements.txt` à la racine :

```text
fastapi
uvicorn
sqlalchemy
pydantic
streamlit
plotly
pandas
requests
pyspark