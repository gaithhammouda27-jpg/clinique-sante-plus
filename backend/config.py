"""Configuration centrale du backend (chemins, variables d'environnement)."""

import os
from pathlib import Path

# Racine du dépôt : .../clinique-sante-plus
ROOT_DIR = Path(__file__).resolve().parent.parent

# Charge le fichier .env (clés API de l'assistant, etc.) s'il existe.
# Il est ignoré par git : les clés ne sont jamais publiées.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except ImportError:  # python-dotenv optionnel : variables d'environnement classiques
    pass

DATABASE_URL = os.getenv(
    "CLINIQUE_DATABASE_URL",
    f"sqlite:///{(ROOT_DIR / 'clinique.db').as_posix()}",
)

UPLOAD_DIR = Path(os.getenv("CLINIQUE_UPLOAD_DIR", ROOT_DIR / "uploads"))

MODELS_DIR = Path(os.getenv("CLINIQUE_MODELS_DIR", ROOT_DIR / "ml" / "models"))

# Mot de passe des comptes de démonstration créés par seed_data.py
DEMO_PASSWORD = os.getenv("CLINIQUE_DEMO_PASSWORD", "Demo2026!")
