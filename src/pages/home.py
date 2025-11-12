"""page d’accueil dash : cartes, histogrammes et graphiques.
pylint: disable=too-many-lines
"""

from __future__ import annotations

from pathlib import Path
import sys
import json

import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# permettre l'import absolu de src.utils
sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
GEOJSON_PATH = ROOT / "departements-version-simplifiee.geojson"
COMMUNES_GEOJSON_PATH = ROOT / "communes.geojson"

# import absolu avec repli pour le lint
try:
    from src.utils.get_data import query_db  # type: ignore
except ImportError:  # pragma: no cover
    def query_db(*_args, **_kwargs):
        raise ImportError("src.utils.get_data introuvable")


# ============================================================================
# composants des pages
# ============================================================================

def _make_departments_choropleth():
    """carte choroplèthe par département."""
    try:
        with GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)

        sql = (
            "SELECT dep AS dept, COUNT(*) AS accidents "
            "FROM caracteristiques GROUP BY dep"
        )
        df = query_db(sql)

        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="aucune donnée disponible",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        df["dept"] = df["dept"].astype(str).str.zfill(2)

        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="dept",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale="Purples",
            title="accidentologie par département (france)",
            hover_name="dept",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=600,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            template="plotly_white",
        )
        return fig

    except (OSError, json.JSONDecodeError, ValueError) as err:
        print(f"erreur carte départements : {err}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"erreur : {str(err)[:100]}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig


def _make_communes_choropleth():
    """carte choroplèthe par commune."""
    try:
        if not COMMUNES_GEOJSON_PATH.exists():
            fig = go.Figure()
            fig.add_annotation(
                text="fichier communes.geojson non trouvé",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        with COMMUNES_GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)

        sql = (
            "SELECT com AS code_commune, COUNT(*) AS accidents "
            "FROM caracteristiques "
            "WHERE com IS NOT NULL "
            "GROUP BY com"
        )
        df = query_db(sql)

        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="aucune donnée de communes disponible",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)

        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="code_commune",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale="Reds",
            title="accidentologie par commune (france)",
            hover_name="code_commune",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=600,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            template="plotly_white",
        )
        return fig

    except (OSError, json.JSONDecodeError, ValueError) as err:
        print(f"erreur carte communes : {err}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"erreur : {str(err)[:100]}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig


def _make_speed_histogram(year=2023):
    """histogramme des écarts de vitesse."""
    try:
        if year == 2021:
            fig = go.Figure()
            fig.add_annotation(
                text="données 2021 non disponibles (à implémenter)",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font={"size": 16, "color": "#7f8c8d"},
            )
            return fig

        sql = (
            "SELECT (mesure - limite) AS delta_v "
            "FROM radars "
            "WHERE mesure IS NOT NULL AND limite IS NOT NULL "
            "LIMIT 10000"
        )
        df = query_db(sql)

        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="aucune donnée disponible",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        df["delta_v"] = pd.to_numeric(df["delta_v"], errors="coerce")
        df = df.dropna(subset=["delta_v"])
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="pas de données valides",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        def categorize_delta_v(value):
            if value < -20:
                return "très sous limite (-20 km/h)"
            if value < -10:
                return "sous limite (-10 à -20)"
            if value < 0:
                return "légèrement sous limite (-0 à -10)"
            if value == 0:
                return "à la limite (0 km/h)"
            if value <= 10:
                return "léger excès (0 à 10 km/h)"
            if value <= 20:
                return "excès modéré (10 à 20 km/h)"
            if value <= 30:
                return "excès important (20 à 30 km/h)"
            return "très gros excès (>30 km/h)"

        df["categorie"] = df["delta_v"].apply(categorize_delta_v)

        fig = px.histogram(
            df,
            x="delta_v",
            nbins=50,
            title=f"mesures radar — analyse des vitesses ({year})",
            labels={
                "delta_v": "écart de vitesse (km/h)",
                "count": "nombre de mesures",
            },
            color_discrete_sequence=["#667eea"],
            hover_data={"categorie": True},
        )

        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="#f093fb",
            line_width=3,
            annotation_text="limite de vitesse",
            annotation_position="top right",
            annotation_font_size=12,
            annotation_font_color="#f093fb",
        )
        fig.add_vrect(
            x0=-60, x1=0, fillcolor="#01d084", opacity=0.05, layer="below", line_width=0
        )
        fig.add_vrect(
            x0=0, x1=60, fillcolor="#ff6b6b", opacity=0.05, layer="below", line_width=0
        )

        fig.update_layout(
            height=550,
            bargap=0.02,
            template="plotly_white",
            title_font_size=18,
            title_x=0.5,
            title_font_color="#2c3e50",
            xaxis_title=(
                "écart de vitesse (km/h)"
                "<br><span style='font-size:11px; color:#7f8c8d'>"
                "négatif = respect limite | positif = excès"
                "</span>"
            ),
            yaxis_title="nombre de mesures",
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            hovermode="x unified",
            paper_bgcolor="white",
            plot_bgcolor="rgba(240, 248, 255, 0.3)",
            margin={"l": 80, "r": 80, "t": 100, "b": 80},
            font={
                "family": "'Segoe UI', Tahoma, Geneva, Verdana",
                "size": 12,
                "color": "#2c3e50",
            },
            showlegend=False,
        )
        fig.update_traces(
            marker_line_color="white",
            marker_line_width=1,
            marker_color="#667eea",
            hovertemplate=(
                "<b>écart:</b> %{x:.1f} km/h<br>"
                "<b>mesures:</b> %{y}<br>"
                "<extra></extra>"
            ),
        )
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="rgba(240, 147, 251, 0.3)",
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(200, 200, 200, 0.2)"
        )
        return fig

    except Exception as err:  # type: ignore[used-before-def]
        # garder large ici si la couche db renvoie des erreurs spécifiques
        print(f"erreur histogramme : {err}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"erreur: {str(err)[:100]}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig


def _make_accidents_by_day_line():
    """courbe : évolution du nombre d'accidents par heure."""
    try:
        sql = (
            "SELECT CAST(SUBSTR(heure, 1, 2) AS INTEGER) AS heure_num, "
            "COUNT(*) AS accidents "
            "FROM caracteristiques "
            "WHERE heure IS NOT NULL "
            "GROUP BY heure_num "
            "ORDER BY heure_num"
        )
        df = query_db(sql)

        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="aucune donnée disponible",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        df = df.sort_values(by="heure_num")
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="pas de données valides",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["heure_num"],
                y=df["accidents"],
                mode="lines+markers",
                name="accidents",
                line={"color": "#6b5bd3", "width": 4, "shape": "spline"},
                marker={
                    "size": 12,
                    "color": "#6b5bd3",
                    "symbol": "circle",
                    "line": {"color": "white", "width": 2},
                },
                fill="tozeroy",
                fillcolor="rgba(107, 91, 211, 0.15)",
                hovertemplate=(
                    "<b>heure %{x:.0f}h</b><br>accidents: <b>%{y}</b><extra></extra>"
                ),
            )
        )
        fig.update_layout(
            title={
                "text": "évolution du nombre d'accidents par heure",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": "#2c3e50", "family": "Arial, sans-serif"},
            },
            xaxis_title="heure (0-23)",
            yaxis_title="nombre d'accidents",
            height=550,
            margin={"l": 80, "r": 60, "t": 100, "b": 80},
            template="plotly_white",
            hovermode="x unified",
            plot_bgcolor="rgba(240, 248, 255, 0.3)",
            paper_bgcolor="white",
            font={"family": "Arial, sans-serif", "size": 12, "color": "#2c3e50"},
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

    except Exception as err:  # type: ignore[used-before-def]
        print(f"erreur courbe accidents/heure : {err}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"erreur: {str(err)[:100]}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig


def _make_accidents_pie_chart():
    """camembert : distribution des accidents par type d'agglomération."""
    try:
        sql = (
            "SELECT agg, COUNT(*) AS count "
            "FROM caracteristiques WHERE agg IS NOT NULL GROUP BY agg"
        )
        df = query_db(sql)

        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="aucune donnée disponible",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        agg_labels = {1: "agglomération", 2: "hors agglomération"}
        df["agg_label"] = df["agg"].map(agg_labels)
        df = df.sort_values(by="count", ascending=False)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df["agg_label"],
                    values=df["count"],
                    marker={
                        "colors": ["#6b5bd3", "#f093fb"],
                        "line": {"color": "white", "width": 2},
                    },
                    textposition="auto",
                    hovertemplate=(
                        "<b>%{label}</b><br>accidents: %{value}"
                        "<br>part: %{percent}<extra></extra>"
                    ),
                    textinfo="label+percent",
                    textfont={"size": 14, "color": "white", "family": "Arial, sans-serif"},
                )
            ]
        )
        fig.update_layout(
            title={
                "text": "distribution des accidents par agglomération",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#2c3e50", "family": "Arial, sans-serif"},
            },
            height=420,
            margin={"l": 20, "r": 20, "t": 80, "b": 20},
            font={"family": "Arial, sans-serif", "size": 12},
            paper_bgcolor="white",
            showlegend=True,
            legend={
                "x": 0.7,
                "y": 0.5,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "#ddd",
                "borderwidth": 1,
            },
        )
        return fig

    except Exception as err:  # type: ignore[used-before-def]
        print(f"erreur camembert accidents : {err}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"erreur: {str(err)[:100]}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig


# ============================================================================
# pages de contenu
# ============================================================================

about_page = html.Div(
    [
        html.H2(
            "à propos",
            style={
                "color": "#2c3e50",
                "borderBottom": "3px solid #3498db",
                "paddingBottom": "10px",
            },
        ),
        html.Div(
            [
                html.P(
                    (
                        "ce dashboard analyse les accidents de la circulation routière "
                        "et les vitesses relevées par radars en france (2023)."
                    ),
                    style={"fontSize": "16px", "lineHeight": "1.6"},
                ),
                html.P(
                    (
                        "les données proviennent de sources publiques (data.gouv.fr) "
                        "et permettent une visualisation complète de l’accidentologie."
                    ),
                    style={"fontSize": "16px", "lineHeight": "1.6"},
                ),
                html.P(
                    "sources : data.gouv.fr — données publiques",
                    style={"fontSize": "14px", "color": "#7f8c8d", "marginTop": "20px"},
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "24px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            },
        ),
    ]
)


def create_histogram_page(year=2023):
    """crée la page histogramme avec sélection d’année."""
    fig = _make_speed_histogram(year)

    active_btn = {
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
        "transition": "all 0.3s cubic-bezier(.25,.46,.45,.94)",
    }
    inactive_btn = {
        "padding": "12px 24px",
        "margin": "8px 0",
        "fontSize": "15px",
        "fontWeight": "600",
        "cursor": "pointer",
        "border": "2px solid #e8e8f0",
        "borderRadius": "6px",
        "backgroundColor": "#f5f5f8",
        "color": "#999",
        "transition": "all 0.3s cubic-bezier(.25,.46,.45,.94)",
    }

    style_2023 = active_btn if year == 2023 else inactive_btn
    style_2021 = active_btn if year == 2021 else inactive_btn

    return html.Div(
        [
            html.H2("distribution des écarts de vitesse"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                figure=fig,
                                config={"responsive": True, "displayModeBar": True},
                            ),
                        ],
                        style={
                            "backgroundColor": "white",
                            "padding": "28px",
                            "borderRadius": "12px",
                            "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.12)",
                            "flex": "1",
                            "minWidth": "0",
                            "borderTop": "4px solid #667eea",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                "année",
                                style={
                                    "fontSize": "15px",
                                    "fontWeight": "700",
                                    "color": "#2c3e50",
                                    "marginBottom": "20px",
                                    "textAlign": "center",
                                    "letterSpacing": "0.5px",
                                },
                            ),
                            html.Button("2023", id="btn-year-2023", n_clicks=0, style=style_2023),
                            html.Button("2021", id="btn-year-2021", n_clicks=0, style=style_2021),
                            html.Hr(style={"margin": "20px 0", "borderColor": "#e8e8f0"}),
                            html.Div(
                                "sélectionnez l’année",
                                style={
                                    "fontSize": "12px",
                                    "color": "#bbb",
                                    "textAlign": "center",
                                    "fontStyle": "italic",
                                },
                            ),
                        ],
                        style={
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
                        },
                    ),
                ],
                style={"display": "flex", "gap": "24px", "alignItems": "stretch", "width": "100%"},
            ),
        ]
    )


