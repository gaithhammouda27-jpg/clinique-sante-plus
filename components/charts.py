"""
Composants de visualisations interactives cinématiques (Plotly)
pour la Clinique Santé+.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


# Palette cinématique bio-luminescente
CINEMATIC_COLORS = {
    "cyan": "#00F2FE",
    "teal": "#0D9488",
    "teal_light": "#14B8A6",
    "emerald": "#10B981",
    "amber": "#F59E0B",
    "rose": "#F43F5E",
    "violet": "#8B5CF6",
    "blue": "#38BDF8",
    "card_bg": "rgba(15, 23, 42, 0.75)",
    "plot_bg": "rgba(10, 16, 31, 0.5)",
    "border": "rgba(255, 255, 255, 0.08)",
    "grid": "rgba(255, 255, 255, 0.05)",
    "text": "#F8FAFC",
    "text_muted": "#94A3B8"
}


def apply_cinematic_theme(fig, height=360, title=None):
    """
    Applique le thème cinématique ambient à n'importe quel graphique Plotly.
    """
    layout_update = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "color": CINEMATIC_COLORS["text"],
            "size": 12
        },
        "margin": {"l": 30, "r": 30, "t": 50 if title else 25, "b": 35},
        "hoverlabel": {
            "bgcolor": "#0B1329",
            "bordercolor": CINEMATIC_COLORS["cyan"],
            "font": {"color": "#FFFFFF", "size": 13, "family": "'Inter', sans-serif"}
        }
    }
    
    if height:
        layout_update["height"] = height
        
    if title:
        layout_update["title"] = {
            "text": f"<b>{title}</b>",
            "font": {"size": 15, "color": "#FFFFFF"},
            "x": 0.02,
            "y": 0.96
        }

    fig.update_layout(**layout_update)
    
    fig.update_xaxes(
        gridcolor=CINEMATIC_COLORS["grid"],
        zerolinecolor=CINEMATIC_COLORS["border"],
        tickfont={"color": CINEMATIC_COLORS["text_muted"]},
        showline=True,
        linecolor=CINEMATIC_COLORS["border"]
    )
    
    fig.update_yaxes(
        gridcolor=CINEMATIC_COLORS["grid"],
        zerolinecolor=CINEMATIC_COLORS["border"],
        tickfont={"color": CINEMATIC_COLORS["text_muted"]},
        showline=True,
        linecolor=CINEMATIC_COLORS["border"]
    )
    
    return fig


def create_ai_risk_gauge(probability, title="Indice de Risque IA", disease="Hypertension"):
    """
    Crée une jauge cinématique radiale de probabilité avec 3 zones d'alerte lumineuses.
    """
    pct = float(probability) * 100
    
    # Détermination de la couleur selon le risque
    if pct < 35:
        bar_color = CINEMATIC_COLORS["emerald"]
        status_text = "RISQUE MINIME"
    elif pct < 65:
        bar_color = CINEMATIC_COLORS["amber"]
        status_text = "VIGILANCE MODÉRÉE"
    else:
        bar_color = CINEMATIC_COLORS["rose"]
        status_text = "ALERTE ÉLEVÉE"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={
            "suffix": "%",
            "font": {"size": 38, "color": "#FFFFFF", "family": "'Inter', sans-serif"}
        },
        title={
            "text": f"<b>{title}</b><br><span style='font-size:12px; color:{bar_color}; font-weight:700;'>● {status_text}</span>",
            "font": {"size": 16, "color": "#E2E8F0"}
        },
        delta={"reference": 50, "increasing": {"color": CINEMATIC_COLORS["rose"]}, "decreasing": {"color": CINEMATIC_COLORS["emerald"]}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": CINEMATIC_COLORS["text_muted"],
                "tickfont": {"size": 11, "color": CINEMATIC_COLORS["text_muted"]}
            },
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": "rgba(30, 41, 59, 0.4)",
            "borderwidth": 1,
            "bordercolor": "rgba(255, 255, 255, 0.1)",
            "steps": [
                {"range": [0, 35], "color": "rgba(16, 185, 129, 0.18)"},
                {"range": [35, 65], "color": "rgba(245, 158, 11, 0.18)"},
                {"range": [65, 100], "color": "rgba(244, 63, 94, 0.22)"}
            ],
            "threshold": {
                "line": {"color": CINEMATIC_COLORS["rose"], "width": 4},
                "thickness": 0.8,
                "value": 65
            }
        }
    ))

    apply_cinematic_theme(fig, height=280)
    fig.update_layout(margin={"l": 30, "r": 30, "t": 60, "b": 25})
    return fig


def create_biometric_radar(metrics_dict=None, title="Profil Biométrique & Constantes"):
    """
    Crée un radar polar cinématique comparant les constantes du patient aux normes médicales.
    metrics_dict: ex: {'Tension': 140, 'Glycémie': 6.2, 'Fréquence': 82, 'IMC': 26, 'SpO2': 98}
    """
    if not metrics_dict:
        metrics_dict = {
            "Tension Sys": 135,
            "Glycémie": 5.8,
            "Fréq. Cardiaque": 76,
            "IMC": 24.5,
            "Saturation O2": 98
        }
    
    # Normalisation entre 0 et 100 pour affichage radar homogène
    # Références standards :
    # Tension Sys: 120 (max 180) -> 120/180 = 66%
    # Glycémie: 5.0 (max 12) -> 5/12 = 41%
    # Fréq: 70 (max 140) -> 50%
    # IMC: 22 (max 40) -> 55%
    # SpO2: 98 (max 100) -> 98%
    
    categories = list(metrics_dict.keys())
    values = []
    ideal_values = []
    
    ranges = {
        "Tension Sys": (120, 180),
        "Tension": (120, 180),
        "Glycémie": (5.0, 12.0),
        "Fréq. Cardiaque": (72, 140),
        "Fréquence": (72, 140),
        "IMC": (22.0, 40.0),
        "Saturation O2": (98, 100),
        "SpO2": (98, 100),
        "Âge": (40, 100)
    }
    
    for cat in categories:
        val = metrics_dict[cat]
        norm_range = ranges.get(cat, (50, 100))
        # Valeur normalisée en % de l'échelle critique
        norm_val = min(100, max(20, (float(val) / norm_range[1]) * 100))
        ideal_norm = min(100, (norm_range[0] / norm_range[1]) * 100)
        values.append(norm_val)
        ideal_values.append(ideal_norm)
        
    # Boucle fermée pour le radar
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    ideal_closed = ideal_values + [ideal_values[0]]
    
    fig = go.Figure()
    
    # Zone cible idéale (Norme médicale)
    fig.add_trace(go.Scatterpolar(
        r=ideal_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.15)',
        line=dict(color=CINEMATIC_COLORS["emerald"], width=1.5, dash='dash'),
        name="Norme Clinique Idéale"
    ))
    
    # Mesures réelles du patient
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(0, 242, 254, 0.25)',
        line=dict(color=CINEMATIC_COLORS["cyan"], width=2.5),
        name="Patient Actuel"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False,
                linecolor=CINEMATIC_COLORS["border"],
                gridcolor=CINEMATIC_COLORS["grid"]
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=CINEMATIC_COLORS["text"]),
                linecolor=CINEMATIC_COLORS["border"],
                gridcolor=CINEMATIC_COLORS["grid"]
            ),
            bgcolor="rgba(10, 16, 31, 0.3)"
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(color=CINEMATIC_COLORS["text_muted"])
        )
    )
    
    apply_cinematic_theme(fig, height=340, title=title)
    return fig


def create_patient_flow_sankey(title="Flux des Flux & Parcours Patients"):
    """
    Crée un diagramme Sankey cinématique illustrant le parcours des patients dans la clinique.
    """
    nodes = [
        "Accueil / Urgences",      # 0
        "Rendez-vous Direct",      # 1
        "Consultation Générale",  # 2
        "Cardiologie",             # 3
        "Pédiatrie",               # 4
        "Analyses Laboratoire",    # 5
        "Hospitalisation (Lits)",  # 6
        "Pharmacie & Sortie",      # 7
        "Suivi Ambulatoire"        # 8
    ]
    
    node_colors = [
        CINEMATIC_COLORS["cyan"],
        CINEMATIC_COLORS["teal"],
        CINEMATIC_COLORS["blue"],
        CINEMATIC_COLORS["rose"],
        CINEMATIC_COLORS["violet"],
        CINEMATIC_COLORS["amber"],
        CINEMATIC_COLORS["rose"],
        CINEMATIC_COLORS["emerald"],
        CINEMATIC_COLORS["teal_light"]
    ]
    
    sources = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6, 6]
    targets = [2, 3, 2, 4, 5, 7, 5, 6, 7, 7, 7, 8]
    values  = [45, 30, 60, 25, 35, 70, 20, 15, 25, 50, 12, 8]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=18,
            line=dict(color="rgba(255,255,255,0.15)", width=1),
            label=nodes,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(6, 182, 212, 0.22)"
        )
    )])
    
    apply_cinematic_theme(fig, height=360, title=title)
    return fig


def create_financial_treemap(df_finances=None, title="Flux Financier : Recettes & Postes de Dépenses"):
    """
    Crée un Treemap hiérarchique interactif des flux financiers de la clinique.
    """
    if df_finances is None or df_finances.empty:
        # Données représentatives de la clinique
        data = {
            "Type": [
                "Recettes", "Recettes", "Recettes", "Recettes",
                "Dépenses", "Dépenses", "Dépenses", "Dépenses"
            ],
            "Catégorie": [
                "Consultations", "Hospitalisations", "Pharmacie", "Laboratoire",
                "Personnel Médical", "Matériel & Réactifs", "Maintenance & Énergie", "Médicaments Stock"
            ],
            "Montant": [
                14200, 28500, 11800, 9300,
                24000, 12500, 7200, 9800
            ]
        }
        df_finances = pd.DataFrame(data)

    fig = px.treemap(
        df_finances,
        path=["Type", "Catégorie"],
        values="Montant",
        color="Type",
        color_discrete_map={
            "Recettes": CINEMATIC_COLORS["teal"],
            "Dépenses": CINEMATIC_COLORS["rose"]
        }
    )
    
    fig.update_traces(
        textinfo="label+value+percent parent",
        marker=dict(line=dict(color="rgba(255,255,255,0.15)", width=1.5)),
        hoverlabel=dict(bgcolor="#0B1329")
    )
    
    apply_cinematic_theme(fig, height=360, title=title)
    return fig


def create_trend_sparkline(df, x_col, y_col, title="Évolution Temporelle", color="cyan", threshold=None, unit=""):
    """
    Crée une courbe d'évolution néon fluide avec zone de gradient et ligne seuil optionnelle.
    """
    trace_color = CINEMATIC_COLORS.get(color, CINEMATIC_COLORS["cyan"])
    
    fig = go.Figure()
    
    # Courbe principale
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        line=dict(color=trace_color, width=3, shape='spline'),
        marker=dict(size=6, color=trace_color, line=dict(color='#FFFFFF', width=1)),
        fill='tozeroy',
        fillcolor='rgba(0, 242, 254, 0.08)' if color == 'cyan' else 'rgba(13, 148, 136, 0.08)',
        name=y_col,
        hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y:.1f}} {unit}<extra></extra>"
    ))
    
    # Seuil d'alerte optionnel
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color=CINEMATIC_COLORS["rose"],
            line_width=2,
            annotation_text=f"Seuil d'alerte ({threshold} {unit})",
            annotation_position="top right",
            annotation_font=dict(color=CINEMATIC_COLORS["rose"], size=11)
        )
        
    apply_cinematic_theme(fig, height=290, title=title)
    return fig


def create_bed_occupancy_chart(stats_lits=None, title="Taux d'Occupation des Lits"):
    """
    Barres cinématiques de répartition des lits d'hospitalisation par statut.
    """
    if not stats_lits:
        stats_lits = {
            "Disponibles": 14,
            "Occupés": 22,
            "Réservés": 5,
            "Maintenance": 2
        }
        
    labels = list(stats_lits.keys())
    values = list(stats_lits.values())
    colors = [
        CINEMATIC_COLORS["emerald"],
        CINEMATIC_COLORS["rose"],
        CINEMATIC_COLORS["amber"],
        CINEMATIC_COLORS["text_muted"]
    ]
    
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker=dict(
            color=colors,
            line=dict(color="rgba(255,255,255,0.15)", width=1.5)
        ),
        text=values,
        textposition="auto",
        textfont=dict(color="#FFFFFF", size=13, family="'Inter', sans-serif")
    )])
    
    apply_cinematic_theme(fig, height=300, title=title)
    return fig
