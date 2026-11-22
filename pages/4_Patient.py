import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from style import apply_custom_style
from components.sidebar import render_sidebar
from components.header import render_header
from components.charts import create_ai_risk_gauge, create_biometric_radar, apply_cinematic_theme
from components.cards import render_metric_card

# ==========================================
# 1. SÉCURITÉ ET STYLE
# ==========================================
if not st.session_state.get("logged_in") or st.session_state.get("role") != "patient":
    st.error("⛔ Accès refusé.")
    st.stop()

apply_custom_style()

nom_patient = st.session_state.get("name", "Patient")
render_sidebar(nom_patient, "patient")
render_header("Mon Espace Santé", f"Bienvenue, {nom_patient} • Dossier médical & constantes", badge="PORTAIL PATIENT")

API_URL = "http://127.0.0.1:8000"

# Récupération de l'ID patient
email_connecte = st.session_state.get("email")
ID_PATIENT = None

if email_connecte:
    try:
        res = requests.get(f"{API_URL}/patients/par-email/{email_connecte}")
        if res.status_code == 200:
            ID_PATIENT = res.json()["id_patient"]
        else:
            st.error(f"Erreur : Impossible de trouver votre dossier (Email: {email_connecte})")
            st.stop()
    except Exception as e:
        st.error(f"Impossible de contacter l'API : {e}")
        st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📅 Mes Rendez-vous", "📊 Mon Historique", "💊 Mes Ordonnances", "🩺 Mon Bilan"])
with tab1:
    st.subheader("Mes prochains rendez-vous")
    if st.button("🔄 Rafraîchir"):
        try:
            res = requests.get(f"{API_URL}/patients/{ID_PATIENT}/rendezvous")
            if res.status_code == 200:
                rdvs = res.json()
                if len(rdvs) == 0:
                    st.info("Vous n'avez aucun rendez-vous.")
                else:
                    st.dataframe(rdvs, use_container_width=True)
            else:
                st.error(f"Erreur : {res.text}")
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")

with tab2:
    st.subheader("Mon historique de prédictions IA")
    try:
        res = requests.get(f"{API_URL}/patients/{ID_PATIENT}/predictions")
        if res.status_code == 200:
            historique = res.json()
            if len(historique) == 0:
                st.info("Aucune analyse IA pour le moment.")
            else:
                df_hist = pd.DataFrame(historique)
                df_hist = df_hist[["date", "probabilite", "risque_eleve", "constantes"]]
                st.dataframe(df_hist, use_container_width=True)
                
                df_hist["date"] = pd.to_datetime(df_hist["date"])
                df_hist = df_hist.sort_values("date")
                fig = px.line(df_hist, x="date", y="probabilite", markers=True, color_discrete_sequence=["#3b82f6"])
                fig.add_hline(y=0.5, line_dash="dash", line_color="#ef4444")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Erreur : {res.text}")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
with tab3:
    st.subheader("💊 Mes ordonnances")
    try:
        res = requests.get(f"{API_URL}/patients/{ID_PATIENT}/ordonnances")
        if res.status_code == 200:
            ordonnances = res.json()
            if len(ordonnances) == 0:
                st.info("Vous n'avez aucune ordonnance pour le moment.")
            else:
                for o in ordonnances:
                    with st.expander(f"Ordonnance du {o['date']} - Dr. {o['medecin']}"):
                        st.write(f"**Médicaments :** {o['medicaments']}")
                        st.write(f"**Posologie :** {o['posologie']}")
                        if o['instructions']:
                            st.write(f"**Instructions :** {o['instructions']}")
        else:
            st.error(f"Erreur : {res.text}")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")

