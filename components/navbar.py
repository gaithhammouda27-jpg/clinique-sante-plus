"""
Barre de navigation supérieure cinématique pour la Clinique Santé+.
"""

import streamlit as st
from style import render_clean_html


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
        if st.button("🏠 Accueil", use_container_width=True):
            st.switch_page("app.py")
            
    with col3:
        if st.button("🩺 Services", use_container_width=True):
            st.toast("Nos spécialités : Cardiologie, Diabétologie, Urgences, Laboratoire & Imagerie.")
            
    with col4:
        if st.button("🧠 IA Clinique", use_container_width=True):
            st.toast("Modèles Spark MLlib prédictifs pour l'hypertension et le diabète connectés.")
            
    with col5:
        if st.button("📞 Contact", use_container_width=True):
            st.toast("Clinique Santé+ • Mahdia, Tunisie • Urgences 24/7 : (+216) 73 000 000")

    with col6:
        if not st.session_state.get("logged_in"):
            if st.button("🔐 Connexion", type="primary", use_container_width=True):
                st.session_state["show_login"] = True
                st.rerun()
        else:
            role = st.session_state.get("role", "Espace")
            if st.button(f"👤 {role.capitalize()}", type="primary", use_container_width=True):
                st.toast(f"Connecté en tant que {st.session_state.get('name')}")
            
    render_clean_html("""
<div style="height:1px;background:linear-gradient(90deg,transparent 0%,rgba(0,242,254,0.3) 50%,transparent 100%);margin-top:10px;margin-bottom:25px;"></div>
""")
