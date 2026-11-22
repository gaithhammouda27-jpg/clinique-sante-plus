"""Backend Clinique Santé+ (API FastAPI, base SQLAlchemy, service IA Spark)."""

import sys

# Les consoles Windows (cp1252) plantent sur les emojis des print() :
# on force l'UTF-8 pour tout le backend (seed, API, service IA).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
