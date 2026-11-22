"""
Barre latérale cinématique pour les espaces connectés de la Clinique Santé+.
"""

import streamlit as st
from style import render_clean_html


def render_sidebar(name, role):
    """
    Rend la sidebar latérale avec le thème cinématique, profil lumineux et liens rapides.
    """
    role_config = {
        "admin": {
            "label": "Administration Centrale",
            "icon": "⚡",
            "badge_color": "#8B5CF6",
            "page": "pages/1_Admin.py"
        },
        "medecin": {
            "label": "Médecin Spécialiste",
            "icon": "🩺",
            "badge_color": "#00F2FE",
            "page": "pages/2_Medecin.py"
        },
        "secretaire": {
            "label": "Secrétariat Médical",
            "icon": "📋",
            "badge_color": "#F59E0B",
            "page": "pages/3_Secretaire.py"
        },
        "patient": {
            "label": "Portail Patient",
            "icon": "👤",
            "badge_color": "#10B981",
            "page": "pages/4_Patient.py"
        }
    }

    config = role_config.get(str(role).lower(), {
        "label": str(role).capitalize(),
        "icon": "👤",
        "badge_color": "#00F2FE",
        "page": "app.py"
    })

    with st.sidebar:
        # Logo & Titre
        render_clean_html("""
<div class="sidebar-brand">
<div class="sidebar-logo">🏥</div>
<div class="sidebar-brand-name">Clinique Santé+</div>
<div class="sidebar-brand-subtitle">AI Clinical Command Center</div>
</div>
<div style="height:1px;background:rgba(255,255,255,0.08);margin:8px 0 16px;"></div>
""")

        # Profil utilisateur connecté
        render_clean_html(f"""
<div class="sidebar-profile">
<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:6px;">
<span class="pulse-dot"></span>
<span style="font-size:0.72rem;color:#10B981;font-weight:700;letter-spacing:0.05em;">SESSION ACTIVE</span>
</div>
<div class="sidebar-avatar">{config['icon']}</div>
<div class="sidebar-user-name">{name}</div>
<div class="sidebar-user-role" style="color:{config['badge_color']} !important;border-color:{config['badge_color']}50;">
{config['label']}
</div>
</div>
<div style="height:1px;background:rgba(255,255,255,0.08);margin:16px 0;"></div>
<div style="color:#94A3B8;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Navigation Système</div>
""")

        st.page_link(
            "app.py",
            label="🏠 Portail d'Accueil",
            use_container_width=True
        )

        st.page_link(
            config["page"],
            label=f"{config['icon']} Mon Espace ({config['label']})",
            use_container_width=True
        )

        render_clean_html("""
<div style="height:1px;background:rgba(255,255,255,0.08);margin:20px 0;"></div>
<div style="color:#94A3B8;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Sécurité</div>
""")

        # Déconnexion
        if st.button("🚪 Déconnexion Sécurisée", key="sidebar_logout_btn", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        render_clean_html("""
<div style="text-align:center;color:#64748B !important;font-size:0.72rem;margin-top:35px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.05);">
Clinique Santé+ • Système SIH<br>
<span style="color:#00F2FE;">v2.0 • Spark MLlib Engine</span>
</div>
""")
