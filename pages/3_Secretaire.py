import streamlit as st
import requests
from datetime import datetime, date, time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from style import apply_custom_style
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import render_metric_card

# ==========================================
# 1. SÉCURITÉ ET STYLE
# ==========================================
if not st.session_state.get("logged_in") or st.session_state.get("role") != "secretaire":
    st.error("⛔ Accès refusé.")
    st.stop()

apply_custom_style()

nom_secretaire = st.session_state.get("name", "Secrétaire")
render_sidebar(nom_secretaire, "secretaire")
render_header("Secrétariat & Accueil Médical", f"Bienvenue, {nom_secretaire} • Prise de rendez-vous et admissions", badge="ESPACE SECRÉTARIAT")

API_URL = "http://127.0.0.1:8000"

tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Prendre un RDV", "📋 Gérer les RDV", "👥 Patients", "🩺 Annuaire", "💰 Facturation"])
# --- ONGLET 1 : PRENDRE UN RDV ---
with tab1:
    st.subheader("Créer un nouveau rendez-vous")
    try:
        res_med = requests.get(f"{API_URL}/medecins/")
        liste_medecins = res_med.json() if res_med.status_code == 200 else []
        res_pat = requests.get(f"{API_URL}/patients/")
        liste_patients = res_pat.json() if res_pat.status_code == 200 else []
    except:
        liste_medecins, liste_patients = [], []
        st.error("Impossible de contacter l'API.")

    if not liste_medecins or not liste_patients:
        st.warning("⚠️ Il manque des médecins ou des patients.")
    else:
        with st.form("form_rdv"):
            col1, col2 = st.columns(2)
            with col1:
                patient_options = {p["id"]: f"Patient ID: {p['id']} (Tel: {p['telephone']})" for p in liste_patients}
                id_patient = st.selectbox("Patient", options=list(patient_options.keys()), format_func=lambda x: patient_options[x])
                medecin_options = {m["id"]: f"{m['nom_complet']} (ID: {m['id']})" for m in liste_medecins}
                id_medecin = st.selectbox("Médecin", options=list(medecin_options.keys()), format_func=lambda x: medecin_options[x])
            with col2:
                date_rdv = st.date_input("Date", min_value=date.today())
                heure_rdv = st.time_input("Heure", time(9, 0))
                motif = st.text_input("Motif", placeholder="Ex: Douleurs")
                salle = st.text_input("Salle", placeholder="Ex: Salle 101")
                type_consultation = st.selectbox("Type", ["Première visite", "Suivi"])

            submit = st.form_submit_button("✅ Enregistrer le rendez-vous")

            if submit:
                if not motif:
                    st.warning("Veuillez saisir un motif.")
                else:
                    date_heure_str = datetime.combine(date_rdv, heure_rdv).isoformat()
                    payload = {
                        "id_patient": id_patient, "id_medecin": id_medecin,
                        "date_heure": date_heure_str, "motif": motif,
                        "salle": salle, "type_consultation": type_consultation
                    }
                    res = requests.post(f"{API_URL}/rendezvous/", json=payload)
                    if res.status_code == 200:
                        st.success(f"✅ Rendez-vous créé ! (ID: {res.json()['id']})")
                    else:
                        st.error(f"Erreur : {res.text}")

