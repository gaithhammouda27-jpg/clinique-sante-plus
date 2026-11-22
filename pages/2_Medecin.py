import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from style import apply_custom_style, render_clean_html
from components.sidebar import render_sidebar
from components.header import render_header
from components.charts import create_ai_risk_gauge, create_biometric_radar, apply_cinematic_theme
from components.cards import render_metric_card

if not st.session_state.get("logged_in") or st.session_state.get("role") != "medecin":
    st.error("⛔ Accès refusé.")
    st.stop()

apply_custom_style()

nom_medecin = st.session_state.get("name", "Médecin")
render_sidebar(nom_medecin, "medecin")
render_header(
    f"Cabinet Médical — Dr. {nom_medecin}",
    "Planning des consultations, dossier patient informatisé & assistance diagnostique IA",
    badge="ESPACE MÉDECIN CLINICIEN"
)

API_URL = "http://127.0.0.1:8000"
ID_MEDECIN_CONNECTE = st.session_state.get("user_id")

# --- SÉLECTION DU PATIENT ---
try:
    res_patients = requests.get(f"{API_URL}/patients/")
    liste_patients = res_patients.json() if res_patients.status_code == 200 else []
except:
    liste_patients = []
    st.error("Impossible de récupérer la liste des patients.")

if not liste_patients:
    st.warning("Aucun patient dans la base.")
    st.stop()

patient_options = {p["id"]: f"{p.get('nom_complet', 'Patient')} (Tél: {p['telephone']})" for p in liste_patients}

st.markdown("### 👤 Espace patient")
st.caption("Sélectionnez un patient pour consulter son dossier et ses informations.")

col_select, col_info = st.columns([2, 1])

with col_select:
    patient_selectionne_id = st.selectbox(
        "Patient",
        options=list(patient_options.keys()),
        format_func=lambda x: patient_options[x],
        key="patient_global_select"
    )

with col_info:
    render_clean_html("""
<div style="background:rgba(15,23,42,0.8);border:1px solid rgba(0,242,254,0.3);border-radius:12px;padding:13px;margin-top:8px;color:#E2E8F0;">
<b style="color:#00F2FE;">📁 Dossier sélectionné</b><br>
<span style="font-size:0.8rem;color:#94A3B8;">Les informations affichées correspondent au patient choisi.</span>
</div>
""")
    st.divider()

tab1, tab2, tab3 = st.tabs(["📅 Mon Planning", "🧠 Diagnostic IA", "📁 Dossier Médical"])

# --- ONGLET 1 : PLANNING ---

