import os
import sys
from datetime import datetime, date, time

import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_client as api
from auth import require_role
from style import apply_custom_style
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import render_metric_card

# ==========================================
# 1. SÉCURITÉ ET STYLE
# ==========================================
require_role("secretaire")
apply_custom_style()

nom_secretaire = st.session_state.get("name", "Secrétaire")
render_sidebar(nom_secretaire, "secretaire")
render_header("Secrétariat & Accueil Médical", f"Bienvenue, {nom_secretaire} • Prise de rendez-vous et admissions", badge="ESPACE SECRÉTARIAT")

STATUTS_RDV = ["en_attente", "confirmé", "terminé", "annulé"]
DEVISE = "TND"  # cohérent avec l'espace Admin (avant : « € » ici, « TND » ailleurs)


def flash(message: str):
    """Message affiché APRÈS st.rerun() (sinon il disparaît immédiatement)."""
    st.session_state["_flash_secretaire"] = message


if "_flash_secretaire" in st.session_state:
    st.success(st.session_state.pop("_flash_secretaire"))

# --- Données partagées par les onglets (chargées une seule fois par exécution) ---
liste_medecins = api.get_json("/medecins/", default=None)
liste_patients = api.get_json("/patients/", default=None)
if liste_medecins is None or liste_patients is None:
    st.error("Impossible de contacter l'API. Vérifiez qu'elle est démarrée.")
    st.stop()

noms_patients = {p["id"]: p.get("nom_complet") or f"Patient {p['id']}" for p in liste_patients}
noms_medecins = {m["id"]: m["nom_complet"] for m in liste_medecins}


def libelle_patient(pid):
    p = next((x for x in liste_patients if x["id"] == pid), {})
    return f"{noms_patients.get(pid, pid)} — Tél : {p.get('telephone') or '—'}"


tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Prendre un RDV", "📋 Gérer les RDV", "👥 Patients", "🩺 Annuaire", "💰 Facturation"])