# --- ONGLET 2 : GÉRER LES RDV ---
with tab2:
    st.subheader("Tous les rendez-vous")
    try:
        res = requests.get(f"{API_URL}/rendezvous/")
        if res.status_code == 200:
            rdvs = res.json()
            if len(rdvs) == 0:
                st.info("Aucun rendez-vous.")
            else:
                total_rdv = len(rdvs)
                conf = len([r for r in rdvs if r.get("statut") in ["confirmé", "confirme"]])
                att = len([r for r in rdvs if r.get("statut") in ["en_attente", "en attente"]])
                ann = len([r for r in rdvs if r.get("statut") in ["annulé", "annule"]])

                c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                with c_m1:
                    render_metric_card("Total Planning", total_rdv, icon="📅", color="cyan")
                with c_m2:
                    render_metric_card("Confirmés", conf, icon="✅", color="teal")
                with c_m3:
                    render_metric_card("En Attente", att, icon="⏳", color="amber")
                with c_m4:
                    render_metric_card("Annulés", ann, icon="🚫", color="rose")

                st.dataframe(rdvs, use_container_width=True)
                st.divider()
                st.subheader("✏️ Modifier un rendez-vous")
                
                rdv_options = {r["id"]: f"RDV n°{r['id']} (Patient {r['id_patient']})" for r in rdvs}
                rdv_id_selectionne = st.selectbox("Sélectionnez le RDV", options=list(rdv_options.keys()), format_func=lambda x: rdv_options[x])
                rdv_actuel = next((r for r in rdvs if r["id"] == rdv_id_selectionne), None)
                
                if rdv_actuel:
                    res_med = requests.get(f"{API_URL}/medecins/")
                    medecins = res_med.json() if res_med.status_code == 200 else []
                    medecin_options = {m["id"]: m["nom_complet"] for m in medecins}

                    with st.form("form_modif_rdv"):
                        col_mod1, col_mod2 = st.columns(2)
                        with col_mod1:
                            new_medecin = st.selectbox("Médecin", options=list(medecin_options.keys()), format_func=lambda x: medecin_options[x], index=list(medecin_options.keys()).index(rdv_actuel["id_medecin"]) if rdv_actuel["id_medecin"] in medecin_options else 0)
                            new_salle = st.text_input("Salle", value=rdv_actuel["salle"] or "")
                            new_motif = st.text_input("Motif", value=rdv_actuel["motif"] or "")
                        with col_mod2:
                            try:
                                dt_actuel = datetime.strptime(rdv_actuel["date_heure"], "%Y-%m-%d %H:%M:%S")
                                date_defaut = dt_actuel.date()
                                heure_defaut = dt_actuel.time()
                            except:
                                date_defaut = date.today()
                                heure_defaut = time(9, 0)

                            new_date = st.date_input("Date", value=date_defaut)
                            new_heure = st.time_input("Heure", value=heure_defaut)
                            new_statut = st.selectbox("Statut", ["en_attente", "confirmé", "annulé"], index=["en_attente", "confirmé", "annulé"].index(rdv_actuel["statut"]))

                        submit_modif = st.form_submit_button("💾 Enregistrer les modifications")
                        if submit_modif:
                            new_date_heure_str = datetime.combine(new_date, new_heure).isoformat()
                            payload = {"id_medecin": new_medecin, "date_heure": new_date_heure_str, "salle": new_salle, "motif": new_motif, "statut": new_statut}
                            res_modif = requests.put(f"{API_URL}/rendezvous/{rdv_id_selectionne}/modifier", json=payload)
                            if res_modif.status_code == 200:
                                st.success("✅ Modifié avec succès !")
                                st.rerun()
                            else:
                                st.error(f"Erreur : {res_modif.text}")
    except Exception as e:
        st.error(f"Erreur : {e}")

