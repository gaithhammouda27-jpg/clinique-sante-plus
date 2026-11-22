# Audit du projet Clinique Santé+ (22/11/2026)

## 1. Structure d'origine — points faibles

- Tous les fichiers à la racine : API, base, IA, seed, frontend mélangés.
- **Fichiers de sauvegarde versionnés** : `api_backup_before_analytics.py` (2 773 lignes),
  `app_backup.py`, `pages/1_Admin_backup.py`. Ce dernier était même une **page Streamlit
  accessible** par URL (`/Admin_backup`). → supprimés (l'historique git les conserve).
- Fichiers géants : `api.py` ≈ 3 000 lignes, `pages/1_Admin.py` ≈ 3 100 lignes.
- Chemins codés en dur : `D:\health_project\models\...`, `D:\hadoop`, `./clinique.db`
  (relatif au dossier courant). Le projet ne tournait que sur la machine de l'auteur.
- `requirements.txt` cassé (`pysparkfastapi`, liste dupliquée), dépendances manquantes
  (`passlib`, `bcrypt`, `python-multipart`).
- README mal formaté (blocs de code non fermés, texte du requirements collé dedans).
- `API_URL` copié dans 5 fichiers, pas de timeout sur la plupart des requêtes.

## 2. Nouvelle organisation

`backend/` (API, base, IA, sécurité, config, seed) · `frontend/` (app, pages, composants,
client API, auth) · `ml/` (données, modèles, scripts) · scripts `setup/run_*.ps1`.
Voir le README pour l'arborescence complète.

## 3. Bugs corrigés

### Bloquants
| Bug | Cause | Correctif |
|---|---|---|
| Connexion et création de compte plantent sur une installation neuve | `passlib` 1.7.4 incompatible avec `bcrypt` ≥ 4.1 (`ValueError: password cannot be longer than 72 bytes`) | `backend/security.py` utilise `bcrypt` directement (hachages existants compatibles) |
| Comptes démo inexistants : espaces Admin et Secrétariat **inaccessibles** | `seed_data.py` ne créait ni admin ni secrétaire ; l'accès démo ouvrait une session avec des ID codés en dur (64, 1, 12, 13) sans rapport avec la base | Le seed crée les 4 comptes ; l'accès démo passe par la vraie route `/login` |
| Seed qui plante sous Windows | `print()` d'emojis sur console cp1252 → exception → rollback | Sortie UTF-8 forcée dans `backend/__init__.py` |
| Interface illisible par endroits | Thème Streamlit **clair** sous le CSS sombre : en-tête blanc, `st.info` blanc sur blanc | `.streamlit/config.toml` (thème sombre) |

### Espace Patient
- Onglet « Historique » : appel à `/patients/{id}/predictions`, **route inexistante** → erreur 404.
- Onglet « Bilan » toujours vide : regex `Age:50, Tension:130` alors que les constantes
  sont stockées en **JSON**.
- Rendez-vous affichés seulement après un clic sur « Rafraîchir ».
- `ID_PATIENT = None` possible → requêtes vers `/patients/None/...`.

### Espace Secrétariat
- Onglet RDV entier en erreur dès qu'un RDV est « terminé » (`.index()` → `ValueError`).
- Antécédents saisis à la création d'un patient **jamais envoyés** à l'API.
- Patients affichés « Patient ID: 3 (Tel: …) » au lieu de leur nom ; tableau RDV avec ID bruts.
- Échec de mise à jour d'un dossier : aucun message.
- Facturation : liste vide → `id_rendez_vous=None` → erreur 422 ; RDV facturables plusieurs fois ;
  devise « € » alors que l'Admin affiche « TND ».
- Messages de succès invisibles (effacés par `st.rerun()`).

### Espace Médecin
- « Marquer comme terminé » via un champ numérique libre : on pouvait clore le RDV d'un autre
  médecin, sans aucun retour d'erreur → remplacé par une liste des RDV du médecin + statut.
- Historique des analyses trié sur la chaîne `jj/mm/aaaa` (ordre faux).
- Tous les documents re-téléchargés à **chaque** interaction → téléchargement à la demande.
- « Dr. Dr. Martin » dans les titres.

### Navigation / général
- Lien « Portail d'Accueil » inutilisable une fois connecté (redirection automatique immédiate).
- Bouton « ← Retour à l'accueil » de l'Admin qui **déconnectait** l'utilisateur.
- Déconnexion depuis la sidebar → l'utilisateur restait sur une page « Accès refusé ».
- Paramètre `use_container_width` déprécié (avertissements) → `width="stretch"`.
- Coquille « MAHIDA » → « MAHDIA ».

### Backend / IA (nécessaires au frontend)
- **Sexe toujours encodé « femme »** : `StringIndexer` ré-entraîné sur la seule ligne reçue
  (index 0 quel que soit le sexe). Entraînement : F = 0, M = 1 → encodage explicite.
- `/medecins/` et `/utilisateurs/par-email/` renvoyaient le **hachage du mot de passe**.
- Spark démarré à l'import et modèles sur `D:\health_project` → chargement paresseux,
  chemins relatifs au dépôt, message d'erreur court si Java/Hadoop manquent.

## 4. Recommandations (par priorité)

1. **Sécurité de l'API (critique)** : aucune route n'est protégée. N'importe qui peut lire tous
   les dossiers médicaux ou créer un admin via `POST /utilisateurs/` avec `curl`. Le contrôle des
   rôles n'existe que dans Streamlit. → JWT (`/login` renvoie un token), dépendance FastAPI
   `get_current_user` + vérification du rôle sur chaque route, et un patient ne lit que *son* dossier.
2. **Découper les fichiers géants** : `api.py` → `APIRouter` par domaine (`routers/patients.py`,
   `rendezvous.py`, `pharmacie.py`…) ; `1_Admin.py` → une fonction/module par onglet.
3. **Tests automatisés** : `pytest` + `TestClient` FastAPI sur une base SQLite temporaire
   (login, création RDV, conflits d'horaire, facturation). Aucun test aujourd'hui.
4. **Migrations** : Alembic au lieu de `create_all` (impossible de modifier une colonne sans perdre la base).
5. **Modèle de données** : dates stockées en `String` dans plusieurs tables (RDV, ordonnances,
   prédictions) → `DateTime` ; statuts libres (`"payé"`, `"payee"`, `"confirme"`…) → `Enum`.
6. **Performance** : nombreuses requêtes N+1 (une requête par ligne pour retrouver le médecin) →
   `joinedload` / jointures ; cache Streamlit (`st.cache_data(ttl=…)`) pour les listes.
7. **IA** : Spark est disproportionné pour prédire une ligne (démarrage ≈ 10 s, Java + Hadoop
   requis sous Windows). Exporter le modèle vers **scikit-learn** (ou ONNX) rendrait l'IA instantanée
   et sans Java. Afficher l'AUC réelle et la date d'entraînement au lieu de valeurs codées.
8. **Données factices dans l'UI** : l'accueil affiche des KPI en dur (48 lits, 385 actes, 4.7/5)
   → les calculer depuis `/analytics/dashboard`.
9. **Outillage** : `ruff` (lint + format), `pre-commit`, GitHub Actions (lint + tests) ;
   Dockerfile/docker-compose pour lancer API + frontend en une commande.
10. **RGPD / données de santé** : journaliser les accès aux dossiers, chiffrer les documents
    uploadés, ne jamais commiter `clinique.db` ni `uploads/` (désormais dans `.gitignore`).
