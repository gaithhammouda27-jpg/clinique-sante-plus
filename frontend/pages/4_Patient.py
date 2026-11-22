import json
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_client as api
from auth import require_role
from style import apply_custom_style
from components.sidebar import render_sidebar
from components.header import render_header
from components.charts import create_ai_risk_gauge, create_biometric_radar, apply_cinematic_theme
from components.cards import render_metric_card

# ==========================================
# 1. SÉCURITÉ ET STYLE
# ==========================================
require_role("patient")
apply_custom_style()

nom_patient = st.session_state.get("name", "Patient")
render_sidebar(nom_patient, "patient")
render_header("Mon Espace Santé", f"Bienvenue, {nom_patient} • Dossier médical & constantes", badge="PORTAIL PATIENT")

# ==========================================
# 2. IDENTIFICATION DU DOSSIER PATIENT
# ==========================================
email_connecte = st.session_state.get("email")
if not email_connecte:
    st.error("Session invalide : e-mail introuvable. Veuillez vous reconnecter.")
    st.stop()

try:
    res = api.get(f"/patients/par-email/{email_connecte}")
except api.RequestException as e:
    st.error(f"Impossible de contacter l'API : {e}")
    st.stop()

if res.status_code != 200:
    st.error(f"Impossible de trouver votre dossier ({api.error_detail(res)}).")
    st.stop()

ID_PATIENT = res.json()["id_patient"]

# Une seule requête pour tout le dossier (avant : 4 appels, dont un vers
# /patients/{id}/predictions qui n'existe pas dans l'API → erreur 404).
try:
    res_dossier = api.get(f"/patients/{ID_PATIENT}/dossier-complet")
except api.RequestException as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

if res_dossier.status_code != 200:
    st.error(f"Impossible de charger votre dossier : {api.error_detail(res_dossier)}")
    st.stop()

dossier = res_dossier.json()
patient_info = dossier["patient"]
predictions = dossier.get("predictions", [])


def lire_constantes(valeur) -> dict:
    """Les constantes sont stockées en JSON par /ia/predire.

    L'ancien code cherchait un texte « Age:50, Tension:130 » via regex et ne
    trouvait donc jamais rien : le bilan restait vide.
    """
    if isinstance(valeur, dict):
        return valeur
    try:
        data = json.loads(valeur or "{}")
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError):
        return {}


def construire_historique(preds) -> pd.DataFrame:
    lignes = []
    for p in preds:
        c = lire_constantes(p.get("constantes"))
        lignes.append({
            "Date": p.get("date"),
            "Maladie": str(p.get("maladie") or "").capitalize(),
            "Probabilité": p.get("probabilite"),
            "Âge": c.get("age"),
            "Tension": c.get("systolic_bp") or c.get("blood_pressure"),
            "Glycémie": c.get("glucose"),
            "Fréq. cardiaque": c.get("heart_rate"),
            "IMC": c.get("bmi"),
        })
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Probabilité"] = pd.to_numeric(df["Probabilité"], errors="coerce")
    return df.dropna(subset=["Date", "Probabilité"]).sort_values("Date")


df_hist = construire_historique(predictions)

tab1, tab2, tab3, tab4 = st.tabs(["📅 Mes Rendez-vous", "📊 Mon Historique", "💊 Mes Ordonnances", "🩺 Mon Bilan"])