histogram_page = create_histogram_page(2023)


def create_choropleth_page(carte_mode="dept"):
    """crée la page choroplèthe dynamiquement."""
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
            "transition": "all 0.3s cubic-bezier(.25,.46,.45,.94)",
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
            "transition": "all 0.3s cubic-bezier(.25,.46,.45,.94)",
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
            "transition": "all 0.3s cubic-bezier(.25,.46,.45,.94)",
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
            "transition": "all 0.3s cubic-bezier(.25,.46,.45,.94)",
        }

    return html.Div(
        [
            html.H2("carte choroplèthe des accidents"),
            html.Div(
                [
                    html.Button("vue par département", id="btn-carte-dept", n_clicks=0, style=dept_style),
                    html.Button("vue par commune", id="btn-carte-commune", n_clicks=0, style=commune_style),
                ],
                style={
                    "textAlign": "center",
                    "marginBottom": "24px",
                    "display": "flex",
                    "justifyContent": "center",
                    "gap": "12px",
                },
            ),
            html.Div(
                [dcc.Graph(figure=fig, config={"responsive": True, "displayModeBar": True})],
                style={
                    "backgroundColor": "white",
                    "padding": "28px",
                    "borderRadius": "12px",
                    "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                    "borderTop": "4px solid #3498db",
                },
            ),
        ],
        id="choropleth-page-container",
    )


