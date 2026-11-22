import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_client as api
from auth import require_login, normalize_role
from style import apply_custom_style
from components.sidebar import render_sidebar
from components.header import render_header

st.set_page_config(page_title="Assistant IA | Clinique Santé+", page_icon="🤖", layout="wide")

# ==========================================
# 1. SÉCURITÉ ET STYLE
# ==========================================
require_login()
apply_custom_style()

nom = st.session_state.get("name", "Utilisateur")
role = normalize_role(st.session_state.get("role"))
render_sidebar(nom, role)
render_header("Assistant IA", "Posez vos questions en langage naturel sur la clinique", badge="ASSISTANT IA")

SUGGESTIONS = {
    "admin": ["Fais-moi un point sur la clinique aujourd'hui", "Quel est notre solde financier ?",
              "Y a-t-il des médicaments en alerte ?", "Combien de lits sont disponibles par service ?"],
    "medecin": ["Quels sont mes rendez-vous des 7 prochains jours ?", "Résume le dossier de Jean Dupont",
                "Y a-t-il des médicaments en stock faible ?", "Rédige un modèle de compte rendu de consultation"],
    "secretaire": ["Quels rendez-vous sont en attente de confirmation ?", "Quels cardiologues sont disponibles ?",
                   "Rédige un SMS de rappel de rendez-vous", "Combien de lits sont libres ?"],
    "patient": ["Quand est mon prochain rendez-vous ?", "Résume mon dossier médical",
                "Quels médecins sont cardiologues ?", "Comment préparer ma prise de sang ?"],
}

# ==========================================
# 2. ÉTAT DE L'ASSISTANT
# ==========================================
statut = api.get_json("/assistant/status", default=None)
if statut is None:
    st.error("Impossible de contacter l'API. Vérifiez qu'elle est démarrée.")
    st.stop()

if not statut.get("configure"):
    st.warning("**Assistant non configuré.** Il faut une clé API gratuite (2 minutes) :")
    st.markdown(
        "1. Créez une clé gratuite sur **https://console.groq.com/keys** (sans carte bancaire).\n"
        "2. À la racine du projet, copiez `.env.example` en `.env`, puis renseignez `GROQ_API_KEY=...`.\n"
        "3. Redémarrez l'API (`.\\run_api.ps1`) et rechargez cette page.\n\n"
        "Alternatives : **Google Gemini** (`ASSISTANT_PROVIDER=gemini` + `GEMINI_API_KEY`) ou "
        "**Ollama** en local, sans clé ni Internet (`ASSISTANT_PROVIDER=ollama`)."
    )
    st.stop()

c1, c2 = st.columns([4, 1])
with c1:
    st.caption(f"🟢 Connecté à **{statut['fournisseur']}** · modèle `{statut['modele']}` · "
               "réponses basées sur les données de la clinique selon votre rôle.")
with c2:
    if st.button("🗑️ Nouvelle conversation", width="stretch"):
        st.session_state["assistant_messages"] = []
        st.rerun()

st.caption("⚠️ Les questions sont envoyées à un service d'IA externe gratuit : n'y saisissez pas de "
           "données de santé réelles. L'assistant ne remplace pas l'avis d'un médecin.")

messages = st.session_state.setdefault("assistant_messages", [])

# ==========================================
# 3. CONVERSATION
# ==========================================
question = None
if not messages:
    st.markdown("#### 💡 Suggestions")
    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS.get(role, [])):
        with cols[i % 2]:
            if st.button(s, key=f"sugg_{i}", width="stretch"):
                question = s

for m in messages:
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])
        if m.get("outils"):
            st.caption("🔧 Données consultées : " + ", ".join(dict.fromkeys(m["outils"])))

saisie = st.chat_input("Écrivez votre question…")
question = saisie or question

if question:
    messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("L'assistant réfléchit…"):
            try:
                res = api.post("/assistant/chat", timeout=120, json={
                    "user_id": st.session_state["user_id"],
                    "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
                })
                if res.status_code == 200:
                    data = res.json()
                    st.markdown(data["reponse"])
                    if data.get("outils"):
                        st.caption("🔧 Données consultées : " + ", ".join(dict.fromkeys(data["outils"])))
                    messages.append({"role": "assistant", "content": data["reponse"], "outils": data.get("outils")})
                else:
                    messages.pop()  # on retire la question pour pouvoir la reposer
                    st.error(api.error_detail(res))
            except api.RequestException as e:
                messages.pop()
                st.error(f"Erreur de connexion : {e}")
