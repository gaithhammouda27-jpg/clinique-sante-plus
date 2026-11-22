import os

import streamlit as st
import api_client as api

from style import apply_custom_style, render_clean_html
from components.navbar import afficher_navbar
from components.charts import (
    create_ai_risk_gauge,
    create_biometric_radar,
    create_patient_flow_sankey
)
from components.cards import render_metric_card
from auth import ROLE_PAGES, login_user, logout

# ============================================================
# 1. CONFIGURATION DE LA PAGE
# ============================================================

st.set_page_config(
    page_title="Clinique Santé+ | Portail Médical & IA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_custom_style()
afficher_navbar()

# Comptes de démonstration (créés par `python -m backend.seed_data`).
# L'accès rapide passe par la vraie route /login : avant, il ouvrait une
# session avec des ID codés en dur qui ne correspondaient à aucune ligne en base.
DEMO_PASSWORD = os.getenv("CLINIQUE_DEMO_PASSWORD", "Demo2026!")
DEMO_ACCOUNTS = {
    "Administrateur": "admin@clinique.com",
    "Dr. Martin (Médecin)": "dr.martin@clinique.com",
    "Sophie (Secrétariat)": "secretaire@clinique.com",
    "Jean Dupont (Patient)": "jean.dupont@email.com",
}


def tenter_connexion(email: str, password: str) -> None:
    """Appelle /login, ouvre la session et redirige vers l'espace du rôle."""
    try:
        response = api.post(
            "/login",
            json={"email": email.strip(), "mot_de_passe": password},
            timeout=8,
        )
    except api.RequestException:
        st.error("Impossible de contacter l'API. Assurez-vous qu'elle est démarrée (voir README).")
        return

    if response.status_code == 200:
        destination = login_user(response.json())
        if destination:
            st.session_state["show_login"] = False
            st.switch_page(destination)
        else:
            st.error("Rôle utilisateur non reconnu.")
    elif response.status_code == 401:
        st.error("Identifiants invalides.")
    else:
        st.error(f"Erreur serveur : {api.error_detail(response)}")

from clinic_info import CLINIQUE  # noqa: E402  (source unique, partagée avec la navbar)


@st.cache_data(ttl=60, show_spinner=False)
def charger_stats_publiques():
    """KPI réels de l'accueil (avant : valeurs codées en dur)."""
    return api.get_json("/stats/public", default=None)

# Plus de redirection automatique quand on est connecté : elle rendait le
# lien « Portail d'Accueil » de la sidebar inutilisable (retour immédiat).
MY_PAGE = ROLE_PAGES.get(st.session_state.get("role", "")) if st.session_state.get("logged_in") else None

if "show_login" not in st.session_state:
    st.session_state["show_login"] = False


# ============================================================
# 2. VUE MODALE DE CONNEXION (SI ACTIVÉE)
# ============================================================

if st.session_state["show_login"]:
    render_clean_html("""
<div style="max-width:650px;margin:0 auto;padding-top:10px;">
<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:8px;">
<span class="pulse-dot"></span>
<span class="glow-badge">AUTHENTIFICATION SÉCURISÉE</span>
</div>
<h2 style="text-align:center;margin-bottom:24px;">Portail d'Accès Hospitalier</h2>
</div>
""")

    col_space_l, col_form, col_space_r = st.columns([1, 2, 1])

    with col_form:
        # Onglets entre Connexion Standard et Démonstration Rapide
        tab_login_std, tab_login_demo = st.tabs(["🔐 Identifiants", "⚡ Accès Rapide Démo"])

        with tab_login_std:
            with st.form("login_form"):
                email = st.text_input("Adresse e-mail professionnelle ou patient", placeholder="ex: dr.martin@clinique.com")
                password = st.text_input("Mot de passe", type="password", placeholder="••••••••••••")
                
                submit = st.form_submit_button("Se connecter au SIH", width="stretch", type="primary")

                if submit:
                    if not email.strip() or not password:
                        st.warning("Veuillez remplir tous les champs.")
                    else:
                        with st.spinner("Vérification auprès du serveur d'authentification..."):
                            tenter_connexion(email, password)

        with tab_login_demo:
            st.info("💡 Sélectionnez un profil préconfiguré pour explorer immédiatement les espaces du système :")
            
            for label, demo_email in DEMO_ACCOUNTS.items():
                col_d_info, col_d_btn = st.columns([2.5, 1.2])
                with col_d_info:
                    render_clean_html(f"<b>{label}</b><br><span style='color:#94A3B8;font-size:0.8rem;'>{demo_email}</span>")
                with col_d_btn:
                    if st.button("Entrer", key=f"demo_{demo_email}", width="stretch"):
                        tenter_connexion(demo_email, DEMO_PASSWORD)
                render_clean_html("<div style='height:1px;background:rgba(255,255,255,0.06);margin:6px 0 10px;'></div>")

        if st.button("← Retour à l'accueil public", width="stretch"):
            st.session_state["show_login"] = False
            st.rerun()

    st.stop()


# ============================================================
# 3. ACCUEIL PRINCIPAL CINÉMATIQUE
# ============================================================

# Hero Banner
render_clean_html("""
<div class="cinematic-hero">
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
<div style="display:flex;align-items:center;gap:10px;">
<span class="pulse-dot"></span>
<span class="glow-badge">SYSTÈME D'INFORMATION HOSPITALIER v2.0 • IA CONNECTÉE</span>
</div>
<div style="font-size:0.8rem;color:#38BDF8;font-weight:600;letter-spacing:0.05em;">ANALYTIQUE EN TEMPS RÉEL • MAHDIA, TUNISIE</div>
</div>
<div style="display:flex;align-items:flex-start;gap:24px;flex-wrap:wrap;">
<div style="flex:1;min-width:320px;">
<h1>Clinique Santé+ — L'Intelligence Médicale Hospitalière</h1>
<p style="color:#94A3B8;font-size:1rem;line-height:1.6;">Plateforme clinique de nouvelle génération unifiant le dossier patient informatisé, la coordination des soins, la gestion hospitalière et l'aide à la décision diagnostique propulsée par Apache Spark MLlib.</p>
</div>
</div>
</div>
""")

# Barre d'actions rapides sous le Hero
c_hero_btn1, c_hero_btn2, c_hero_stat = st.columns([1.2, 1.2, 2.6])
with c_hero_btn1:
    if st.button("🔐 Accéder à mon Espace", type="primary", width="stretch"):
        if MY_PAGE:
            st.switch_page(MY_PAGE)
        st.session_state["show_login"] = True
        st.rerun()
with c_hero_btn2:
    if MY_PAGE:
        if st.button("🚪 Se déconnecter", width="stretch"):
            logout()
            st.rerun()
    elif st.button("⚡ Démonstration Immédiate", width="stretch"):
        st.session_state["show_login"] = True
        st.rerun()
stats = charger_stats_publiques() or {}

with c_hero_stat:
    nb_patients = stats.get("patients", "—")
    auc = stats.get("auc_modele_hypertension")
    render_clean_html(f"""
<div style="display:flex;align-items:center;justify-content:flex-end;gap:24px;height:100%;padding-right:10px;color:#94A3B8;font-size:0.82rem;">
<div><b style="color:#00F2FE;font-size:1.1rem;">{nb_patients}</b> Patients Suivis</div>
<div><b style="color:#10B981;font-size:1.1rem;">{f"{auc:.0%}" if auc else "—"}</b> AUC Modèle IA</div>
<div><b style="color:#38BDF8;font-size:1.1rem;">24/7</b> Service Urgences</div>
</div>
""")

render_clean_html("<div style='height:15px;'></div>")

# ------------------------------------------------------------
# 4. CARTE DES MÉTRIQUES CLÉS DU SYSTÈME (données réelles de la base)
# ------------------------------------------------------------
if not stats:
    st.info("Indicateurs indisponibles : l'API n'est pas démarrée.")
else:
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        render_metric_card(
            title="Capacité d'Accueil",
            value=stats["lits_total"],
            unit="Lits",
            icon="🛏️",
            color="teal",
            subtitle=f"{stats['lits_disponibles']} lit(s) disponible(s) actuellement",
        )

    with col_kpi2:
        render_metric_card(
            title="Performance Modèle IA",
            value=f"{stats['auc_modele_hypertension'] * 100:.0f}",
            unit="% AUC",
            icon="🧠",
            color="cyan",
            subtitle="Random Forest Spark MLlib (hypertension)",
        )

    with col_kpi3:
        mois, precedent = stats["consultations_mois"], stats["consultations_mois_precedent"]
        evolution = None
        if precedent:
            evolution = (mois - precedent) / precedent * 100
        render_metric_card(
            title="Consultations ce mois",
            value=mois,
            unit="Actes",
            delta=f"{evolution:+.0f}% vs mois précédent" if evolution is not None else None,
            delta_positive=(evolution or 0) >= 0,
            icon="🩺",
            color="emerald",
            subtitle=f"{stats['consultations_total']} consultations au total",
        )

    with col_kpi4:
        moyenne = stats.get("satisfaction_moyenne")
        render_metric_card(
            title="Satisfaction Patient",
            value=f"{moyenne:.1f}" if moyenne is not None else "—",
            unit="/ 5",
            icon="⭐",
            color="amber",
            subtitle=f"Basé sur {stats['satisfaction_avis']} avis",
        )

render_clean_html("<div style='height:25px;'></div>")


# ------------------------------------------------------------
# 5. VISUALISATIONS INTERACTIVES EN DIRECT (DEMO VIVANTE)
# ------------------------------------------------------------
render_clean_html("""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
<div>
<h3 style="margin:0;">🔬 Simulateur Clinique & Visualisation Télémétrique</h3>
<p style="color:#94A3B8;font-size:0.88rem;margin:4px 0 0 0;">
Testez en temps réel l'évaluation du risque cardiovasculaire et explorez les flux hospitaliers interactifs.
</p>
</div>
<span class="glow-badge">EXPÉRIENCE INTERACTIVE</span>
</div>
""")

tab_demo_ia, tab_demo_flux = st.tabs(["🧠 Simulateur de Risque IA", "🌊 Cartographie des Flux Hospitaliers (Sankey)"])

with tab_demo_ia:
    col_ctrl, col_gauge, col_radar = st.columns([1.2, 1.4, 1.4])
    
    with col_ctrl:
        render_clean_html("<div style='color:#38BDF8;font-size:0.85rem;font-weight:700;text-transform:uppercase;margin-bottom:10px;'>Paramètres Biométriques</div>")
        demo_systolic = st.slider("Tension Systolique (mmHg)", 90, 200, 138, step=1)
        demo_glucose = st.slider("Glycémie à jeun (mmol/L)", 3.5, 16.0, 6.2, step=0.1)
        demo_heart_rate = st.slider("Fréquence Cardiaque (bpm)", 50, 140, 78, step=1)
        demo_bmi = st.slider("Indice de Masse Corporelle (IMC)", 18.0, 42.0, 26.5, step=0.5)
        demo_age = st.slider("Âge du Patient", 20, 85, 54, step=1)
        
        # Calcul heuristique de probabilité pour la démonstration en temps réel
        # (modèle Spark MLlib réel connecté dans l'espace médecin)
        score_base = (
            (demo_systolic - 120) * 0.008 +
            (demo_glucose - 5.0) * 0.05 +
            (demo_heart_rate - 70) * 0.004 +
            (demo_bmi - 22.0) * 0.02 +
            (demo_age - 40) * 0.008
        )
        simulated_prob = max(0.05, min(0.95, 0.25 + score_base))
        
    with col_gauge:
        st.plotly_chart(
            create_ai_risk_gauge(simulated_prob, title="Indice de Risque Prédit", disease="Hypertension"),
            width="stretch"
        )
        
    with col_radar:
        st.plotly_chart(
            create_biometric_radar({
                "Tension Sys": demo_systolic,
                "Glycémie": demo_glucose,
                "Fréq. Cardiaque": demo_heart_rate,
                "IMC": demo_bmi,
                "Saturation O2": 98
            }, title="Radar Comparatif vs Norme Médicale"),
            width="stretch"
        )

with tab_demo_flux:
    render_clean_html("""
<div style="color:#94A3B8;font-size:0.88rem;margin-bottom:12px;">
Visualisation dynamique du parcours patient au sein de la clinique : depuis l'admission (urgences ou prise de rendez-vous)
jusqu'aux consultations spécialisées, examens complémentaires, hospitalisation et sortie.
</div>
""")
    st.plotly_chart(
        create_patient_flow_sankey("Trajectoire & Flux des Patients (Clinique Santé+)"),
        width="stretch"
    )

render_clean_html("<div style='height:30px;'></div>")


# ------------------------------------------------------------
# 6. MATRICE DES ESPACES DE LA CLINIQUE
# ------------------------------------------------------------
render_clean_html("""
<div style="margin-bottom:18px;">
<h3 style="margin:0;">🏛️ Espaces et Modules Fonctionnels</h3>
<p style="color:#94A3B8;font-size:0.88rem;margin:4px 0 0 0;">
Une suite logicielle complète adaptée aux prérogatives de chaque acteur hospitalier.
</p>
</div>
""")

col_mod1, col_mod2, col_mod3, col_mod4 = st.columns(4)

with col_mod1:
    render_clean_html("""
<div class="cinematic-card">
<div style="font-size:2rem;margin-bottom:10px;">⚡</div>
<h4 style="color:#FFFFFF;margin-bottom:6px;">Administration</h4>
<p style="color:#94A3B8;font-size:0.85rem;line-height:1.5;">
Centre de pilotage stratégique : trésorerie, gestion du personnel, taux d'occupation des lits, pharmacie et audit.
</p>
<span class="glow-badge" style="border-color:#8B5CF6;color:#A78BFA;background:rgba(139,92,246,0.12);">Rôle Admin</span>
</div>
""")

with col_mod2:
    render_clean_html("""
<div class="cinematic-card">
<div style="font-size:2rem;margin-bottom:10px;">🩺</div>
<h4 style="color:#FFFFFF;margin-bottom:6px;">Médecin</h4>
<p style="color:#94A3B8;font-size:0.85rem;line-height:1.5;">
Dossier médical complet, cockpit de constantes, prescriptions électroniques et moteur d'aide diagnostique IA.
</p>
<span class="glow-badge" style="border-color:#00F2FE;color:#38BDF8;background:rgba(0,242,254,0.12);">Rôle Médecin</span>
</div>
""")

with col_mod3:
    render_clean_html("""
<div class="cinematic-card">
<div style="font-size:2rem;margin-bottom:10px;">📋</div>
<h4 style="color:#FFFFFF;margin-bottom:6px;">Secrétariat</h4>
<p style="color:#94A3B8;font-size:0.85rem;line-height:1.5;">
Gestion des flux de rendez-vous, admissions, création de fiches patients, annuaire médical et facturation.
</p>
<span class="glow-badge" style="border-color:#F59E0B;color:#FBBF24;background:rgba(245,158,11,0.12);">Rôle Secrétaire</span>
</div>
""")

with col_mod4:
    render_clean_html("""
<div class="cinematic-card">
<div style="font-size:2rem;margin-bottom:10px;">👤</div>
<h4 style="color:#FFFFFF;margin-bottom:6px;">Patient</h4>
<p style="color:#94A3B8;font-size:0.85rem;line-height:1.5;">
Portail personnel sécurisé : consultation des ordonnances, planning des rendez-vous et jauge de suivi santé.
</p>
<span class="glow-badge" style="border-color:#10B981;color:#34D399;background:rgba(16,185,129,0.12);">Rôle Patient</span>
</div>
""")

render_clean_html("<div style='height:25px;'></div>")


# ------------------------------------------------------------
# 7. INFORMATIONS PRATIQUES & HORAIRES
# ------------------------------------------------------------
col_info_a, col_info_b = st.columns([1.5, 1])

with col_info_a:
    render_clean_html(f"""
<div class="cinematic-card">
<h4 style="color:#FFFFFF;margin-bottom:14px;">📍 Coordonnées & Prise en Charge</h4>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
<div>
<b style="color:#38BDF8;">Adresse Principale</b><br>
<span style="color:#94A3B8;font-size:0.88rem;">{CLINIQUE['adresse']}</span>
</div>
<div>
<b style="color:#38BDF8;">Standard Téléphonique</b><br>
<span style="color:#94A3B8;font-size:0.88rem;">{CLINIQUE['telephone']}</span>
</div>
<div>
<b style="color:#F43F5E;">Service Urgences 24/7</b><br>
<span style="color:#F43F5E;font-size:0.88rem;font-weight:700;">{CLINIQUE['urgences']}</span>
</div>
<div>
<b style="color:#38BDF8;">Contact Courriel</b><br>
<span style="color:#94A3B8;font-size:0.88rem;">{CLINIQUE['email']}</span>
</div>
</div>
</div>
""")

with col_info_b:
    horaires_html = "".join([f"<div style='display:flex;justify-content:space-between;padding:4px 0;'><span style='color:#E2E8F0;font-size:0.85rem;'>📅 <b>{j}</b></span><span style='color:#38BDF8;font-size:0.85rem;'>{h}</span></div>" for j, h in CLINIQUE["horaires"]])
    render_clean_html(f"""
<div class="cinematic-card">
<h4 style="color:#FFFFFF;margin-bottom:14px;">🕒 Horaires d'Ouverture</h4>
{horaires_html}
</div>
""")

# ------------------------------------------------------------
# 8. PIED DE PAGE CINÉMATIQUE
# ------------------------------------------------------------
render_clean_html("""
<div style="text-align:center;color:#64748B;padding:35px 20px 20px;margin-top:50px;border-top:1px solid rgba(255,255,255,0.08);">
<div style="font-size:1.1rem;font-weight:700;color:#E2E8F0;margin-bottom:6px;">🏥 Clinique Santé+</div>
<div style="font-size:0.82rem;color:#94A3B8;margin-bottom:12px;">Plateforme d'Information Hospitalière & Diagnostic Assisté par Intelligence Artificielle</div>
<div style="font-size:0.75rem;color:#64748B;">© 2026 Clinique Santé+ • Tous droits réservés • Moteur Spark MLlib v3.5 • Développé pour la santé d'excellence</div>
</div>
""")
