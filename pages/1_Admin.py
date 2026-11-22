
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import sys
import os

# ============================================================
# 1. CONFIGURATION
# ============================================================

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from style import apply_custom_style, render_clean_html
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import render_metric_card
from components.charts import apply_cinematic_theme

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Administration | Clinique Santé+",
    page_icon="🏥",
    layout="wide"
)

# ============================================================
# 2. SECURITE
# ============================================================

# ============================================================
# 2. SÉCURITÉ (REDIRECTION AUTOMATIQUE)
# ============================================================
if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
    # On affiche un petit message de chargement au lieu d'une erreur
    st.info("Redirection vers la page de connexion...")
    # On redirige vers l'accueil
    st.switch_page("app.py")
    st.stop() # On arrête l'exécution de la page Admin
apply_custom_style()
col_retour, col_vide = st.columns([1, 5])

with col_retour:
    if st.button("← Retour à l'accueil", use_container_width=True):
        # On nettoie la session pour être sûr de ne pas rester connecté
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # On redirige vers app.py (qui est à la racine)
        st.switch_page("app.py")


# ============================================================
# NAVIGATION PRINCIPALE TOUJOURS VISIBLE
# ============================================================


# ============================================================
# 3. FONCTIONS UTILITAIRES
# ============================================================

def get_api_data(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=15
        )

        if response.status_code == 200:
            return response.json()

        st.warning(
            f"Impossible de récupérer {endpoint} "
            f"(HTTP {response.status_code})."
        )

    except requests.RequestException as e:
        st.warning(f"Erreur de connexion à {endpoint} : {e}")

    return None


def format_money(value):
    try:
        return f"{float(value or 0):,.2f} TND".replace(",", " ")
    except (ValueError, TypeError):
        return "0.00 TND"


def show_empty(message="Aucune donnée disponible pour le moment."):
    st.info(f"ℹ️ {message}")


def dataframe_or_empty(data):
    if isinstance(data, list) and len(data) > 0:
        return pd.DataFrame(data)
    return pd.DataFrame()

def preparer_rendez_vous(rdvs, users):
    """Prépare les rendez-vous pour les analyses complémentaires."""
    df = dataframe_or_empty(rdvs)

    if df.empty or "date_heure" not in df.columns:
        return pd.DataFrame()

    df["date_dt"] = pd.to_datetime(
        df["date_heure"],
        errors="coerce"
    )

    df = df.dropna(subset=["date_dt"]).copy()

    if df.empty:
        return df

    df["heure"] = df["date_dt"].dt.hour

    jours = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche"
    }

    df["jour"] = df["date_dt"].dt.dayofweek.map(jours)

    medecins = {
        str(u.get("id")): {
            "nom": u.get("nom_complet", "Médecin inconnu"),
            "specialite": u.get("specialite") or "Non renseignée"
        }
        for u in users
        if u.get("role") == "medecin"
    }

    df["medecin"] = df["id_medecin"].astype(str).map(
        lambda x: medecins.get(x, {}).get("nom", "Médecin inconnu")
    )

    df["specialite"] = df["id_medecin"].astype(str).map(
        lambda x: medecins.get(x, {}).get("specialite", "Non renseignée")
    )

    return df


def preparer_age_patients(patients):
    """Calcule les tranches d'âge à partir des dates de naissance."""
    df = dataframe_or_empty(patients)

    if df.empty or "date_naissance" not in df.columns:
        return pd.DataFrame()

    naissance = pd.to_datetime(
        df["date_naissance"],
        errors="coerce"
    )

    aujourd_hui = pd.Timestamp.today().normalize()

    df["age"] = (
        (aujourd_hui - naissance).dt.days / 365.2425
    )

    df = df.dropna(subset=["age"]).copy()

    df = df[
        (df["age"] >= 0) &
        (df["age"] <= 120)
    ]

    df["tranche_age"] = pd.cut(
        df["age"],
        bins=[0, 18, 30, 45, 60, 75, 120],
        labels=[
            "0–18 ans",
            "19–30 ans",
            "31–45 ans",
            "46–60 ans",
            "61–75 ans",
            "Plus de 75 ans"
        ],
        include_lowest=True
    )

    return df



# ============================================================
# 4. EN-TETE CINEMATIQUE
# ============================================================

admin_name = st.session_state.get('name', 'Administrateur')
render_sidebar(admin_name, "admin")

col_head, col_refresh = st.columns([5, 1])

with col_head:
    render_header(
        "Centre de Commandement Administratif",
        f"Session active : {admin_name} • Pilotage stratégique, indicateurs cliniques et financiers",
        badge="ESPACE ADMINISTRATION CENTRALE"
    )

with col_refresh:
    st.write("")
    if st.button("🔄 Actualiser", use_container_width=True):
        st.rerun()

st.divider()

# ============================================================
# 5. RECUPERATION DES DONNEES
# ============================================================

with st.spinner("Chargement des données de la clinique..."):

    users = get_api_data("/utilisateurs/") or []
    patients = get_api_data("/patients/") or []
    rdvs = get_api_data("/rendezvous/") or []

    analytics = get_api_data("/analytics/dashboard")

# Protection contre les réponses inattendues
if not isinstance(users, list):
    users = []

if not isinstance(patients, list):
    patients = []

if not isinstance(rdvs, list):
    rdvs = []

if not isinstance(analytics, dict):
    analytics = {}

ind = analytics.get("indicateurs", {})
finance = analytics.get("finance", {})
rdv_data = analytics.get("rendez_vous", {})
consult_data = analytics.get("consultations", {})
pharmacie = analytics.get("pharmacie", {})
hospitalisation = analytics.get("hospitalisations", {})
satisfaction = analytics.get("satisfaction", {})
activite = analytics.get("activite", {})

# ============================================================
# 6. INDICATEURS GENERAUX
# ============================================================

st.markdown("## 📊 Vue générale de la clinique")

nb_medecins = sum(
    1 for u in users
    if u.get("role") == "medecin"
)

