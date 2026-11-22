"""
Barre de navigation supérieure cinématique pour la Clinique Santé+.
"""

import streamlit as st

import api_client as api
from clinic_info import CLINIQUE
from style import render_clean_html


def _nom_propre(nom: str) -> str:
    return str(nom or "").replace("[TEST]", "").strip()


@st.dialog("🩺 Nos services médicaux", width="large")
def dialogue_services():
    """Services et médecins réels, lus depuis l'API (avant : simple toast statique)."""
    services = api.get_json("/services-medicaux/", default=None)
    medecins = api.get_json("/medecins/annuaire", default=[]) or []

    if services is None:
        st.error("Impossible de contacter l'API pour charger les services.")
        return
    if not services:
        st.info("Aucun service médical n'est encore enregistré.")
    for s in services:
        statut = "🟢 Actif" if s.get("statut") == "actif" else f"⚪ {s.get('statut')}"
        st.markdown(f"**{_nom_propre(s['nom'])}** — {statut} · capacité {s.get('capacite') or 0} patients")
        if s.get("description"):
            st.caption(_nom_propre(s["description"]))

    if medecins:
        st.divider()
        st.markdown("**👨‍⚕️ Nos médecins**")
        for m in medecins:
            st.markdown(f"- {m['nom_complet']} — {m.get('specialite') or 'Généraliste'}")


@st.dialog("🧠 Intelligence artificielle clinique", width="large")
def dialogue_ia():
    """Présente les modèles et l'assistant, avec un raccourci vers l'assistant."""
    st.markdown(
        "- **Prédiction du risque** d'hypertension et de diabète : modèles Random Forest "
        "(Spark MLlib), AUC ≈ 0.78, entraînés sur 1 000 dossiers synthétiques.\n"
        "- **Assistant IA** : pose des questions en langage naturel sur les rendez-vous, "
        "les patients, la pharmacie ou les finances (selon votre rôle)."
    )
    statut = api.get_json("/assistant/status", default=None)
    if statut and statut.get("configure"):
        st.success(f"Assistant connecté : {statut['fournisseur']} · {statut['modele']}")
    else:
        st.warning("Assistant non configuré : ajoute une clé API gratuite dans le fichier .env (voir README).")
    st.caption("⚠️ Aide à la décision uniquement : ne remplace pas l'avis d'un médecin.")

    if st.session_state.get("logged_in"):
        if st.button("🤖 Ouvrir l'assistant IA", type="primary", width="stretch"):
            st.switch_page("pages/5_Assistant.py")
    else:
        if st.button("🔐 Se connecter pour utiliser l'assistant", type="primary", width="stretch"):
            st.session_state["show_login"] = True
            st.switch_page("app.py")


@st.dialog("📞 Nous contacter")
def dialogue_contact():
    st.markdown(f"📍 **Adresse** : {CLINIQUE['adresse']}")
    st.markdown(f"☎️ **Standard** : {CLINIQUE['telephone']}")
    st.markdown(f"🚨 **Urgences** : {CLINIQUE['urgences']}")
    st.markdown(f"✉️ **E-mail** : [{CLINIQUE['email']}](mailto:{CLINIQUE['email']})")
    st.divider()
    for jour, heures in CLINIQUE["horaires"]:
        st.markdown(f"🕒 **{jour}** : {heures}")


def afficher_navbar():
    """
    Rend la barre de navigation supérieure avec glassmorphism sombre et boutons intégrés.
    """
    col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1, 1, 1, 1, 1.2])
    
    with col1:
        render_clean_html("""
<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">
<span style="font-size:1.8rem;filter:drop-shadow(0 0 10px rgba(0,242,254,0.4));">🏥</span>
<div>
<span style="font-size:1.25rem;font-weight:800;letter-spacing:-0.02em;background:linear-gradient(120deg,#FFFFFF 0%,#38BDF8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Clinique Santé+</span>
<div style="font-size:0.68rem;color:#64748B;letter-spacing:0.08em;text-transform:uppercase;">Hospital Intelligence Platform</div>
</div>
</div>
""")
    
    with col2:
        if st.button("🏠 Accueil", width="stretch"):
            st.switch_page("app.py")
            
    with col3:
        if st.button("🩺 Services", width="stretch"):
            dialogue_services()

    with col4:
        if st.button("🧠 IA Clinique", width="stretch"):
            dialogue_ia()

    with col5:
        if st.button("📞 Contact", width="stretch"):
            dialogue_contact()

    with col6:
        if not st.session_state.get("logged_in"):
            if st.button("🔐 Connexion", type="primary", width="stretch"):
                st.session_state["show_login"] = True
                st.rerun()
        else:
            from auth import ROLE_PAGES

            role = st.session_state.get("role", "Espace")
            if st.button(f"👤 {role.capitalize()}", type="primary", width="stretch",
                         help=f"Connecté en tant que {st.session_state.get('name')}"):
                page = ROLE_PAGES.get(role)
                if page:
                    st.switch_page(page)
            
    render_clean_html("""
<div style="height:1px;background:linear-gradient(90deg,transparent 0%,rgba(0,242,254,0.3) 50%,transparent 100%);margin-top:10px;margin-bottom:25px;"></div>
""")