choropleth_page = create_choropleth_page("dept")

graph_page = html.Div(
    [
        html.H2("analyses temporelles — évolution des accidents"),
        html.Div(
            [
                html.H3(
                    "filtres",
                    style={
                        "fontSize": "16px",
                        "fontWeight": "700",
                        "color": "#2c3e50",
                        "marginBottom": "16px",
                        "borderBottom": "2px solid #6b5bd3",
                        "paddingBottom": "12px",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "sexe",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#2c3e50",
                                        "marginBottom": "6px",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="filter-sexe",
                                    options=[
                                        {"label": "tous", "value": "all"},
                                        {"label": "homme", "value": "H"},
                                        {"label": "femme", "value": "F"},
                                    ],
                                    value="all",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                            style={"flex": "1", "minWidth": "150px", "marginRight": "16px"},
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "année",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#2c3e50",
                                        "marginBottom": "6px",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="filter-annee",
                                    options=[
                                        {"label": "toutes", "value": "all"},
                                        {"label": "2023", "value": 2023},
                                    ],
                                    value="all",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                            style={"flex": "1", "minWidth": "150px", "marginRight": "16px"},
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "luminosité",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#2c3e50",
                                        "marginBottom": "6px",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="filter-luminosite",
                                    options=[
                                        {"label": "toutes", "value": "all"},
                                        {"label": "jour", "value": 1},
                                        {"label": "crépuscule/aube", "value": 2},
                                        {"label": "nuit", "value": 3},
                                        {"label": "nuit sans éclairage", "value": 4},
                                        {"label": "nuit avec éclairage", "value": 5},
                                    ],
                                    value="all",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                            style={"flex": "1", "minWidth": "150px", "marginRight": "16px"},
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "agglomération",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#2c3e50",
                                        "marginBottom": "6px",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="filter-agglomeration",
                                    options=[
                                        {"label": "tous", "value": "all"},
                                        {"label": "agglomération", "value": 1},
                                        {"label": "hors agglomération", "value": 2},
                                    ],
                                    value="all",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                            style={"flex": "1", "minWidth": "150px", "marginRight": "16px"},
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "département",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                        "color": "#2c3e50",
                                        "marginBottom": "6px",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="filter-departement",
                                    options=[{"label": "tous", "value": "all"}],
                                    value="all",
                                    style={"width": "100%"},
                                    clearable=False,
                                    disabled=True,
                                ),
                            ],
                            style={"flex": "1", "minWidth": "150px"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "gap": "16px",
                        "flexWrap": "wrap",
                        "alignItems": "flex-start",
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            "réinitialiser filtres",
                            id="btn-reset-filters",
                            n_clicks=0,
                            style={
                                "marginTop": "12px",
                                "padding": "8px 16px",
                                "backgroundColor": "#ecf0f1",
                                "border": "1px solid #bdc3c7",
                                "borderRadius": "4px",
                                "cursor": "pointer",
                                "fontSize": "13px",
                                "color": "#7f8c8d",
                                "transition": "all 0.2s",
                            },
                        )
                    ],
                    style={"marginTop": "12px"},
                ),
            ],
            style={
                "backgroundColor": "#f9f9fb",
                "padding": "20px",
                "borderRadius": "12px",
                "boxShadow": "0 2px 10px rgba(0,0,0,0.04)",
                "border": "1px solid #ecf0f1",
                "marginBottom": "28px",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            "courbe 1 — accidents par heure",
                            style={
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "color": "#2c3e50",
                                "marginBottom": "16px",
                                "borderLeft": "4px solid #6b5bd3",
                                "paddingLeft": "12px",
                            },
                        ),
                        dcc.Graph(
                            figure=_make_accidents_by_day_line(),
                            config={"responsive": True, "displayModeBar": True},
                        ),
                    ],
                    style={
                        "backgroundColor": "white",
                        "padding": "28px",
                        "borderRadius": "12px",
                        "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                        "borderTop": "4px solid #6b5bd3",
                        "width": "100%",
                    },
                )
            ],
            style={"marginBottom": "28px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            "courbe 2 — distribution par agglomération",
                            style={
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "color": "#2c3e50",
                                "marginBottom": "16px",
                                "borderLeft": "4px solid #f093fb",
                                "paddingLeft": "12px",
                            },
                        ),
                        dcc.Graph(
                            figure=_make_accidents_pie_chart(),
                            config={"responsive": True, "displayModeBar": True},
                        ),
                    ],
                    style={
                        "backgroundColor": "white",
                        "padding": "28px",
                        "borderRadius": "12px",
                        "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                        "borderTop": "4px solid #f093fb",
                        "flex": "1",
                        "minWidth": "45%",
                    },
                ),
                html.Div(
                    [
                        html.H3(
                            "courbe 3 — à venir",
                            style={
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "color": "#999",
                                "marginBottom": "16px",
                                "borderLeft": "4px solid #bdc3c7",
                                "paddingLeft": "12px",
                            },
                        ),
                        html.Div(
                            "nouvelle courbe à implémenter...",
                            style={
                                "height": "420px",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "color": "#bbb",
                                "fontSize": "16px",
                                "fontStyle": "italic",
                            },
                        ),
                    ],
                    style={
                        "backgroundColor": "#f9f9fb",
                        "padding": "28px",
                        "borderRadius": "12px",
                        "boxShadow": "0 2px 10px rgba(0,0,0,0.04)",
                        "borderTop": "4px solid #bdc3c7",
                        "border": "2px dashed #e8e8f0",
                        "flex": "1",
                        "minWidth": "45%",
                    },
                ),
            ],
            style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "width": "100%"},
        ),
        html.Div(style={"marginTop": "40px"}),
    ]
)

