"""
Composants de cartes, badges et panneaux cinématiques
pour l'interface Clinique Santé+.
"""

import streamlit as st
from style import render_clean_html


COLOR_MAP = {
    "cyan": {"border": "#00F2FE", "bg": "rgba(0, 242, 254, 0.12)", "text": "#38BDF8"},
    "teal": {"border": "#0D9488", "bg": "rgba(13, 148, 136, 0.12)", "text": "#2DD4BF"},
    "emerald": {"border": "#10B981", "bg": "rgba(16, 185, 129, 0.12)", "text": "#34D399"},
    "amber": {"border": "#F59E0B", "bg": "rgba(245, 158, 11, 0.12)", "text": "#FBBF24"},
    "rose": {"border": "#F43F5E", "bg": "rgba(244, 63, 94, 0.12)", "text": "#FB7185"},
    "violet": {"border": "#8B5CF6", "bg": "rgba(139, 92, 246, 0.12)", "text": "#A78BFA"},
}


def render_metric_card(title, value, unit="", delta=None, delta_positive=True, icon="📊", color="cyan", subtitle=None):
    """
    Rend une carte métrique cinématique lumineuse avec bordure illuminée et badge tendance.
    """
    c = COLOR_MAP.get(color, COLOR_MAP["cyan"])
    
    delta_html = ""
    if delta is not None:
        delta_color = "#10B981" if delta_positive else "#F43F5E"
        arrow = "↑" if delta_positive else "↓"
        delta_html = f'<span style="display:inline-flex;align-items:center;gap:3px;font-size:0.78rem;font-weight:700;color:{delta_color};background:rgba(15,23,42,0.6);padding:2px 8px;border-radius:9999px;border:1px solid {delta_color}40;">{arrow} {delta}</span>'
        
    subtitle_html = f"<div style='color:#64748B;font-size:0.75rem;margin-top:6px;'>{subtitle}</div>" if subtitle else ""
    
    html = f"""
<div style="background:linear-gradient(145deg,rgba(15,23,42,0.85) 0%,rgba(30,41,59,0.65) 100%);border:1px solid rgba(255,255,255,0.08);border-left:4px solid {c['border']};border-radius:14px;padding:18px 20px;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 6px 20px rgba(0,0,0,0.35);margin-bottom:12px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="background:{c['bg']};border:1px solid {c['border']}50;border-radius:8px;padding:4px 7px;font-size:0.95rem;">{icon}</span>
<span style="color:#94A3B8;font-size:0.82rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">{title}</span>
</div>
{delta_html}
</div>
<div style="display:flex;align-items:baseline;gap:6px;">
<span style="color:#FFFFFF;font-size:1.85rem;font-weight:750;letter-spacing:-0.02em;">{value}</span>
<span style="color:#94A3B8;font-size:0.9rem;font-weight:500;">{unit}</span>
</div>
{subtitle_html}
</div>
"""
    render_clean_html(html)


def render_hero_banner(title, subtitle, badge="ESPACE SANTÉ+", icon="🏥"):
    """
    Bannière hero cinématique avec lueur d'ambiance et badge d'état.
    """
    html = f"""
<div class="cinematic-hero">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
<span class="pulse-dot"></span>
<span class="glow-badge">{badge}</span>
</div>
<div style="display:flex;align-items:flex-start;gap:18px;">
<div style="font-size:2.8rem;background:rgba(0,242,254,0.12);border:1px solid rgba(0,242,254,0.35);border-radius:16px;padding:10px 16px;box-shadow:0 0 20px rgba(0,242,254,0.2);">{icon}</div>
<div>
<h1>{title}</h1>
<p>{subtitle}</p>
</div>
</div>
</div>
"""
    render_clean_html(html)


def render_status_pill(text, status="success"):
    """
    Badge pilule luminescent (success, warning, danger, info, neutral).
    """
    styles = {
        "success": ("#10B981", "rgba(16, 185, 129, 0.15)", "●"),
        "warning": ("#F59E0B", "rgba(245, 158, 11, 0.15)", "▲"),
        "danger": ("#F43F5E", "rgba(244, 63, 94, 0.15)", "■"),
        "info": ("#00F2FE", "rgba(0, 242, 254, 0.15)", "✦"),
        "neutral": ("#94A3B8", "rgba(148, 163, 184, 0.12)", "○")
    }
    color, bg, symbol = styles.get(status, styles["neutral"])
    
    return f'<span style="display:inline-flex;align-items:center;gap:5px;background:{bg};color:{color};border:1px solid {color}50;border-radius:9999px;padding:3px 10px;font-size:0.78rem;font-weight:700;letter-spacing:0.04em;box-shadow:0 0 10px {color}25;">{symbol} {text}</span>'


def render_patient_telemetry(nom, age, tension, glycemie, frequence, imc, risque_ia=None):
    """
    Affiche une carte de télémétrie biométrique temps réel façon moniteur de chevet.
    """
    risque_html = ""
    if risque_ia is not None:
        pct = float(risque_ia) * 100
        r_color = "#F43F5E" if pct > 60 else ("#F59E0B" if pct > 35 else "#10B981")
        risque_html = f'<div style="background:rgba(15,23,42,0.8);border:1px solid {r_color}60;border-radius:10px;padding:8px 14px;text-align:center;"><div style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;">Risque IA</div><div style="font-size:1.25rem;font-weight:800;color:{r_color};">{pct:.1f}%</div></div>'
        
    html = f"""
<div style="background:linear-gradient(135deg,rgba(15,23,42,0.9) 0%,rgba(30,41,59,0.75) 100%);border:1px solid rgba(0,242,254,0.3);border-radius:16px;padding:20px 24px;box-shadow:0 10px 30px rgba(0,0,0,0.4),0 0 15px rgba(0,242,254,0.15);margin-bottom:20px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
<div style="display:flex;align-items:center;gap:12px;">
<span class="pulse-dot"></span>
<div>
<h4 style="margin:0;color:#FFFFFF;font-size:1.15rem;font-weight:700;">{nom}</h4>
<span style="color:#94A3B8;font-size:0.82rem;">Âge: <b>{age} ans</b></span>
</div>
</div>
{risque_html}
</div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px;text-align:center;">
<div style="color:#94A3B8;font-size:0.72rem;text-transform:uppercase;">Tension</div>
<div style="color:#38BDF8;font-size:1.25rem;font-weight:750;">{tension} <span style="font-size:0.7rem;color:#94A3B8;">mmHg</span></div>
</div>
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px;text-align:center;">
<div style="color:#94A3B8;font-size:0.72rem;text-transform:uppercase;">Glycémie</div>
<div style="color:#FBBF24;font-size:1.25rem;font-weight:750;">{glycemie} <span style="font-size:0.7rem;color:#94A3B8;">mmol/L</span></div>
</div>
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px;text-align:center;">
<div style="color:#94A3B8;font-size:0.72rem;text-transform:uppercase;">Fréquence</div>
<div style="color:#FB7185;font-size:1.25rem;font-weight:750;">{frequence} <span style="font-size:0.7rem;color:#94A3B8;">bpm</span></div>
</div>
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px;text-align:center;">
<div style="color:#94A3B8;font-size:0.72rem;text-transform:uppercase;">IMC</div>
<div style="color:#34D399;font-size:1.25rem;font-weight:750;">{imc}</div>
</div>
</div>
</div>
"""
    render_clean_html(html)
