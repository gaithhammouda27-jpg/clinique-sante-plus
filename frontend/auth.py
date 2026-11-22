"""Gestion de session côté interface (connexion, garde d'accès, déconnexion)."""

import streamlit as st

ROLE_PAGES = {
    "admin": "pages/1_Admin.py",
    "administrateur": "pages/1_Admin.py",
    "medecin": "pages/2_Medecin.py",
    "médecin": "pages/2_Medecin.py",
    "secretaire": "pages/3_Secretaire.py",
    "secrétaire": "pages/3_Secretaire.py",
    "patient": "pages/4_Patient.py",
}

# Normalise les variantes accentuées vers le rôle canonique utilisé par les pages
CANONICAL_ROLE = {
    "administrateur": "admin",
    "médecin": "medecin",
    "secrétaire": "secretaire",
}


def normalize_role(role) -> str:
    role = str(role or "").strip().lower()
    return CANONICAL_ROLE.get(role, role)


def login_user(user_data: dict) -> str | None:
    """Enregistre l'utilisateur en session et renvoie la page de destination."""
    role = normalize_role(user_data.get("role"))
    destination = ROLE_PAGES.get(role)
    if not destination:
        return None
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user_data["id"]
    st.session_state["email"] = user_data["email"]
    st.session_state["name"] = user_data.get("nom_complet") or user_data["email"]
    st.session_state["role"] = role
    return destination


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def require_login():
    """Bloque la page si personne n'est connecté (tous rôles acceptés)."""
    if st.session_state.get("logged_in") and normalize_role(st.session_state.get("role")) in ROLE_PAGES:
        return
    st.error("⛔ Accès refusé : veuillez vous connecter.")
    if st.button("🔐 Aller à la page de connexion", type="primary"):
        logout()
        st.session_state["show_login"] = True
        st.switch_page("app.py")
    st.stop()


def require_role(role: str):
    """Bloque la page si l'utilisateur n'est pas connecté avec le bon rôle."""
    if st.session_state.get("logged_in") and normalize_role(st.session_state.get("role")) == role:
        return

    st.error("⛔ Accès refusé : veuillez vous connecter avec un compte autorisé.")
    if st.button("🔐 Aller à la page de connexion", type="primary"):
        logout()
        st.session_state["show_login"] = True
        st.switch_page("app.py")
    st.stop()