# --- ONGLET 3 : PATIENTS ---
with tab3:
    st.subheader("Dossiers des Patients")
    with st.expander("➕ Ajouter un nouveau patient"):
        with st.form("form_nouveau_patient"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                nom = st.text_input("Nom complet")
                email = st.text_input("Email")
                mdp = st.text_input("Mot de passe", type="password")
            with col_p2:
                tel = st.text_input("Téléphone")
                date_naiss = st.date_input("Date de naissance")
                antecedents = st.text_area("Antécédents")
            
            if st.form_submit_button("Créer le dossier patient"):
                if not nom or not email or not mdp:
                    st.warning("Champs obligatoires manquants.")
                else:
                    payload = {"nom_complet": nom, "email": email, "mot_de_passe": mdp, "date_naissance": str(date_naiss), "telephone": tel}
                    res = requests.post(f"{API_URL}/secretaire/creer-patient", json=payload)
                    if res.status_code == 200:
                        st.success("✅ Patient créé !")
                        st.rerun()
                    else:
                        st.error(f"Erreur : {res.text}")

    try:
        res_patients = requests.get(f"{API_URL}/patients/")
        if res_patients.status_code == 200:
            patients = res_patients.json()
            if len(patients) > 0:
                patient_options = {p["id"]: f"ID {p['id']} - Tel: {p['telephone']}" for p in patients}
                patient_selectionne_id = st.selectbox("Sélectionnez un patient", options=list(patient_options.keys()), format_func=lambda x: patient_options[x])
                
                if patient_selectionne_id:
                    res_details = requests.get(f"{API_URL}/patients/details/{patient_selectionne_id}")
                    if res_details.status_code == 200:
                        patient_data = res_details.json()
                        st.markdown(f"### 📁 Dossier de : **{patient_data['nom_complet']}**")
                        with st.form("form_modif_patient"):
                            col_d1, col_d2 = st.columns(2)
                            with col_d1:
                                new_nom = st.text_input("Nom", value=patient_data['nom_complet'])
                                new_email = st.text_input("Email", value=patient_data['email'])
                                new_tel = st.text_input("Téléphone", value=patient_data['telephone'])
                            with col_d2:
                                st.text_input("Date de naissance", value=patient_data['date_naissance'], disabled=True)
                                new_antecedents = st.text_area("Antécédents", value=patient_data['antecedents'] or "")
                            
                            if st.form_submit_button("💾 Mettre à jour"):
                                payload = {"nom_complet": new_nom, "email": new_email, "telephone": new_tel, "antecedents": new_antecedents}
                                res_modif = requests.put(f"{API_URL}/patients/{patient_selectionne_id}/modifier", json=payload)
                                if res_modif.status_code == 200:
                                    st.success("✅ Dossier mis à jour !")
                                    st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# --- ONGLET 4 : ANNUAIRE ---
with tab4:
    st.subheader("🩺 Annuaire du personnel médical")
    try:
        res_annuaire = requests.get(f"{API_URL}/medecins/annuaire")
        if res_annuaire.status_code == 200:
            annuaire = res_annuaire.json()
            if len(annuaire) > 0:
                for med in annuaire:
                    titre_medecin = f"👨‍⚕️ {med['nom_complet']} - {med['specialite']} (Bureau: {med['bureau']})"
                    with st.expander(titre_medecin):
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.write(f"📧 **Email :** {med['email']}")
                            st.write(f"📞 **Téléphone :** {med['telephone']}")
                        with col_info2:
                            st.write(f"🏢 **Bureau :** {med['bureau']}")
                            st.write(f"👥 **Patients suivis :** {med['nombre_patients']}")
    except Exception as e:
        st.error(f"Erreur : {e}")
# --- ONGLET 5 : FACTURATION ---
with tab5:
    st.subheader("💰 Gestion de la Facturation")
    
    try:
        factures = requests.get(f"{API_URL}/factures/").json()
        rdvs = requests.get(f"{API_URL}/rendezvous/").json()
    except:
        factures, rdvs = [], []
        st.error("Impossible de contacter l'API.")

    # 1. Créer une nouvelle facture
    with st.expander("➕ Créer une facture pour une consultation"):
        with st.form("form_facture"):
            rdv_options = {r["id"]: f"RDV n°{r['id']} (Patient {r['id_patient']} - {r['date_heure']})" for r in rdvs}
            rdv_id = st.selectbox("Sélectionnez le rendez-vous", options=list(rdv_options.keys()), format_func=lambda x: rdv_options[x])
            montant = st.number_input("Montant de la consultation (en €)", min_value=0.0, step=10.0, value=50.0)
            
            if st.form_submit_button("Générer la facture"):
                res = requests.post(f"{API_URL}/factures/", json={"id_rendez_vous": rdv_id, "montant": montant})
                if res.status_code == 200:
                    st.success("Facture générée avec succès !")
                    st.rerun()
                else:
                    st.error(f"Erreur : {res.text}")

    st.divider()
    
    # 2. Afficher et gérer les factures existantes
    st.subheader("Liste des factures")
    if len(factures) == 0:
        st.info("Aucune facture émise pour le moment.")
    else:
        for f in factures:
            with st.expander(f"Facture n°{f['id']} - Montant : {f['montant']}€ - Statut : {f['statut_paiement']}"):
                st.write(f"**Rendez-vous associé :** {f['id_rendez_vous']}")
                st.write(f"**Date d'émission :** {f['date_emission']}")
                
                if f['statut_paiement'] == "en_attente":
                    if st.button(f"✅ Marquer la facture {f['id']} comme PAYÉE", key=f"pay_{f['id']}"):
                        res = requests.put(f"{API_URL}/factures/{f['id']}/statut", json={"statut_paiement": "payé"})
                        if res.status_code == 200:
                            st.success("Paiement enregistré !")
                            st.rerun()
                elif f['statut_paiement'] == "payé":
                    st.success("✅ Cette facture est déjà payée.")