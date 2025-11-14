"""page d’accueil dash : cartes, histogrammes et graphiques.
pylint: disable=too-many-lines
"""

from __future__ import annotations

from pathlib import Path
import sys
import json
import re

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
# utilitaires dynamiques
# ============================================================================

def _available_years() -> list[int]:
    """Retourne la liste des années disponibles selon les tables 'caracteristiques_YYYY'."""
    try:
        df = query_db(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'caracteristiques_%'"
        )
        years: list[int] = []
        for name in df["name"] if "name" in df.columns else []:  # type: ignore
            m = re.match(r"caracteristiques_(\d{4})$", str(name))
            if m:
                years.append(int(m.group(1)))
        years = sorted(set(years))
        return years if years else [2023, 2021]
    except Exception:
        return [2023, 2021]


def _available_radar_years() -> list[int]:
    """Retourne la liste des années avec données radars disponibles."""
    try:
        df = query_db(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'radars_%'"
        )
        years: list[int] = []
        for name in df["name"] if "name" in df.columns else []:  # type: ignore
            m = re.match(r"radars_(\d{4})$", str(name))
            if m:
                years.append(int(m.group(1)))
        years = sorted(set(years))
        return years if years else [2023, 2021]
    except Exception:
        return [2023, 2021]


def _compute_radar_delta_bounds() -> tuple[float, float]:
    """Calcule une plage x commune (symétrique autour de 0) pour les histogrammes.

    Objectif: conserver la même position de 0 lors du changement d'année.
    """
    try:
        years = _available_radar_years()
        mins: list[float] = []
        maxs: list[float] = []
        for y in years:
            table = f"radars_{y}"
            sql = (
                f"SELECT MIN(mesure - limite) AS min_d, MAX(mesure - limite) AS max_d "
                f"FROM {table} WHERE mesure IS NOT NULL AND limite IS NOT NULL"
            )
            df = query_db(sql)
            if df is not None and not df.empty:
                min_d = df.iloc[0].get("min_d")
                max_d = df.iloc[0].get("max_d")
                if pd.notna(min_d):
                    mins.append(float(min_d))
                if pd.notna(max_d):
                    maxs.append(float(max_d))

        if mins and maxs:
            lo = min(mins)
            hi = max(maxs)
            max_abs = max(abs(lo), abs(hi))
            # borne de sécurité pour éviter des outliers extrêmes
            max_abs = float(min(max_abs, 120.0))
            # arrondir à la dizaine supérieure pour plus de stabilité visuelle
            max_abs = float((int(max_abs + 9) // 10) * 10)
            max_abs = max(20.0, max_abs)
            return (-max_abs, max_abs)
        return (-60.0, 60.0)
    except Exception:
        return (-60.0, 60.0)


# ============================================================================
# composants des pages
# ============================================================================

def _make_departments_choropleth(year=2023):
    """carte choroplèthe par département."""
    try:
        with GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)

        table_name = f"caracteristiques_{year}"
        sql = (
            f"SELECT dep AS dept, COUNT(*) AS accidents "
            f"FROM {table_name} GROUP BY dep"
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
            color_continuous_scale=[[0, "#1a2035"], [0.5, "#3ae7ff"], [1, "#ff57c2"]],
            title="ACCIDENTOLOGIE PAR DÉPARTEMENT (FRANCE)",
            hover_name="dept",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=600,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            template="plotly_dark",
            paper_bgcolor="#181d31",
            plot_bgcolor="#14192a",
            font={"color": "#e6e9f2"},
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


def _make_communes_choropleth(year=2023):
    """carte choroplèthe par commune (gère les arrondissements)."""
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

        table_name = f"caracteristiques_{year}"
        sql = (
            f"SELECT com AS code_commune, COUNT(*) AS accidents "
            f"FROM {table_name} "
            f"WHERE com IS NOT NULL "
            f"GROUP BY com"
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

        # Convertir code commune en string et padding
        df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
        
        # Mapping des arrondissements vers codes INSEE commune
        # Paris: 75101-75120 -> 75056
        # Lyon: 69381-69389 -> 69123
        # Marseille: 13201-13216 -> 13055
        arrondissement_map = {}
        for i in range(1, 21):  # Paris 20 arrondissements
            arrondissement_map[f"751{i:02d}"] = "75056"
        for i in range(1, 10):  # Lyon 9 arrondissements
            arrondissement_map[f"6938{i}"] = "69123"
        for i in range(1, 17):  # Marseille 16 arrondissements
            arrondissement_map[f"132{i:02d}"] = "13055"
        
        # Appliquer le mapping
        df["code_commune"] = df["code_commune"].apply(
            lambda x: arrondissement_map.get(x, x)
        )
        
        # Agréger les accidents après transformation (pour grouper les arrondissements)
        df = df.groupby("code_commune", as_index=False).agg({"accidents": "sum"})

        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="code_commune",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale=[[0, "#1a2035"], [0.5, "#3ae7ff"], [1, "#ff57c2"]],
            title="ACCIDENTOLOGIE PAR COMMUNE (FRANCE)",
            hover_name="code_commune",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        # enlever les contours des communes pour n'afficher que les couleurs
        fig.update_traces(marker_line_width=0, marker_line_color="rgba(0,0,0,0)")
        fig.update_layout(
            height=600,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            template="plotly_dark",
            paper_bgcolor="#181d31",
            plot_bgcolor="#14192a",
            font={"color": "#e6e9f2"},
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
        table_name = f"radars_{year}"
        
        sql = (
            f"SELECT (mesure - limite) AS delta_v "
            f"FROM {table_name} "
            f"WHERE mesure IS NOT NULL AND limite IS NOT NULL "
            f"LIMIT 10000"
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

        # plage x symétrique autour de 0 calculée rapidement depuis le dataframe courant
        try:
            min_v = float(df["delta_v"].min())
            max_v = float(df["delta_v"].max())
            max_abs = max(abs(min_v), abs(max_v))
            max_abs = min(max_abs, 120.0)
            max_abs = float((int(max_abs + 9) // 10) * 10)  # arrondi dizaine sup
            max_abs = max(20.0, max_abs)
            x_lo, x_hi = -max_abs, max_abs
        except Exception:
            x_lo, x_hi = -60.0, 60.0

        fig = px.histogram(
            df,
            x="delta_v",
            nbins=50,
            title=f"MESURES RADAR — ANALYSE DES VITESSES ({year})",
            labels={
                "delta_v": "écart de vitesse (km/h)",
                "count": "nombre de mesures",
            },
            color_discrete_sequence=["#3ae7ff"],
            hover_data={"categorie": True},
        )

        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="#ff57c2",
            line_width=3,
            annotation_text="limite de vitesse",
            annotation_position="top right",
            annotation_font_size=12,
            annotation_font_color="#f093fb",
        )
        fig.add_vrect(x0=x_lo, x1=0, fillcolor="#01d084", opacity=0.05, layer="below", line_width=0)
        fig.add_vrect(x0=0, x1=x_hi, fillcolor="#ff6b6b", opacity=0.05, layer="below", line_width=0)

        fig.update_layout(
            height=550,
            bargap=0.02,
            template="plotly_dark",
            title_font_size=18,
            title_x=0.5,
            title_font_color="#e6e9f2",
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
            paper_bgcolor="#181d31",
            plot_bgcolor="#14192a",
            margin={"l": 80, "r": 80, "t": 100, "b": 80},
            font={
                "family": "'Segoe UI', Tahoma, Geneva, Verdana",
                "size": 12,
                "color": "#e6e9f2",
            },
            showlegend=False,
        )
        fig.update_traces(
            marker_line_color="#0e111b",
            marker_line_width=1,
            marker_color="#3ae7ff",
            hovertemplate=(
                "<b>écart:</b> %{x:.1f} km/h<br>"
                "<b>mesures:</b> %{y}<br>"
                "<extra></extra>"
            ),
        )
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255, 255, 255, 0.06)",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="rgba(255, 87, 194, 0.35)",
            range=[x_lo, x_hi],
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(255, 255, 255, 0.06)"
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


def _make_time_series(year=2023, agg_filter: int | str | None = None, unit: str = "hour"):
    """courbe : évolution du nombre d'accidents par heure/jour/mois.

    unit: "hour" | "day" | "month"
    year: 2021 | 2023 | "all" pour agréger plusieurs années.
    agg_filter: 1 (agglomération) | 2 (hors agglomération) | None
    """
    try:
        unit = unit or "hour"
        unit = unit.lower()

        def _query_one(y: int) -> pd.DataFrame:
            table_name = f"caracteristiques_{y}"
            params: dict = {}
            where_parts = []

            if unit == "hour":
                select_x = "CAST(SUBSTR(heure,1,2) AS INTEGER) AS x"
                where_parts.append("heure IS NOT NULL")
            elif unit == "day":
                select_x = "CAST(jour AS INTEGER) AS x"
                where_parts.append("jour IS NOT NULL")
            else:  # month
                select_x = "CAST(mois AS INTEGER) AS x"
                where_parts.append("mois IS NOT NULL")

            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter

            where_clause = " AND ".join(where_parts) if where_parts else "1=1"
            sql = (
                f"SELECT {select_x}, COUNT(*) AS accidents "
                f"FROM {table_name} WHERE {where_clause} "
                f"GROUP BY x ORDER BY x"
            )
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            parts = [
                _query_one(y) for y in _available_years()
            ]
            parts = [p for p in parts if p is not None and not p.empty]
            if parts:
                df = pd.concat(parts, ignore_index=True).groupby("x", as_index=False).agg({"accidents": "sum"})
            else:
                df = pd.DataFrame(columns=["x", "accidents"])  # empty
        else:
            df = _query_one(int(year))

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

        df = df.sort_values(by="x")
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

        title_map = {
            "hour": "évolution du nombre d'accidents par heure",
            "day": "évolution du nombre d'accidents par jour",
            "month": "évolution du nombre d'accidents par mois",
        }
        x_title_map = {
            "hour": "heure (0-23)",
            "day": "jour (1-31)",
            "month": "mois (1-12)",
        }
        x_range_map = {
            "hour": [-0.5, 23.5],
            "day": [0.5, 31.5],
            "month": [0.5, 12.5],
        }

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["x"],
                y=df["accidents"],
                mode="lines+markers",
                name="accidents",
                line={"color": "#3ae7ff", "width": 4, "shape": "spline"},
                marker={
                    "size": 10,
                    "color": "#3ae7ff",
                    "symbol": "circle",
                    "line": {"color": "#0e111b", "width": 1},
                },
                fill="tozeroy",
                fillcolor="rgba(58, 231, 255, 0.15)",
                hovertemplate=(
                    "<b>%{x}</b><br>accidents: <b>%{y}</b><extra></extra>"
                ),
            )
        )
        fig.update_layout(
            title={
                "text": title_map.get(unit, title_map["hour"]),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": "#e6e9f2", "family": "Arial, sans-serif"},
            },
            xaxis_title=x_title_map.get(unit, x_title_map["hour"]),
            yaxis_title="nombre d'accidents",
            height=550,
            margin={"l": 80, "r": 60, "t": 100, "b": 80},
            template="plotly_dark",
            hovermode="x unified",
            plot_bgcolor="#14192a",
            paper_bgcolor="#181d31",
            font={"family": "Arial, sans-serif", "size": 12, "color": "#e6e9f2"},
            showlegend=False,
        )
        fig.update_xaxes(
            tickmode="linear",
            dtick=1,
            range=x_range_map.get(unit, x_range_map["hour"]),
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
        print(f"erreur courbe temporelle : {err}")
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


def _make_accidents_pie_chart(year=2023, agg_filter: int | str | None = None):
    """camembert : distribution des accidents par type d'agglomération.

    year: 2021 | 2023 | "all" pour agréger les deux années.
    agg_filter: 1 (agglomération) | 2 (hors agglomération) | "all" | None.
    """
    try:
        def _query_one(y: int) -> pd.DataFrame:
            table_name = f"caracteristiques_{y}"
            where_parts = ["agg IS NOT NULL"]
            params = {}
            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter
            where_clause = " AND ".join(where_parts)
            sql = (
                f"SELECT agg, COUNT(*) AS count "
                f"FROM {table_name} WHERE {where_clause} GROUP BY agg"
            )
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            df1 = _query_one(2021)
            df2 = _query_one(2023)
            df = pd.concat([df1, df2], ignore_index=True)
            df = df.groupby("agg", as_index=False).agg({"count": "sum"})
        else:
            df = _query_one(int(year))

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
                        "colors": ["#3ae7ff", "#ff57c2"],
                        "line": {"color": "#0e111b", "width": 2},
                    },
                    textposition="auto",
                    hovertemplate=(
                        "<b>%{label}</b><br>accidents: %{value}"
                        "<br>part: %{percent}<extra></extra>"
                    ),
                    textinfo="label+percent",
                    textfont={"size": 14, "color": "#e6e9f2", "family": "Arial, sans-serif"},
                )
            ]
        )
        fig.update_layout(
            title={
                "text": "DISTRIBUTION DES ACCIDENTS PAR AGGLOMÉRATION",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#e6e9f2", "family": "Arial, sans-serif"},
            },
            height=420,
            margin={"l": 20, "r": 20, "t": 80, "b": 20},
            font={"family": "Arial, sans-serif", "size": 12, "color": "#e6e9f2"},
            paper_bgcolor="#181d31",
            plot_bgcolor="#14192a",
            showlegend=True,
            legend={
                "x": 0.7,
                "y": 0.5,
                "bgcolor": "rgba(14,17,27,0.6)",
                "bordercolor": "#2b3150",
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
            className="page-card",
            style={"padding": "24px"},
        ),
    ]
)


