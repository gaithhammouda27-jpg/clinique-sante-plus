"""
En-tête cinématographique avec statut système temps réel
pour la Clinique Santé+.
"""

import streamlit as st
from datetime import datetime
from style import render_clean_html


def render_header(title, subtitle=None, badge="CLINIQUE SANTÉ+ • SYSTÈME HOSPITALIER IA", show_status=True):
    """
    Affiche une barre d'en-tête futuriste avec badge lumineux et statut télémétrique.
    """
    now_str = datetime.now().strftime("%d %b %Y • %H:%M")
    
    status_html = ""
    if show_status:
        status_html = f"""
<div style="display:flex;align-items:center;gap:14px;background:rgba(15,23,42,0.7);border:1px solid rgba(255,255,255,0.08);border-radius:9999px;padding:6px 16px;backdrop-filter:blur(10px);">
<div style="display:flex;align-items:center;gap:6px;">
<span class="pulse-dot"></span>
<span style="font-size:0.78rem;font-weight:700;color:#10B981;letter-spacing:0.05em;">MOTEUR IA CONNECTÉ</span>
</div>
<span style="color:rgba(255,255,255,0.2);">|</span>
<span style="font-size:0.76rem;color:#94A3B8;font-weight:500;">{now_str}</span>
</div>
"""
        
    subtitle_html = f"<p style='color:#94A3B8;font-size:0.95rem;margin-top:4px;margin-bottom:0;'>{subtitle}</p>" if subtitle else ""

    html = f"""
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;padding-bottom:18px;margin-bottom:22px;border-bottom:1px solid rgba(255,255,255,0.08);">
<div>
<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
<span class="glow-badge">{badge}</span>
</div>
<h2 style="margin:0;font-size:1.85rem;font-weight:800;letter-spacing:-0.02em;background:linear-gradient(120deg,#FFFFFF 0%,#38BDF8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{title}</h2>
{subtitle_html}
</div>
<div>
{status_html}
</div>
</div>
"""
    render_clean_html(html)