nb_secretaires = sum(
    1 for u in users
    if u.get("role") == "secretaire"
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_metric_card("Utilisateurs", len(users), icon="👥", color="violet")

with k2:
    render_metric_card("Médecins", nb_medecins, icon="🩺", color="cyan")

with k3:
    render_metric_card("Patients", ind.get("total_patients", len(patients)), icon="🧑‍🤝‍🧑", color="teal")

with k4:
    render_metric_card("Rendez-vous", ind.get("total_rendez_vous", len(rdvs)), icon="📅", color="amber")

st.divider()

# ============================================================
# 7. INDICATEURS FINANCIERS ET OPERATIONNELS
# ============================================================

st.markdown("## 💼 Performance opérationnelle")

f1, f2, f3, f4 = st.columns(4)

with f1:
    render_metric_card("Factures émises", format_money(ind.get("montant_factures", 0)), icon="📄", color="cyan")

with f2:
    render_metric_card("Encaissements validés", format_money(ind.get("montant_encaisse", 0)), icon="💳", color="emerald")

with f3:
    render_metric_card("Dépenses", format_money(ind.get("total_depenses", 0)), icon="📉", color="rose")

with f4:
    solde = ind.get("solde_net", 0) or 0
    render_metric_card("Solde net", format_money(solde), icon="📈", color="teal" if solde >= 0 else "rose")

if ind.get("total_factures", 0) > 0 and ind.get("montant_encaisse", 0) == 0:
    st.info(
        "Aucun paiement validé n'est enregistré. "
        "Le montant des factures n'est pas considéré comme de l'argent encaissé."
    )

st.divider()


# ============================================================
# 8. ONGLETS ANALYTIQUES
# ============================================================


# ============================================================
# 8. ONGLETS ANALYTIQUES AMELIORES
# ============================================================

tab_overview, tab_rdv, tab_finance, tab_pharma, tab_hospital, tab_activity ,tab_users = st.tabs([
    "📊 Vue globale",
    "📅 Rendez-vous",
    "💰 Finance",
    "💊 Pharmacie",
    "🏥 Infrastructure",
    "⭐ Satisfaction & Activité",
    "👥 Gestion des utilisateurs"
])

# ------------------------------------------------------------
# FONCTIONS DE PREPARATION DES GRAPHIQUES
# ------------------------------------------------------------

def valeur_nombre(valeur):
    try:
        return float(valeur or 0)
    except (ValueError, TypeError):
        return 0.0


def preparer_dataframe(data, colonnes=None):
    df = dataframe_or_empty(data)

    if not df.empty and colonnes:
        for colonne in colonnes:
            if colonne not in df.columns:
                df[colonne] = None

    return df


def afficher_graphique(fig, hauteur=380):
    fig.update_layout(
        template="plotly_white",
        height=hauteur,
        margin=dict(l=30, r=30, t=65, b=35),
        hovermode="closest"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# Préparation locale des rendez-vous
rdvs_df = dataframe_or_empty(rdvs)

if not rdvs_df.empty and "date_heure" in rdvs_df.columns:
    rdvs_df["date_convertie"] = pd.to_datetime(
        rdvs_df["date_heure"],
        errors="coerce"
    )

    rdvs_df = rdvs_df.dropna(
        subset=["date_convertie"]
    )

    jours_fr = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche"
    }

    rdvs_df["jour"] = rdvs_df["date_convertie"].dt.dayofweek.map(
        jours_fr
    )

    rdvs_df["heure"] = rdvs_df["date_convertie"].dt.hour
    rdvs_df["mois_local"] = rdvs_df["date_convertie"].dt.strftime("%Y-%m")


# ============================================================
# ONGLET 1 : VUE GLOBALE
# ============================================================


with tab_overview:

    st.subheader("📊 Tableau de bord stratégique de la clinique")
    st.caption("Synthèse de l'activité médicale, administrative et financière.")

    # ========================================================
    # 1. INDICATEURS GENERAUX
    # ========================================================

    st.markdown("### 🏥 Vue générale de la clinique")

    nb_medecins = sum(1 for u in users if u.get("role") == "medecin")
    nb_secretaires = sum(1 for u in users if u.get("role") == "secretaire")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("👥 Utilisateurs", len(users))
    c2.metric("🩺 Médecins", nb_medecins)
    c3.metric("🧑‍🤝‍🧑 Patients", ind.get("total_patients", len(patients)))
    c4.metric("📅 Rendez-vous", ind.get("total_rendez_vous", len(rdvs)))

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("🧑‍💼 Secrétaires", nb_secretaires)
    c6.metric("🩺 Consultations", ind.get("total_consultations", 0))
    c7.metric("🏥 Hospitalisations", ind.get("hospitalisations_en_cours", 0))
    c8.metric(
        "⭐ Satisfaction",
        f"{valeur_nombre(ind.get('note_satisfaction_moyenne', 0)):.2f}/5"
    )

    st.divider()

    # ========================================================
    # 2. ANALYSE DES RENDEZ-VOUS
    # ========================================================

    st.markdown("### 📅 Analyse de l'activité des rendez-vous")

    status_df = preparer_dataframe(
        rdv_data.get("par_statut", []),
        ["statut", "total"]
    )

    monthly_rdv = preparer_dataframe(
        rdv_data.get("par_mois", []),
        ["mois", "total"]
    )

    col1, col2 = st.columns(2)

    with col1:

        if not status_df.empty:

            status_df["total"] = pd.to_numeric(
                status_df["total"], errors="coerce"
            ).fillna(0)

            fig = px.pie(
                status_df,
                names="statut",
                values="total",
                hole=0.55,
                title="Répartition des rendez-vous par statut",
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            fig.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}<br>Nombre : %{value}<extra></extra>"
            )

            afficher_graphique(fig)

        else:
            show_empty("Aucune donnée sur les statuts des rendez-vous.")

    with col2:

        if not monthly_rdv.empty:

            monthly_rdv["total"] = pd.to_numeric(
                monthly_rdv["total"], errors="coerce"
            ).fillna(0)

            monthly_rdv = monthly_rdv.sort_values("mois")

            fig = px.line(
                monthly_rdv,
                x="mois",
                y="total",
                markers=True,
                title="Évolution mensuelle des rendez-vous",
                labels={
                    "mois": "Mois",
                    "total": "Nombre de rendez-vous"
                }
            )

            fig.update_traces(
                mode="lines+markers",
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate="Mois : %{x}<br>Rendez-vous : %{y}<extra></extra>"
            )

            afficher_graphique(fig)

        else:
            show_empty("Aucune évolution mensuelle disponible.")

    st.divider()

    # ========================================================
    # 3. PERFORMANCE DE L'EQUIPE MEDICALE
    # ========================================================

    st.markdown("### 🩺 Performance de l'équipe médicale")

    medecins_df = preparer_dataframe(
        consult_data.get("par_medecin", []),
        ["medecin", "specialite", "total"]
    )

    if not medecins_df.empty:

        medecins_df["total"] = pd.to_numeric(
            medecins_df["total"], errors="coerce"
        ).fillna(0)

        medecins_df = medecins_df.sort_values(
            "total", ascending=True
        )

        fig = px.bar(
            medecins_df,
            x="total",
            y="medecin",
            color="specialite",
            orientation="h",
            text="total",
            title="Volume de consultations par médecin",
            labels={
                "medecin": "Médecin",
                "total": "Nombre de consultations",
                "specialite": "Spécialité"
            },
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        fig.update_traces(textposition="outside")

        afficher_graphique(
            fig,
            hauteur=max(350, len(medecins_df) * 55)
        )

    else:
        show_empty("Aucune consultation enregistrée.")

    st.divider()

    # ========================================================
    # 4. PERFORMANCE FINANCIERE
    # ========================================================

    st.markdown("### 💰 Performance financière")

    f1, f2, f3, f4 = st.columns(4)

    montant_factures = valeur_nombre(ind.get("montant_factures", 0))
    montant_encaisse = valeur_nombre(ind.get("montant_encaisse", 0))
    total_depenses = valeur_nombre(ind.get("total_depenses", 0))
    solde_net = valeur_nombre(ind.get("solde_net", 0))

    f1.metric("🧾 Factures émises", format_money(montant_factures))
    f2.metric("💳 Encaissements", format_money(montant_encaisse))
    f3.metric("📉 Dépenses", format_money(total_depenses))
    f4.metric("📈 Solde net", format_money(solde_net))

    if ind.get("total_factures", 0) > 0 and montant_encaisse == 0:
        st.info(
            "Aucun paiement validé n'est enregistré. "
            "Le montant des factures ne représente pas les encaissements."
        )

    st.divider()

    # ========================================================
    # 5. RESUME ET INTERPRETATION
    # ========================================================

    st.markdown("### 📌 Résumé de l'activité")

    total_rdv = valeur_nombre(ind.get("total_rendez_vous", len(rdvs)))
    total_consultations = valeur_nombre(ind.get("total_consultations", 0))
    total_hospitalisations = valeur_nombre(
        ind.get("hospitalisations_en_cours", 0)
    )

    r1, r2, r3 = st.columns(3)

    r1.metric("Rendez-vous enregistrés", int(total_rdv))
    r2.metric("Consultations réalisées", int(total_consultations))
    r3.metric("Hospitalisations en cours", int(total_hospitalisations))

# ============================================================
# ONGLET 2 : RENDEZ-VOUS
# ============================================================

with tab_rdv:

    st.subheader("📅 Centre d'analyse des rendez-vous")

    status_df = preparer_dataframe(
        rdv_data.get("par_statut", []),
        ["statut", "total"]
    )

    total_rdv = valeur_nombre(
        ind.get("total_rendez_vous", len(rdvs))
    )

    confirmes = 0
    en_attente = 0
    autres = 0

    if not status_df.empty:

        for _, ligne in status_df.iterrows():

            statut = str(ligne["statut"]).lower().strip()
            total = valeur_nombre(ligne["total"])

            if statut in ["confirmé", "confirme"]:
                confirmes += total

            elif statut == "en_attente":
                en_attente += total

            else:
                autres += total

    taux_confirmation = (
        confirmes / total_rdv * 100
        if total_rdv > 0 else 0
    )

    r1, r2, r3, r4 = st.columns(4)

    r1.metric("Total", int(total_rdv))
    r2.metric("Confirmés", int(confirmes))
    r3.metric("En attente", int(en_attente))
    r4.metric("Taux de confirmation", f"{taux_confirmation:.1f}%")

    st.progress(
        min(max(taux_confirmation / 100, 0), 1)
    )

    st.divider()

    # Statuts
    st.markdown("### 📊 Répartition des statuts")

    col1, col2 = st.columns(2)

    with col1:

        if not status_df.empty:

            fig = px.pie(
                status_df,
                names="statut",
                values="total",
                hole=0.55,
                title="Statuts des rendez-vous",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig.update_traces(
                textinfo="percent+label"
            )

            afficher_graphique(fig)

        else:
            show_empty()

    with col2:

        if not status_df.empty:

            fig = px.bar(
                status_df,
                x="statut",
                y="total",
                color="statut",
                text="total",
                title="Nombre de rendez-vous par statut"
            )

            fig.update_traces(
                textposition="outside"
            )

            afficher_graphique(fig)

        else:
            show_empty()

    st.divider()

    # Evolution mensuelle
    st.markdown("### 📈 Évolution mensuelle")

    monthly_df = preparer_dataframe(
        rdv_data.get("par_mois", []),
        ["mois", "total"]
    )

    if not monthly_df.empty:

        monthly_df["total"] = pd.to_numeric(
            monthly_df["total"],
            errors="coerce"
        ).fillna(0)

        monthly_df = monthly_df.sort_values("mois")

        fig = px.line(
            monthly_df,
            x="mois",
            y="total",
            markers=True,
            text="total",
            title="Tendance des rendez-vous",
            labels={
                "mois": "Mois",
                "total": "Nombre de rendez-vous"
            }
        )

        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=10),
            textposition="top center"
        )

        afficher_graphique(fig)

    else:
        show_empty("Aucune donnée mensuelle.")

    st.divider()

    # Analyse des jours
    st.markdown("### 🗓️ Activité selon le jour de la semaine")

    if not rdvs_df.empty and "jour" in rdvs_df.columns:

        jours_df = (
            rdvs_df.groupby("jour")
            .size()
            .reset_index(name="total")
        )

        ordre_jours = [
            "Lundi", "Mardi", "Mercredi",
            "Jeudi", "Vendredi", "Samedi", "Dimanche"
        ]

        jours_df["jour"] = pd.Categorical(
            jours_df["jour"],
            categories=ordre_jours,
            ordered=True
        )

        jours_df = jours_df.sort_values("jour")

        fig = px.bar(
            jours_df,
            x="jour",
            y="total",
            text="total",
            title="Nombre de rendez-vous par jour",
            labels={
                "jour": "Jour",
                "total": "Rendez-vous"
            }
        )

        afficher_graphique(fig)

    else:
        show_empty(
            "Les dates des rendez-vous ne permettent pas cette analyse."
        )

    # Analyse des heures
    st.markdown("### 🕒 Répartition par heure")

    if not rdvs_df.empty and "heure" in rdvs_df.columns:

        heures_df = (
            rdvs_df.groupby("heure")
            .size()
            .reset_index(name="total")
        )

        heures_df["heure"] = heures_df["heure"].astype(str) + "h"

        fig = px.bar(
            heures_df,
            x="heure",
            y="total",
            text="total",
            title="Heures des rendez-vous",
            labels={
                "heure": "Heure",
                "total": "Rendez-vous"
            }
        )

        afficher_graphique(fig)

    else:
        show_empty("Aucune heure de rendez-vous disponible.")