def create_histogram_page(year=2023):
    """crée la page histogramme avec sélection d’année (barre à gauche)."""
    fig = _make_speed_histogram(year)

    base_btn = {
        "padding": "12px 16px",
        "fontSize": "14px",
        "fontWeight": "700",
        "cursor": "pointer",
        "borderRadius": "10px",
        "border": "1px solid var(--border)",
        "backgroundColor": "#1a2035",
        "color": "#b9bfd3",
        "textAlign": "center",
        "boxShadow": "0 6px 20px rgba(0,0,0,0.25)",
        "margin": "6px 0",
    }
    active_btn = {
        **base_btn,
        "backgroundColor": "#3ae7ff",
        "color": "#0e111b",
        "border": "1px solid rgba(58,231,255,0.9)",
        "boxShadow": "0 0 10px rgba(58,231,255,0.55)",
    }
    inactive_btn = base_btn

    radar_years = sorted(_available_radar_years(), reverse=True)
    year_buttons = [
        html.Button(
            str(y),
            id=f"btn-year-{y}",
            n_clicks=0,
            style=active_btn if y == year else inactive_btn,
        )
        for y in radar_years
    ]

    return html.Div(
        [
            html.H2("distribution des écarts de vitesse"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "année",
                                style={
                                    "fontSize": "12px",
                                    "color": "var(--text-300)",
                                    "marginBottom": "8px",
                                },
                            ),
                            *year_buttons,
                            html.Hr(style={"margin": "16px 0"}),
                        ],
                        className="page-card",
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "justifyContent": "flex-start",
                            "width": "200px",
                            "marginRight": "24px",
                            "padding": "20px 16px",
                            "position": "sticky",
                            "top": "100px",
                            "alignSelf": "flex-start",
                        },
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                figure=fig,
                                config={"responsive": True, "displayModeBar": True},
                            ),
                        ],
                        className="page-card",
                        style={
                            "padding": "28px",
                            "flex": "1",
                            "minWidth": "0",
                        },
                    ),
                ],
                style={"display": "flex", "gap": "24px", "alignItems": "stretch", "width": "100%"},
            ),
        ]
    )


