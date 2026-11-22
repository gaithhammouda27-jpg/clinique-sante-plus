
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

from style import apply_custom_style

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Administration | Clinique Santé+",
    page_icon="🏥",
    layout="wide"
)

# ============================================================
# 2. SECURITE
# ============================================================

if (
    not st.session_state.get("logged_in")
    or st.session_state.get("role") != "admin"
):
    st.error("⛔ Accès refusé. Veuillez vous connecter en tant qu'administrateur.")
    st.stop()

apply_custom_style()

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


# ============================================================
# 4. EN-TETE
# ============================================================

col_title, col_refresh = st.columns([5, 1])

with col_title:
    st.title("🏥 Clinique Santé+")
    st.subheader("Espace Administration")
    st.caption(
        f"Bienvenue, {st.session_state.get('name', 'Administrateur')}"
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

k1.metric(
    "👥 Utilisateurs",
    len(users)
)

k2.metric(
    "🩺 Médecins",
    nb_medecins
)

k3.metric(
    "🧑‍🤝‍🧑 Patients",
    ind.get("total_patients", len(patients))
)

k4.metric(
    "📅 Rendez-vous",
    ind.get("total_rendez_vous", len(rdvs))
)

st.divider()

# ============================================================
# 7. INDICATEURS FINANCIERS ET OPERATIONNELS
# ============================================================

st.markdown("## 💼 Performance opérationnelle")

f1, f2, f3, f4 = st.columns(4)

f1.metric(
    "💰 Factures émises",
    format_money(ind.get("montant_factures", 0))
)

f2.metric(
    "💳 Encaissements validés",
    format_money(ind.get("montant_encaisse", 0))
)

f3.metric(
    "📉 Dépenses",
    format_money(ind.get("total_depenses", 0))
)

f4.metric(
    "📈 Solde net",
    format_money(ind.get("solde_net", 0))
)

if ind.get("total_factures", 0) > 0 and ind.get("montant_encaisse", 0) == 0:
    st.info(
        "Aucun paiement validé n'est enregistré. "
        "Le montant des factures n'est pas considéré comme de l'argent encaissé."
    )

st.divider()

# ============================================================
# 8. ONGLETS ANALYTIQUES
# ============================================================

tab_overview, tab_rdv, tab_finance, tab_pharma, tab_hospital, tab_activity = st.tabs([
    "📊 Vue globale",
    "📅 Rendez-vous",
    "💰 Finance",
    "💊 Pharmacie",
    "🏥 Infrastructure",
    "⭐ Satisfaction & Activité"
])

# ============================================================
# ONGLET 1 : VUE GLOBALE
# ============================================================

with tab_overview:

    st.subheader("📈 Indicateurs de la clinique")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Consultations",
            ind.get("total_consultations", 0)
        )

    with c2:
        st.metric(
            "Hospitalisations en cours",
            ind.get("hospitalisations_en_cours", 0)
        )

    with c3:
        st.metric(
            "Note moyenne",
            f"{ind.get('note_satisfaction_moyenne', 0)}/5"
        )

    st.divider()

    st.markdown("### 📅 Évolution mensuelle des rendez-vous")

    monthly_rdv = dataframe_or_empty(
        rdv_data.get("par_mois", [])
    )

    if not monthly_rdv.empty:
        fig = px.bar(
            monthly_rdv,
            x="mois",
            y="total",
            text="total",
            title="Nombre de rendez-vous par mois",
            labels={
                "mois": "Mois",
                "total": "Nombre de rendez-vous"
            },
            template="plotly_white"
        )

        fig.update_traces(
            textposition="outside",
            marker_color="#2563EB"
        )

        fig.update_layout(
            height=380,
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucun rendez-vous daté disponible.")

    st.divider()

    st.markdown("### 🩺 Répartition des consultations par médecin")

    medecins_df = dataframe_or_empty(
        consult_data.get("par_medecin", [])
    )

    if not medecins_df.empty:
        fig = px.bar(
            medecins_df,
            x="medecin",
            y="total",
            color="specialite",
            text="total",
            title="Activité médicale par médecin",
            labels={
                "medecin": "Médecin",
                "total": "Consultations",
                "specialite": "Spécialité"
            },
            template="plotly_white"
        )

        fig.update_layout(height=400)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucune consultation enregistrée.")

# ============================================================
# ONGLET 2 : RENDEZ-VOUS
# ============================================================

with tab_rdv:

    st.subheader("📅 Analyse des rendez-vous")

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Total",
        ind.get("total_rendez_vous", 0)
    )

    r2.metric(
        "Confirmés",
        sum(
            x.get("total", 0)
            for x in rdv_data.get("par_statut", [])
            if str(x.get("statut", "")).lower() in ("confirmé", "confirme")
        )
    )

    r3.metric(
        "En attente",
        sum(
            x.get("total", 0)
            for x in rdv_data.get("par_statut", [])
            if x.get("statut") == "en_attente"
        )
    )

    st.divider()

    status_df = dataframe_or_empty(
        rdv_data.get("par_statut", [])
    )

    if not status_df.empty:
        fig = px.pie(
            status_df,
            names="statut",
            values="total",
            hole=0.55,
            title="Répartition des rendez-vous par statut",
            template="plotly_white"
        )

        fig.update_traces(
            textinfo="percent+label"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucun statut de rendez-vous disponible.")

    st.markdown("### Évolution mensuelle")

    monthly_df = dataframe_or_empty(
        rdv_data.get("par_mois", [])
    )

    if not monthly_df.empty:
        fig = px.line(
            monthly_df,
            x="mois",
            y="total",
            markers=True,
            title="Tendance mensuelle des rendez-vous",
            labels={
                "mois": "Mois",
                "total": "Rendez-vous"
            },
            template="plotly_white"
        )

        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=9)
        )

        fig.update_layout(height=380)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty()