# --- ONGLET : MON BILAN DE SANTÉ ---
# --- ONGLET : MON BILAN DE SANTÉ (DASHBOARD AVANCÉ) ---
with tab4:
    st.subheader("🩺 Mon Tableau de Bord Santé")
    st.markdown("Suivez l'évolution de vos constantes et de votre état de santé général.")
    
    try:
        res_dossier = requests.get(f"{API_URL}/patients/{ID_PATIENT}/dossier-complet")
        if res_dossier.status_code == 200:
            dossier = res_dossier.json()
            patient_info = dossier["patient"]
            predictions = dossier["predictions"]
            
            # 1. Bandeau d'information générale
            st.info(f"🩸 **Groupe / Antécédents :** {patient_info['antecedents'] or 'Aucun antécédent signalé'}")
            st.divider()

            if len(predictions) == 0:
                st.warning("Aucune analyse IA n'a encore été réalisée. Consultez un médecin pour commencer le suivi.")
            else:
                # 2. Extraction des données depuis la chaîne "constantes"
                # Format de la chaîne : "Age:50, Tension:130, Glycémie:5.5"
                data_extraite = []
                for p in predictions:
                    try:
                        # On utilise une expression régulière pour extraire les chiffres
                        match_age = re.search(r"Age:(\d+)", p["constantes"])
                        match_tension = re.search(r"Tension:(\d+)", p["constantes"])
                        match_glycemie = re.search(r"Glycémie:([\d\.]+)", p["constantes"])
                        
                        data_extraite.append({
                            "Date": p["date"],
                            "Probabilité": p["probabilite"],
                            "Âge": int(match_age.group(1)) if match_age else None,
                            "Tension": int(match_tension.group(1)) if match_tension else None,
                            "Glycémie": float(match_glycemie.group(1)) if match_glycemie else None
                        })
                    except:
                        pass # Si le format est incorrect, on ignore

                if len(data_extraite) == 0:
                    st.error("Les données historiques sont illisibles.")
                else:
                    df = pd.DataFrame(data_extraite)
                    df["Date"] = pd.to_datetime(df["Date"])
                    df = df.sort_values("Date")
                    
                    # 3. KPI (Indicateurs clés) - Dernières mesures
                    derniere_mesure = df.iloc[-1]
                    
                    st.markdown("### 📌 Mes dernières constantes biométriques")
                    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                    
                    with col_kpi1:
                        render_metric_card(
                            "Tension Systolique",
                            derniere_mesure['Tension'] or '--',
                            unit="mmHg",
                            icon="🩸",
                            color="cyan" if (derniere_mesure['Tension'] or 0) < 135 else "rose"
                        )
                    with col_kpi2:
                        render_metric_card(
                            "Glycémie à jeun",
                            derniere_mesure['Glycémie'] or '--',
                            unit="mmol/L",
                            icon="🍬",
                            color="emerald" if (derniere_mesure['Glycémie'] or 0) < 6.0 else "amber"
                        )
                    with col_kpi3:
                        render_metric_card(
                            "Âge Patient",
                            derniere_mesure['Âge'] or '--',
                            unit="ans",
                            icon="👤",
                            color="teal"
                        )
                    with col_kpi4:
                        est_eleve = derniere_mesure['Probabilité'] > 0.5
                        render_metric_card(
                            "Statut Prédictif",
                            "Élevé" if est_eleve else "Normal",
                            unit=f"({derniere_mesure['Probabilité']:.0%})",
                            icon="🧠",
                            color="rose" if est_eleve else "emerald",
                            delta="Alerte active" if est_eleve else "Paramètres stables",
                            delta_positive=not est_eleve
                        )

                    st.divider()

                    # 4. Graphique Géant : Évolution de toutes les constantes
                    st.markdown("### 📈 Évolution temporelle des constantes")
                    
                    # Onglets internes pour les graphiques
                    g1, g2, g3 = st.tabs(["📉 Risque Prédictif", "🩸 Tension Artérielle", "🍬 Glycémie"])
                    
                    with g1:
                        fig_risk = px.area(
                            df, x="Date", y="Probabilité",
                            title="Historique de la Probabilité d'Hypertension",
                            color_discrete_sequence=["#00F2FE"]
                        )
                        fig_risk.add_hline(y=0.5, line_dash="dash", line_color="#F43F5E", annotation_text="Seuil de vigilance (50%)")
                        fig_risk.update_layout(yaxis_range=[0, 1])
                        apply_cinematic_theme(fig_risk, height=300)
                        st.plotly_chart(fig_risk, use_container_width=True)
                        
                    with g2:
                        fig_tension = px.line(
                            df, x="Date", y="Tension", markers=True,
                            title="Tension Artérielle Systolique (mmHg)",
                            color_discrete_sequence=["#38BDF8"]
                        )
                        fig_tension.add_hrect(y0=0, y1=120, fillcolor="#10B981", opacity=0.1, annotation_text="Zone Normale")
                        fig_tension.add_hrect(y0=120, y1=140, fillcolor="#F59E0B", opacity=0.1, annotation_text="Pré-hypertension")
                        fig_tension.add_hrect(y0=140, y1=220, fillcolor="#F43F5E", opacity=0.1, annotation_text="Hypertension")
                        apply_cinematic_theme(fig_tension, height=300)
                        st.plotly_chart(fig_tension, use_container_width=True)
                        
                    with g3:
                        fig_glycemie = px.line(
                            df, x="Date", y="Glycémie", markers=True,
                            title="Glycémie (mmol/L)",
                            color_discrete_sequence=["#F59E0B"]
                        )
                        fig_glycemie.add_hline(y=7.0, line_dash="dash", line_color="#F43F5E", annotation_text="Seuil Diabète (7.0)")
                        apply_cinematic_theme(fig_glycemie, height=300)
                        st.plotly_chart(fig_glycemie, use_container_width=True)

                    # 5. Jauges et radar interactifs
                    st.divider()
                    st.markdown("### 🎯 Synthèse Biomédicale & Jauge de Risque")
                    
                    col_gauge_p, col_radar_p = st.columns([1.2, 1.3])
                    
                    with col_gauge_p:
                        st.plotly_chart(
                            create_ai_risk_gauge(
                                derniere_mesure['Probabilité'],
                                title="Indice de Risque IA Patient",
                                disease="Hypertension"
                            ),
                            use_container_width=True
                        )
                        
                    with col_radar_p:
                        st.plotly_chart(
                            create_biometric_radar({
                                "Tension Sys": derniere_mesure['Tension'] or 120,
                                "Glycémie": derniere_mesure['Glycémie'] or 5.5,
                                "Âge": derniere_mesure['Âge'] or 50,
                                "Fréquence": 75,
                                "Saturation O2": 98
                            }, title="Radar Biométrique Actuel"),
                            use_container_width=True
                        )

                    # 6. Conseils personnalisés
                    if derniere_mesure['Probabilité'] > 0.5:
                        st.error("⚠️ **Alerte :** Votre tension ou votre glycémie indique un risque élevé. Veuillez consulter un médecin rapidement.")
                    else:
                        st.success("✅ **Bonne santé :** Vos derniers résultats sont dans les normes. Continuez à maintenir un mode de vie sain.")

        else:
            st.error("Impossible de charger votre bilan.")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")