histogram_page = create_histogram_page()


def create_choropleth_page(carte_mode="dept", year=2023):
    """crée la page choroplèthe avec une barre latérale à gauche."""
    # figure selon le mode
    fig = _make_communes_choropleth(year) if carte_mode == "commune" else _make_departments_choropleth(year)

    # palette et styles boutons (dark + néon)
    base_btn = {
        "padding": "12px 16px",
        "fontSize": "14px",
        "fontWeight": "700",
        "cursor": "pointer",
        "borderRadius": "10px",
        "border": "1px solid var(--border)",
        "backgroundColor": "#1a2035",
        "color": "#b9bfd3",
        "textAlign": "center",
        "boxShadow": "0 6px 20px rgba(0,0,0,0.25)",
    }
    dept_active = {
        **base_btn,
        "backgroundColor": "#7b5cff",
        "color": "white",
        "boxShadow": "0 0 10px rgba(123,92,255,0.6)",
        "border": "1px solid rgba(123,92,255,0.8)",
    }
    commune_active = {
        **base_btn,
        "backgroundColor": "#ff57c2",
        "color": "white",
        "boxShadow": "0 0 10px rgba(255,87,194,0.6)",
        "border": "1px solid rgba(255,87,194,0.8)",
    }
    dept_style = dept_active if carte_mode == "dept" else base_btn
    commune_style = commune_active if carte_mode == "commune" else base_btn

    active_year_style = {
        **base_btn,
        "backgroundColor": "#3ae7ff",
        "color": "#0e111b",
        "border": "1px solid rgba(58,231,255,0.9)",
        "boxShadow": "0 0 10px rgba(58,231,255,0.55)",
    }
    inactive_year_style = base_btn
    
    available_carte_years = sorted(_available_years(), reverse=True)
    year_buttons = [
        html.Button(
            str(y),
            id=f"btn-carte-year-{y}",
            n_clicks=0,
            style=active_year_style if y == year else inactive_year_style,
        )
        for y in available_carte_years
    ]

    return html.Div(
        [
            html.H2("carte choroplèthe des accidents"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("vue", style={"fontSize": "12px", "color": "var(--text-300)", "marginBottom": "6px"}),
                            html.Button("vue par département", id="btn-carte-dept", n_clicks=0, style=dept_style),
                            html.Button("vue par commune", id="btn-carte-commune", n_clicks=0, style=commune_style),
                            html.Hr(style={"margin": "16px 0"}),
                            html.Div("année", style={"fontSize": "12px", "color": "var(--text-300)", "marginBottom": "8px"}),
                            html.Div(year_buttons, style={"display": "grid", "gridTemplateColumns": "repeat(2, 1fr)", "gap": "10px"}),
                        ],
                        className="page-card",
                        style={
                            "width": "230px",
                            "padding": "16px",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "10px",
                            "position": "sticky",
                            "top": "100px",
                            "alignSelf": "flex-start",
                        },
                    ),
                    html.Div(
                        [dcc.Graph(figure=fig, config={"responsive": True, "displayModeBar": True})],
                        className="page-card",
                        style={"padding": "20px", "flex": "1", "minWidth": "0"},
                    ),
                ],
                style={"display": "flex", "gap": "24px", "alignItems": "flex-start"},
            ),
        ],
        id="choropleth-page-container",
    )


