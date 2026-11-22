import streamlit as st

def clean_html(html_str: str) -> str:
    """
    Supprime les indentations et lignes vides pour empêcher le parseur
    Markdown de Streamlit de convertir le HTML en blocs de code <pre><code>.
    """
    return "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())


def render_clean_html(html_str: str, unsafe_allow_html: bool = True, **kwargs):
    """
    Rend du code HTML en toute sécurité dans Streamlit sans risque de déformation en bloc de code.
    Concatène toutes les lignes en une seule ligne pour éviter le bug CommonMark (texte nu → <pre><code>).
    """
    cleaned = clean_html(html_str)
    # Jointure en une seule ligne pour éviter que le parseur Markdown traite le texte nu
    # comme un bloc de code (règle des 4 espaces ou CommonMark raw HTML block rule)
    single_line = " ".join(cleaned.splitlines())
    st.markdown(single_line, unsafe_allow_html=unsafe_allow_html, **kwargs)


def apply_custom_style():
    """
    Applique le système de design 'Obsidian Luminescence / Cyber-Clinical Ambient'.
    Combine une atmosphère cinématographique sombre, du glassmorphism haute fidélité,
    des accents bio-luminescents et des micro-interactions soignées.
    """
    render_clean_html("""
    <style>
    /* ==========================================================
       1. VARIABLES DU SYSTÈME DE DESIGN AMBIENT CINÉMATIQUE
    ========================================================== */
    :root {
        --bg-main: #070B14;
        --bg-surface: rgba(15, 23, 42, 0.78);
        --bg-surface-elevated: rgba(30, 41, 59, 0.85);
        --bg-glass-card: rgba(15, 23, 42, 0.65);
        
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        
        --accent-cyan: #00F2FE;
        --accent-teal: #0D9488;
        --accent-teal-glow: #14B8A6;
        --accent-emerald: #10B981;
        --accent-amber: #F59E0B;
        --accent-rose: #F43F5E;
        --accent-violet: #8B5CF6;
        
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-glow: rgba(0, 242, 254, 0.3);
        --border-glass: rgba(255, 255, 255, 0.12);
        
        --shadow-ambient: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
        --shadow-glow-cyan: 0 0 25px rgba(0, 242, 254, 0.25);
        --shadow-glow-teal: 0 0 25px rgba(20, 184, 166, 0.25);
    }

    /* ==========================================================
       2. FOND DE L'APPLICATION & TYPOGRAPHIE
    ========================================================== */
    html {
        scroll-behavior: smooth;
    }

    .stApp {
        background-color: var(--bg-main) !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.07) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.06) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Conteneur principal */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
        max-width: 1440px !important;
    }

    /* Titres avec lueur cinématographique */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    h1 {
        text-shadow: 0 0 30px rgba(0, 242, 254, 0.25);
    }

    p, span, label {
        color: var(--text-primary);
    }

    /* ==========================================================
       3. NAVIGATION TABS (ONGLETS CAPSULES FLUIDES)
    ========================================================== */
    div[data-testid="stTabs"] {
        position: relative;
        z-index: 50;
    }

    div[data-testid="stTabs"] [role="tablist"] {
        position: sticky !important;
        top: 0 !important;
        z-index: 99 !important;
        background: rgba(7, 11, 20, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        padding: 12px 10px !important;
        margin-bottom: 24px !important;
        border-radius: 16px !important;
        border: 1px solid var(--border-subtle) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
        display: flex !important;
        gap: 8px !important;
    }

    div[data-testid="stTabs"] button[role="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 12px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid transparent !important;
    }

    div[data-testid="stTabs"] button[role="tab"]:hover {
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #FFFFFF !important;
        background: linear-gradient(135deg, rgba(13, 148, 136, 0.85) 0%, rgba(6, 182, 212, 0.75) 100%) !important;
        border: 1px solid var(--accent-cyan) !important;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.35) !important;
    }

    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* ==========================================================
       4. BOUTONS CINÉMATIQUES & LUMINESCENCE
    ========================================================== */
    .stButton > button {
        background: linear-gradient(135deg, #0F766E 0%, #06B6D4 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 14px rgba(6, 182, 212, 0.25) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(6, 182, 212, 0.45) !important;
        border-color: var(--accent-cyan) !important;
    }

    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ==========================================================
       5. CHAMPS DE FORMULAIRE ET ENTRÉES SÈCHES
    ========================================================== */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stTextArea textarea {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        padding: 0.65rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTimeInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.3) !important;
        outline: none !important;
    }

    /* Selectbox baseweb */
    div[data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.3) !important;
    }

    /* ==========================================================
       6. CARTES & PANNEAUX GLASSMORPHIC (CLASSES CSS GLOBALES)
    ========================================================== */
    .cinematic-hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(11, 25, 44, 0.9) 0%, rgba(15, 44, 66, 0.85) 100%);
        border: 1px solid rgba(0, 242, 254, 0.25);
        border-radius: 20px;
        padding: 40px 45px;
        margin-bottom: 28px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
    }

    .cinematic-hero::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 380px;
        height: 380px;
        background: radial-gradient(circle, rgba(0, 242, 254, 0.12) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .cinematic-hero h1 {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 12px;
        background: linear-gradient(120deg, #FFFFFF 0%, #A5F3FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .cinematic-hero p {
        font-size: 1.1rem;
        color: #94A3B8;
        line-height: 1.6;
        max-width: 850px;
    }

    .cinematic-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        margin-bottom: 20px;
    }

    .cinematic-card:hover {
        border-color: rgba(0, 242, 254, 0.35);
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45), 0 0 20px rgba(0, 242, 254, 0.15);
    }

    /* Carte métrique lumineuse */
    .metric-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--accent-cyan);
        border-radius: 14px;
        padding: 20px 22px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.25s ease;
        margin-bottom: 15px;
    }

    .metric-card:hover {
        border-color: rgba(0, 242, 254, 0.4);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 242, 254, 0.18);
        transform: translateY(-2px);
    }

    .metric-title {
        color: #94A3B8;
        font-size: 0.88rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .metric-value {
        color: #FFFFFF;
        font-size: 1.85rem;
        font-weight: 750;
        letter-spacing: -0.02em;
    }

    /* Badges de statut et pulsations */
    .pulse-dot {
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background-color: var(--accent-emerald);
        box-shadow: 0 0 10px var(--accent-emerald);
        animation: pulse-animation 2s infinite;
        margin-right: 8px;
    }

    @keyframes pulse-animation {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.15); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .glow-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        background: rgba(6, 182, 212, 0.12);
        color: var(--accent-cyan);
        border: 1px solid rgba(6, 182, 212, 0.35);
        box-shadow: 0 0 12px rgba(6, 182, 212, 0.2);
    }

    /* ==========================================================
       7. SIDEBAR AMBIANTE CINÉMATIQUE
    ========================================================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090E1A 0%, #0F172A 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4) !important;
    }

    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    [data-testid="stSidebarNav"], [data-testid="collapsedControl"] {
        display: none !important;
    }

    .sidebar-brand {
        text-align: center;
        padding: 24px 12px 16px;
    }

    .sidebar-logo {
        font-size: 2.4rem;
        margin-bottom: 8px;
        filter: drop-shadow(0 0 12px rgba(0, 242, 254, 0.4));
    }

    .sidebar-brand-name {
        font-size: 1.25rem;
        font-weight: 750;
        background: linear-gradient(120deg, #FFFFFF 0%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.01em;
    }

    .sidebar-brand-subtitle {
        font-size: 0.75rem;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 4px;
    }

    .sidebar-profile {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 16px;
        margin: 12px 0;
        text-align: center;
        backdrop-filter: blur(10px);
    }

    .sidebar-avatar {
        font-size: 1.8rem;
        margin-bottom: 6px;
    }

    .sidebar-user-name {
        font-weight: 700;
        font-size: 1rem;
        color: #F8FAFC !important;
    }

    .sidebar-user-role {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent-cyan) !important;
        background: rgba(6, 182, 212, 0.15);
        border: 1px solid rgba(6, 182, 212, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        margin-top: 6px;
    }

    /* ==========================================================
       8. NOTIFICATIONS & ALERTES STREAMLIT
    ========================================================== */
    .stAlert {
        border-radius: 14px !important;
        border: 1px solid var(--border-subtle) !important;
        backdrop-filter: blur(12px) !important;
        background: rgba(15, 23, 42, 0.8) !important;
        color: #F1F5F9 !important;
    }

    /* Tableaux et dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid var(--border-subtle) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    /* Séparateurs */
    hr {
        border-color: rgba(255, 255, 255, 0.07) !important;
        margin: 28px 0 !important;
    }

    /* Barres de progression */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0D9488 0%, #00F2FE 100%) !important;
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.4) !important;
    }
    </style>
    """)
