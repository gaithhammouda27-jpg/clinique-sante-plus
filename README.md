# 🏥 Clinique Santé+ — Système d'Information Hospitalier avec IA

Système d'Information Hospitalier (SIH) : gestion des patients, médecins, rendez-vous,
facturation, pharmacie et infrastructure, avec un module d'**aide au diagnostic**
(hypertension, diabète) basé sur **Apache Spark MLlib**.

## ✨ Fonctionnalités

| Espace | Contenu |
|---|---|
| **Admin** | Tableau de bord global, finances, pharmacie, lits/salles, satisfaction, journal, gestion des utilisateurs |
| **Médecin** | Planning, diagnostic IA, dossier patient (documents, ordonnances, consultations, évolution) |
| **Secrétariat** | Prise et modification de RDV, création de dossiers patients, annuaire, facturation |
| **Patient** | Rendez-vous, historique IA, ordonnances, bilan de santé |
| **Tous** | Assistant IA conversationnel sur les données de la clinique |

## 🏗️ Architecture

```
clinique-sante-plus/
├── backend/                 API FastAPI + base de données
│   ├── api.py               routes REST
│   ├── database.py          modèles SQLAlchemy
│   ├── ia_service.py        prédictions Spark (chargement paresseux)
│   ├── assistant.py         assistant IA (Groq / Gemini / Ollama) + outils par rôle
│   ├── security.py          hachage des mots de passe (bcrypt)
│   ├── config.py            chemins + variables d'environnement
│   └── seed_data.py         données et comptes de démonstration
├── frontend/                Interface Streamlit
│   ├── app.py               accueil + connexion
│   ├── pages/               un fichier par rôle + page Assistant IA
│   ├── components/          cartes, graphiques, en-tête, navbar, sidebar
│   ├── api_client.py        client HTTP commun (URL configurable, timeouts)
│   ├── auth.py              session, garde d'accès par rôle, déconnexion
│   └── style.py             thème CSS
├── ml/                      Intelligence artificielle
│   ├── data/raw/            jeux de données (CSV)
│   ├── models/              modèles Random Forest entraînés
│   └── scripts/             génération des données + entraînement
├── .streamlit/config.toml   thème sombre Streamlit
├── requirements.txt
└── setup.ps1 / run_api.ps1 / run_frontend.ps1
```

- **Frontend** : Streamlit — **Backend** : FastAPI — **Base** : SQLite (SQLAlchemy)
- **IA** : Spark MLlib, Random Forest (AUC ≈ 0.78 sur données synthétiques)

## 🚀 Installation

Prérequis : **Python 3.11+**. Pour l'IA uniquement : **Java 17** et, sous Windows,
`winutils.exe` + `hadoop.dll` dans `<HADOOP_HOME>\bin` (par défaut `D:\hadoop`).
Sans Java/Hadoop, toute l'application fonctionne sauf le bouton « Lancer l'analyse IA ».

Toutes les commandes se lancent **depuis la racine du projet**.

```powershell
.\setup.ps1          # crée .venv, installe les dépendances, crée la base + données démo
```

Puis, dans deux terminaux :

```powershell
.\run_api.ps1        # API sur http://127.0.0.1:8000 (doc : /docs)
```

```powershell
.\run_frontend.ps1   # Interface sur http://localhost:8501
```

<details><summary>Équivalent manuel</summary>

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.seed_data
uvicorn backend.api:app --reload
streamlit run frontend/app.py
```
</details>

## 🔑 Comptes de démonstration

Créés par `python -m backend.seed_data` (mot de passe : `Demo2026!`, modifiable via
`CLINIQUE_DEMO_PASSWORD`). Accessibles aussi via l'onglet **« Accès Rapide Démo »**.

| Rôle | E-mail |
|---|---|
| Admin | admin@clinique.com |
| Médecin | dr.martin@clinique.com |
| Secrétaire | secretaire@clinique.com |
| Patient | jean.dupont@email.com |

## 🤖 Assistant IA (gratuit)

Page **« 🤖 Assistant IA »** (lien dans la barre latérale, ou bouton « IA Clinique » de l'accueil).
Il répond en langage naturel à partir des **vraies données** de la clinique, avec des outils en
lecture seule filtrés par rôle :

| Rôle | Peut consulter |
|---|---|
| Admin | statistiques, rendez-vous, patients, dossiers, pharmacie, **finances**, lits, médecins |
| Médecin | ses rendez-vous, patients, dossiers, pharmacie, lits, médecins |
| Secrétaire | rendez-vous, recherche de patients, lits, médecins (pas les dossiers médicaux) |
| Patient | **ses** rendez-vous et **son** dossier uniquement, annuaire des médecins |

Le rôle est vérifié **dans la base**, pas déclaré par le navigateur.

**Activer l'assistant (2 minutes)** :
1. Créez une clé gratuite sur https://console.groq.com/keys (sans carte bancaire).
2. Copiez `.env.example` en `.env` à la racine et renseignez `GROQ_API_KEY=...`.
3. Redémarrez l'API (`.\run_api.ps1`).

Autres fournisseurs (même code, API compatible OpenAI) : **Google Gemini**
(`ASSISTANT_PROVIDER=gemini` + `GEMINI_API_KEY`), **OpenRouter** (modèles `:free`) ou
**Ollama** en local, sans clé ni Internet (`ASSISTANT_PROVIDER=ollama`).
`ASSISTANT_MODEL` permet de choisir un autre modèle.

> ⚠️ Les offres gratuites envoient les questions à un service externe (et Gemini gratuit peut
> les utiliser pour s'améliorer) : n'utilisez que des **données fictives**. Pour de vraies
> données de santé, préférez Ollama en local.
> Le fichier `.env` est ignoré par git : la clé n'est jamais publiée.

## ⚙️ Configuration

Voir [.env.example](.env.example) : `CLINIQUE_API_URL`, `CLINIQUE_DATABASE_URL`,
`CLINIQUE_DEMO_PASSWORD`, `HADOOP_HOME`. Toutes ont une valeur par défaut.

## 🧠 Ré-entraîner les modèles

```bash
python ml/scripts/generate_data.py      # données hypertension
python ml/scripts/train_model.py        # -> ml/models/hypertension_model
python ml/scripts/generate_diabetes.py
python ml/scripts/train_diabetes.py     # -> ml/models/diabetes_model
```

> ⚠️ Projet pédagogique : les modèles sont entraînés sur des **données synthétiques**.
> Les probabilités affichées ne constituent pas un diagnostic médical.

Voir [docs/ANALYSE.md](docs/ANALYSE.md) pour l'audit du projet et la feuille de route.