try:
    choropleth_page = create_choropleth_page("dept")
except Exception:
    choropleth_page = html.Div(
        html.P("Données en chargement... Rafraîchissez la page dans quelques secondes."),
        style={"padding": "40px", "textAlign": "center", "color": "#999", "fontSize": "16px"}
    )

graph_page = html.Div(
    [
        html.H2("analyses temporelles — évolution des accidents"),
        html.Div(
            [
                # Sidebar filtres à gauche
                html.Div(
                    [
                        html.H3(
                            "filtres",
                            style={
                                "fontSize": "16px",
                                "fontWeight": "700",
                                "color": "#e6e9f2",
                                "marginBottom": "16px",
                                "borderBottom": "2px solid #6b5bd3",
                                "paddingBottom": "12px",
                            },
                        ),
                        html.Label("sexe", style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"}),
                        dcc.Dropdown(
                            id="filter-sexe",
                            options=[{"label": "tous", "value": "all"}, {"label": "homme", "value": "H"}, {"label": "femme", "value": "F"}],
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label("année", style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"}),
                        dcc.Dropdown(
                            id="filter-annee",
                            options=([{"label": "toutes", "value": "all"}] + [{"label": str(y), "value": y} for y in sorted(_available_years(), reverse=True)]),
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label("luminosité", style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"}),
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
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label("agglomération", style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"}),
                        dcc.Dropdown(
                            id="filter-agglomeration",
                            options=[{"label": "tous", "value": "all"}, {"label": "agglomération", "value": 1}, {"label": "hors agglomération", "value": 2}],
                            value="all",
                            clearable=False,
                        ),
                        html.Button(
                            "réinitialiser filtres",
                            id="btn-reset-filters",
                            n_clicks=0,
                            style={
                                "marginTop": "16px",
                                "padding": "10px 16px",
                                "backgroundColor": "#1a2035",
                                "border": "1px solid var(--border)",
                                "borderRadius": "8px",
                                "cursor": "pointer",
                                "fontSize": "13px",
                                "color": "#b9bfd3",
                                "boxShadow": "0 6px 20px rgba(0,0,0,0.25)",
                            },
                        ),
                    ],
                    className="page-card",
                    style={
                        "width": "260px",
                        "padding": "20px",
                        "position": "sticky",
                        "top": "100px",
                        "alignSelf": "flex-start",
                    },
                ),

                # Contenu principal à droite
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "courbe — accidents (heures/jours/mois)",
                                            style={
                                                "fontSize": "16px",
                                                "fontWeight": "600",
                                                "color": "#e6e9f2",
                                                "marginBottom": "12px",
                                                "borderLeft": "4px solid #6b5bd3",
                                                "paddingLeft": "12px",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Button("heures", id="btn-ts-hour", n_clicks=0, style={"padding": "8px 14px", "borderRadius": "8px", "border": "1px solid var(--border)", "backgroundColor": "#1a2035", "color": "#b9bfd3"}),
                                                html.Button("jours", id="btn-ts-day", n_clicks=0, style={"padding": "8px 14px", "borderRadius": "8px", "border": "1px solid var(--border)", "backgroundColor": "#1a2035", "color": "#b9bfd3", "marginLeft": "8px"}),
                                                html.Button("mois", id="btn-ts-month", n_clicks=0, style={"padding": "8px 14px", "borderRadius": "8px", "border": "1px solid var(--border)", "backgroundColor": "#1a2035", "color": "#b9bfd3", "marginLeft": "8px"}),
                                            ],
                                            style={"display": "flex", "justifyContent": "flex-start", "marginBottom": "12px"},
                                        ),
                                    ]
                                ),
                                dcc.Graph(
                                    id="graph-accidents-heure",
                                    figure=_make_time_series(),
                                    config={"responsive": True, "displayModeBar": True},
                                ),
                            ],
                            className="page-card",
                            style={"padding": "20px", "borderTop": "4px solid #7b5cff"},
                        ),

                        html.Div(
                            [
                                html.H3(
                                    "courbe 2 — distribution par agglomération",
                                    style={
                                        "fontSize": "16px",
                                        "fontWeight": "600",
                                        "color": "#e6e9f2",
                                        "marginBottom": "16px",
                                        "borderLeft": "4px solid #f093fb",
                                        "paddingLeft": "12px",
                                    },
                                ),
                                dcc.Graph(
                                    id="graph-accidents-pie",
                                    figure=_make_accidents_pie_chart(),
                                    config={"responsive": True, "displayModeBar": True},
                                ),
                            ],
                            className="page-card",
                            style={"padding": "20px", "borderTop": "4px solid #ff57c2", "marginTop": "24px"},
                        ),
                    ],
                    style={"flex": "1", "minWidth": "0"},
                ),
            ],
            style={"display": "flex", "gap": "24px"},
        ),
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
            "borderRadius": "8px",
            "backgroundColor": "transparent",
            "color": "inherit",
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
                            "DASHBOARD ACCIDENTOLOGIE",
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
                "minHeight": "75px",
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
    [
        Input("btn-carte-dept", "n_clicks"),
        Input("btn-carte-commune", "n_clicks"),
        *[Input(f"btn-carte-year-{y}", "n_clicks") for y in _available_years()],
    ],
    prevent_initial_call=True,
)
def update_carte_view(*_args):
    """met à jour la vue de la carte selon le mode et l'année."""
    ctx = dash.callback_context
    if not ctx.triggered:
        default_year = _available_years()[-1] if _available_years() else 2023
        return create_choropleth_page("dept", default_year)

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Déterminer le mode (dept ou commune)
    if button_id in ["btn-carte-dept", "btn-carte-commune"]:
        mode = "commune" if button_id == "btn-carte-commune" else "dept"
        default_year = _available_years()[-1] if _available_years() else 2023
        return create_choropleth_page(mode, default_year)
    
    # Déterminer l'année
    m = re.match(r"btn-carte-year-(\d{4})", button_id)
    if m:
        year = int(m.group(1))
        return create_choropleth_page("dept", year)
    
    default_year = _available_years()[-1] if _available_years() else 2023
    return create_choropleth_page("dept", default_year)


