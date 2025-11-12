"""
test
"""
from __future__ import annotations
import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
GEOJSON_PATH = ROOT / "departements-version-simplifiee.geojson"
COMMUNES_GEOJSON_PATH = ROOT / "communes.geojson"

try:
    from ..utils.get_data import query_db
except Exception:
    from src.utils.get_data import query_db


# ============================================================================
# Composants des pages
# ============================================================================

def _make_departments_choropleth():
    """Carte choroplèthe par département"""
    try:
        with GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)
        
        # Charger les données d'accidents par département
        sql = "SELECT dep AS dept, COUNT(*) AS accidents FROM caracteristiques GROUP BY dep"
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        df["dept"] = df["dept"].astype(str).str.zfill(2)
        
        # Construire la choroplèthe par département
        try:
            fig = px.choropleth(
                df,
                geojson=geojson,
                locations="dept",
                color="accidents",
                featureidkey="properties.code",
                projection="mercator",
                color_continuous_scale="Purples",
                title="Accidentologie par département (France)",
                hover_name="dept",
            )

            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                height=600,
                margin=dict(l=0, r=0, t=40, b=0),
                template="plotly_white",
            )

        except Exception as e:
            print(f"Erreur construction choroplethe départements: {e}")
            fig = go.Figure()
            fig.add_annotation(text=f"Erreur: {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

        dept_style = {
            "padding": "12px 24px",
            "margin": "0 8px",
            "fontSize": "14px",
            "fontWeight": "600",
            "cursor": "pointer",
            "border": "2px solid #3498db",
            "borderRadius": "6px",
            "backgroundColor": "#3498db",
            "color": "white",
            "boxShadow": "0 4px 12px rgba(52, 152, 219, 0.3)",
            "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        }
        commune_style = {
            "padding": "12px 24px",
            "margin": "0 8px",
            "fontSize": "14px",
            "fontWeight": "600",
            "cursor": "pointer",
            "border": "2px solid #bdc3c7",
            "borderRadius": "6px",
            "backgroundColor": "#ecf0f1",
            "color": "#7f8c8d",
            "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        }
        return fig
    except Exception as e:
        print(f"Erreur carte : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur : {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


def _make_communes_choropleth():
    """Carte choroplèthe par commune"""
    try:
        # Charger le GeoJSON communes
        if not COMMUNES_GEOJSON_PATH.exists():
            fig = go.Figure()
            fig.add_annotation(text="Fichier communes.geojson non trouvé", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        with COMMUNES_GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)
        
        # Charger les données d'accidents par commune
        sql = """
            SELECT com AS code_commune, COUNT(*) AS accidents 
            FROM caracteristiques 
            WHERE com IS NOT NULL 
            GROUP BY com
        """
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée de communes disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Normaliser les codes communes (5 chiffres)
        df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
        
        # Créer la choroplèthe
        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="code_commune",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale="Reds",
            title="Accidentologie par commune (France)",
            hover_name="code_commune",
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            template="plotly_white",
        )
        
        return fig
    
    except Exception as e:
        print(f"Erreur carte communes : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur : {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


def _make_speed_histogram(year=2023):
    """Histogramme des écarts de vitesse (delta_v)"""
    try:
        # Récupérer delta_v depuis la base de données
        # Note: Pour 2021, on affichera un message car les données ne sont pas encore chargées
        if year == 2021:
            fig = go.Figure()
            fig.add_annotation(
                text="Données 2021 non disponibles<br>(À implémenter)",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="#7f8c8d")
            )
            return fig
        
        sql = """
            SELECT (mesure - limite) AS delta_v 
            FROM radars 
            WHERE mesure IS NOT NULL AND limite IS NOT NULL
            LIMIT 10000
        """
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Convertir en numérique
        df["delta_v"] = pd.to_numeric(df["delta_v"], errors="coerce")
        df = df.dropna(subset=["delta_v"])
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Pas de données valides", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Créer des catégories pour le hover
        def categorize_delta_v(value):
            if value < -20:
                return "Très sous limite (-20 km/h)"
            elif value < -10:
                return "Sous limite (-10 à -20)"
            elif value < 0:
                return "Légèrement sous limite (-0 à -10)"
            elif value == 0:
                return "À la limite (0 km/h)"
            elif value <= 10:
                return "Léger excès (0 à 10 km/h)"
            elif value <= 20:
                return "Excès modéré (10 à 20 km/h)"
            elif value <= 30:
                return "Excès important (20 à 30 km/h)"
            else:
                return "Très gros excès (>30 km/h)"
        
        df["categorie"] = df["delta_v"].apply(categorize_delta_v)
        
        # Créer l'histogramme
        fig = px.histogram(
            df, 
            x="delta_v", 
            nbins=50,
            title=f"<b>Mesures radar - Analyse des vitesses ({year})</b>",
            labels={"delta_v": "<b>Écart de vitesse (km/h)</b>", "count": "<b>Nombre de mesures</b>"},
            color_discrete_sequence=["#667eea"],
            hover_data={"categorie": True},
        )
        
        # Ajouter une ligne verticale à delta_v = 0 (limite de vitesse)
        fig.add_vline(
            x=0, 
            line_dash="dash", 
            line_color="#f093fb", 
            line_width=3,
            annotation_text="<b>Limite de vitesse</b>",
            annotation_position="top right",
            annotation_font_size=12,
            annotation_font_color="#f093fb",
        )
        
        # Ajouter des annotations pour les zones
        fig.add_vrect(x0=-60, x1=0, fillcolor="#01d084", opacity=0.05, layer="below", line_width=0)
        fig.add_vrect(x0=0, x1=60, fillcolor="#ff6b6b", opacity=0.05, layer="below", line_width=0)
        
        # Améliorer l'apparence
        fig.update_layout(
            height=550,
            bargap=0.02,
            template="plotly_white",
            title_font_size=18,
            title_x=0.5,
            title_font_color="#2c3e50",
            xaxis_title="<b>Écart de vitesse (km/h)</b><br><span style='font-size:11px; color:#7f8c8d'>Négatif = respect limite  |  Positif = excès de vitesse</span>",
            yaxis_title="<b>Nombre de mesures</b>",
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            hovermode="x unified",
            paper_bgcolor="white",
            plot_bgcolor="rgba(240, 248, 255, 0.3)",
            margin=dict(l=80, r=80, t=100, b=80),
            font=dict(family="'Segoe UI', Tahoma, Geneva, Verdana", size=12, color="#2c3e50"),
            showlegend=False,
        )
        
        fig.update_traces(
            marker_line_color="white",
            marker_line_width=1,
            marker_color="#667eea",
            hovertemplate="<b>Écart:</b> %{x:.1f} km/h<br>" +
                         "<b>Mesures:</b> %{y}<br>" +
                         "<extra></extra>",
        )
        
        # Améliorer les axes
        fig.update_xaxes(
            showgrid=True, 
            gridwidth=1, 
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="rgba(240, 147, 251, 0.3)",
        )
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(200, 200, 200, 0.2)")
        
        return fig
    
    except Exception as e:
        print(f"Erreur histogramme : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur: {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


def _make_accidents_by_day_line():
    """Courbe — Évolution du nombre d'accidents par heure"""
    try:
        sql = """
            SELECT 
                CAST(SUBSTR(heure, 1, 2) AS INTEGER) AS heure_num,
                COUNT(*) AS accidents 
            FROM caracteristiques 
            WHERE heure IS NOT NULL 
            GROUP BY heure_num 
            ORDER BY heure_num
        """
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        df = df.sort_values(by="heure_num")
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Pas de données valides", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = go.Figure()
        
        # Ajouter la ligne avec lissage
        fig.add_trace(go.Scatter(
            x=df["heure_num"],
            y=df["accidents"],
            mode="lines+markers",
            name="Accidents",
            line=dict(color="#6b5bd3", width=4, shape="spline"),
            marker=dict(size=12, color="#6b5bd3", symbol="circle", line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor="rgba(107, 91, 211, 0.15)",
            hovertemplate="<b>Heure %{x:.0f}h</b><br>Accidents: <b>%{y}</b><extra></extra>",
        ))
        
        fig.update_layout(
            title={
                "text": "Évolution du nombre d'accidents par heure",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": "#2c3e50", "family": "Arial, sans-serif"}
            },
            xaxis_title="Heure (0-23)",
            yaxis_title="Nombre d'accidents",
            height=550,
            margin=dict(l=80, r=60, t=100, b=80),
            template="plotly_white",
            hovermode="x unified",
            plot_bgcolor="rgba(240, 248, 255, 0.3)",
            paper_bgcolor="white",
            font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
            showlegend=False,
        )
        
        fig.update_xaxes(
            tickmode="linear",
            dtick=1,
            range=[-0.5, 23.5],
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(200, 200, 200, 0.2)",
            showline=True,
            linewidth=2,
            linecolor="#ddd",
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(200, 200, 200, 0.2)",
            showline=True,
            linewidth=2,
            linecolor="#ddd",
        )
        
        return fig
    
    except Exception as e:
        print(f"Erreur courbe accidents/heure : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur: {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


def _make_accidents_pie_chart():
    """Camembert — Distribution des accidents par type d'agglomération"""
    try:
        sql = "SELECT agg, COUNT(*) AS count FROM caracteristiques WHERE agg IS NOT NULL GROUP BY agg"
        df = query_db(sql)
        
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Mapping des codes agglomération
        agg_labels = {
            1: "Agglomération",
            2: "Hors agglomération",
        }
        df["agg_label"] = df["agg"].map(agg_labels)
        df = df.sort_values(by="count", ascending=False)
        
        fig = go.Figure(data=[go.Pie(
            labels=df["agg_label"],
            values=df["count"],
            marker=dict(colors=["#6b5bd3", "#f093fb"], line=dict(color="white", width=2)),
            textposition="auto",
            hovertemplate="<b>%{label}</b><br>Accidents: %{value}<br>Part: %{percent}<extra></extra>",
            textinfo="label+percent",
            textfont=dict(size=14, color="white", family="Arial, sans-serif"),
        )])
        
        fig.update_layout(
            title={
                "text": "Distribution des accidents par agglomération",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#2c3e50", "family": "Arial, sans-serif"}
            },
            height=420,
            margin=dict(l=20, r=20, t=80, b=20),
            font=dict(family="Arial, sans-serif", size=12),
            paper_bgcolor="white",
            showlegend=True,
            legend=dict(x=0.7, y=0.5, bgcolor="rgba(255,255,255,0.8)", bordercolor="#ddd", borderwidth=1),
        )
        
        return fig
    
    except Exception as e:
        print(f"Erreur camembert accidents : {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur: {str(e)[:100]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


# ============================================================================
# Pages de contenu
# ============================================================================

about_page = html.Div([
    html.H2("À propos", style={"color": "#2c3e50", "borderBottom": "3px solid #3498db", "paddingBottom": "10px"}),
    html.Div([
        html.P("Ce dashboard analyse les accidents de la circulation routière et les vitesses relevées par radars en France (2023).", style={"fontSize": "16px", "lineHeight": "1.6"}),
        html.P("Les données proviennent de sources publiques (data.gouv.fr) et permettent une visualisation complète de l'accidentologie française.", style={"fontSize": "16px", "lineHeight": "1.6"}),
        html.P("Sources : data.gouv.fr - Données publiques", style={"fontSize": "14px", "color": "#7f8c8d", "marginTop": "20px"}),
    ], style={
        "backgroundColor": "white",
        "padding": "24px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    })
])
    
    
def create_histogram_page(year=2023):
    """Crée la page histogramme dynamiquement avec sélection d'année"""
    fig = _make_speed_histogram(year)
    
    # Styles des boutons
    style_2023 = {
        "padding": "12px 24px",
        "margin": "8px 0",
        "fontSize": "15px",
        "fontWeight": "600",
        "cursor": "pointer",
        "border": "2px solid #667eea",
        "borderRadius": "6px",
        "backgroundColor": "#667eea",
        "color": "white",
        "boxShadow": "0 4px 15px rgba(102, 126, 234, 0.4)",
        "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    } if year == 2023 else {
        "padding": "12px 24px",
        "margin": "8px 0",
        "fontSize": "15px",
        "fontWeight": "600",
        "cursor": "pointer",
        "border": "2px solid #e8e8f0",
        "borderRadius": "6px",
        "backgroundColor": "#f5f5f8",
        "color": "#999",
        "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    }
    
    style_2021 = {
        "padding": "12px 24px",
        "margin": "8px 0",
        "fontSize": "15px",
        "fontWeight": "600",
        "cursor": "pointer",
        "border": "2px solid #667eea",
        "borderRadius": "6px",
        "backgroundColor": "#667eea",
        "color": "white",
        "boxShadow": "0 4px 15px rgba(102, 126, 234, 0.4)",
        "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    } if year == 2021 else {
        "padding": "12px 24px",
        "margin": "8px 0",
        "fontSize": "15px",
        "fontWeight": "600",
        "cursor": "pointer",
        "border": "2px solid #e8e8f0",
        "borderRadius": "6px",
        "backgroundColor": "#f5f5f8",
        "color": "#999",
        "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    }
    
    return html.Div([
        html.H2("📊 Distribution des écarts de vitesse"),
        
        # Conteneur flex pour le graphique et les boutons
        html.Div([
            # Graphique (gauche)
            html.Div([
                dcc.Graph(figure=fig, config={"responsive": True, "displayModeBar": True}),
            ], style={
                "backgroundColor": "white",
                "padding": "28px",
                "borderRadius": "12px",
                "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.12)",
                "flex": "1",
                "minWidth": "0",
                "borderTop": "4px solid #667eea",
            }),
            
            # Boutons d'année (droite)
            html.Div([
                html.Div(
                    "📅 Année",
                    style={
                        "fontSize": "15px",
                        "fontWeight": "700",
                        "color": "#2c3e50",
                        "marginBottom": "20px",
                        "textAlign": "center",
                        "letterSpacing": "0.5px",
                    }
                ),
                html.Button(
                    "2023",
                    id="btn-year-2023",
                    n_clicks=0,
                    style=style_2023
                ),
                html.Button(
                    "2021",
                    id="btn-year-2021",
                    n_clicks=0,
                    style=style_2021
                ),
                html.Hr(style={"margin": "20px 0", "borderColor": "#e8e8f0"}),
                html.Div(
                    "✓ Sélectionnez l'année",
                    style={
                        "fontSize": "12px",
                        "color": "#bbb",
                        "textAlign": "center",
                        "fontStyle": "italic",
                    }
                ),
            ], style={
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "flex-start",
                "width": "160px",
                "marginLeft": "24px",
                "padding": "28px 20px",
                "backgroundColor": "#f8f9fc",
                "borderRadius": "12px",
                "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.08)",
                "borderTop": "4px solid #f093fb",
            })
        ], style={
            "display": "flex",
            "gap": "24px",
            "alignItems": "stretch",
            "width": "100%",
        })
    ])

histogram_page = create_histogram_page(2023)

def create_choropleth_page(carte_mode="dept"):
    """Crée la page choroplèthe dynamiquement"""
    if carte_mode == "commune":
        fig = _make_communes_choropleth()
        dept_style = {
            "padding": "12px 24px",
            "margin": "0 8px",
            "fontSize": "14px",
            "fontWeight": "600",
            "cursor": "pointer",
            "border": "2px solid #bdc3c7",
            "borderRadius": "6px",
            "backgroundColor": "#ecf0f1",
            "color": "#7f8c8d",
            "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        }
        commune_style = {
            "padding": "12px 24px",
            "margin": "0 8px",
            "fontSize": "14px",
            "fontWeight": "600",
            "cursor": "pointer",
            "border": "2px solid #3498db",
            "borderRadius": "6px",
            "backgroundColor": "#3498db",
            "color": "white",
            "boxShadow": "0 4px 12px rgba(52, 152, 219, 0.3)",
            "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        }
    else:
        fig = _make_departments_choropleth()
        dept_style = {
            "padding": "12px 24px",
            "margin": "0 8px",
            "fontSize": "14px",
            "fontWeight": "600",
            "cursor": "pointer",
            "border": "2px solid #3498db",
            "borderRadius": "6px",
            "backgroundColor": "#3498db",
            "color": "white",
            "boxShadow": "0 4px 12px rgba(52, 152, 219, 0.3)",
            "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        }
        commune_style = {
            "padding": "12px 24px",
            "margin": "0 8px",
            "fontSize": "14px",
            "fontWeight": "600",
            "cursor": "pointer",
            "border": "2px solid #bdc3c7",
            "borderRadius": "6px",
            "backgroundColor": "#ecf0f1",
            "color": "#7f8c8d",
            "transition": "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        }
    
    return html.Div([
        html.H2("🗺️ Carte choroplèthe des accidents"),
        # Boutons de sélection
        html.Div([
            html.Button(
                "Vue par Département",
                id="btn-carte-dept",
                n_clicks=0,
                style=dept_style
            ),
            html.Button(
                "Vue par Commune",
                id="btn-carte-commune",
                n_clicks=0,
                style=commune_style
            ),
        ], style={
            "textAlign": "center", 
            "marginBottom": "24px",
            "display": "flex",
            "justifyContent": "center",
            "gap": "12px",
        }),
        # Carte affichée
        html.Div([
            dcc.Graph(figure=fig, config={"responsive": True, "displayModeBar": True}),
        ], style={
            "backgroundColor": "white",
            "padding": "28px",
            "borderRadius": "12px",
            "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
            "borderTop": "4px solid #3498db",
        })
    ], id="choropleth-page-container")

choropleth_page = create_choropleth_page("dept")

graph_page = html.Div([
    html.H2("📈 Analyses Temporelles — Évolution des Accidents"),
    
    # Ligne 1 : Line chart (fullwidth)
    html.Div([
        html.Div([
            html.H3("Courbe 1 — Accidents par heure", style={
                "fontSize": "16px",
                "fontWeight": "600",
                "color": "#2c3e50",
                "marginBottom": "16px",
                "borderLeft": "4px solid #6b5bd3",
                "paddingLeft": "12px",
            }),
            dcc.Graph(figure=_make_accidents_by_day_line(), config={"responsive": True, "displayModeBar": True}),
        ], style={
            "backgroundColor": "white",
            "padding": "28px",
            "borderRadius": "12px",
            "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
            "borderTop": "4px solid #6b5bd3",
            "width": "100%",
        }),
    ], style={
        "marginBottom": "28px",
    }),
    
    # Ligne 2 : Camembert (50%) + Placeholder (50%)
    html.Div([
        # Camembert (gauche)
        html.Div([
            html.H3("Courbe 2 — Distribution par agglomération", style={
                "fontSize": "16px",
                "fontWeight": "600",
                "color": "#2c3e50",
                "marginBottom": "16px",
                "borderLeft": "4px solid #f093fb",
                "paddingLeft": "12px",
            }),
            dcc.Graph(figure=_make_accidents_pie_chart(), config={"responsive": True, "displayModeBar": True}),
        ], style={
            "backgroundColor": "white",
            "padding": "28px",
            "borderRadius": "12px",
            "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
            "borderTop": "4px solid #f093fb",
            "flex": "1",
            "minWidth": "45%",
        }),
        
        # Placeholder (droite)
        html.Div([
            html.H3("Courbe 3 — À venir", style={
                "fontSize": "16px",
                "fontWeight": "600",
                "color": "#999",
                "marginBottom": "16px",
                "borderLeft": "4px solid #bdc3c7",
                "paddingLeft": "12px",
            }),
            html.Div(
                "Nouvelle courbe à implémenter...",
                style={
                    "height": "420px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "color": "#bbb",
                    "fontSize": "16px",
                    "fontStyle": "italic",
                }
            ),
        ], style={
            "backgroundColor": "#f9f9fb",
            "padding": "28px",
            "borderRadius": "12px",
            "boxShadow": "0 2px 10px rgba(0,0,0,0.04)",
            "borderTop": "4px solid #bdc3c7",
            "border": "2px dashed #e8e8f0",
            "flex": "1",
            "minWidth": "45%",
        }),
    ], style={
        "display": "flex",
        "gap": "24px",
        "flexWrap": "wrap",
        "width": "100%",
    }),
    
    # Espace pour courbes supplémentaires
    html.Div(style={"marginTop": "40px"}),
])

authors_page = html.Div([
    html.H2("👥 Auteurs & Crédits"),
    html.Div([
        html.P("Projet d'analyse d'accidentologie routière en France", style={"fontSize": "16px", "lineHeight": "1.8", "fontWeight": "500"}),
        html.P("2025", style={"fontSize": "16px", "color": "#667eea", "fontWeight": "600"}),
        html.Hr(style={"margin": "20px 0", "borderColor": "#ecf0f1"}),
        html.P("📚 Technologie", style={"fontSize": "15px", "fontWeight": "700", "color": "#2c3e50", "marginTop": "20px"}),
        html.P("Développé avec Dash, Plotly et SQLite", style={"fontSize": "14px", "color": "#7f8c8d"}),
        html.P("Données : data.gouv.fr", style={"fontSize": "14px", "color": "#7f8c8d", "marginTop": "15px"}),
    ], style={
        "backgroundColor": "white",
        "padding": "28px",
        "borderRadius": "12px",
        "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.12)",
        "borderTop": "4px solid #f093fb",
    })
])


# ============================================================================
# Barre de navigation
# ============================================================================

def create_nav_button(label, button_id, active=False):
    """Crée un bouton de navigation stylisé"""
    return html.Button(
        label,
        id=button_id,
        n_clicks=0,
        style={
            "padding": "12px 24px",
            "margin": "0 5px",
            "fontSize": "15px",
            "fontWeight": "500",
            "cursor": "pointer",
            "border": "none",
            "borderRadius": "4px",
            "backgroundColor": "#3498db" if active else "transparent",
            "color": "white",
            "transition": "all 0.3s ease",
        },
        className="nav-button"
    )

navbar = html.Div([
    html.Div([
        html.Div([
            html.H3("📊 Dashboard Accidentologie", style={"color": "white", "margin": "0 20px 0 0", "letterSpacing": "0.5px"}),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            create_nav_button("À Propos", "btn-about"),
            create_nav_button("Histogramme", "btn-histogram"),
            create_nav_button("Carte", "btn-choropleth"),
            create_nav_button("Graphique", "btn-graph"),
            create_nav_button("Auteurs", "btn-authors"),
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "gap": "10px",
            "flex": "1",
        }),
        html.Div(style={"width": "120px"}),  # Espace pour équilibre
      ], style={
      "display": "flex",
      "justifyContent": "space-between",
      "alignItems": "center",
      "padding": "0 30px",
          "backgroundColor": "#6b5bd3",
      "minHeight": "75px",
      "boxShadow": "0 8px 32px rgba(0,0,0,0.15)",
    })
], id="navbar", style={
    "position": "sticky",
    "top": "0",
    "zIndex": "1000",
})


# ============================================================================
# Layout principal avec callback
# ============================================================================

layout = html.Div([
    navbar,
    html.Div(id="page-content", style={
        "padding": "40px 30px",
        "maxWidth": "1400px",
        "margin": "0 auto",
        "minHeight": "calc(100vh - 75px)",
    }),
], style={
    "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
         "backgroundColor": "#efe6ff",
    "minHeight": "100vh",
})


# Callback pour afficher le contenu de la page
@callback(
    Output("page-content", "children"),
    [
        Input("btn-about", "n_clicks"),
        Input("btn-histogram", "n_clicks"),
        Input("btn-choropleth", "n_clicks"),
        Input("btn-graph", "n_clicks"),
        Input("btn-authors", "n_clicks"),
    ]
)
def display_page(about_clicks, hist_clicks, chor_clicks, graph_clicks, auth_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return about_page
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "btn-about":
        return about_page
    elif button_id == "btn-histogram":
        return histogram_page
    elif button_id == "btn-choropleth":
        return create_choropleth_page("dept")
    elif button_id == "btn-graph":
        return graph_page
    elif button_id == "btn-authors":
        return authors_page
    
    return about_page


# Callback pour les boutons de sélection de carte (utilisé via JavaScript)
# Ce callback ne s'exécute que quand les boutons existent dans le DOM
@callback(
    Output("page-content", "children", allow_duplicate=True),
    [
        Input("btn-carte-dept", "n_clicks"),
        Input("btn-carte-commune", "n_clicks"),
    ],
    prevent_initial_call=True,
    allow_duplicate=True
)
def update_carte_view(dept_clicks, commune_clicks):
    """Met à jour la vue de la carte"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return create_choropleth_page("dept")
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "btn-carte-commune":
        return create_choropleth_page("commune")
    else:
        return create_choropleth_page("dept")


# Callback pour les boutons de sélection d'année dans l'histogramme
@callback(
    Output("page-content", "children", allow_duplicate=True),
    [
        Input("btn-year-2023", "n_clicks"),
        Input("btn-year-2021", "n_clicks"),
    ],
    prevent_initial_call=True,
    allow_duplicate=True
)
def update_histogram_year(year_2023_clicks, year_2021_clicks):
    """Met à jour l'histogramme selon l'année sélectionnée"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return create_histogram_page(2023)
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "btn-year-2021":
        return create_histogram_page(2021)
    else:
        return create_histogram_page(2023)