# --- ONGLET 1 : PLANNING ---
with tab1:
    st.markdown("### 📅 Mon planning")
    st.caption(
        "Consultez vos rendez-vous et suivez leur état d'avancement."
    )

    try:
        res_rdvs = requests.get(
            f"{API_URL}/medecins/{ID_MEDECIN_CONNECTE}/rendezvous"
        )

        if res_rdvs.status_code == 200:
            rdvs = res_rdvs.json()

            # Indicateurs du planning
            total_rdvs = len(rdvs)
            rdvs_confirmes = len([
                r for r in rdvs
                if r.get("statut") == "confirmé"
            ])
            rdvs_attente = len([
                r for r in rdvs
                if r.get("statut") == "en_attente"
            ])

            col_stat1, col_stat2, col_stat3 = st.columns(3)

            with col_stat1:
                render_metric_card("Total Rendez-vous", total_rdvs, icon="📅", color="cyan")

            with col_stat2:
                render_metric_card("Confirmés", rdvs_confirmes, icon="✅", color="teal")

            with col_stat3:
                render_metric_card("En Attente", rdvs_attente, icon="⏳", color="amber")

            st.divider()

            # Liste des rendez-vous
            st.markdown("#### 📋 Liste des rendez-vous")

            if rdvs:
                df_rdvs = pd.DataFrame(rdvs)

                st.dataframe(
                    df_rdvs,
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                # Clôturer un rendez-vous
                st.markdown("#### ✅ Gestion des rendez-vous")

                st.caption(
                    "Saisissez l'identifiant du rendez-vous à marquer "
                    "comme terminé."
                )

                col_action, col_button = st.columns([2, 1])

                with col_action:
                    rdv_id = st.number_input(
                        "ID du rendez-vous",
                        min_value=1,
                        step=1
                    )

                with col_button:
                    st.write("")
                    st.write("")

                    if st.button(
                        "✅ Marquer comme terminé",
                        use_container_width=True
                    ):
                        requests.put(
                            f"{API_URL}/rendezvous/{rdv_id}/statut",
                            json={"statut": "terminé"}
                        )
                        st.rerun()

            else:
                st.info(
                    "📭 Aucun rendez-vous n'est enregistré pour le moment."
                )

        else:
            st.error(
                f"Impossible de récupérer les rendez-vous : "
                f"{res_rdvs.status_code}"
            )

    except Exception as e:
        st.error(f"Erreur API : {e}")

# --- ONGLET 2 : DIAGNOSTIC IA DYNAMIQUE ---

# --- ONGLET 2 : DIAGNOSTIC IA DYNAMIQUE ---
with tab2:
    st.markdown("### 🧠 Analyse assistée par intelligence artificielle")
    st.caption(
        "Renseignez les paramètres du patient pour obtenir une estimation "
        "expérimentale produite par le modèle IA."
    )

    # Choix de la maladie
    st.markdown("#### 1. Sélection de l'analyse")

    col_maladie, col_patient = st.columns([1, 1])

    with col_maladie:
        maladie_choisie = st.selectbox(
            "Maladie à analyser",
            ["Hypertension", "Diabete"],
            key="maladie_ia_medecin"
        )

    with col_patient:
        st.text_input(
            "Patient sélectionné",
            value=patient_options[patient_selectionne_id],
            disabled=True
        )

    st.divider()

    # Formulaire des paramètres
    st.markdown("#### 2. Paramètres du patient")

    with st.form("form_ia_dynamique"):

        age = st.number_input(
            "Âge",
            min_value=18,
            max_value=100,
            value=50
        )

        col1, col2 = st.columns(2)

        # Paramètres hypertension
        if maladie_choisie == "Hypertension":

            st.info("🩺 Paramètres utilisés pour l'analyse de l'hypertension.")

            with col1:
                gender = st.selectbox("Sexe", ["M", "F"])

                systolic_bp = st.number_input(
                    "Tension systolique (mmHg)",
                    min_value=80,
                    max_value=220,
                    value=130
                )

            with col2:
                glucose = st.number_input(
                    "Glycémie (mmol/L)",
                    min_value=3.0,
                    max_value=20.0,
                    value=5.5,
                    step=0.1
                )

                heart_rate = st.number_input(
                    "Fréquence cardiaque (bpm)",
                    min_value=40,
                    max_value=180,
                    value=75
                )

        # Paramètres diabète
        elif maladie_choisie == "Diabete":

            st.info("🧪 Paramètres utilisés pour l'analyse du diabète.")

            with col1:
                glucose = st.number_input(
                    "Glycémie (mmol/L)",
                    min_value=3.0,
                    max_value=20.0,
                    value=5.5,
                    step=0.1
                )

                bmi = st.number_input(
                    "IMC",
                    min_value=10.0,
                    max_value=50.0,
                    value=25.0,
                    step=0.1
                )

            with col2:
                blood_pressure = st.number_input(
                    "Tension diastolique (mmHg)",
                    min_value=40,
                    max_value=120,
                    value=80
                )

        st.divider()

        submit = st.form_submit_button(
            "🧠 Lancer l'analyse IA",
            use_container_width=True
        )

    # Traitement du résultat
    if submit:

        payload = {
            "maladie": maladie_choisie.lower(),
            "age": age,
            "id_patient": patient_selectionne_id,
            "id_medecin": ID_MEDECIN_CONNECTE
        }

        if maladie_choisie == "Hypertension":
            payload.update({
                "gender": gender,
                "systolic_bp": systolic_bp,
                "glucose": glucose,
                "heart_rate": heart_rate
            })

        elif maladie_choisie == "Diabete":
            payload.update({
                "glucose": glucose,
                "bmi": bmi,
                "blood_pressure": blood_pressure
            })

        with st.spinner("🧠 Analyse en cours..."):

            try:
                res = requests.post(
                    f"{API_URL}/ia/predire",
                    json=payload,
                    timeout=60
                )

                if res.status_code == 200:

                    data = res.json()

                    prob = data.get("probabilite", 0)
                    risque = data.get("risque_eleve", False)

                    st.divider()
                    st.markdown("#### 3. Évaluation Visuelle & Diagnostic IA")

                    col_gauge, col_radar = st.columns([1.2, 1.3])

                    with col_gauge:
                        st.plotly_chart(
                            create_ai_risk_gauge(
                                prob,
                                title=f"Risque Prédit : {maladie_choisie}",
                                disease=maladie_choisie
                            ),
                            use_container_width=True
                        )

                    with col_radar:
                        # Préparation des métriques radar selon la pathologie
                        radar_data = {}
                        if maladie_choisie == "Hypertension":
                            radar_data = {
                                "Tension Sys": systolic_bp,
                                "Glycémie": glucose,
                                "Fréq. Cardiaque": heart_rate,
                                "Âge": age,
                                "Saturation O2": 98
                            }
                        else:
                            radar_data = {
                                "Glycémie": glucose,
                                "IMC": bmi,
                                "Tension": blood_pressure,
                                "Âge": age,
                                "Fréquence": 75
                            }
                            
                        st.plotly_chart(
                            create_biometric_radar(
                                radar_data,
                                title=f"Profil Biométrique Comparatif ({maladie_choisie})"
                            ),
                            use_container_width=True
                        )

                    # Diagnostic interprété
                    if risque:
                        render_clean_html(f"""
<div style="background:rgba(244,63,94,0.12);border:1px solid rgba(244,63,94,0.35);border-radius:12px;padding:16px;margin-top:10px;">
<div style="color:#FB7185;font-weight:700;font-size:1rem;margin-bottom:4px;">⚠️ Alerte Clinique : Risque Élevé Détecté ({prob:.1%})</div>
<div style="color:#E2E8F0;font-size:0.88rem;">Le modèle Spark MLlib estime une probabilité anormale pour <b>{maladie_choisie}</b>. Il est recommandé d'approfondir les explorations (MAPA, ECG, bilan métabolique complet) et de programmer une consultation de suivi rapprochée.</div>
</div>
""")
                    else:
                        render_clean_html(f"""
<div style="background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.35);border-radius:12px;padding:16px;margin-top:10px;">
<div style="color:#34D399;font-weight:700;font-size:1rem;margin-bottom:4px;">✅ Risque Modéré / Contrôlé ({prob:.1%})</div>
<div style="color:#E2E8F0;font-size:0.88rem;">Les indicateurs biométriques se situent dans un intervalle de vigilance standard. Poursuivre le protocole de suivi préventif habituel.</div>
</div>
""")

                    st.caption(
                        "ℹ️ Analyse fournie à titre d'aide à la décision clinique. "
                        "Ne remplace pas le jugement clinique souverain du praticien."
                    )

                else:
                    st.error(
                        f"Erreur API ({res.status_code}) : {res.text}"
                    )

            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de connexion à l'API : {e}")

with tab3:
    st.subheader(f"📁 Dossier Médical de {patient_options[patient_selectionne_id]}")
    
    try:
        res_dossier = requests.get(f"{API_URL}/patients/{patient_selectionne_id}/dossier-complet")
        if res_dossier.status_code == 200:
            dossier = res_dossier.json()
            patient_info = dossier["patient"]
            
            st.markdown(f"### 👤 {patient_info['nom_complet']}")
            col1, col2, col3 = st.columns(3)
            with col1: st.write(f"📞 **Tél :** {patient_info['telephone']}")
            with col2: st.write(f"🎂 **Naissance :** {patient_info['date_naissance']}")
            with col3: st.write(f"📧 **Email :** {patient_info['email']}")
            st.info(f"🩺 **Antécédents :** {patient_info['antecedents'] or 'Aucun'}")
            st.divider()
            
            sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["📎 Documents", "💊 Ordonnances", "📋 Notes", "📊 Évolution"])
            

            with sub_tab1:
                st.markdown("### 📎 Gestion des documents médicaux")

                # Formulaire d'ajout
                with st.expander("➕ Ajouter un nouveau document", expanded=False):
                    with st.form("form_ajout_document"):
                        fichier = st.file_uploader(
                            "Choisir un document",
                            type=["pdf", "jpg", "jpeg", "png"]
                        )

                        description = st.text_area("Description du document")

                        ajouter_doc = st.form_submit_button("📤 Ajouter le document")

                        if ajouter_doc:
                            if fichier is None:
                                st.warning("Veuillez sélectionner un fichier.")
                            else:
                                try:
                                    res = requests.post(
                                        f"{API_URL}/patients/{patient_selectionne_id}/documents",
                                        params={
                                            "id_medecin": ID_MEDECIN_CONNECTE,
                                            "description": description
                                        },
                                        files={
                                            "fichier": (
                                                fichier.name,
                                                fichier.getvalue(),
                                                fichier.type
                                            )
                                        },
                                        timeout=60
                                    )

                                    if res.status_code == 200:
                                        st.success("Document ajouté avec succès.")
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur : {res.text}")

                                except requests.exceptions.RequestException as e:
                                    st.error(f"Erreur de connexion : {e}")

                st.divider()

                documents = dossier.get("documents", [])

                if documents:
                    for doc in documents:
                        with st.expander(
                            f"📄 {doc['nom_fichier']} — {doc['date_ajout']}"
                        ):
                            st.write("**Description :**", doc.get("description") or "Aucune")
                            st.write("**Médecin :**", doc.get("medecin", "Inconnu"))

                            # Modifier la description
                            with st.form(f"modifier_doc_{doc['id']}"):
                                nouvelle_description = st.text_area(
                                    "Modifier la description",
                                    value=doc.get("description") or "",
                                    key=f"description_{doc['id']}"
                                )

                                modifier = st.form_submit_button("💾 Enregistrer")

                                if modifier:
                                    try:
                                        res = requests.put(
                                            f"{API_URL}/documents/{doc['id']}",
                                            params={"description": nouvelle_description},
                                            timeout=30
                                        )

                                        if res.status_code == 200:
                                            st.success("Description modifiée.")
                                            st.rerun()
                                        else:
                                            st.error(res.text)

                                    except requests.exceptions.RequestException as e:
                                        st.error(f"Erreur : {e}")

                            # Télécharger le document
                            try:
                                res_download = requests.get(
                                    f"{API_URL}/documents/{doc['id']}/telecharger",
                                    timeout=30
                                )

                                if res_download.status_code == 200:
                                    st.download_button(
                                        "⬇️ Télécharger",
                                        data=res_download.content,
                                        file_name=doc["nom_fichier"],
                                        key=f"download_{doc['id']}"
                                    )
                                else:
                                    st.warning("Téléchargement indisponible.")

                            except requests.exceptions.RequestException:
                                st.warning("Impossible de contacter le serveur.")

                            # Supprimer le document
                            if st.button(
                                "🗑️ Supprimer ce document",
                                key=f"supprimer_doc_{doc['id']}"
                            ):
                                st.session_state[f"confirmer_doc_{doc['id']}"] = True

                            if st.session_state.get(f"confirmer_doc_{doc['id']}", False):
                                st.warning("Confirmer la suppression de ce document ?")

                                col_a, col_b = st.columns(2)

                                with col_a:
                                    if st.button("Oui, supprimer", key=f"oui_doc_{doc['id']}"):
                                        res = requests.delete(
                                            f"{API_URL}/documents/{doc['id']}",
                                            timeout=30
                                        )

                                        if res.status_code == 200:
                                            st.session_state.pop(
                                                f"confirmer_doc_{doc['id']}", None
                                            )
                                            st.success("Document supprimé.")
                                            st.rerun()
                                        else:
                                            st.error(res.text)

                                with col_b:
                                    if st.button("Annuler", key=f"non_doc_{doc['id']}"):
                                        st.session_state.pop(
                                            f"confirmer_doc_{doc['id']}", None
                                        )
                                        st.rerun()

                else:
                    st.info("📭 Aucun document enregistré pour ce patient.")

                                


            with sub_tab2:
                st.markdown("### 💊 Gestion des ordonnances")

                # ==========================
                # CRÉATION D'UNE ORDONNANCE
                # ==========================
                with st.expander("➕ Créer une ordonnance", expanded=False):
                    with st.form("form_nouvelle_ordonnance"):

                        medicaments = st.text_area(
                            "💊 Médicaments",
                            placeholder="Exemple : Médicament A, Médicament B..."
                        )

                        posologie = st.text_area(
                            "📋 Posologie",
                            placeholder="Préciser les instructions de prise..."
                        )

                        instructions = st.text_area(
                            "📝 Instructions complémentaires"
                        )

                        creer = st.form_submit_button("💾 Enregistrer l'ordonnance")

                        if creer:
                            if not medicaments.strip() or not posologie.strip():
                                st.warning("Les médicaments et la posologie sont obligatoires.")
                            else:
                                payload_ordonnance = {
                                    "id_patient": patient_selectionne_id,
                                    "id_medecin": ID_MEDECIN_CONNECTE,
                                    "medicaments": medicaments.strip(),
                                    "posologie": posologie.strip(),
                                    "instructions": instructions.strip()
                                }

                                try:
                                    res = requests.post(
                                        f"{API_URL}/ordonnances/",
                                        json=payload_ordonnance,
                                        timeout=30
                                    )

                                    if res.status_code in (200, 201):
                                        st.success("Ordonnance créée avec succès.")
                                        st.rerun()
                                    else:
                                        st.error(
                                            f"Erreur création ({res.status_code}) : {res.text}"
                                        )

                                except requests.exceptions.RequestException as e:
                                    st.error(f"Erreur API : {e}")

                st.divider()

                # ==========================
                # LISTE DES ORDONNANCES
                # ==========================
                ordonnances = dossier.get("ordonnances", [])

                if ordonnances:

                    for o in ordonnances:

                        with st.expander(
                            f"💊 Ordonnance du {o['date']} — Dr. {o['medecin']}"
                        ):

                            st.markdown("**Médicaments :**")
                            st.write(o["medicaments"])

                            st.markdown("**Posologie :**")
                            st.write(o["posologie"])

                            st.markdown("**Instructions complémentaires :**")
                            st.write(o.get("instructions") or "Aucune")

                            st.caption(f"Identifiant de l'ordonnance : {o['id']}")

                            st.divider()

                            # ==========================
                            # MODIFICATION
                            # ==========================
                            st.markdown("#### ✏️ Modifier cette ordonnance")

                            with st.form(f"modifier_ordonnance_{o['id']}"):

                                nouveaux_medicaments = st.text_area(
                                    "💊 Médicaments",
                                    value=o.get("medicaments") or "",
                                    key=f"med_{o['id']}"
                                )

                                nouvelle_posologie = st.text_area(
                                    "📋 Posologie",
                                    value=o.get("posologie") or "",
                                    key=f"pos_{o['id']}"
                                )

                                nouvelles_instructions = st.text_area(
                                    "📝 Instructions complémentaires",
                                    value=o.get("instructions") or "",
                                    key=f"inst_{o['id']}"
                                )

                                modifier = st.form_submit_button("💾 Enregistrer les modifications")

                                if modifier:

                                    if not nouveaux_medicaments.strip() or not nouvelle_posologie.strip():
                                        st.warning("Les médicaments et la posologie sont obligatoires.")

                                    else:
                                        try:
                                            res = requests.put(
                                                f"{API_URL}/ordonnances/{o['id']}",
                                                params={
                                                    "medicaments": nouveaux_medicaments.strip(),
                                                    "posologie": nouvelle_posologie.strip(),
                                                    "instructions": nouvelles_instructions.strip()
                                                },
                                                timeout=30
                                            )

                                            if res.status_code == 200:
                                                st.success("Ordonnance modifiée avec succès.")
                                                st.rerun()
                                            else:
                                                st.error(
                                                    f"Erreur modification ({res.status_code}) : {res.text}"
                                                )

                                        except requests.exceptions.RequestException as e:
                                            st.error(f"Erreur API : {e}")

                            st.divider()

                            # ==========================
                            # SUPPRESSION
                            # ==========================
                            st.markdown("#### 🗑️ Supprimer cette ordonnance")

                            cle_confirmation = f"confirmer_ord_{o['id']}"

                            if st.button(
                                "🗑️ Supprimer l'ordonnance",
                                key=f"supprimer_ord_{o['id']}"
                            ):
                                st.session_state[cle_confirmation] = True

                            if st.session_state.get(cle_confirmation, False):

                                st.warning(
                                    "Voulez-vous vraiment supprimer cette ordonnance ? "
                                    "Cette action est définitive."
                                )

                                col_a, col_b = st.columns(2)

                                with col_a:
                                    if st.button(
                                        "Oui, confirmer",
                                        key=f"oui_ord_{o['id']}"
                                    ):
                                        try:
                                            res = requests.delete(
                                                f"{API_URL}/ordonnances/{o['id']}",
                                                timeout=30
                                            )

                                            if res.status_code == 200:
                                                st.session_state.pop(cle_confirmation, None)
                                                st.success("Ordonnance supprimée avec succès.")
                                                st.rerun()
                                            else:
                                                st.error(
                                                    f"Erreur suppression ({res.status_code}) : {res.text}"
                                                )

                                        except requests.exceptions.RequestException as e:
                                            st.error(f"Erreur API : {e}")

                                with col_b:
                                    if st.button(
                                        "Annuler",
                                        key=f"non_ord_{o['id']}"
                                    ):
                                        st.session_state.pop(cle_confirmation, None)
                                        st.rerun()

                else:
                    st.info("📭 Aucune ordonnance enregistrée.")
            with sub_tab3:
                st.markdown("### 📋 Gestion des consultations")

                # Ajouter une consultation
                with st.expander("➕ Ajouter une consultation", expanded=False):
                    with st.form("form_nouvelle_consultation"):

                        diagnostic = st.text_area(
                            "🩺 Diagnostic",
                            placeholder="Saisir le diagnostic..."
                        )

                        traitement = st.text_area(
                            "💊 Traitement",
                            placeholder="Saisir le traitement proposé..."
                        )

                        ajouter = st.form_submit_button("💾 Enregistrer la consultation")

                        if ajouter:
                            if not diagnostic.strip() or not traitement.strip():
                                st.warning("Le diagnostic et le traitement sont obligatoires.")
                            else:
                                payload_consultation = {
                                    "id_patient": patient_selectionne_id,
                                    "id_medecin": ID_MEDECIN_CONNECTE,
                                    "diagnostic": diagnostic,
                                    "traitement": traitement
                                }

                                try:
                                    res = requests.post(
                                        f"{API_URL}/consultations/",
                                        json=payload_consultation,
                                        timeout=30
                                    )

                                    if res.status_code == 200:
                                        st.success("Consultation enregistrée.")
                                        st.rerun()
                                    else:
                                        st.error(res.text)

                                except requests.exceptions.RequestException as e:
                                    st.error(f"Erreur API : {e}")

                st.divider()

                consultations = dossier.get("consultations", [])

                if consultations:
                    for c in consultations:
                        with st.expander(
                            f"📋 Consultation du {c['date']} — Dr. {c['medecin']}"
                        ):
                            st.write("**Diagnostic :**", c["diagnostic"])
                            st.write("**Traitement :**", c.get("traitement") or "Aucun")

                            # Modification
                            with st.form(f"modifier_consultation_{c['id']}"):

                                nouveau_diagnostic = st.text_area(
                                    "Diagnostic",
                                    value=c["diagnostic"],
                                    key=f"diag_{c['id']}"
                                )

                                nouveau_traitement = st.text_area(
                                    "Traitement",
                                    value=c.get("traitement") or "",
                                    key=f"trait_{c['id']}"
                                )

                                modifier = st.form_submit_button("💾 Modifier")

                                if modifier:
                                    try:
                                        res = requests.put(
                                            f"{API_URL}/consultations/{c['id']}",
                                            params={
                                                "diagnostic": nouveau_diagnostic,
                                                "traitement": nouveau_traitement
                                            },
                                            timeout=30
                                        )

                                        if res.status_code == 200:
                                            st.success("Consultation modifiée.")
                                            st.rerun()
                                        else:
                                            st.error(res.text)

                                    except requests.exceptions.RequestException as e:
                                        st.error(f"Erreur : {e}")

                            # Suppression
                            if st.button(
                                "🗑️ Supprimer la consultation",
                                key=f"supprimer_cons_{c['id']}"
                            ):
                                st.session_state[f"confirmer_cons_{c['id']}"] = True

                            if st.session_state.get(f"confirmer_cons_{c['id']}", False):
                                st.warning("Confirmer la suppression ?")

                                col_a, col_b = st.columns(2)

                                with col_a:
                                    if st.button("Oui, supprimer", key=f"oui_cons_{c['id']}"):
                                        res = requests.delete(
                                            f"{API_URL}/consultations/{c['id']}",
                                            timeout=30
                                        )

                                        if res.status_code == 200:
                                            st.session_state.pop(
                                                f"confirmer_cons_{c['id']}", None
                                            )
                                            st.success("Consultation supprimée.")
                                            st.rerun()
                                        else:
                                            st.error(res.text)

                                with col_b:
                                    if st.button("Annuler", key=f"non_cons_{c['id']}"):
                                        st.session_state.pop(
                                            f"confirmer_cons_{c['id']}", None
                                        )
                                        st.rerun()

                else:
                    st.info("📭 Aucune consultation enregistrée.")
                            
           
            with sub_tab4:
                st.markdown("## 📊 Tableau de bord – Évolution des analyses IA")
                st.caption("Suivi chronologique des estimations produites par les modèles d'intelligence artificielle.")

                predictions = dossier.get("predictions", [])

                if predictions:

                    # Préparation des données
                    df = pd.DataFrame(predictions)

                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df["probabilite"] = pd.to_numeric(df["probabilite"], errors="coerce")

                    df = df.dropna(subset=["date", "probabilite"])
                    df["probabilite_pct"] = df["probabilite"] * 100

                    if not df.empty:

                        df = df.sort_values("date")

                        # -----------------------------
                        # 1. FILTRE PAR MALADIE
                        # -----------------------------
                        maladies = ["Toutes"] + sorted(
                            df["maladie"].dropna().unique().tolist()
                        )

                        choix = st.selectbox(
                            "🔎 Filtrer les analyses par maladie",
                            maladies,
                            key="filtre_evolution"
                        )

                        if choix == "Toutes":
                            df_filtre = df.copy()
                        else:
                            df_filtre = df[df["maladie"] == choix].copy()

                        # -----------------------------
                        # 2. INDICATEURS
                        # -----------------------------
                        derniere = df_filtre.iloc[-1]

                        total = len(df_filtre)
                        derniere_prob = derniere["probabilite_pct"]
                        derniere_date = derniere["date"].strftime("%d/%m/%Y %H:%M")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "🧠 Nombre d'analyses",
                                total
                            )

                        with col2:
                            st.metric(
                                "📈 Dernière probabilité estimée",
                                f"{derniere_prob:.1f}%"
                            )

                        with col3:
                            st.metric(
                                "📅 Dernière analyse",
                                derniere["date"].strftime("%d/%m/%Y")
                            )

                        st.divider()

                        # -----------------------------
                        # 3. DERNIÈRE ANALYSE
                        # -----------------------------
                        st.markdown("### 🎯 Dernière analyse")

                        nom_maladie = str(derniere["maladie"]).capitalize()

                        st.markdown(f"**Maladie analysée :** {nom_maladie}")
                        st.markdown(f"**Date :** {derniere_date}")

                        if derniere_prob >= 50:
                            st.warning(
                                f"Probabilité estimée par le modèle : {derniere_prob:.1f}%"
                            )
                        else:
                            st.info(
                                f"Probabilité estimée par le modèle : {derniere_prob:.1f}%"
                            )

                        st.caption(
                            "Attention : cette probabilité est une sortie expérimentale "
                            "du modèle IA. Elle ne constitue pas un diagnostic médical. "
                            "Le seuil de 50 % est uniquement un seuil technique."
                        )

                        st.divider()

                        # -----------------------------
                        # 4. GRAPHIQUE INTERACTIF
                        # -----------------------------
                        st.markdown("### 📈 Évolution des probabilités")

                        import plotly.express as px

                        fig = px.line(
                            df_filtre,
                            x="date",
                            y="probabilite_pct",
                            color="maladie",
                            markers=True,
                            hover_data={
                                "id": True,
                                "date": "|%d/%m/%Y %H:%M",
                                "probabilite_pct": ":.2f",
                                "maladie": True
                            },
                            labels={
                                "date": "Date de l'analyse",
                                "probabilite_pct": "Probabilité estimée (%)",
                                "maladie": "Maladie"
                            },
                            template="plotly_dark"
                        )

                        fig.update_traces(
                            line=dict(width=3),
                            marker=dict(size=10)
                        )

                        fig.update_layout(
                            height=450,
                            hovermode="x unified",
                            legend_title="Maladie",
                            xaxis_title="Date",
                            yaxis_title="Probabilité estimée (%)",
                            margin=dict(l=20, r=20, t=30, b=20)
                        )

                        fig.update_yaxes(
                            range=[0, 100],
                            ticksuffix="%"
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                        st.divider()

                        # -----------------------------
                        # 5. HISTORIQUE DES ANALYSES
                        # -----------------------------
                        st.markdown("### 📋 Historique des analyses")

                        historique = df_filtre[
                            ["id", "maladie", "date", "probabilite_pct"]
                        ].copy()

                        historique["date"] = historique["date"].dt.strftime(
                            "%d/%m/%Y %H:%M"
                        )

                        historique = historique.rename(columns={
                            "id": "ID",
                            "maladie": "Maladie",
                            "date": "Date",
                            "probabilite_pct": "Probabilité (%)"
                        })

                        historique["Probabilité (%)"] = historique[
                            "Probabilité (%)"
                        ].round(2)

                        st.dataframe(
                            historique.sort_values(
                                "Date",
                                ascending=False
                            ),
                            use_container_width=True,
                            hide_index=True
                        )

                        st.divider()

                        # -----------------------------
                        # 6. DÉTAILS DES ANALYSES
                        # -----------------------------
                        st.markdown("### 🔍 Détails des analyses")

                        for _, prediction in df_filtre.sort_values(
                            "date",
                            ascending=False
                        ).iterrows():

                            date_affichee = prediction["date"].strftime(
                                "%d/%m/%Y %H:%M"
                            )

                            titre = (
                                f"Analyse #{prediction['id']} — "
                                f"{str(prediction['maladie']).capitalize()} "
                                f"— {date_affichee}"
                            )

                            with st.expander(titre):

                                col_a, col_b = st.columns(2)

                                with col_a:
                                    st.metric(
                                        "Probabilité estimée",
                                        f"{prediction['probabilite_pct']:.2f}%"
                                    )

                                with col_b:
                                    st.write(
                                        "**Maladie :**",
                                        str(prediction["maladie"]).capitalize()
                                    )

                                constantes = prediction.get("constantes")

                                if constantes:
                                    try:
                                        if isinstance(constantes, str):
                                            constantes = json.loads(constantes)

                                        st.markdown("**🩺 Constantes utilisées :**")
                                        st.json(constantes)

                                    except (json.JSONDecodeError, TypeError):
                                        st.text(str(constantes))
                                else:
                                    st.caption("Aucune constante enregistrée.")

                    else:
                        st.info("Aucune donnée de prédiction exploitable.")

                else:
                    st.info(
                        "📭 Aucune analyse IA enregistrée pour ce patient."
                    )

        else:
            st.error(f"Erreur : {res_dossier.text}")
    except Exception as e:
        st.error(f"Erreur : {e}")