authors_page = html.Div(
    [
        html.H2("auteurs et crédits"),
        html.Div(
            [
                html.P(
                    "projet d’analyse d’accidentologie routière en france",
                    style={"fontSize": "16px", "lineHeight": "1.8", "fontWeight": "500"},
                ),
                html.P("2025", style={"fontSize": "16px", "color": "#667eea", "fontWeight": "600"}),
                html.Hr(style={"margin": "20px 0", "borderColor": "#ecf0f1"}),
                html.P(
                    "technologie",
                    style={"fontSize": "15px", "fontWeight": "700", "color": "#2c3e50", "marginTop": "20px"},
                ),
                html.P("développé avec dash, plotly et sqlite", style={"fontSize": "14px", "color": "#7f8c8d"}),
                html.P("données : data.gouv.fr", style={"fontSize": "14px", "color": "#7f8c8d", "marginTop": "15px"}),
            ],
            style={
                "backgroundColor": "white",
                "padding": "28px",
                "borderRadius": "12px",
                "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.12)",
                "borderTop": "4px solid #f093fb",
            },
        ),
    ]
)


# ============================================================================
# barre de navigation
# ============================================================================

def create_nav_button(label, button_id, active=False):
    """crée un bouton de navigation stylisé."""
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
        className="nav-button",
    )


