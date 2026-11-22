import streamlit as st
import requests

from style import apply_custom_style
from components.sidebar import render_sidebar
# ==========================================
# 1. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="Clinique Santé+ | Portail",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_custom_style()



API_URL = "http://127.0.0.1:8000"

# ==========================================
# 3
# ==========================================
# 3. PAGE DE CONNEXION
# ==========================================
if not st.session_state.get("logged_in"):

    st.markdown("""
        <div class="login-header">
            <div class="login-logo">🏥</div>
            <h1>Clinique Santé+</h1>
            <p>Votre espace de santé intelligent</p>
            <span>Plateforme de gestion médicale et d'aide au diagnostic par l'IA</span>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        with st.form("login_form"):
            st.subheader("🔐 Connexion sécurisée")

            email = st.text_input(
                "Adresse Email",
                placeholder="ex: dr.martin@clinique.com"
            )

            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Votre mot de passe"
            )

            submit = st.form_submit_button(
                "Se connecter",
                use_container_width=True
            )

            if submit:
                with st.spinner("Vérification des identifiants..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/login",
                            json={
                                "email": email,
                                "mot_de_passe": password
                            },
                            timeout=10
                        )

                        if res.status_code == 200:
                            user_data = res.json()

                            st.session_state["logged_in"] = True
                            st.session_state["user_id"] = user_data["id"]
                            st.session_state["email"] = user_data["email"]
                            st.session_state["name"] = user_data["nom_complet"]
                            st.session_state["role"] = user_data["role"]

                            st.rerun()

                        else:
                            st.error("Email ou mot de passe incorrect.")

                    except requests.exceptions.RequestException:
                        st.error("Impossible de contacter le serveur. Vérifiez que l'API est démarrée.")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="login-footer">
            © 2026 Clinique Santé+ — Tous droits réservés
        </div>
    """, unsafe_allow_html=True)
# ==========================================
# 4. TABLEAU DE BORD (Une fois connecté)
# ==========================================
else:
    role = st.session_state["role"]
    name = st.session_state["name"]
    
    # --- BARRE LATÉRALE ---

    # ==========================================
    # TABLEAU DE BORD PRINCIPAL
    # ==========================================

    # Redirection de l'administrateur vers son espace
    if role == "admin":
        st.switch_page("pages/1_Admin.py")

    # Configuration selon le rôle
    dashboard_config = {
        "medecin": {
            "title": "Espace Médecin",
            "description": "Gérez votre activité médicale et consultez vos dossiers.",
            "icon": "🩺",
            "cards": [
                {
                    "icon": "📅",
                    "title": "Mon planning",
                    "description": "Consulter les rendez-vous et organiser votre journée.",
                    "button": "Voir mon planning",
                    "key": "dashboard_planning"
                },
                {
                    "icon": "🧠",
                    "title": "Diagnostic assisté par IA",
                    "description": "Accéder aux outils d'analyse prédictive.",
                    "button": "Ouvrir l'analyse IA",
                    "key": "dashboard_ia"
                },
                {
                    "icon": "📁",
                    "title": "Dossiers médicaux",
                    "description": "Consulter les dossiers et le suivi des patients.",
                    "button": "Accéder aux dossiers",
                    "key": "dashboard_dossiers"
                }
            ],
            "page": "pages/2_Medecin.py"
        },

        "secretaire": {
            "title": "Espace Secrétariat",
            "description": "Gérez les rendez-vous et les informations administratives.",
            "icon": "📋",
            "cards": [
                {
                    "icon": "📅",
                    "title": "Rendez-vous",
                    "description": "Créer et gérer les rendez-vous des patients.",
                    "button": "Gérer les rendez-vous",
                    "key": "dashboard_rdv"
                },
                {
                    "icon": "👥",
                    "title": "Gestion des patients",
                    "description": "Consulter et gérer les informations des patients.",
                    "button": "Gérer les patients",
                    "key": "dashboard_patients"
                },
                {
                    "icon": "🩺",
                    "title": "Annuaire médical",
                    "description": "Consulter les informations des médecins.",
                    "button": "Voir l'annuaire",
                    "key": "dashboard_annuaire"
                }
            ],
            "page": "pages/3_Secretaire.py"
        },

        "patient": {
            "title": "Mon espace santé",
            "description": "Retrouvez vos rendez-vous et votre historique médical.",
            "icon": "👤",
            "cards": [
                {
                    "icon": "📅",
                    "title": "Mes rendez-vous",
                    "description": "Consulter vos rendez-vous médicaux.",
                    "button": "Voir mes rendez-vous",
                    "key": "dashboard_patient_rdv"
                },
                {
                    "icon": "📊",
                    "title": "Mon historique",
                    "description": "Consulter les informations de votre suivi médical.",
                    "button": "Voir mon historique",
                    "key": "dashboard_historique"
                },
                {
                    "icon": "📁",
                    "title": "Mon dossier médical",
                    "description": "Accéder aux informations de votre dossier.",
                    "button": "Voir mon dossier",
                    "key": "dashboard_dossier_patient"
                }
            ],
            "page": "pages/4_Patient.py"
        }
    }

    config = dashboard_config.get(role)

    if config:

        # En-tête personnalisé
        st.markdown(f"""
            <div class="dashboard-welcome">
                <h1>{config['icon']} Bonjour {name} !</h1>
                <p>{config['description']}</p>
                <span class="dashboard-role">{config['title']}</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="dashboard-section-title">Accès rapide</div>',
            unsafe_allow_html=True
        )

        # Affichage des cartes
        cards = config["cards"]

        columns = st.columns(len(cards))

        for index, card in enumerate(cards):

            with columns[index]:

                st.markdown(f"""
                    <div class="dashboard-card">
                        <div class="dashboard-card-icon">
                            {card['icon']}
                        </div>
                        <h3>{card['title']}</h3>
                        <p>{card['description']}</p>
                    </div>
                """, unsafe_allow_html=True)

                if st.button(
                    card["button"],
                    key=card["key"],
                    use_container_width=True
                ):
                    st.switch_page(config["page"])

        # Information complémentaire
        st.markdown(f"""
            <div class="dashboard-info">
                <strong>💡 Espace personnel</strong><br>
                Vous êtes connecté à votre espace :
                <strong>{config['title']}</strong>.
                Utilisez le menu latéral pour naviguer dans l'application.
            </div>
        """, unsafe_allow_html=True)

    else:
        st.error("Rôle utilisateur non reconnu.")

    # Pied de page
    st.markdown("""
        <div class="dashboard-footer">
            Clinique Santé+ · Plateforme de gestion médicale
        </div>
    """, unsafe_allow_html=True)