# ============================================================
# ONGLET 3 : FINANCE
# ============================================================

with tab_finance:

    st.subheader("💰 Centre de pilotage financier")

    montant_factures = valeur_nombre(
        ind.get("montant_factures", 0)
    )

    montant_encaisse = valeur_nombre(
        ind.get("montant_encaisse", 0)
    )

    total_depenses = valeur_nombre(
        ind.get("total_depenses", 0)
    )

    solde_net = valeur_nombre(
        ind.get("solde_net", montant_encaisse - total_depenses)
    )

    taux_encaissement = (
        montant_encaisse / montant_factures * 100
        if montant_factures > 0 else 0
    )

    a, b, c, d = st.columns(4)

    a.metric("Factures émises", format_money(montant_factures))
    b.metric("Encaissements", format_money(montant_encaisse))
    c.metric("Dépenses", format_money(total_depenses))
    d.metric("Solde net", format_money(solde_net))

    st.divider()

    st.markdown("### 📊 Indicateurs financiers")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Taux d'encaissement",
            f"{taux_encaissement:.1f}%"
        )

        st.progress(
            min(max(taux_encaissement / 100, 0), 1)
        )

    with col2:

        reste = max(montant_factures - montant_encaisse, 0)

        st.metric(
            "Montant non encore encaissé",
            format_money(reste)
        )

    st.divider()

    # Comparaison financière
    st.markdown("### 📈 Comparaison des montants")

    finance_compare = pd.DataFrame({
        "Catégorie": [
            "Factures émises",
            "Encaissements",
            "Dépenses",
            "Solde net"
        ],
        "Montant": [
            montant_factures,
            montant_encaisse,
            total_depenses,
            solde_net
        ]
    })

    fig = px.bar(
        finance_compare,
        x="Catégorie",
        y="Montant",
        color="Catégorie",
        text="Montant",
        title="Vue financière globale",
        labels={
            "Montant": "Montant en TND"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.2f} TND",
        textposition="outside"
    )

    afficher_graphique(fig, 430)

    st.divider()

    # Evolution mensuelle
    st.markdown("### 📅 Évolution mensuelle des finances")

    paiements_df = preparer_dataframe(
        finance.get("paiements_par_mois", []),
        ["mois", "montant"]
    )

    depenses_df = preparer_dataframe(
        finance.get("depenses_par_mois", []),
        ["mois", "montant"]
    )

    if not paiements_df.empty or not depenses_df.empty:

        if paiements_df.empty:
            paiements_df = pd.DataFrame(
                columns=["mois", "montant"]
            )

        if depenses_df.empty:
            depenses_df = pd.DataFrame(
                columns=["mois", "montant"]
            )

        paiements_df["montant"] = pd.to_numeric(
            paiements_df["montant"],
            errors="coerce"
        ).fillna(0)

        depenses_df["montant"] = pd.to_numeric(
            depenses_df["montant"],
            errors="coerce"
        ).fillna(0)

        paiements_df = (
            paiements_df.groupby("mois", as_index=False)["montant"]
            .sum()
            .rename(columns={"montant": "Encaissements"})
        )

        depenses_df = (
            depenses_df.groupby("mois", as_index=False)["montant"]
            .sum()
            .rename(columns={"montant": "Dépenses"})
        )

        evolution = pd.merge(
            paiements_df,
            depenses_df,
            on="mois",
            how="outer"
        ).fillna(0)

        evolution = evolution.sort_values("mois")

        evolution_long = evolution.melt(
            id_vars="mois",
            var_name="Type",
            value_name="Montant"
        )

        fig = px.bar(
            evolution_long,
            x="mois",
            y="Montant",
            color="Type",
            barmode="group",
            text_auto=".2f",
            title="Encaissements et dépenses par mois"
        )

        afficher_graphique(fig, 430)

    else:
        show_empty("Aucune donnée financière mensuelle.")

    st.divider()

    # Dépenses par catégorie
    st.markdown("### 🧾 Répartition des dépenses")

    categories_df = preparer_dataframe(
        finance.get("depenses_par_categorie", []),
        ["categorie", "montant"]
    )

    if not categories_df.empty:

        categories_df["montant"] = pd.to_numeric(
            categories_df["montant"],
            errors="coerce"
        ).fillna(0)

        fig = px.pie(
            categories_df,
            names="categorie",
            values="montant",
            hole=0.5,
            title="Dépenses par catégorie",
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_traces(
            textinfo="percent+label"
        )

        afficher_graphique(fig)

        st.dataframe(
            categories_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        show_empty("Aucune dépense catégorisée.")


# ============================================================
# ONGLET 4 : PHARMACIE
# ============================================================

with tab_pharma:

    st.subheader("💊 Tableau de bord de la pharmacie")

    p1, p2, p3 = st.columns(3)

    p1.metric(
        "Médicaments",
        ind.get("total_medicaments", 0)
    )

    p2.metric(
        "Unités en stock",
        ind.get("stock_total", 0)
    )

    p3.metric(
        "Alertes",
        ind.get("medicaments_en_alerte", 0)
    )

    st.divider()

    # Alertes
    st.markdown("### 🚨 Surveillance du stock")

    alertes_df = dataframe_or_empty(
        pharmacie.get("medicaments_en_alerte", [])
    )

    if not alertes_df.empty:

        st.warning(
            f"{len(alertes_df)} médicament(s) nécessitent une vérification du stock."
        )

        st.dataframe(
            alertes_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        show_empty(
            "Aucun médicament en alerte ou aucune donnée disponible."
        )

    st.divider()

    # Mouvements
    st.markdown("### 📦 Analyse des mouvements de stock")

    mouvements_df = preparer_dataframe(
        pharmacie.get("mouvements_par_type", []),
        ["type", "total"]
    )

    if not mouvements_df.empty:

        mouvements_df["total"] = pd.to_numeric(
            mouvements_df["total"],
            errors="coerce"
        ).fillna(0)

        col1, col2 = st.columns(2)

        with col1:

            fig = px.pie(
                mouvements_df,
                names="type",
                values="total",
                hole=0.55,
                title="Répartition des mouvements",
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            afficher_graphique(fig)

        with col2:

            fig = px.bar(
                mouvements_df,
                x="type",
                y="total",
                color="type",
                text="total",
                title="Volume des mouvements"
            )

            afficher_graphique(fig)

    else:
        show_empty("Aucun mouvement de stock enregistré.")

    st.divider()

    st.markdown("### ℹ️ Interprétation")

    st.caption(
        "Les mouvements d'entrée, de sortie et d'ajustement permettent "
        "de suivre l'évolution du stock. Les alertes signalent les produits "
        "dont le stock atteint ou dépasse le seuil configuré."
    )


# ============================================================
# ONGLET 5 : INFRASTRUCTURE
# ============================================================


with tab_hospital:

    import html

    st.subheader("🏥 Tableau de bord de l'infrastructure")

    st.markdown("""
<style>
.infra-nav {
    position: sticky;
    top: 65px;
    z-index: 998;
    background: var(--background-color);
    padding: 8px 0;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="infra-nav">
</div>
""", unsafe_allow_html=True)

    nav1, nav2, nav3, nav4, nav5, nav6, nav7 = st.columns(7)

    with nav1:
        if st.button("📊 Indicateurs", key="nav_infra_1"):
            st.session_state["infra_section"] = "indicateurs"

    with nav2:
        if st.button("🛏️ Occupation", key="nav_infra_2"):
            st.session_state["infra_section"] = "occupation"

    with nav3:
        if st.button("📈 Graphiques", key="nav_infra_3"):
            st.session_state["infra_section"] = "graphiques"

    with nav4:
        if st.button("🏥 Services", key="nav_infra_4"):
            st.session_state["infra_section"] = "services"

    with nav5:
        if st.button("🚪 Salles", key="nav_infra_5"):
            st.session_state["infra_section"] = "salles"

    with nav6:
        if st.button("🛏️ Lits", key="nav_infra_6"):
            st.session_state["infra_section"] = "lits"

    with nav7:
        if st.button("📋 Résumé", key="nav_infra_7"):
            st.session_state["infra_section"] = "resume"

    # ==========================================================
    # 1. RECUPERATION DES DONNEES
    # ==========================================================

    def infra_liste(donnees):

        if isinstance(donnees, list):
            return donnees

        if isinstance(donnees, dict):
            return donnees.get("value", [])

        return []

    services_data = infra_liste(
        get_api_data("/services-medicaux/")
    )

    salles_data = infra_liste(
        get_api_data("/salles-medicales/")
    )

    lits_data = infra_liste(
        get_api_data("/lits/")
    )

    if not services_data:
        st.warning("Aucun service médical disponible.")

    else:

        df_services = pd.DataFrame(services_data)
        df_salles = pd.DataFrame(salles_data)
        df_lits = pd.DataFrame(lits_data)

        # Colonnes de sécurité
        for col in ["id", "nom", "capacite", "statut"]:
            if col not in df_services.columns:
                df_services[col] = None

        for col in [
            "id", "id_service", "nom",
            "type_salle", "capacite", "statut"
        ]:
            if col not in df_salles.columns:
                df_salles[col] = None

        for col in [
            "id", "id_salle", "numero",
            "type_lit", "statut"
        ]:
            if col not in df_lits.columns:
                df_lits[col] = None

        # Conversion des identifiants et capacités
        for df, colonnes in [
            (df_services, ["id", "capacite"]),
            (df_salles, ["id", "id_service", "capacite"]),
            (df_lits, ["id", "id_salle"])
        ]:
            for col in colonnes:
                df[col] = pd.to_numeric(
                    df[col], errors="coerce"
                )

        df_services["capacite"] = (
            df_services["capacite"].fillna(0)
        )

        df_salles["capacite"] = (
            df_salles["capacite"].fillna(0)
        )

        # Normalisation des statuts
        def infra_statut(valeur):

            valeur = str(valeur or "").strip().lower()

            return (
                valeur.replace("é", "e")
                .replace("è", "e")
                .replace("ê", "e")
                .replace("à", "a")
                .replace(" ", "_")
            )

        df_lits["statut_normalise"] = (
            df_lits["statut"].apply(infra_statut)
        )

        df_salles["statut_normalise"] = (
            df_salles["statut"].apply(infra_statut)
        )

        # ======================================================
        # 2. CALCULS GLOBAUX
        # ======================================================

        total_services = len(df_services)
        total_salles = len(df_salles)
        total_lits = len(df_lits)

        lits_occupes = int(
            df_lits["statut_normalise"].isin(
                ["occupe", "occupé"]
            ).sum()
        )

        lits_disponibles = int(
            df_lits["statut_normalise"].isin(
                ["disponible", "libre"]
            ).sum()
        )

        lits_maintenance = int(
            df_lits["statut_normalise"].isin(
                ["maintenance", "hors_service"]
            ).sum()
        )

        lits_autres = (
            total_lits
            - lits_occupes
            - lits_disponibles
            - lits_maintenance
        )

        taux_occupation = (
            lits_occupes / total_lits * 100
            if total_lits > 0 else 0
        )

        taux_disponibilite = (
            lits_disponibles / total_lits * 100
            if total_lits > 0 else 0
        )

        hospitalisations_en_cours = valeur_nombre(
            ind.get("hospitalisations_en_cours", 0)
        )

        # ======================================================
        # 3. PREPARATION DES SALLES
        # ======================================================

        noms_services = dict(
            zip(
                df_services["id"],
                df_services["nom"]
            )
        )

        salles_preparees = []

        for _, salle in df_salles.iterrows():

            salle_id = salle["id"]

            lits_salle = df_lits[
                df_lits["id_salle"] == salle_id
            ]

            capacite = int(salle["capacite"])

            nombre_lits = len(lits_salle)

            occupes = int(
                lits_salle["statut_normalise"].isin(
                    ["occupe", "occupé"]
                ).sum()
            )

            disponibles = int(
                lits_salle["statut_normalise"].isin(
                    ["disponible", "libre"]
                ).sum()
            )

            maintenance = int(
                lits_salle["statut_normalise"].isin(
                    ["maintenance", "hors_service"]
                ).sum()
            )

            service = noms_services.get(
                salle["id_service"],
                "Service inconnu"
            )

            statut_salle = salle["statut_normalise"]

            if statut_salle in [
                "maintenance", "hors_service"
            ]:
                etat = "Maintenance"

            elif capacite > 0 and occupes >= capacite:
                etat = "Complète"

            elif disponibles > 0 and occupes > 0:
                etat = "Partiellement occupée"

            elif disponibles > 0:
                etat = "Disponible"

            elif nombre_lits < capacite:
                etat = "À équiper"

            elif occupes > 0:
                etat = "Complète"

            else:
                etat = "Indisponible"

            salles_preparees.append({
                "id": int(salle_id),
                "service": service,
                "nom": salle["nom"],
                "type": salle["type_salle"],
                "capacite": capacite,
                "total_lits": nombre_lits,
                "occupes": occupes,
                "disponibles": disponibles,
                "maintenance": maintenance,
                "statut": etat,
                "id_service": salle["id_service"]
            })

        df_salles_detail = pd.DataFrame(
            salles_preparees
        )

        # ======================================================
        # 4. CARTES KPI
        # ======================================================

        st.markdown("### 📊 Indicateurs principaux")

        k1, k2, k3, k4 = st.columns(4)

        k1.metric(
            "Services médicaux",
            total_services
        )

        k2.metric(
            "Salles médicales",
            total_salles
        )

        k3.metric(
            "Total des lits",
            total_lits
        )

        k4.metric(
            "Hospitalisations en cours",
            int(hospitalisations_en_cours)
        )

        k5, k6, k7, k8 = st.columns(4)

        k5.metric(
            "Lits disponibles",
            lits_disponibles
        )

        k6.metric(
            "Lits occupés",
            lits_occupes
        )

        k7.metric(
            "En maintenance",
            lits_maintenance
        )

        k8.metric(
            "Taux d'occupation",
            f"{taux_occupation:.1f}%"
        )

        st.divider()

        # ======================================================
        # 5. TAUX D'OCCUPATION ET DISPONIBILITE
        # ======================================================

        st.markdown("### 🛏️ Occupation et disponibilité")

        gauche, droite = st.columns(2)

        with gauche:

            st.markdown("**Taux d'occupation**")

            st.metric(
                "Lits occupés",
                f"{taux_occupation:.1f}%"
            )

            st.progress(
                min(max(taux_occupation / 100, 0), 1)
            )

        with droite:

            st.markdown("**Taux de disponibilité**")

            st.metric(
                "Lits disponibles",
                f"{taux_disponibilite:.1f}%"
            )

            st.progress(
                min(max(taux_disponibilite / 100, 0), 1)
            )

        # ======================================================
        # 6. GRAPHIQUES DE REPARTITION
        # ======================================================

        st.divider()
        st.markdown("### 📈 Analyses graphiques")

        col1, col2 = st.columns(2)

        with col1:

            repartition = pd.DataFrame({
                "Statut": [
                    "Disponibles",
                    "Occupés",
                    "Maintenance",
                    "Autres"
                ],
                "Nombre": [
                    lits_disponibles,
                    lits_occupes,
                    lits_maintenance,
                    lits_autres
                ]
            })

            repartition = repartition[
                repartition["Nombre"] > 0
            ]

            if not repartition.empty:

                fig = px.pie(
                    repartition,
                    names="Statut",
                    values="Nombre",
                    hole=0.55,
                    title="Répartition des lits",
                    color="Statut",
                    color_discrete_map={
                        "Disponibles": "#16A34A",
                        "Occupés": "#DC2626",
                        "Maintenance": "#F59E0B",
                        "Autres": "#64748B"
                    }
                )

                fig.update_traces(
                    textinfo="percent+label"
                )

                afficher_graphique(fig)

            else:
                show_empty("Aucun lit enregistré.")

        with col2:

            if not df_salles_detail.empty:

                fig = px.bar(
                    df_salles_detail,
                    x="nom",
                    y=["disponibles", "occupes", "maintenance"],
                    title="État des lits par salle",
                    labels={
                        "value": "Nombre de lits",
                        "nom": "Salle",
                        "variable": "Statut"
                    },
                    barmode="stack",
                    color_discrete_map={
                        "disponibles": "#16A34A",
                        "occupes": "#DC2626",
                        "maintenance": "#F59E0B"
                    }
                )

                afficher_graphique(fig)

            else:
                show_empty("Aucune salle enregistrée.")

        # ======================================================
        # 7. COMPARAISON DES SERVICES
        # ======================================================

        st.markdown("### 🏥 Comparaison entre les services")

        if not df_salles_detail.empty:

            services_stats = (
                df_salles_detail
                .groupby("service", as_index=False)
                .agg(
                    salles=("id", "count"),
                    capacite=("capacite", "sum"),
                    lits=("total_lits", "sum"),
                    occupes=("occupes", "sum"),
                    disponibles=("disponibles", "sum"),
                    maintenance=("maintenance", "sum")
                )
            )

            services_stats["taux_occupation"] = (
                services_stats["occupes"]
                / services_stats["lits"].replace(0, pd.NA)
                * 100
            ).fillna(0)

            col1, col2 = st.columns(2)

            with col1:

                fig = px.bar(
                    services_stats,
                    x="service",
                    y=["occupes", "disponibles"],
                    barmode="group",
                    title="Lits occupés et disponibles par service",
                    labels={
                        "service": "Service",
                        "value": "Nombre de lits",
                        "variable": "Statut"
                    },
                    color_discrete_map={
                        "occupes": "#DC2626",
                        "disponibles": "#16A34A"
                    }
                )

                afficher_graphique(fig)

            with col2:

                fig = px.bar(
                    services_stats,
                    x="service",
                    y="capacite",
                    text="capacite",
                    title="Capacité totale par service",
                    labels={
                        "service": "Service",
                        "capacite": "Capacité"
                    },
                    color="service"
                )

                afficher_graphique(fig)

            st.dataframe(
                services_stats,
                use_container_width=True,
                hide_index=True
            )

        # ======================================================
        # 8. TABLEAU COMPLET DES SERVICES
        # ======================================================

        st.divider()
        st.markdown("### 📋 Tous les services médicaux")

        colonnes = [
            "id", "nom", "description",
            "capacite", "statut"
        ]

        st.dataframe(
            df_services[colonnes],
            use_container_width=True,
            hide_index=True
        )

        # ======================================================
        # 9. TABLEAU ET BADGES DES SALLES
        # ======================================================

        st.divider()
        st.markdown("### 🚪 État détaillé des salles")

        couleurs = {
            "Disponible": "#16A34A",
            "Complète": "#DC2626",
            "Partiellement occupée": "#D97706",
            "Maintenance": "#D97706",
            "À équiper": "#64748B",
            "Indisponible": "#64748B"
        }

        if not df_salles_detail.empty:

            for service in df_salles_detail["service"].unique():

                st.markdown(f"#### 🏥 {service}")

                salles_service = df_salles_detail[
                    df_salles_detail["service"] == service
                ]

                colonnes_salles = st.columns(2)

                for index, (_, salle) in enumerate(
                    salles_service.iterrows()
                ):

                    with colonnes_salles[index % 2]:

                        couleur = couleurs.get(
                            salle["statut"],
                            "#64748B"
                        )

                        statut_html = html.escape(
                            salle["statut"]
                        )

                        nom_html = html.escape(
                            str(salle["nom"])
                        )

                        with st.container(border=True):

                            render_clean_html(
                                f"""
                                <div style="
                                    display:flex;
                                    justify-content:space-between;
                                    align-items:center;
                                    gap:8px;
                                    flex-wrap:wrap;
                                ">
                                    <b>🚪 {nom_html}</b>
                                    <span style="
                                        background:{couleur};
                                        color:white;
                                        padding:4px 10px;
                                        border-radius:20px;
                                        font-size:12px;
                                        font-weight:600;
                                    ">{statut_html}</span>
                                </div>
                                """
                            )

                            st.caption(
                                f"ID : {salle['id']} | "
                                f"Type : {salle['type']}"
                            )

                            a, b, c = st.columns(3)

                            a.metric(
                                "Capacité",
                                int(salle["capacite"])
                            )

                            b.metric(
                                "Occupés",
                                int(salle["occupes"])
                            )

                            c.metric(
                                "Disponibles",
                                int(salle["disponibles"])
                            )

                            st.caption(
                                f"Lits enregistrés : "
                                f"{int(salle['total_lits'])} / "
                                f"{int(salle['capacite'])}"
                            )

        else:
            show_empty("Aucune salle enregistrée.")

        # ======================================================
        # 10. DETAIL DE TOUS LES LITS
        # ======================================================

        st.divider()
        st.markdown("### 🛏️ Inventaire détaillé des lits")

        if not df_lits.empty:

            service_filtre = st.selectbox(
                "Filtrer par service",
                ["Tous les services"] +
                list(df_services["nom"].dropna().unique()),
                key="infra_filtre_service"
            )

            df_lits_affichage = df_lits.copy()

            # Association lit -> salle -> service
            df_lits_affichage = df_lits_affichage.merge(
                df_salles[
                    ["id", "id_service", "nom"]
                ].rename(columns={
                    "id": "id_salle",
                    "nom": "nom_salle"
                }),
                on="id_salle",
                how="left"
            )

            df_lits_affichage["service"] = (
                df_lits_affichage["id_service"].map(
                    noms_services
                )
            )

            if service_filtre != "Tous les services":

                df_lits_affichage = df_lits_affichage[
                    df_lits_affichage["service"] == service_filtre
                ]

            for _, lit in df_lits_affichage.iterrows():

                statut = infra_statut(lit["statut"])

                if statut in ["disponible", "libre"]:
                    couleur = "#16A34A"
                    libelle = "Disponible"

                elif statut in ["occupe", "occupé"]:
                    couleur = "#DC2626"
                    libelle = "Occupé"

                elif statut in ["maintenance", "hors_service"]:
                    couleur = "#D97706"
                    libelle = "Maintenance"

                else:
                    couleur = "#64748B"
                    libelle = str(lit["statut"])

                render_clean_html(
                    f"""
                    <div style="
                        border:1px solid rgba(128,128,128,.3);
                        border-radius:9px;
                        padding:10px 14px;
                        margin-bottom:7px;
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        flex-wrap:wrap;
                        gap:8px;
                    ">
                        <span>
                            🛏️ <b>{html.escape(str(lit['numero']))}</b>
                            <small>
                                — {html.escape(str(lit['service']))}
                                / {html.escape(str(lit['nom_salle']))}
                            </small>
                        </span>
                        <span style="
                            background:{couleur};
                            color:white;
                            border-radius:20px;
                            padding:4px 10px;
                            font-size:12px;
                            font-weight:600;
                        ">
                            {html.escape(libelle)}
                        </span>
                    </div>
                    """
                )

        else:
            show_empty("Aucun lit enregistré.")

        # ======================================================
        # 11. RESUME FINAL
        # ======================================================

        st.divider()
        st.markdown("### 📊 Résumé général")

        resume = pd.DataFrame({
            "Indicateur": [
                "Services médicaux",
                "Salles médicales",
                "Capacité théorique des salles",
                "Lits enregistrés",
                "Lits occupés",
                "Lits disponibles",
                "Lits en maintenance",
                "Taux d'occupation",
                "Taux de disponibilité",
                "Hospitalisations en cours"
            ],
            "Valeur": [
                total_services,
                total_salles,
                int(df_salles["capacite"].sum()),
                total_lits,
                lits_occupes,
                lits_disponibles,
                lits_maintenance,
                f"{taux_occupation:.1f}%",
                f"{taux_disponibilite:.1f}%",
                int(hospitalisations_en_cours)
            ]
        })

        st.dataframe(
            resume,
            use_container_width=True,
            hide_index=True
        )




# ============================================================
# ONGLET 6 : SATISFACTION ET ACTIVITE
# ============================================================

with tab_activity:

    st.subheader("⭐ Expérience et activité de la clinique")

    moyenne = valeur_nombre(
        ind.get("note_satisfaction_moyenne", 0)
    )

    total_evaluations = valeur_nombre(
        ind.get("total_evaluations", 0)
    )

    total_activites = valeur_nombre(
        ind.get("total_activites", 0)
    )

    s1, s2, s3 = st.columns(3)

    s1.metric(
        "Note moyenne",
        f"{moyenne:.2f}/5"
    )

    s2.metric(
        "Évaluations",
        int(total_evaluations)
    )

    s3.metric(
        "Actions enregistrées",
        int(total_activites)
    )

    st.divider()

    # Satisfaction
    st.markdown("### ⭐ Analyse de la satisfaction")

    satisfaction_df = preparer_dataframe(
        satisfaction.get("distribution", []),
        ["note", "total"]
    )

    if not satisfaction_df.empty and total_evaluations > 0:

        satisfaction_df["note"] = pd.to_numeric(
            satisfaction_df["note"],
            errors="coerce"
        )

        satisfaction_df["total"] = pd.to_numeric(
            satisfaction_df["total"],
            errors="coerce"
        ).fillna(0)

        satisfaction_df = satisfaction_df.dropna(
            subset=["note"]
        )

        satisfaction_df = satisfaction_df.sort_values("note")

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                satisfaction_df,
                x="note",
                y="total",
                text="total",
                title="Nombre d'évaluations par note",
                labels={
                    "note": "Note sur 5",
                    "total": "Évaluations"
                },
                color="note",
                color_continuous_scale="Blues"
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode="linear",
                    tick0=1,
                    dtick=1
                ),
                coloraxis_showscale=False
            )

            afficher_graphique(fig)

        with col2:

            fig = px.pie(
                satisfaction_df,
                names="note",
                values="total",
                hole=0.58,
                title="Distribution des notes",
                color_discrete_sequence=px.colors.sequential.Blues
            )

            fig.update_traces(
                textinfo="percent+label"
            )

            afficher_graphique(fig)

    else:
        show_empty("Aucune évaluation de satisfaction enregistrée.")

    st.divider()

    # Activité par module
    st.markdown("### 📋 Activité par module")

    modules_df = preparer_dataframe(
        activite.get("par_module", []),
        ["module", "total"]
    )

    if not modules_df.empty:

        modules_df["total"] = pd.to_numeric(
            modules_df["total"],
            errors="coerce"
        ).fillna(0)

        modules_df = modules_df.sort_values(
            "total",
            ascending=True
        )

        fig = px.bar(
            modules_df,
            x="total",
            y="module",
            orientation="h",
            color="module",
            text="total",
            title="Nombre d'actions par module"
        )

        fig.update_traces(
            textposition="outside"
        )

        afficher_graphique(
            fig,
            hauteur=max(350, len(modules_df) * 55)
        )

    else:
        show_empty("Aucune activité enregistrée.")

    st.divider()

    # Activité par action
    st.markdown("### ⚙️ Répartition des actions")

    actions_df = preparer_dataframe(
        activite.get("par_action", []),
        ["action", "total"]
    )

    if not actions_df.empty:

        fig = px.pie(
            actions_df,
            names="action",
            values="total",
            hole=0.5,
            title="Types d'actions effectuées",
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_traces(
            textinfo="percent+label"
        )

        afficher_graphique(fig)

    else:
        show_empty("Aucune action disponible dans le journal.")



# ============================================================
# 9. GESTION DES UTILISATEURS - ANALYTICS AVANCES
# ============================================================

# Fonctions de récupération avec cache pour éviter
# 59 requêtes API à chaque interaction Streamlit.

@st.cache_data(ttl=120, show_spinner=False)
def charger_consultations_api():

    consultations = []

    try:
        response = requests.get(
            f"{API_URL}/patients/",
            timeout=20
        )

        response.raise_for_status()
        liste_patients = response.json()

        if not isinstance(liste_patients, list):
            return []

        for patient in liste_patients:

            patient_id = patient.get("id")

            if patient_id is None:
                continue

            try:
                rep = requests.get(
                    f"{API_URL}/patients/{patient_id}/consultations",
                    timeout=10
                )

                if rep.status_code != 200:
                    continue

                resultat = rep.json()

                if isinstance(resultat, dict):
                    resultat = resultat.get("consultations", [])

                if not isinstance(resultat, list):
                    continue

                for c in resultat:

                    consultations.append({
                        "id": c.get("id"),
                        "id_patient": patient_id,
                        "nom_patient": patient.get("nom_complet"),
                        "medecin": c.get("medecin"),
                        "date": c.get("date") or c.get("date_consultation"),
                        "diagnostic": c.get("diagnostic")
                    })

            except requests.RequestException:
                continue

    except (requests.RequestException, ValueError):
        return []

    return consultations


@st.cache_data(ttl=60, show_spinner=False)
def charger_journal_api():

    try:
        response = requests.get(
            f"{API_URL}/journal-activite/",
            timeout=15
        )

        response.raise_for_status()

        resultat = response.json()

        return resultat if isinstance(resultat, list) else []

    except (requests.RequestException, ValueError):
        return []


def normaliser_role(role):

    role = str(role or "").strip().lower()

    return (
        role.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
    )


def normaliser_nom(nom):

    import unicodedata

    nom = str(nom or "").strip().lower()

    nom = unicodedata.normalize("NFKD", nom)

    nom = "".join(
        c for c in nom
        if not unicodedata.combining(c)
    )

    nom = nom.replace("dr.", "").replace("dr ", "")

    return " ".join(nom.split())


def afficher_graphique_users(fig, hauteur=380):

    fig.update_layout(
        template="plotly_white",
        height=hauteur,
        margin=dict(l=30, r=30, t=60, b=35)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with tab_users:

    st.markdown("## 👥 Gestion des utilisateurs")

    st.caption(
        "Gestion des comptes, suivi individuel et analyse de l'activité."
    )

    # --------------------------------------------------------
    # 1. PREPARATION DES DONNEES
    # --------------------------------------------------------

    users_list = users if isinstance(users, list) else []
    patients_list = patients if isinstance(patients, list) else []
    rdvs_list = rdvs if isinstance(rdvs, list) else []

    with st.spinner("Chargement des statistiques utilisateurs..."):

        activites_list = charger_journal_api()
        consultations_list = charger_consultations_api()

    medecins = [
        u for u in users_list
        if normaliser_role(u.get("role")) == "medecin"
    ]

    secretaires = [
        u for u in users_list
        if normaliser_role(u.get("role")) == "secretaire"
    ]

    administrateurs = [
        u for u in users_list
        if normaliser_role(u.get("role")) in [
            "admin", "administrateur"
        ]
    ]

    comptes_patients = [
        u for u in users_list
        if normaliser_role(u.get("role")) == "patient"
    ]

    # --------------------------------------------------------
    # 2. INDICATEURS GLOBAUX
    # --------------------------------------------------------

    st.markdown("### 📊 Effectifs de la clinique")

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("🩺 Médecins", len(medecins))
    k2.metric("👩‍💼 Secrétaires", len(secretaires))
    k3.metric("🛡️ Administrateurs", len(administrateurs))
    k4.metric("👥 Comptes patients", len(comptes_patients))
    k5.metric("🏥 Dossiers patients", len(patients_list))

    st.caption(
        "Les comptes patients et les dossiers patients sont deux "
        "notions distinctes. Ils ne sont pas additionnés."
    )

    st.divider()

    # --------------------------------------------------------
    # 3. INDICATEURS D'ACTIVITE
    # --------------------------------------------------------

    st.markdown("### 📈 Activité enregistrée")

    a1, a2, a3, a4 = st.columns(4)

    a1.metric("📅 Rendez-vous", len(rdvs_list))
    a2.metric("🩺 Consultations", len(consultations_list))
    a3.metric("⭐ Actions journalisées", len(activites_list))

    nb_succes = sum(
        1 for a in activites_list
        if normaliser_role(a.get("statut")) in [
            "succes", "success"
        ]
    )

    nb_echecs = sum(
        1 for a in activites_list
        if normaliser_role(a.get("statut")) in [
            "echec", "failure", "erreur"
        ]
    )

    a4.metric("✅ Actions réussies", nb_succes)

    st.caption(
        f"Actions en échec identifiées dans le journal : {nb_echecs}"
    )

    st.divider()

    # --------------------------------------------------------
    # 4. GRAPHIQUES GLOBAUX
    # --------------------------------------------------------

    st.markdown("### 📊 Répartition des utilisateurs")

    col1, col2 = st.columns(2)

    with col1:

        roles_df = pd.DataFrame({
            "Rôle": [
                "Médecins",
                "Secrétaires",
                "Administrateurs",
                "Patients"
            ],
            "Nombre": [
                len(medecins),
                len(secretaires),
                len(administrateurs),
                len(comptes_patients)
            ]
        })

        roles_df = roles_df[roles_df["Nombre"] > 0]

        if not roles_df.empty:

            fig = px.pie(
                roles_df,
                names="Rôle",
                values="Nombre",
                hole=0.58,
                title="Composition des comptes",
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            fig.update_traces(
                textinfo="percent+label"
            )

            afficher_graphique_users(fig)

        else:
            show_empty("Aucun compte utilisateur.")

    with col2:

        effectifs_df = roles_df.copy()

        if not effectifs_df.empty:

            fig = px.bar(
                effectifs_df,
                x="Rôle",
                y="Nombre",
                color="Rôle",
                text="Nombre",
                title="Effectifs par rôle"
            )

            fig.update_traces(
                textposition="outside"
            )

            afficher_graphique_users(fig)

        else:
            show_empty()

    st.divider()

    # --------------------------------------------------------
    # 5. ANALYSE DES ACTIVITES
    # --------------------------------------------------------

    st.markdown("### ⚙️ Activité par module")

    if activites_list:

        df_activites_global = pd.DataFrame(activites_list)

        if "module" in df_activites_global.columns:

            modules_df = (
                df_activites_global["module"]
                .fillna("Non renseigné")
                .value_counts()
                .reset_index()
            )

            modules_df.columns = ["Module", "Nombre"]

            fig = px.bar(
                modules_df,
                x="Nombre",
                y="Module",
                orientation="h",
                color="Module",
                text="Nombre",
                title="Volume d'actions par module"
            )

            afficher_graphique_users(
                fig,
                max(350, len(modules_df) * 55)
            )

        if "date_action" in df_activites_global.columns:

            df_activites_global["date_action"] = pd.to_datetime(
                df_activites_global["date_action"],
                errors="coerce"
            )

            df_temp = df_activites_global.dropna(
                subset=["date_action"]
            ).copy()

            if not df_temp.empty:

                df_temp["jour"] = (
                    df_temp["date_action"].dt.date.astype(str)
                )

                evolution = (
                    df_temp.groupby("jour")
                    .size()
                    .reset_index(name="Actions")
                )

                fig = px.line(
                    evolution,
                    x="jour",
                    y="Actions",
                    markers=True,
                    title="Évolution quotidienne des actions"
                )

                afficher_graphique_users(fig)

    else:
        show_empty("Aucune activité journalisée.")

    st.divider()

    # --------------------------------------------------------
    # 6. RECHERCHE ET FILTRES
    # --------------------------------------------------------

    st.markdown("### 📋 Annuaire des utilisateurs")

    if users_list:

        users_df = pd.DataFrame([
            {
                "ID": u.get("id"),
                "Nom complet": u.get("nom_complet"),
                "Email": u.get("email"),
                "Rôle": u.get("role"),
                "Spécialité": u.get("specialite"),
                "Bureau": u.get("bureau"),
                "Téléphone": u.get("telephone")
            }
            for u in users_list
        ])

        col_search, col_role = st.columns([2, 1])

        with col_search:

            recherche = st.text_input(
                "🔎 Rechercher un utilisateur",
                placeholder="Nom, email, spécialité...",
                key="search_admin_user_v2"
            )

        with col_role:

            roles_disponibles = ["Tous"] + sorted(
                users_df["Rôle"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filtre_role = st.selectbox(
                "Filtrer par rôle",
                roles_disponibles,
                key="filter_admin_role_v2"
            )

        df_filtre = users_df.copy()

        if recherche:

            masque = df_filtre.astype(str).apply(
                lambda colonne: colonne.str.contains(
                    recherche,
                    case=False,
                    na=False
                )
            ).any(axis=1)

            df_filtre = df_filtre[masque]

        if filtre_role != "Tous":

            df_filtre = df_filtre[
                df_filtre["Rôle"] == filtre_role
            ]

        st.caption(
            f"{len(df_filtre)} utilisateur(s) trouvé(s)"
        )

        st.dataframe(
            df_filtre,
            use_container_width=True,
            hide_index=True
        )

    else:
        show_empty("Aucun utilisateur enregistré.")

    st.divider()

    # --------------------------------------------------------
    # 7. FICHE INDIVIDUELLE
    # --------------------------------------------------------

    st.markdown("### 🔍 Analyse individuelle")

    if users_list:

        user_options = {
            (
                f"{u.get('nom_complet', 'Sans nom')} | "
                f"{u.get('role', 'Sans rôle')} | ID {u.get('id')}"
            ): u
            for u in users_list
        }

        selected_label = st.selectbox(
            "Choisir un utilisateur",
            list(user_options.keys()),
            key="selected_admin_user_v2"
        )

        selected_user = user_options[selected_label]

        user_id = selected_user.get("id")
        user_role = normaliser_role(selected_user.get("role"))

        col_info, col_detail = st.columns([1, 2])

        with col_info:

            st.markdown("#### 👤 Informations")

            st.write(
                "**Nom :**",
                selected_user.get("nom_complet") or "Non renseigné"
            )

            st.write(
                "**Email :**",
                selected_user.get("email") or "Non renseigné"
            )

            st.write(
                "**Rôle :**",
                selected_user.get("role") or "Non renseigné"
            )

            st.write(
                "**Spécialité :**",
                selected_user.get("specialite") or "Non renseignée"
            )

            st.write(
                "**Bureau :**",
                selected_user.get("bureau") or "Non renseigné"
            )

            st.write(
                "**Téléphone :**",
                selected_user.get("telephone") or "Non renseigné"
            )

        with col_detail:

            st.markdown("#### 📈 Indicateurs individuels")

            # =================================================
            # PROFIL MEDECIN
            # =================================================

            if user_role == "medecin":

                rdvs_medecin = [
                    r for r in rdvs_list
                    if str(r.get("id_medecin")) == str(user_id)
                ]

                nom_medecin = normaliser_nom(
                    selected_user.get("nom_complet")
                )

                consultations_medecin = [
                    c for c in consultations_list
                    if normaliser_nom(c.get("medecin")) == nom_medecin
                ]

                patients_ids = set()

                for r in rdvs_medecin:

                    if r.get("id_patient") is not None:
                        patients_ids.add(str(r["id_patient"]))

                for c in consultations_medecin:

                    if c.get("id_patient") is not None:
                        patients_ids.add(str(c["id_patient"]))

                m1, m2, m3 = st.columns(3)

                m1.metric(
                    "📅 Rendez-vous",
                    len(rdvs_medecin)
                )

                m2.metric(
                    "🩺 Consultations",
                    len(consultations_medecin)
                )

                m3.metric(
                    "👥 Patients associés",
                    len(patients_ids)
                )

                if rdvs_medecin:

                    st.markdown("##### 📅 Rendez-vous par statut")

                    df_rdv_med = pd.DataFrame(rdvs_medecin)

                    df_statut = (
                        df_rdv_med["statut"]
                        .fillna("Non renseigné")
                        .value_counts()
                        .reset_index()
                    )

                    df_statut.columns = ["Statut", "Nombre"]

                    fig = px.pie(
                        df_statut,
                        names="Statut",
                        values="Nombre",
                        hole=0.5,
                        title="Répartition des rendez-vous"
                    )

                    afficher_graphique_users(fig)

                    if "date_heure" in df_rdv_med.columns:

                        df_rdv_med["date_heure"] = pd.to_datetime(
                            df_rdv_med["date_heure"],
                            errors="coerce"
                        )

                        df_rdv_med = df_rdv_med.dropna(
                            subset=["date_heure"]
                        )

                        if not df_rdv_med.empty:

                            df_rdv_med["Mois"] = (
                                df_rdv_med["date_heure"]
                                .dt.to_period("M")
                                .astype(str)
                            )

                            tendance = (
                                df_rdv_med.groupby("Mois")
                                .size()
                                .reset_index(name="Rendez-vous")
                            )

                            fig = px.line(
                                tendance,
                                x="Mois",
                                y="Rendez-vous",
                                markers=True,
                                title="Évolution mensuelle des rendez-vous"
                            )

                            afficher_graphique_users(fig)

                if consultations_medecin:

                    st.markdown("##### 🩺 Historique des consultations")

                    df_consult = pd.DataFrame(
                        consultations_medecin
                    )

                    colonnes = [
                        "id",
                        "id_patient",
                        "nom_patient",
                        "date",
                        "medecin"
                    ]

                    colonnes = [
                        c for c in colonnes
                        if c in df_consult.columns
                    ]

                    st.dataframe(
                        df_consult[colonnes],
                        use_container_width=True,
                        hide_index=True
                    )

                if not rdvs_medecin and not consultations_medecin:

                    show_empty(
                        "Aucun rendez-vous ou consultation associé à ce médecin."
                    )

                st.caption(
                    "L'association des consultations au médecin est "
                    "effectuée à partir du nom renvoyé par l'API. "
                    "Pour une identification garantie, l'API devrait "
                    "également renvoyer id_medecin."
                )

            # =================================================
            # PROFIL SECRETAIRE
            # =================================================

            elif user_role == "secretaire":

                activites_user = [
                    a for a in activites_list
                    if str(a.get("id_utilisateur")) == str(user_id)
                ]

                succes_user = sum(
                    1 for a in activites_user
                    if normaliser_role(a.get("statut")) in [
                        "succes", "success"
                    ]
                )

                echec_user = sum(
                    1 for a in activites_user
                    if normaliser_role(a.get("statut")) in [
                        "echec", "erreur", "failure"
                    ]
                )

                s1, s2, s3 = st.columns(3)

                s1.metric("⭐ Actions", len(activites_user))
                s2.metric("✅ Réussites", succes_user)
                s3.metric("⚠️ Échecs", echec_user)

                if activites_user:

                    df_sec = pd.DataFrame(activites_user)

                    if "module" in df_sec.columns:

                        modules = (
                            df_sec["module"]
                            .fillna("Non renseigné")
                            .value_counts()
                            .reset_index()
                        )

                        modules.columns = ["Module", "Nombre"]

                        fig = px.bar(
                            modules,
                            x="Module",
                            y="Nombre",
                            color="Module",
                            text="Nombre",
                            title="Activité par module"
                        )

                        afficher_graphique_users(fig)

                    st.markdown("##### Historique des actions")

                    colonnes = [
                        "action",
                        "module",
                        "description",
                        "date_action",
                        "statut"
                    ]

                    colonnes = [
                        c for c in colonnes
                        if c in df_sec.columns
                    ]

                    st.dataframe(
                        df_sec[colonnes],
                        use_container_width=True,
                        hide_index=True
                    )

                else:
                    show_empty(
                        "Aucune activité enregistrée pour cette secrétaire."
                    )

                st.caption(
                    "Les rendez-vous créés par une secrétaire ne peuvent "
                    "pas être attribués individuellement avec le modèle "
                    "actuel : la table rendez_vous ne contient pas "
                    "d'identifiant du créateur."
                )

            # =================================================
            # PROFIL ADMINISTRATEUR
            # =================================================

            elif user_role in ["admin", "administrateur"]:

                activites_user = [
                    a for a in activites_list
                    if str(a.get("id_utilisateur")) == str(user_id)
                ]

                reussites = sum(
                    1 for a in activites_user
                    if normaliser_role(a.get("statut")) in [
                        "succes", "success"
                    ]
                )

                echecs = sum(
                    1 for a in activites_user
                    if normaliser_role(a.get("statut")) in [
                        "echec", "erreur", "failure"
                    ]
                )

                x1, x2, x3 = st.columns(3)

                x1.metric("Actions", len(activites_user))
                x2.metric("Réussites", reussites)
                x3.metric("Échecs", echecs)

                if activites_user:

                    df_admin = pd.DataFrame(activites_user)

                    st.markdown("##### Actions par module")

                    modules_admin = (
                        df_admin["module"]
                        .fillna("Non renseigné")
                        .value_counts()
                        .reset_index()
                    )

                    modules_admin.columns = ["Module", "Nombre"]

                    fig = px.bar(
                        modules_admin,
                        x="Module",
                        y="Nombre",
                        color="Module",
                        text="Nombre"
                    )

                    afficher_graphique_users(fig)

                    st.markdown("##### Historique des actions")

                    colonnes = [
                        c for c in [
                            "action",
                            "module",
                            "description",
                            "date_action",
                            "statut"
                        ]
                        if c in df_admin.columns
                    ]

                    st.dataframe(
                        df_admin[colonnes],
                        use_container_width=True,
                        hide_index=True
                    )

                else:
                    show_empty(
                        "Aucune activité enregistrée pour cet administrateur."
                    )

            # =================================================
            # PROFIL PATIENT
            # =================================================

            elif user_role == "patient":

                st.info(
                    "Ce compte correspond à un patient. "
                    "Les statistiques de son dossier médical sont "
                    "consultables dans les modules médicaux."
                )

            else:

                show_empty(
                    "Aucune analyse individuelle disponible pour ce rôle."
                )

        st.divider()

    # --------------------------------------------------------
    # 8. CREATION D'UN UTILISATEUR
    # --------------------------------------------------------

    st.markdown("### ➕ Créer un nouvel utilisateur")

    with st.expander("Ouvrir le formulaire de création"):

        with st.form("form_admin_create_user_v2"):

            col1, col2 = st.columns(2)

            with col1:

                nom = st.text_input("Nom complet *")
                email = st.text_input("Email *")

                mdp = st.text_input(
                    "Mot de passe *",
                    type="password"
                )

            with col2:

                role = st.selectbox(
                    "Rôle",
                    ["medecin", "secretaire"]
                )

                specialite = st.text_input(
                    "Spécialité",
                    placeholder="Ex : Cardiologue"
                )

                bureau = st.text_input(
                    "Bureau",
                    placeholder="Ex : Salle 102"
                )

                telephone = st.text_input("Téléphone")

            submit = st.form_submit_button(
                "➕ Créer l'utilisateur",
                use_container_width=True
            )

            if submit:

                if not nom.strip() or not email.strip() or not mdp:

                    st.warning(
                        "Veuillez remplir les champs obligatoires."
                    )

                elif "@" not in email:

                    st.warning(
                        "Veuillez saisir une adresse email valide."
                    )

                else:

                    payload = {
                        "nom_complet": nom.strip(),
                        "email": email.strip(),
                        "mot_de_passe": mdp,
                        "role": role,
                        "specialite": specialite.strip() or None,
                        "bureau": bureau.strip() or None,
                        "telephone": telephone.strip() or None
                    }

                    try:

                        response = requests.post(
                            f"{API_URL}/utilisateurs/",
                            json=payload,
                            timeout=15
                        )

                        if response.status_code in (200, 201):

                            st.success(
                                f"Utilisateur {nom} créé avec succès."
                            )

                            charger_consultations_api.clear()
                            charger_journal_api.clear()

                            st.rerun()

                        else:

                            st.error(
                                f"Erreur de création : {response.text}"
                            )

                    except requests.RequestException as e:

                        st.error(
                            f"Impossible de contacter l'API : {e}"
                        )

    st.divider()

    st.info(
        "La présence réelle (arrivée, départ et absences) nécessite "
        "un système de pointage dédié. Elle ne peut pas être déduite "
        "des rendez-vous ou du journal d'activité."
    )


# ============================================================
# 11. PIED DE PAGE
# ============================================================

st.divider()

st.caption(
    "Clinique Santé+ | Tableau de bord administratif et analytique"
)