navbar = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            "dashboard accidentologie",
                            style={"color": "white", "margin": "0 20px 0 0", "letterSpacing": "0.5px"},
                        )
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                html.Div(
                    [
                        create_nav_button("à propos", "btn-about"),
                        create_nav_button("histogramme", "btn-histogram"),
                        create_nav_button("carte", "btn-choropleth"),
                        create_nav_button("graphique", "btn-graph"),
                        create_nav_button("auteurs", "btn-authors"),
                    ],
                    style={"display": "flex", "justifyContent": "center", "gap": "10px", "flex": "1"},
                ),
                html.Div(style={"width": "120px"}),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "0 30px",
                "backgroundColor": "#6b5bd3",
                "minHeight": "75px",
                "boxShadow": "0 8px 32px rgba(0,0,0,0.15)",
            },
        )
    ],
    id="navbar",
    style={"position": "sticky", "top": "0", "zIndex": "1000"},
)


# ============================================================================
# layout principal avec callback
# ============================================================================

layout = html.Div(
    [
        navbar,
        html.Div(
            id="page-content",
            style={
                "padding": "40px 30px",
                "maxWidth": "1400px",
                "margin": "0 auto",
                "minHeight": "calc(100vh - 75px)",
            },
        ),
    ],
    style={
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "backgroundColor": "#efe6ff",
        "minHeight": "100vh",
    },
)


