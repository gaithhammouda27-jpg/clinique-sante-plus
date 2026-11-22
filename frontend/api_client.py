"""Client HTTP partagé par toutes les pages Streamlit.

- URL de l'API configurable : variable d'environnement CLINIQUE_API_URL.
- Timeout par défaut sur TOUTES les requêtes (avant : certaines requêtes
  n'en avaient pas et bloquaient l'interface si l'API ne répondait pas).
"""

import os

import requests

API_URL = os.getenv("CLINIQUE_API_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_TIMEOUT = float(os.getenv("CLINIQUE_API_TIMEOUT", "15"))

RequestException = requests.RequestException

_session = requests.Session()


def _request(method, url, **kwargs):
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    if url.startswith("/"):
        url = f"{API_URL}{url}"
    return _session.request(method, url, **kwargs)


def get(url, **kwargs):
    return _request("GET", url, **kwargs)


def post(url, **kwargs):
    return _request("POST", url, **kwargs)


def put(url, **kwargs):
    return _request("PUT", url, **kwargs)


def patch(url, **kwargs):
    return _request("PATCH", url, **kwargs)


def delete(url, **kwargs):
    return _request("DELETE", url, **kwargs)


def get_json(url, default=None, **kwargs):
    """GET qui renvoie le JSON, ou `default` en cas d'erreur réseau / HTTP."""
    try:
        res = get(url, **kwargs)
        if res.status_code == 200:
            return res.json()
    except (RequestException, ValueError):
        pass
    return default


def error_detail(res) -> str:
    """Message d'erreur lisible à partir d'une réponse FastAPI."""
    try:
        detail = res.json().get("detail")
        if isinstance(detail, list):  # erreurs de validation pydantic
            return "; ".join(str(d.get("msg", d)) for d in detail)
        if detail:
            return str(detail)
    except (ValueError, AttributeError):
        pass
    return f"HTTP {res.status_code}"