# ============================================================
# ONGLET 3 : FINANCE
# ============================================================

with tab_finance:

    st.subheader("💰 Analyse financière")

    a, b, c = st.columns(3)

    a.metric(
        "Factures émises",
        format_money(ind.get("montant_factures", 0))
    )

    b.metric(
        "Paiements reçus",
        format_money(ind.get("montant_encaisse", 0))
    )

    c.metric(
        "Dépenses",
        format_money(ind.get("total_depenses", 0))
    )

    st.divider()

    st.markdown("### 📊 Comparaison financière")

    finance_compare = pd.DataFrame({
        "Catégorie": [
            "Factures émises",
            "Encaissements",
            "Dépenses",
            "Solde net"
        ],
        "Montant": [
            ind.get("montant_factures", 0),
            ind.get("montant_encaisse", 0),
            ind.get("total_depenses", 0),
            ind.get("solde_net", 0)
        ]
    })

    fig = px.bar(
        finance_compare,
        x="Catégorie",
        y="Montant",
        text="Montant",
        title="Situation financière globale",
        template="plotly_white"
    )

    fig.update_traces(
        texttemplate="%{text:.2f} TND",
        textposition="outside"
    )

    fig.update_layout(height=400)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    st.markdown("### 📈 Encaissements et dépenses par mois")

    paiements_df = dataframe_or_empty(
        finance.get("paiements_par_mois", [])
    )

    depenses_df = dataframe_or_empty(
        finance.get("depenses_par_mois", [])
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

        paiements_df = paiements_df.rename(
            columns={"montant": "Encaissements"}
        )

        depenses_df = depenses_df.rename(
            columns={"montant": "Dépenses"}
        )

        evolution = pd.merge(
            paiements_df,
            depenses_df,
            on="mois",
            how="outer"
        ).fillna(0)

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
            title="Évolution financière mensuelle",
            template="plotly_white"
        )

        fig.update_layout(height=400)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty(
            "Aucun paiement ou aucune dépense enregistrée."
        )

    st.divider()

    st.markdown("### 🧾 Dépenses par catégorie")

    categories_df = dataframe_or_empty(
        finance.get("depenses_par_categorie", [])
    )

    if not categories_df.empty:
        fig = px.pie(
            categories_df,
            names="categorie",
            values="montant",
            hole=0.45,
            title="Répartition des dépenses",
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucune dépense catégorisée.")

# ============================================================
# ONGLET 4 : PHARMACIE
# ============================================================

with tab_pharma:

    st.subheader("💊 Gestion analytique de la pharmacie")

    p1, p2, p3 = st.columns(3)

    p1.metric(
        "Médicaments",
        ind.get("total_medicaments", 0)
    )

    p2.metric(
        "Stock total",
        ind.get("stock_total", 0)
    )

    p3.metric(
        "Alertes de stock",
        ind.get("medicaments_en_alerte", 0)
    )

    st.divider()

    st.markdown("### ⚠️ Médicaments nécessitant une attention")

    alertes_df = dataframe_or_empty(
        pharmacie.get("medicaments_en_alerte", [])
    )

    if not alertes_df.empty:

        st.warning(
            f"{len(alertes_df)} médicament(s) au niveau ou sous le seuil d'alerte."
        )

        st.dataframe(
            alertes_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        show_empty(
            "Aucun médicament en alerte ou aucune donnée de pharmacie."
        )

    st.divider()

    st.markdown("### 📦 Mouvements de stock")

    mouvements_df = dataframe_or_empty(
        pharmacie.get("mouvements_par_type", [])
    )

    if not mouvements_df.empty:

        fig = px.bar(
            mouvements_df,
            x="type",
            y="total",
            color="type",
            text="total",
            title="Répartition des mouvements",
            template="plotly_white"
        )

        fig.update_layout(height=350)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucun mouvement de stock enregistré.")

# ============================================================
# ONGLET 5 : INFRASTRUCTURE
# ============================================================

with tab_hospital:

    st.subheader("🏥 Analyse de l'infrastructure")

    h1, h2, h3 = st.columns(3)

    h1.metric(
        "Hospitalisations en cours",
        ind.get("hospitalisations_en_cours", 0)
    )

    h2.metric(
        "Lits occupés",
        ind.get("lits_occupes", 0)
    )

    h3.metric(
        "Lits disponibles",
        ind.get("lits_disponibles", 0)
    )

    st.divider()

    total_lits = ind.get("total_lits", 0)
    taux = ind.get("taux_occupation", 0)

    st.markdown("### 🛏️ Taux d'occupation des lits")

    if total_lits > 0:

        st.metric(
            "Taux d'occupation",
            f"{taux}%"
        )

        st.progress(
            min(max(float(taux) / 100, 0), 1)
        )

        lits_df = dataframe_or_empty(
            hospitalisation.get("lits_par_statut", [])
        )

        if not lits_df.empty:

            fig = px.pie(
                lits_df,
                names="statut",
                values="total",
                hole=0.5,
                title="Répartition des lits",
                template="plotly_white"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:
        show_empty(
            "Aucun lit enregistré. Le taux d'occupation sera calculé "
            "lorsque les lits seront ajoutés."
        )

# ============================================================
# ONGLET 6 : SATISFACTION ET ACTIVITE
# ============================================================

with tab_activity:

    st.subheader("⭐ Satisfaction des patients")

    s1, s2 = st.columns(2)

    with s1:
        st.metric(
            "Note moyenne",
            f"{ind.get('note_satisfaction_moyenne', 0)}/5"
        )

    with s2:
        st.metric(
            "Nombre d'évaluations",
            ind.get("total_evaluations", 0)
        )

    satisfaction_df = dataframe_or_empty(
        satisfaction.get("distribution", [])
    )

    if (
        not satisfaction_df.empty
        and ind.get("total_evaluations", 0) > 0
    ):

        fig = px.bar(
            satisfaction_df,
            x="note",
            y="total",
            text="total",
            title="Distribution des notes de satisfaction",
            labels={
                "note": "Note sur 5",
                "total": "Nombre d'évaluations"
            },
            template="plotly_white"
        )

        fig.update_layout(
            xaxis=dict(
                tickmode="linear",
                tick0=1,
                dtick=1
            ),
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucune évaluation de satisfaction enregistrée.")

    st.divider()

    st.subheader("📋 Activité de la clinique")

    st.metric(
        "Total des actions enregistrées",
        ind.get("total_activites", 0)
    )

    modules_df = dataframe_or_empty(
        activite.get("par_module", [])
    )

    if not modules_df.empty:

        fig = px.bar(
            modules_df,
            x="module",
            y="total",
            color="module",
            text="total",
            title="Activité par module",
            template="plotly_white"
        )

        fig.update_layout(height=350)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        show_empty("Aucune activité enregistrée dans le journal.")

    actions_df = dataframe_or_empty(
        activite.get("par_action", [])
    )

    if not actions_df.empty:

        fig = px.pie(
            actions_df,
            names="action",
            values="total",
            hole=0.45,
            title="Répartition des actions",
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ============================================================
# 9. GESTION DES UTILISATEURS
# ============================================================

st.divider()

st.markdown("## 👥 Gestion des utilisateurs")

st.caption(
    "Consulter les comptes de la clinique et gérer les nouveaux utilisateurs."
)

if not users:

    st.info("Aucun utilisateur dans la base.")

else:

    # Ne jamais afficher le mot de passe ou son empreinte.
    safe_users = [
        {
            "ID": u.get("id"),
            "Nom complet": u.get("nom_complet"),
            "Email": u.get("email"),
            "Rôle": u.get("role"),
            "Spécialité": u.get("specialite"),
            "Bureau": u.get("bureau"),
            "Téléphone": u.get("telephone")
        }
        for u in users
    ]

    users_df = pd.DataFrame(safe_users)

    search_user = st.text_input(
        "🔎 Rechercher un utilisateur",
        placeholder="Nom, email ou rôle..."
    )

    if search_user:
        mask = users_df.astype(str).apply(
            lambda column: column.str.contains(
                search_user,
                case=False,
                na=False
            )
        ).any(axis=1)

        users_df = users_df[mask]

    st.dataframe(
        users_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# 10. CREATION D'UN UTILISATEUR
# ============================================================

st.divider()

st.markdown("## ➕ Créer un nouvel utilisateur")

with st.form("form_admin_create_user"):

    col_form1, col_form2 = st.columns(2)

    with col_form1:

        nom = st.text_input("Nom complet *")

        email = st.text_input("Email *")

        mdp = st.text_input(
            "Mot de passe *",
            type="password"
        )

    with col_form2:

        role = st.selectbox(
            "Rôle",
            ["medecin", "secretaire"]
        )

        specialite = st.text_input(
            "Spécialité",
            placeholder="Ex: Cardiologue"
        )

        bureau = st.text_input(
            "Bureau",
            placeholder="Ex: Salle 102"
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

            st.warning("Veuillez saisir une adresse email valide.")

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
                        f"✅ Utilisateur {nom} créé avec succès !"
                    )

                    st.rerun()

                else:

                    st.error(
                        f"Erreur lors de la création : {response.text}"
                    )

            except requests.RequestException as e:

                st.error(
                    f"Impossible de contacter l'API : {e}"
                )

# ============================================================
# 11. PIED DE PAGE
# ============================================================

st.divider()

st.caption(
    "Clinique Santé+ | Tableau de bord administratif et analytique"
)