@callback(
    Output("page-content", "children", allow_duplicate=True),
    [Input(f"btn-year-{y}", "n_clicks") for y in _available_radar_years()],
    prevent_initial_call=True,
)
def update_histogram_year(*_args):
    """met à jour l'histogramme selon l'année sélectionnée."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_histogram_page()

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    m = re.match(r"btn-year-(\d{4})", button_id)
    year = int(m.group(1)) if m else None
    return create_histogram_page(year)


@callback(
    [Output("graph-accidents-heure", "figure"), Output("graph-accidents-pie", "figure")],
    [
        Input("filter-annee", "value"),
        Input("filter-agglomeration", "value"),
        Input("btn-ts-hour", "n_clicks"),
        Input("btn-ts-day", "n_clicks"),
        Input("btn-ts-month", "n_clicks"),
    ],
)
def update_graph_page_charts(annee, agg_value, _n_h, _n_d, _n_m):
    """met à jour la courbe temporelle (heures/jours/mois) et le camembert."""
    ctx = dash.callback_context
    year = annee

    # normaliser l'agglo
    if agg_value in (1, 2):
        agg_filter = agg_value
    elif isinstance(agg_value, str) and agg_value in ("1", "2"):
        agg_filter = int(agg_value)
    else:
        agg_filter = None

    # déterminer l'unité depuis le bouton cliqué
    unit = "hour"
    if ctx.triggered:
        btn = ctx.triggered[0]["prop_id"].split(".")[0]
        if btn == "btn-ts-day":
            unit = "day"
        elif btn == "btn-ts-month":
            unit = "month"

    return (
        _make_time_series(year, agg_filter=agg_filter, unit=unit),
        _make_accidents_pie_chart(year, agg_filter=agg_filter),
    )