# --- ONGLET 1 : PRENDRE UN RDV ---
with tab1:
    st.subheader("Créer un nouveau rendez-vous")

    if not liste_medecins or not liste_patients:
        st.warning("⚠️ Il manque des médecins ou des patients.")
    else:
        with st.form("form_rdv", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                id_patient = st.selectbox("Patient", options=list(noms_patients), format_func=libelle_patient)
                id_medecin = st.selectbox(
                    "Médecin", options=list(noms_medecins),
                    format_func=lambda x: f"{noms_medecins[x]} — {next((m.get('specialite') or '' for m in liste_medecins if m['id'] == x), '')}",
                )
                type_consultation = st.selectbox("Type", ["Première visite", "Suivi"])
            with col2:
                date_rdv = st.date_input("Date", min_value=date.today(), format="DD/MM/YYYY")
                heure_rdv = st.time_input("Heure", time(9, 0), step=900)
                motif = st.text_input("Motif *", placeholder="Ex : Douleurs thoraciques")
                salle = st.text_input("Salle", placeholder="Ex : Salle 101")

            if st.form_submit_button("✅ Enregistrer le rendez-vous", type="primary"):
                if not motif.strip():
                    st.warning("Veuillez saisir un motif.")
                elif datetime.combine(date_rdv, heure_rdv) < datetime.now():
                    st.warning("Impossible de créer un rendez-vous dans le passé.")
                else:
                    payload = {
                        "id_patient": id_patient, "id_medecin": id_medecin,
                        "date_heure": datetime.combine(date_rdv, heure_rdv).isoformat(),
                        "motif": motif.strip(), "salle": salle.strip(), "type_consultation": type_consultation,
                    }
                    try:
                        res = api.post("/rendezvous/", json=payload)
                        if res.status_code == 200:
                            st.success(f"✅ Rendez-vous créé ! (n°{res.json()['id']})")
                        else:
                            st.error(f"Erreur : {api.error_detail(res)}")
                    except api.RequestException as e:
                        st.error(f"Erreur de connexion : {e}")

# --- ONGLET 2 : GÉRER LES RDV ---
with tab2:
    st.subheader("Tous les rendez-vous")
    rdvs = api.get_json("/rendezvous/", default=None)

    if rdvs is None:
        st.error("Impossible de charger les rendez-vous.")
    elif not rdvs:
        st.info("Aucun rendez-vous.")
    else:
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        compter = lambda *s: len([r for r in rdvs if r.get("statut") in s])  # noqa: E731
        with c_m1:
            render_metric_card("Total Planning", len(rdvs), icon="📅", color="cyan")
        with c_m2:
            render_metric_card("Confirmés", compter("confirmé", "confirme"), icon="✅", color="teal")
        with c_m3:
            render_metric_card("En Attente", compter("en_attente", "en attente"), icon="⏳", color="amber")
        with c_m4:
            render_metric_card("Annulés", compter("annulé", "annule"), icon="🚫", color="rose")

        # Tableau lisible (noms au lieu des ID bruts)
        df_rdv = pd.DataFrame(rdvs)
        df_rdv["Patient"] = df_rdv["id_patient"].map(noms_patients)
        df_rdv["Médecin"] = df_rdv["id_medecin"].map(noms_medecins)
        df_rdv["date_heure"] = pd.to_datetime(df_rdv["date_heure"], errors="coerce")

        f1, f2 = st.columns(2)
        with f1:
            filtre_statut = st.multiselect("Filtrer par statut", STATUTS_RDV, default=[])
        with f2:
            recherche = st.text_input("Rechercher un patient", placeholder="Nom…")
        vue = df_rdv
        if filtre_statut:
            vue = vue[vue["statut"].isin(filtre_statut)]
        if recherche.strip():
            vue = vue[vue["Patient"].fillna("").str.contains(recherche.strip(), case=False)]

        st.dataframe(
            vue.sort_values("date_heure", ascending=False)[
                ["id", "date_heure", "Patient", "Médecin", "motif", "salle", "type_consultation", "statut"]
            ].rename(columns={"id": "N°", "date_heure": "Date & heure", "motif": "Motif", "salle": "Salle",
                              "type_consultation": "Type", "statut": "Statut"}),
            width="stretch", hide_index=True,
            column_config={"Date & heure": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")},
        )

        st.divider()
        st.subheader("✏️ Modifier un rendez-vous")

        rdv_options = {
            r["id"]: f"RDV n°{r['id']} — {noms_patients.get(r['id_patient'], r['id_patient'])} — {r['date_heure']}"
            for r in sorted(rdvs, key=lambda r: r["id"], reverse=True)
        }
        rdv_id_selectionne = st.selectbox("Sélectionnez le RDV", options=list(rdv_options), format_func=rdv_options.get)
        rdv_actuel = next((r for r in rdvs if r["id"] == rdv_id_selectionne), None)

        if rdv_actuel and noms_medecins:
            ids_medecins = list(noms_medecins)
            try:
                dt_actuel = datetime.fromisoformat(rdv_actuel["date_heure"])
                date_defaut, heure_defaut = dt_actuel.date(), dt_actuel.time()
            except (TypeError, ValueError):
                date_defaut, heure_defaut = date.today(), time(9, 0)

            # Avant : .index(statut) levait ValueError pour « terminé » et
            # faisait planter tout l'onglet.
            statut_actuel = rdv_actuel.get("statut") or "en_attente"
            statuts = STATUTS_RDV if statut_actuel in STATUTS_RDV else STATUTS_RDV + [statut_actuel]

            with st.form(f"form_modif_rdv_{rdv_id_selectionne}"):
                col_mod1, col_mod2 = st.columns(2)
                with col_mod1:
                    new_medecin = st.selectbox(
                        "Médecin", options=ids_medecins, format_func=noms_medecins.get,
                        index=ids_medecins.index(rdv_actuel["id_medecin"]) if rdv_actuel["id_medecin"] in ids_medecins else 0,
                    )
                    new_salle = st.text_input("Salle", value=rdv_actuel.get("salle") or "")
                    new_motif = st.text_input("Motif", value=rdv_actuel.get("motif") or "")
                with col_mod2:
                    new_date = st.date_input("Date", value=date_defaut, format="DD/MM/YYYY")
                    new_heure = st.time_input("Heure", value=heure_defaut, step=900)
                    new_statut = st.selectbox("Statut", statuts, index=statuts.index(statut_actuel))

                if st.form_submit_button("💾 Enregistrer les modifications", type="primary"):
                    payload = {
                        "id_medecin": new_medecin,
                        "date_heure": datetime.combine(new_date, new_heure).isoformat(),
                        "salle": new_salle, "motif": new_motif, "statut": new_statut,
                    }
                    try:
                        res_modif = api.put(f"/rendezvous/{rdv_id_selectionne}/modifier", json=payload)
                        if res_modif.status_code == 200:
                            flash(f"✅ Rendez-vous n°{rdv_id_selectionne} modifié avec succès !")
                            st.rerun()
                        else:
                            st.error(f"Erreur : {api.error_detail(res_modif)}")
                    except api.RequestException as e:
                        st.error(f"Erreur de connexion : {e}")

# --- ONGLET 3 : PATIENTS ---
with tab3:
    st.subheader("Dossiers des Patients")
    with st.expander("➕ Ajouter un nouveau patient"):
        with st.form("form_nouveau_patient", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                nom = st.text_input("Nom complet *")
                email = st.text_input("Email *")
                mdp = st.text_input("Mot de passe *", type="password")
            with col_p2:
                tel = st.text_input("Téléphone")
                date_naiss = st.date_input(
                    "Date de naissance", value=date(1990, 1, 1),
                    min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY",
                )
                antecedents = st.text_area("Antécédents")

            if st.form_submit_button("Créer le dossier patient", type="primary"):
                if not nom.strip() or not email.strip() or not mdp:
                    st.warning("Champs obligatoires manquants.")
                elif "@" not in email:
                    st.warning("Adresse e-mail invalide.")
                elif len(mdp) < 8:
                    st.warning("Le mot de passe doit contenir au moins 8 caractères.")
                else:
                    # Les antécédents étaient saisis mais jamais envoyés à l'API.
                    payload = {
                        "nom_complet": nom.strip(), "email": email.strip().lower(), "mot_de_passe": mdp,
                        "date_naissance": str(date_naiss), "telephone": tel.strip(),
                        "antecedents": antecedents.strip(),
                    }
                    try:
                        res = api.post("/secretaire/creer-patient", json=payload)
                        if res.status_code == 200:
                            flash(f"✅ Dossier de {nom.strip()} créé !")
                            st.rerun()
                        else:
                            st.error(f"Erreur : {api.error_detail(res)}")
                    except api.RequestException as e:
                        st.error(f"Erreur de connexion : {e}")

    if liste_patients:
        patient_selectionne_id = st.selectbox("Sélectionnez un patient", options=list(noms_patients), format_func=libelle_patient)
        res_details = api.get(f"/patients/details/{patient_selectionne_id}")
        if res_details.status_code == 200:
            patient_data = res_details.json()
            st.markdown(f"### 📁 Dossier de : **{patient_data['nom_complet']}**")
            with st.form(f"form_modif_patient_{patient_selectionne_id}"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    new_nom = st.text_input("Nom", value=patient_data['nom_complet'])
                    new_email = st.text_input("Email", value=patient_data['email'])
                    new_tel = st.text_input("Téléphone", value=patient_data['telephone'] or "")
                with col_d2:
                    st.text_input("Date de naissance", value=patient_data['date_naissance'] or "", disabled=True)
                    new_antecedents = st.text_area("Antécédents", value=patient_data['antecedents'] or "")

                if st.form_submit_button("💾 Mettre à jour", type="primary"):
                    payload = {"nom_complet": new_nom, "email": new_email, "telephone": new_tel, "antecedents": new_antecedents}
                    try:
                        res_modif = api.put(f"/patients/{patient_selectionne_id}/modifier", json=payload)
                        if res_modif.status_code == 200:
                            flash("✅ Dossier mis à jour !")
                            st.rerun()
                        else:
                            # Avant : un échec n'affichait rien.
                            st.error(f"Erreur : {api.error_detail(res_modif)}")
                    except api.RequestException as e:
                        st.error(f"Erreur de connexion : {e}")
        else:
            st.error(f"Impossible de charger le dossier : {api.error_detail(res_details)}")
    else:
        st.info("Aucun patient enregistré.")

# --- ONGLET 4 : ANNUAIRE ---
with tab4:
    st.subheader("🩺 Annuaire du personnel médical")
    annuaire = api.get_json("/medecins/annuaire", default=None)
    if annuaire is None:
        st.error("Impossible de charger l'annuaire.")
    elif not annuaire:
        st.info("Aucun médecin enregistré.")
    else:
        for med in annuaire:
            titre = f"👨‍⚕️ {med['nom_complet']} — {med.get('specialite') or 'Spécialité non renseignée'}"
            with st.expander(titre):
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"📧 **Email :** {med.get('email') or '—'}")
                    st.write(f"📞 **Téléphone :** {med.get('telephone') or '—'}")
                with col_info2:
                    st.write(f"🏢 **Bureau :** {med.get('bureau') or '—'}")
                    st.write(f"👥 **Patients suivis :** {med.get('nombre_patients', 0)}")

# --- ONGLET 5 : FACTURATION ---
with tab5:
    st.subheader("💰 Gestion de la Facturation")

    factures = api.get_json("/factures/", default=None)
    rdvs_fact = api.get_json("/rendezvous/", default=None)
    if factures is None or rdvs_fact is None:
        st.error("Impossible de contacter l'API.")
        factures, rdvs_fact = [], []

    deja_factures = {f["id_rendez_vous"] for f in factures}
    rdvs_a_facturer = [r for r in rdvs_fact if r["id"] not in deja_factures and r.get("statut") != "annulé"]

    with st.expander("➕ Créer une facture pour une consultation"):
        if not rdvs_a_facturer:
            # Avant : selectbox vide → id None → erreur 422 de l'API
            st.info("Tous les rendez-vous sont déjà facturés.")
        else:
            with st.form("form_facture"):
                rdv_options = {
                    r["id"]: f"RDV n°{r['id']} — {noms_patients.get(r['id_patient'], r['id_patient'])} — {r['date_heure']}"
                    for r in rdvs_a_facturer
                }
                rdv_id = st.selectbox("Sélectionnez le rendez-vous", options=list(rdv_options), format_func=rdv_options.get)
                montant = st.number_input(f"Montant de la consultation ({DEVISE})", min_value=1.0, step=10.0, value=50.0)

                if st.form_submit_button("Générer la facture", type="primary"):
                    try:
                        res = api.post("/factures/", json={"id_rendez_vous": rdv_id, "montant": montant})
                        if res.status_code == 200:
                            flash("Facture générée avec succès !")
                            st.rerun()
                        else:
                            st.error(f"Erreur : {api.error_detail(res)}")
                    except api.RequestException as e:
                        st.error(f"Erreur de connexion : {e}")

    st.divider()
    st.subheader("Liste des factures")
    if not factures:
        st.info("Aucune facture émise pour le moment.")
    else:
        rdv_par_id = {r["id"]: r for r in rdvs_fact}
        payees = [f for f in factures if f["statut_paiement"] in ("payé", "payee", "payée")]
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("Factures", len(factures), icon="🧾", color="cyan")
        with c2:
            render_metric_card("Payées", len(payees), icon="✅", color="emerald")
        with c3:
            render_metric_card("En attente", len(factures) - len(payees), icon="⏳", color="amber")

        for f in sorted(factures, key=lambda x: x["id"], reverse=True):
            rdv = rdv_par_id.get(f["id_rendez_vous"], {})
            patient = noms_patients.get(rdv.get("id_patient"), "—")
            with st.expander(f"Facture n°{f['id']} — {patient} — {f['montant']:.2f} {DEVISE} — {f['statut_paiement']}"):
                st.write(f"**Rendez-vous associé :** n°{f['id_rendez_vous']} ({rdv.get('date_heure', '—')})")
                st.write(f"**Date d'émission :** {f['date_emission']}")

                if f['statut_paiement'] == "en_attente":
                    if st.button(f"✅ Marquer la facture {f['id']} comme PAYÉE", key=f"pay_{f['id']}"):
                        res = api.put(f"/factures/{f['id']}/statut", json={"statut_paiement": "payé"})
                        if res.status_code == 200:
                            flash(f"Paiement de la facture n°{f['id']} enregistré !")
                            st.rerun()
                        else:
                            st.error(f"Erreur : {api.error_detail(res)}")
                elif f in payees:
                    st.success("✅ Cette facture est déjà payée.")