@callback(
    Output("page-content", "children"),
    [
        Input("btn-about", "n_clicks"),
        Input("btn-histogram", "n_clicks"),
        Input("btn-choropleth", "n_clicks"),
        Input("btn-graph", "n_clicks"),
        Input("btn-authors", "n_clicks"),
    ],
)
def display_page(_about_clicks, _hist_clicks, _chor_clicks, _graph_clicks, _auth_clicks):
    """affiche la page demandée selon le bouton cliqué."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return about_page

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    mapping = {
        "btn-about": about_page,
        "btn-histogram": histogram_page,
        "btn-choropleth": create_choropleth_page("dept"),
        "btn-graph": graph_page,
        "btn-authors": authors_page,
    }
    return mapping.get(button_id, about_page)


@callback(
    Output("page-content", "children", allow_duplicate=True),
    [Input("btn-carte-dept", "n_clicks"), Input("btn-carte-commune", "n_clicks")],
    prevent_initial_call=True,
)
def update_carte_view(_dept_clicks, _commune_clicks):
    """met à jour la vue de la carte."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_choropleth_page("dept")

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return create_choropleth_page("commune" if button_id == "btn-carte-commune" else "dept")


@callback(
    Output("page-content", "children", allow_duplicate=True),
    [Input("btn-year-2023", "n_clicks"), Input("btn-year-2021", "n_clicks")],
    prevent_initial_call=True,
)
def update_histogram_year(_year_2023_clicks, _year_2021_clicks):
    """met à jour l'histogramme selon l'année sélectionnée."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_histogram_page(2023)

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return create_histogram_page(2021 if button_id == "btn-year-2021" else 2023)