# --- ONGLET 1 : RENDEZ-VOUS (chargés directement, plus besoin de cliquer) ---
with tab1:
    st.subheader("Mes rendez-vous")
    rdvs = api.get_json(f"/patients/{ID_PATIENT}/rendezvous", default=None)
    if rdvs is None:
        st.error("Impossible de charger vos rendez-vous.")
    elif not rdvs:
        st.info("Vous n'avez aucun rendez-vous.")
    else:
        df_rdv = pd.DataFrame(rdvs)
        df_rdv["date_heure"] = pd.to_datetime(df_rdv["date_heure"], errors="coerce")
        maintenant = pd.Timestamp.now()
        a_venir = df_rdv[(df_rdv["date_heure"] >= maintenant) & (df_rdv["statut"] != "annulé")]

        c1, c2 = st.columns(2)
        with c1:
            render_metric_card("Rendez-vous à venir", len(a_venir), icon="📅", color="cyan")
        with c2:
            render_metric_card("Total", len(df_rdv), icon="🗂️", color="teal")

        colonnes = {
            "date_heure": "Date & heure", "medecin": "Médecin", "motif": "Motif",
            "salle": "Salle", "type_consultation": "Type", "statut": "Statut",
        }
        affichage = df_rdv.sort_values("date_heure", ascending=False)[list(colonnes)].rename(columns=colonnes)
        st.dataframe(
            affichage, width="stretch", hide_index=True,
            column_config={"Date & heure": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")},
        )

# --- ONGLET 2 : HISTORIQUE IA ---
with tab2:
    st.subheader("Mon historique de prédictions IA")
    if df_hist.empty:
        st.info("Aucune analyse IA pour le moment.")
    else:
        df_aff = df_hist.copy()
        df_aff["Risque élevé"] = df_aff["Probabilité"] >= 0.5
        st.dataframe(
            df_aff[["Date", "Maladie", "Probabilité", "Risque élevé", "Tension", "Glycémie"]]
            .sort_values("Date", ascending=False),
            width="stretch", hide_index=True,
            column_config={
                "Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                "Probabilité": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="percent"),
            },
        )
        fig = px.line(df_hist, x="Date", y="Probabilité", color="Maladie", markers=True)
        fig.add_hline(y=0.5, line_dash="dash", line_color="#ef4444")
        fig.update_layout(yaxis_range=[0, 1])
        apply_cinematic_theme(fig, height=320)
        st.plotly_chart(fig, width="stretch")

# --- ONGLET 3 : ORDONNANCES ---
with tab3:
    st.subheader("💊 Mes ordonnances")
    ordonnances = dossier.get("ordonnances", [])
    if not ordonnances:
        st.info("Vous n'avez aucune ordonnance pour le moment.")
    else:
        for o in ordonnances:
            # Le nom du médecin contient déjà « Dr. » : on ne le préfixe plus.
            with st.expander(f"Ordonnance du {o['date']} — {o['medecin']}"):
                st.write(f"**Médicaments :** {o['medicaments']}")
                st.write(f"**Posologie :** {o['posologie']}")
                if o.get('instructions'):
                    st.write(f"**Instructions :** {o['instructions']}")

# --- ONGLET 4 : MON BILAN DE SANTÉ (DASHBOARD AVANCÉ) ---
with tab4:
    st.subheader("🩺 Mon Tableau de Bord Santé")
    st.markdown("Suivez l'évolution de vos constantes et de votre état de santé général.")

    st.info(f"🩸 **Antécédents :** {patient_info.get('antecedents') or 'Aucun antécédent signalé'}")
    st.divider()

    df = df_hist[df_hist["Maladie"] == "Hypertension"] if not df_hist.empty else df_hist
    if df.empty:
        df = df_hist

    if df.empty:
        st.warning("Aucune analyse IA n'a encore été réalisée. Consultez un médecin pour commencer le suivi.")
    else:
        derniere = df.iloc[-1]

        def val(champ, defaut=None):
            v = derniere.get(champ)
            return defaut if v is None or pd.isna(v) else v

        tension, glycemie, age = val("Tension"), val("Glycémie"), val("Âge")
        proba = float(derniere["Probabilité"])
        est_eleve = proba >= 0.5

        st.markdown("### 📌 Mes dernières constantes biométriques")
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            render_metric_card("Tension Systolique", int(tension) if tension is not None else "--", unit="mmHg",
                               icon="🩸", color="cyan" if (tension or 0) < 135 else "rose")
        with col_kpi2:
            render_metric_card("Glycémie à jeun", glycemie if glycemie is not None else "--", unit="mmol/L",
                               icon="🍬", color="emerald" if (glycemie or 0) < 6.0 else "amber")
        with col_kpi3:
            render_metric_card("Âge", int(age) if age is not None else "--", unit="ans", icon="👤", color="teal")
        with col_kpi4:
            render_metric_card(
                "Statut Prédictif", "Élevé" if est_eleve else "Normal", unit=f"({proba:.0%})",
                icon="🧠", color="rose" if est_eleve else "emerald",
                delta="Alerte active" if est_eleve else "Paramètres stables", delta_positive=not est_eleve,
            )

        st.divider()
        st.markdown("### 📈 Évolution temporelle des constantes")
        g1, g2, g3 = st.tabs(["📉 Risque Prédictif", "🩸 Tension Artérielle", "🍬 Glycémie"])

        with g1:
            fig_risk = px.area(df, x="Date", y="Probabilité", title=f"Historique du risque ({derniere['Maladie']})",
                               color_discrete_sequence=["#00F2FE"])
            fig_risk.add_hline(y=0.5, line_dash="dash", line_color="#F43F5E", annotation_text="Seuil de vigilance (50%)")
            fig_risk.update_layout(yaxis_range=[0, 1])
            apply_cinematic_theme(fig_risk, height=300)
            st.plotly_chart(fig_risk, width="stretch")

        with g2:
            if df["Tension"].notna().any():
                fig_tension = px.line(df, x="Date", y="Tension", markers=True, title="Tension Artérielle (mmHg)",
                                      color_discrete_sequence=["#38BDF8"])
                fig_tension.add_hrect(y0=0, y1=120, fillcolor="#10B981", opacity=0.1, annotation_text="Zone Normale")
                fig_tension.add_hrect(y0=120, y1=140, fillcolor="#F59E0B", opacity=0.1, annotation_text="Pré-hypertension")
                fig_tension.add_hrect(y0=140, y1=220, fillcolor="#F43F5E", opacity=0.1, annotation_text="Hypertension")
                apply_cinematic_theme(fig_tension, height=300)
                st.plotly_chart(fig_tension, width="stretch")
            else:
                st.info("Aucune mesure de tension enregistrée.")

        with g3:
            if df["Glycémie"].notna().any():
                fig_glycemie = px.line(df, x="Date", y="Glycémie", markers=True, title="Glycémie (mmol/L)",
                                       color_discrete_sequence=["#F59E0B"])
                fig_glycemie.add_hline(y=7.0, line_dash="dash", line_color="#F43F5E", annotation_text="Seuil Diabète (7.0)")
                apply_cinematic_theme(fig_glycemie, height=300)
                st.plotly_chart(fig_glycemie, width="stretch")
            else:
                st.info("Aucune mesure de glycémie enregistrée.")

        st.divider()
        st.markdown("### 🎯 Synthèse Biomédicale & Jauge de Risque")
        col_gauge_p, col_radar_p = st.columns([1.2, 1.3])
        with col_gauge_p:
            st.plotly_chart(
                create_ai_risk_gauge(proba, title="Indice de Risque IA", disease=str(derniere["Maladie"])),
                width="stretch",
            )
        with col_radar_p:
            st.plotly_chart(
                create_biometric_radar({
                    "Tension Sys": tension or 120,
                    "Glycémie": glycemie or 5.5,
                    "Fréq. Cardiaque": val("Fréq. cardiaque", 75),
                    "IMC": val("IMC", 24),
                    "Saturation O2": 98,
                }, title="Radar Biométrique Actuel"),
                width="stretch",
            )

        if est_eleve:
            st.error("⚠️ **Alerte :** votre dernier bilan indique un risque élevé. Veuillez consulter un médecin rapidement.")
        else:
            st.success("✅ **Bonne santé :** vos derniers résultats sont dans les normes. Continuez à maintenir un mode de vie sain.")
        st.caption("ℹ️ Estimation produite par un modèle IA expérimental : elle ne remplace pas l'avis d'un médecin.")
