"""page d’accueil dash : cartes, histogrammes et graphiques.
pylint: disable=too-many-lines
"""

from __future__ import annotations

from pathlib import Path
import sys
import json
import re

import dash
from dash import html, dcc, callback, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# permettre l'import absolu de src.utils
sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
GEOJSON_PATH = ROOT / "departements-version-simplifiee.geojson"
COMMUNES_GEOJSON_PATH = ROOT / "communes.geojson"
REGIONS_GEOJSON_PATH = ROOT / "regions-version-simplifiee.geojson"

# import absolu avec repli pour le lint
try:
    from src.utils.get_data import query_db  # type: ignore
except ImportError:  # pragma: no cover

    def query_db(*_args, **_kwargs):
        raise ImportError("src.utils.get_data introuvable")


# mapping département -> région (codes régions 2016)
DEPT_TO_REGION: dict[str, str] = {
    # Auvergne-Rhône-Alpes (84)
    "01": "84",
    "03": "84",
    "07": "84",
    "15": "84",
    "26": "84",
    "38": "84",
    "42": "84",
    "43": "84",
    "63": "84",
    "69": "84",
    "73": "84",
    "74": "84",
    # Bourgogne-Franche-Comté (27)
    "21": "27",
    "25": "27",
    "39": "27",
    "58": "27",
    "70": "27",
    "71": "27",
    "89": "27",
    "90": "27",
    # Bretagne (53)
    "22": "53",
    "29": "53",
    "35": "53",
    "56": "53",
    # Centre-Val de Loire (24)
    "18": "24",
    "28": "24",
    "36": "24",
    "37": "24",
    "41": "24",
    "45": "24",
    # Corse (94)
    "2A": "94",
    "2B": "94",
    # Grand Est (44)
    "08": "44",
    "10": "44",
    "51": "44",
    "52": "44",
    "54": "44",
    "55": "44",
    "57": "44",
    "67": "44",
    "68": "44",
    "88": "44",
    # Hauts-de-France (32)
    "02": "32",
    "59": "32",
    "60": "32",
    "62": "32",
    "80": "32",
    # Île-de-France (11)
    "75": "11",
    "77": "11",
    "78": "11",
    "91": "11",
    "92": "11",
    "93": "11",
    "94": "11",
    "95": "11",
    # Normandie (28)
    "14": "28",
    "27": "28",
    "50": "28",
    "61": "28",
    "76": "28",
    # Nouvelle-Aquitaine (75)
    "16": "75",
    "17": "75",
    "19": "75",
    "23": "75",
    "24": "75",
    "33": "75",
    "40": "75",
    "47": "75",
    "64": "75",
    "79": "75",
    "86": "75",
    "87": "75",
    # Occitanie (76)
    "09": "76",
    "11": "76",
    "12": "76",
    "30": "76",
    "31": "76",
    "32": "76",
    "34": "76",
    "46": "76",
    "48": "76",
    "65": "76",
    "66": "76",
    "81": "76",
    "82": "76",
    # Pays de la Loire (52)
    "44": "52",
    "49": "52",
    "53": "52",
    "72": "52",
    "85": "52",
    # Provence-Alpes-Côte d'Azur (93)
    "04": "93",
    "05": "93",
    "06": "93",
    "13": "93",
    "83": "93",
    "84": "93",
    # Outre-mer
    "971": "01",
    "972": "02",
    "973": "03",
    "974": "04",
    "976": "06",
}

# noms des régions (codes 2016)
REGION_NAMES: dict[str, str] = {
    "84": "Auvergne-Rhône-Alpes",
    "27": "Bourgogne-Franche-Comté",
    "53": "Bretagne",
    "24": "Centre-Val de Loire",
    "94": "Corse",
    "44": "Grand Est",
    "32": "Hauts-de-France",
    "11": "Île-de-France",
    "28": "Normandie",
    "75": "Nouvelle-Aquitaine",
    "76": "Occitanie",
    "52": "Pays de la Loire",
    "93": "Provence-Alpes-Côte d'Azur",
    "01": "Guadeloupe",
    "02": "Martinique",
    "03": "Guyane",
    "04": "La Réunion",
    "06": "Mayotte",
}

# noms des départements
DEPT_NAMES: dict[str, str] = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "976": "Mayotte",
}


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
        df = query_db("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'radars_%'")
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
        sql = f"SELECT dep AS dept, COUNT(*) AS accidents " f"FROM {table_name} GROUP BY dep"
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
        df["nom"] = df["dept"].map(DEPT_NAMES).fillna(df["dept"])

        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="dept",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale=[[0, "#1a2035"], [0.5, "#3ae7ff"], [1, "#ff57c2"]],
            title=f"ACCIDENTOLOGIE PAR DÉPARTEMENT (FRANCE) - {year}",
            hover_name="nom",
            hover_data={"dept": True, "accidents": True, "nom": False},
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
        df["code_commune"] = df["code_commune"].apply(lambda x: arrondissement_map.get(x, x))

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
            title=f"ACCIDENTOLOGIE PAR COMMUNE (FRANCE) - {year}",
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


def _make_regions_choropleth(year=2023):
    """carte choroplèthe par région (agrégation par code région 2016)."""
    try:
        if not REGIONS_GEOJSON_PATH.exists():
            fig = go.Figure()
            fig.add_annotation(
                text="fichier regions geojson manquant",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
            )
            return fig

        with REGIONS_GEOJSON_PATH.open("r", encoding="utf-8") as f:
            geojson = json.load(f)

        table_name = f"caracteristiques_{year}"
        sql = f"SELECT dep AS dept, COUNT(*) AS accidents FROM {table_name} GROUP BY dep"
        df = query_db(sql)

        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="aucune donnée disponible",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
            )
            return fig

        df["dept"] = df["dept"].astype(str).str.strip().str.upper().str.zfill(2)
        # préserver 971..976
        df.loc[df["dept"].str.len() == 3, "dept"] = df.loc[df["dept"].str.len() == 3, "dept"]

        def _map_region(dep: str) -> str | None:
            return DEPT_TO_REGION.get(dep)

        df["region"] = df["dept"].apply(_map_region)
        df = (
            df.dropna(subset=["region"]).groupby("region", as_index=False).agg({"accidents": "sum"})
        )
        df["nom"] = df["region"].map(REGION_NAMES).fillna(df["region"])

        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="region",
            color="accidents",
            featureidkey="properties.code",
            projection="mercator",
            color_continuous_scale=[[0, "#1a2035"], [0.5, "#3ae7ff"], [1, "#ff57c2"]],
            title=f"ACCIDENTOLOGIE PAR RÉGION (FRANCE) - {year}",
            hover_name="nom",
            hover_data={"region": True, "accidents": True, "nom": False},
        )
        fig.update_geos(fitbounds="locations", visible=False)
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
    except Exception as err:
        print(f"erreur carte régions : {err}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"erreur : {str(err)[:100]}",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
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
                "<b>écart:</b> %{x:.1f} km/h<br>" "<b>mesures:</b> %{y}<br>" "<extra></extra>"
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
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255, 255, 255, 0.06)")
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


def _make_time_series(
    year=2023,
    agg_filter: int | str | None = None,
    lum_filter: int | str | None = None,
    atm_filter: int | str | None = None,
    unit: str = "hour",
    sexe_filter: int | None = None,
    trajet_filter: int | None = None,
    birth_year_min: int | None = None,
    birth_year_max: int | None = None,
    catv_filter: int | None = None,
    motor_filter: int | None = None,
):
    """courbe : évolution du nombre d'accidents par heure/jour/mois/jour de semaine.

    unit: "hour" | "day" | "month" | "weekday"
    year: 2020..2024 | "all" pour agréger plusieurs années.
    agg_filter: 1 (agglomération) | 2 (hors agglomération)
    lum_filter: 1-5 (conditions de luminosité)
    usager filters: sexe (1/2), trajet (int), age range
    """
    try:
        unit = unit or "hour"
        unit = unit.lower()

        def _query_one(y: int) -> pd.DataFrame:
            use_join = any(
                v is not None
                for v in (
                    sexe_filter,
                    trajet_filter,
                    birth_year_min,
                    birth_year_max,
                    catv_filter,
                    motor_filter,
                )
            )
            # Pour 2024, pas de vehicule, utiliser caract_usager si filtres usager actifs
            if y == 2024:
                # Ignorer les filtres vehicule pour 2024
                use_join_usager = any(
                    v is not None
                    for v in (sexe_filter, trajet_filter, birth_year_min, birth_year_max)
                )
                table_name = f"caract_usager_{y}" if use_join_usager else f"caracteristiques_{y}"
            else:
                table_name = f"caract_usager_vehicule_{y}" if use_join else f"caracteristiques_{y}"
            
            # Les colonnes lum et atm sont toujours dans caracteristiques, donc OK
            params: dict = {}
            where_parts = []

            if unit == "hour":
                select_x = "CAST(SUBSTR(heure,1,2) AS INTEGER) AS x"
                where_parts.append("heure IS NOT NULL")
            elif unit == "day":
                select_x = "CAST(jour AS INTEGER) AS x"
                where_parts.append("jour IS NOT NULL")
            elif unit == "month":
                select_x = "CAST(mois AS INTEGER) AS x"
                where_parts.append("mois IS NOT NULL")
            elif unit == "weekday":
                # On récupère jour et mois, puis on calcule le jour de semaine côté Python
                select_x = None
                where_parts.extend(["jour IS NOT NULL", "mois IS NOT NULL"])
            else:
                select_x = "CAST(SUBSTR(heure,1,2) AS INTEGER) AS x"
                where_parts.append("heure IS NOT NULL")

            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter

            if lum_filter in (1, 2, 3, 4, 5):
                where_parts.append("CAST(lum AS INTEGER) = :lum")
                params["lum"] = lum_filter
            if atm_filter in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                where_parts.append("CAST(atm AS INTEGER) = :atm")
                params["atm"] = atm_filter

            # usager filters
            if sexe_filter is not None:
                where_parts.append("CAST(sexe AS INTEGER) = :sexe")
                params["sexe"] = sexe_filter
            if trajet_filter is not None:
                where_parts.append("CAST(trajet AS INTEGER) = :trajet")
                params["trajet"] = trajet_filter
            if (birth_year_min is not None) and (birth_year_max is not None):
                where_parts.append(
                    "CAST(an_nais AS INTEGER) BETWEEN :birth_year_min AND :birth_year_max"
                )
                params["birth_year_min"] = birth_year_min
                params["birth_year_max"] = birth_year_max

            # vehicule filters
            if catv_filter is not None:
                where_parts.append("CAST(catv AS INTEGER) = :catv")
                params["catv"] = catv_filter
            if motor_filter is not None:
                where_parts.append("CAST(motor AS INTEGER) = :motor")
                params["motor"] = motor_filter

            where_clause = " AND ".join(where_parts) if where_parts else "1=1"
            if unit == "weekday":
                sql = (
                    f"SELECT CAST(mois AS INTEGER) AS mois, CAST(jour AS INTEGER) AS jour, COUNT(*) AS accidents "
                    f"FROM {table_name} WHERE {where_clause} "
                    f"GROUP BY mois, jour ORDER BY mois, jour"
                )
                df = query_db(sql, params)
                if df is None or df.empty:
                    return df
                # Calculer le jour de semaine (lundi=1 .. dimanche=7)
                df["mois"] = pd.to_numeric(df["mois"], errors="coerce")
                df["jour"] = pd.to_numeric(df["jour"], errors="coerce")
                df = df.dropna(subset=["mois", "jour"]).copy()
                df["mois"] = df["mois"].astype(int)
                df["jour"] = df["jour"].astype(int)
                # Construire des dates avec l'année courante y
                dates = pd.to_datetime(
                    {"year": y, "month": df["mois"], "day": df["jour"]}, errors="coerce"
                )
                dow = dates.dt.dayofweek  # 0=lundi .. 6=dimanche
                df = df.assign(x=(dow + 1))  # 1..7
                df = df.groupby("x", as_index=False).agg({"accidents": "sum"})
                return df
            else:
                sql = (
                    f"SELECT {select_x}, COUNT(*) AS accidents "
                    f"FROM {table_name} WHERE {where_clause} "
                    f"GROUP BY x ORDER BY x"
                )
                return query_db(sql, params)

        show_leg = False
        overlay_sets: list[tuple[int, pd.DataFrame]] = []
        if isinstance(year, str) and year == "all":
            for y in sorted(_available_years()):
                d = _query_one(y)
                if d is not None and not d.empty:
                    overlay_sets.append((y, d.sort_values(by="x")))
            show_leg = len(overlay_sets) > 1
        else:
            d = _query_one(int(year))
            if d is not None and not d.empty:
                overlay_sets.append((int(year), d.sort_values(by="x")))

        if not overlay_sets:
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

        title_map = {
            "hour": "évolution du nombre d'accidents par heure",
            "day": "évolution du nombre d'accidents par jour",
            "month": "évolution du nombre d'accidents par mois",
            "weekday": "évolution du nombre d'accidents par jour de semaine",
        }
        x_title_map = {
            "hour": "heure (0-23)",
            "day": "jour (1-31)",
            "month": "mois (1-12)",
            "weekday": "jour de semaine (1=lundi .. 7=dimanche)",
        }
        x_range_map = {
            "hour": [-0.5, 23.5],
            "day": [0.5, 31.5],
            "month": [0.5, 12.5],
            "weekday": [0.5, 7.5],
        }

        fig = go.Figure()
        palette = [
            "#3ae7ff",  # cyan
            "#ff57c2",  # pink
            "#7b5cff",  # purple
            "#01d084",  # green
            "#f093fb",  # magenta soft
        ]
        for idx, (y, dfx) in enumerate(overlay_sets):
            color = palette[idx % len(palette)]
            fig.add_trace(
                go.Scatter(
                    x=dfx["x"],
                    y=dfx["accidents"],
                    mode="lines+markers",
                    name=str(y),
                    line={"color": color, "width": 3, "shape": "spline"},
                    marker={
                        "size": 8,
                        "color": color,
                        "symbol": "circle",
                        "line": {"color": "#0e111b", "width": 1},
                    },
                    # area fill only for single series to avoid stacking confusion
                    fill="tozeroy" if not show_leg else None,
                    fillcolor=("rgba(58, 231, 255, 0.12)" if not show_leg else None),
                    hovertemplate=(f"<b>année {y}</b><br>%{{x}} → <b>%{{y}}</b><extra></extra>"),
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
            showlegend=show_leg,
            legend={"orientation": "h", "y": 1.05},
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
        if unit == "weekday":
            fig.update_xaxes(
                tickmode="array",
                tickvals=[1, 2, 3, 4, 5, 6, 7],
                ticktext=["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
                range=[0.5, 7.5],
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


def _make_accidents_pie_chart(
    year=2023,
    agg_filter: int | str | None = None,
    lum_filter: int | str | None = None,
    atm_filter: int | str | None = None,
    sexe_filter: int | None = None,
    trajet_filter: int | None = None,
    birth_year_min: int | None = None,
    birth_year_max: int | None = None,
    catv_filter: int | None = None,
    motor_filter: int | None = None,
):
    """camembert : distribution des accidents par sexe.

    year: 2020..2024 | "all" pour agréger plusieurs années.
    """
    try:

        def _query_one(y: int) -> pd.DataFrame:
            # Always use joined table since we're querying 'sexe' column from usager
            if y == 2024:
                # Pour 2024, pas de vehicule, utiliser caract_usager
                table_name = f"caract_usager_{y}"
            else:
                table_name = f"caract_usager_vehicule_{y}"
            where_parts = ["sexe IS NOT NULL"]
            params = {}
            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter
            if lum_filter in (1, 2, 3, 4, 5):
                where_parts.append("CAST(lum AS INTEGER) = :lum")
                params["lum"] = lum_filter
            if atm_filter in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                where_parts.append("CAST(atm AS INTEGER) = :atm")
                params["atm"] = atm_filter
            if sexe_filter is not None:
                where_parts.append("CAST(sexe AS INTEGER) = :sexe")
                params["sexe"] = sexe_filter
            if trajet_filter is not None:
                where_parts.append("CAST(trajet AS INTEGER) = :trajet")
                params["trajet"] = trajet_filter
            if (birth_year_min is not None) and (birth_year_max is not None):
                where_parts.append(
                    "CAST(an_nais AS INTEGER) BETWEEN :birth_year_min AND :birth_year_max"
                )
                params["birth_year_min"] = birth_year_min
                params["birth_year_max"] = birth_year_max
            if catv_filter is not None:
                where_parts.append("CAST(catv AS INTEGER) = :catv")
                params["catv"] = catv_filter
            if motor_filter is not None:
                where_parts.append("CAST(motor AS INTEGER) = :motor")
                params["motor"] = motor_filter
            where_clause = " AND ".join(where_parts)
            sql = (
                f"SELECT sexe, COUNT(*) AS count "
                f"FROM {table_name} WHERE {where_clause} GROUP BY sexe"
            )
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            df1 = _query_one(2021)
            df2 = _query_one(2023)
            df = pd.concat([df1, df2], ignore_index=True)
            df = df.groupby("sexe", as_index=False).agg({"count": "sum"})
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

        sexe_labels = {1: "homme", 2: "femme"}
        df["sexe_label"] = df["sexe"].map(sexe_labels)
        # Filtrer les valeurs null/NaN
        df = df.dropna(subset=["sexe_label"])
        df = df.sort_values(by="count", ascending=False)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df["sexe_label"],
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
                "text": "DISTRIBUTION DES ACCIDENTS PAR SEXE",
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


def _make_catv_pie_chart(
    year=2023,
    agg_filter: int | str | None = None,
    lum_filter: int | str | None = None,
    atm_filter: int | str | None = None,
    sexe_filter: int | None = None,
    trajet_filter: int | None = None,
    birth_year_min: int | None = None,
    birth_year_max: int | None = None,
    catv_filter: int | None = None,
    motor_filter: int | None = None,
):
    """camembert : distribution des accidents par catégorie de véhicule."""
    try:

        def _query_one(y: int) -> pd.DataFrame:
            # Pour 2024, pas de données vehicule
            if y == 2024:
                return pd.DataFrame()

            # Always use joined table since we're querying 'catv' column from vehicule
            table_name = f"caract_usager_vehicule_{y}"
            where_parts = ["catv IS NOT NULL"]
            params = {}
            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter
            if lum_filter in (1, 2, 3, 4, 5):
                where_parts.append("CAST(lum AS INTEGER) = :lum")
                params["lum"] = lum_filter
            if atm_filter in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                where_parts.append("CAST(atm AS INTEGER) = :atm")
                params["atm"] = atm_filter
            if sexe_filter is not None:
                where_parts.append("CAST(sexe AS INTEGER) = :sexe")
                params["sexe"] = sexe_filter
            if trajet_filter is not None:
                where_parts.append("CAST(trajet AS INTEGER) = :trajet")
                params["trajet"] = trajet_filter
            if (birth_year_min is not None) and (birth_year_max is not None):
                where_parts.append(
                    "CAST(an_nais AS INTEGER) BETWEEN :birth_year_min AND :birth_year_max"
                )
                params["birth_year_min"] = birth_year_min
                params["birth_year_max"] = birth_year_max
            if catv_filter is not None:
                where_parts.append("CAST(catv AS INTEGER) = :catv")
                params["catv"] = catv_filter
            if motor_filter is not None:
                where_parts.append("CAST(motor AS INTEGER) = :motor")
                params["motor"] = motor_filter
            where_clause = " AND ".join(where_parts)
            sql = f"SELECT catv, COUNT(*) AS count FROM {table_name} WHERE {where_clause} GROUP BY catv"
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            dfs = []
            for y in [2020, 2021, 2022, 2023]:
                df = _query_one(y)
                if df is not None and not df.empty:
                    dfs.append(df)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
                df = df.groupby("catv", as_index=False).agg({"count": "sum"})
            else:
                df = pd.DataFrame()
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

        catv_labels = {
            1: "vélo",
            2: "cyclo <50cm3",
            3: "voiturette",
            7: "VL seul",
            10: "VL+caravane",
            13: "VL+remorque",
            14: "VU 1.5-3.5T",
            15: "VU >3.5T",
            16: "VU+remorque",
            17: "PL 3.5-7.5T",
            18: "PL >7.5T",
            19: "PL+remorque",
            20: "tracteur seul",
            21: "tracteur+semi",
            30: "scooter immat",
            31: "moto >50cm3",
            32: "scooter <50cm3",
            33: "moto >125cm3",
            34: "scooter >125cm3",
            37: "transport commun",
            38: "tramway",
            40: "quad léger",
            41: "quad lourd",
            42: "cyclomoteur",
            50: "EDP motorisé",
            60: "EDP non motorisé",
            99: "autre",
        }
        df["catv_label"] = df["catv"].map(catv_labels).fillna("inconnu")
        df = df.sort_values(by="count", ascending=False).head(10)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df["catv_label"],
                    values=df["count"],
                    marker={"line": {"color": "#0e111b", "width": 2}},
                    textposition="auto",
                    hovertemplate="<b>%{label}</b><br>accidents: %{value}<br>part: %{percent}<extra></extra>",
                    textinfo="percent",
                    textfont={"size": 12, "color": "#e6e9f2"},
                )
            ]
        )
        fig.update_layout(
            title={
                "text": "TOP 10 CATÉGORIES VÉHICULE",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#e6e9f2"},
            },
            height=420,
            margin={"l": 20, "r": 20, "t": 80, "b": 20},
            font={"family": "Arial, sans-serif", "size": 12, "color": "#e6e9f2"},
            paper_bgcolor="#1a1d2e",
            plot_bgcolor="#1a1d2e",
            showlegend=True,
            legend={"font": {"color": "#e6e9f2"}},
        )
        return fig
    except Exception as err:
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


def _make_motor_pie_chart(
    year=2023,
    agg_filter: int | str | None = None,
    lum_filter: int | str | None = None,
    atm_filter: int | str | None = None,
    sexe_filter: int | None = None,
    trajet_filter: int | None = None,
    birth_year_min: int | None = None,
    birth_year_max: int | None = None,
    catv_filter: int | None = None,
    motor_filter: int | None = None,
):
    """camembert : distribution des accidents par motorisation."""
    try:

        def _query_one(y: int) -> pd.DataFrame:
            # Pour 2024, pas de données vehicule
            if y == 2024:
                return pd.DataFrame()

            # Always use joined table since we're querying 'motor' column from vehicule
            table_name = f"caract_usager_vehicule_{y}"
            where_parts = ["motor IS NOT NULL"]
            params = {}
            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter
            if lum_filter in (1, 2, 3, 4, 5):
                where_parts.append("CAST(lum AS INTEGER) = :lum")
                params["lum"] = lum_filter
            if atm_filter in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                where_parts.append("CAST(atm AS INTEGER) = :atm")
                params["atm"] = atm_filter
            if sexe_filter is not None:
                where_parts.append("CAST(sexe AS INTEGER) = :sexe")
                params["sexe"] = sexe_filter
            if trajet_filter is not None:
                where_parts.append("CAST(trajet AS INTEGER) = :trajet")
                params["trajet"] = trajet_filter
            if (birth_year_min is not None) and (birth_year_max is not None):
                where_parts.append(
                    "CAST(an_nais AS INTEGER) BETWEEN :birth_year_min AND :birth_year_max"
                )
                params["birth_year_min"] = birth_year_min
                params["birth_year_max"] = birth_year_max
            if catv_filter is not None:
                where_parts.append("CAST(catv AS INTEGER) = :catv")
                params["catv"] = catv_filter
            if motor_filter is not None:
                where_parts.append("CAST(motor AS INTEGER) = :motor")
                params["motor"] = motor_filter
            where_clause = " AND ".join(where_parts)
            sql = f"SELECT motor, COUNT(*) AS count FROM {table_name} WHERE {where_clause} GROUP BY motor"
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            dfs = []
            for y in [2020, 2021, 2022, 2023]:
                df = _query_one(y)
                if df is not None and not df.empty:
                    dfs.append(df)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
                df = df.groupby("motor", as_index=False).agg({"count": "sum"})
            else:
                df = pd.DataFrame()
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

        motor_labels = {
            1: "hydrocarbure",
            2: "électrique",
            3: "hydrogène",
            4: "humaine",
            5: "hybride",
            6: "GPL",
            9: "autre",
        }
        df["motor_label"] = df["motor"].map(motor_labels).fillna("inconnu")
        df = df.sort_values(by="count", ascending=False)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df["motor_label"],
                    values=df["count"],
                    marker={"line": {"color": "#0e111b", "width": 2}},
                    textposition="auto",
                    hovertemplate="<b>%{label}</b><br>accidents: %{value}<br>part: %{percent}<extra></extra>",
                    textinfo="percent",
                    textfont={"size": 14, "color": "#e6e9f2"},
                )
            ]
        )
        fig.update_layout(
            title={
                "text": "DISTRIBUTION PAR MOTORISATION",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#e6e9f2"},
            },
            height=420,
            margin={"l": 20, "r": 20, "t": 80, "b": 20},
            font={"family": "Arial, sans-serif", "size": 12, "color": "#e6e9f2"},
            paper_bgcolor="#1a1d2e",
            plot_bgcolor="#1a1d2e",
            showlegend=True,
            legend={"font": {"color": "#e6e9f2"}},
        )
        return fig
    except Exception as err:
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


def _make_catv_gender_bar_chart(
    year=2023,
    agg_filter: int | str | None = None,
    lum_filter: int | str | None = None,
    atm_filter: int | str | None = None,
    sexe_filter: int | None = None,
    trajet_filter: int | None = None,
    birth_year_min: int | None = None,
    birth_year_max: int | None = None,
    catv_filter: int | None = None,
    motor_filter: int | None = None,
):
    """barres empilées : proportion H/F par catégorie de véhicule."""
    try:

        def _query_one(y: int) -> pd.DataFrame:
            # Pour 2024, pas de données vehicule
            if y == 2024:
                return pd.DataFrame()

            use_join = any(
                v is not None
                for v in (
                    sexe_filter,
                    trajet_filter,
                    birth_year_min,
                    birth_year_max,
                    catv_filter,
                    motor_filter,
                )
            )
            table_name = f"caract_usager_vehicule_{y}" if use_join else f"caracteristiques_{y}"
            where_parts = ["catv IS NOT NULL", "sexe IS NOT NULL"]
            params = {}
            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter
            if lum_filter in (1, 2, 3, 4, 5):
                where_parts.append("CAST(lum AS INTEGER) = :lum")
                params["lum"] = lum_filter
            if atm_filter in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                where_parts.append("CAST(atm AS INTEGER) = :atm")
                params["atm"] = atm_filter
            if sexe_filter is not None:
                where_parts.append("CAST(sexe AS INTEGER) = :sexe")
                params["sexe"] = sexe_filter
            if trajet_filter is not None:
                where_parts.append("CAST(trajet AS INTEGER) = :trajet")
                params["trajet"] = trajet_filter
            if (birth_year_min is not None) and (birth_year_max is not None):
                where_parts.append(
                    "CAST(an_nais AS INTEGER) BETWEEN :birth_year_min AND :birth_year_max"
                )
                params["birth_year_min"] = birth_year_min
                params["birth_year_max"] = birth_year_max
            if catv_filter is not None:
                where_parts.append("CAST(catv AS INTEGER) = :catv")
                params["catv"] = catv_filter
            if motor_filter is not None:
                where_parts.append("CAST(motor AS INTEGER) = :motor")
                params["motor"] = motor_filter
            where_clause = " AND ".join(where_parts)
            sql = f"SELECT catv, sexe, COUNT(*) AS count FROM {table_name} WHERE {where_clause} GROUP BY catv, sexe"
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            dfs = []
            for y in [2020, 2021, 2022, 2023]:
                df = _query_one(y)
                if df is not None and not df.empty:
                    dfs.append(df)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
                df = df.groupby(["catv", "sexe"], as_index=False).agg({"count": "sum"})
            else:
                df = pd.DataFrame()
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

        catv_labels = {
            1: "vélo",
            2: "cyclo <50",
            3: "voiturette",
            7: "VL seul",
            10: "VL+caravane",
            13: "VL+remorque",
            14: "VU 1.5-3.5T",
            15: "VU >3.5T",
            16: "VU+remorque",
            17: "PL 3.5-7.5T",
            18: "PL >7.5T",
            19: "PL+remorque",
            20: "tracteur",
            21: "tracteur+semi",
            30: "scooter immat",
            31: "moto >50",
            32: "scooter <50",
            33: "moto >125",
            34: "scooter >125",
            37: "transport com",
            38: "tramway",
            40: "quad léger",
            41: "quad lourd",
            42: "cyclomoteur",
            50: "EDP motor",
            60: "EDP non motor",
            99: "autre",
        }

        # Calculer les totaux par catégorie
        totals = df.groupby("catv")["count"].sum().reset_index()
        totals = totals.sort_values("count", ascending=False).head(10)
        top_catv = totals["catv"].tolist()

        # Filtrer pour garder seulement le top 10
        df = df[df["catv"].isin(top_catv)]
        df["catv_label"] = df["catv"].map(catv_labels).fillna("inconnu")

        # Pivoter pour avoir sexe en colonnes
        pivot = df.pivot_table(
            index="catv_label", columns="sexe", values="count", fill_value=0, aggfunc="sum"
        )

        # Calculer les pourcentages
        pivot["total"] = pivot.sum(axis=1)
        if 1 in pivot.columns:
            pivot["homme_pct"] = (pivot[1] / pivot["total"] * 100).round(1)
        else:
            pivot["homme_pct"] = 0
        if 2 in pivot.columns:
            pivot["femme_pct"] = (pivot[2] / pivot["total"] * 100).round(1)
        else:
            pivot["femme_pct"] = 0

        # Trier par total décroissant
        pivot = pivot.sort_values("total", ascending=True)

        fig = go.Figure()

        # Barre femmes
        fig.add_trace(
            go.Bar(
                y=pivot.index,
                x=pivot["femme_pct"],
                name="Femme",
                orientation="h",
                marker={"color": "#ff57c2"},
                text=pivot["femme_pct"].apply(lambda x: f"{x:.1f}%"),
                textposition="inside",
                textfont={"color": "#ffffff", "size": 11},
                hovertemplate="<b>%{y}</b><br>Femmes: %{x:.1f}%<extra></extra>",
            )
        )

        # Barre hommes
        fig.add_trace(
            go.Bar(
                y=pivot.index,
                x=pivot["homme_pct"],
                name="Homme",
                orientation="h",
                marker={"color": "#3ae7ff"},
                text=pivot["homme_pct"].apply(lambda x: f"{x:.1f}%"),
                textposition="inside",
                textfont={"color": "#000000", "size": 11},
                hovertemplate="<b>%{y}</b><br>Hommes: %{x:.1f}%<extra></extra>",
            )
        )

        fig.update_layout(
            title={
                "text": "PROPORTION H/F PAR CATÉGORIE VÉHICULE (TOP 10)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#e6e9f2"},
            },
            barmode="stack",
            height=500,
            margin={"l": 150, "r": 20, "t": 80, "b": 60},
            font={"family": "Arial, sans-serif", "size": 12, "color": "#e6e9f2"},
            paper_bgcolor="#1a1d2e",
            plot_bgcolor="#1a1d2e",
            xaxis={
                "title": "Pourcentage (%)",
                "gridcolor": "#2d3548",
                "range": [0, 100],
                "tickfont": {"color": "#e6e9f2"},
            },
            yaxis={"tickfont": {"color": "#e6e9f2"}},
            legend={
                "font": {"color": "#e6e9f2"},
                "orientation": "h",
                "yanchor": "bottom",
                "y": -0.15,
                "xanchor": "center",
                "x": 0.5,
            },
        )
        return fig
    except Exception as err:
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


def _make_age_histogram(
    year=2023,
    agg_filter: int | str | None = None,
    lum_filter: int | str | None = None,
    atm_filter: int | str | None = None,
    sexe_filter: int | None = None,
    trajet_filter: int | None = None,
    birth_year_min: int | None = None,
    birth_year_max: int | None = None,
    catv_filter: int | None = None,
    motor_filter: int | None = None,
):
    """histogramme de distribution par âge des conducteurs."""
    try:

        def _query_one(y: int) -> pd.DataFrame:
            # Toujours besoin de usager pour an_nais
            if y == 2024:
                table_name = "caract_usager_2024"
            else:
                table_name = f"caract_usager_vehicule_{y}"

            where_parts = ["an_nais IS NOT NULL", "CAST(an_nais AS INTEGER) > 0"]
            params = {}
            if agg_filter in (1, 2):
                where_parts.append("CAST(agg AS INTEGER) = :agg")
                params["agg"] = agg_filter
            if lum_filter in (1, 2, 3, 4, 5):
                where_parts.append("CAST(lum AS INTEGER) = :lum")
                params["lum"] = lum_filter
            if atm_filter in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                where_parts.append("CAST(atm AS INTEGER) = :atm")
                params["atm"] = atm_filter
            if sexe_filter is not None:
                where_parts.append("CAST(sexe AS INTEGER) = :sexe")
                params["sexe"] = sexe_filter
            if trajet_filter is not None:
                where_parts.append("CAST(trajet AS INTEGER) = :trajet")
                params["trajet"] = trajet_filter
            if (birth_year_min is not None) and (birth_year_max is not None):
                where_parts.append(
                    "CAST(an_nais AS INTEGER) BETWEEN :birth_year_min AND :birth_year_max"
                )
                params["birth_year_min"] = birth_year_min
                params["birth_year_max"] = birth_year_max
            if y != 2024:
                if catv_filter is not None:
                    where_parts.append("CAST(catv AS INTEGER) = :catv")
                    params["catv"] = catv_filter
                if motor_filter is not None:
                    where_parts.append("CAST(motor AS INTEGER) = :motor")
                    params["motor"] = motor_filter
            where_clause = " AND ".join(where_parts)
            sql = f"SELECT an_nais, annee, COUNT(*) AS count FROM {table_name} WHERE {where_clause} GROUP BY an_nais, annee"
            return query_db(sql, params)

        if isinstance(year, str) and year == "all":
            dfs = []
            for y in [2020, 2021, 2022, 2023, 2024]:
                df = _query_one(y)
                if df is not None and not df.empty:
                    dfs.append(df)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
            else:
                df = pd.DataFrame()
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

        # Convertir an_nais et annee en entiers et calculer l'âge
        df["an_nais"] = pd.to_numeric(df["an_nais"], errors="coerce")
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df = df.dropna(subset=["an_nais", "annee"])
        df["an_nais"] = df["an_nais"].astype(int)
        df["annee"] = df["annee"].astype(int)
        df = df[(df["an_nais"] >= 1900) & (df["an_nais"] <= 2024)]  # Filtrer les années aberrantes
        
        # Calculer l'âge au moment de l'accident
        df["age"] = df["annee"] - df["an_nais"]
        df = df[(df["age"] >= 0) & (df["age"] <= 120)]  # Filtrer les âges aberrants
        
        # Agréger par âge
        df = df.groupby("age", as_index=False).agg({"count": "sum"})
        df = df.sort_values("age")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df["age"],
                y=df["count"],
                marker={"color": "#3ae7ff", "line": {"color": "#1a8fa8", "width": 1}},
                hovertemplate="<b>Âge: %{x} ans</b><br>Accidents: %{y}<extra></extra>",
            )
        )

        fig.update_layout(
            title={
                "text": "RÉPARTITION DES CONDUCTEURS PAR ÂGE",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#e6e9f2"},
            },
            xaxis={
                "title": "Âge (années)",
                "gridcolor": "#2d3548",
                "tickfont": {"color": "#e6e9f2"},
                "tickmode": "linear",
                "dtick": 5,
            },
            yaxis={
                "title": "Nombre d'accidents",
                "gridcolor": "#2d3548",
                "tickfont": {"color": "#e6e9f2"},
            },
            height=500,
            margin={"l": 60, "r": 20, "t": 80, "b": 60},
            font={"family": "Arial, sans-serif", "size": 12, "color": "#e6e9f2"},
            paper_bgcolor="#1a1d2e",
            plot_bgcolor="#1a1d2e",
            bargap=0.1,
        )
        return fig
    except Exception as err:
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
    if carte_mode == "commune":
        fig = _make_communes_choropleth(year)
    elif carte_mode == "region":
        fig = _make_regions_choropleth(year)
    else:
        fig = _make_departments_choropleth(year)

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
    region_active = {
        **base_btn,
        "backgroundColor": "#3ae7ff",
        "color": "#0e111b",
        "boxShadow": "0 0 10px rgba(58,231,255,0.6)",
        "border": "1px solid rgba(58,231,255,0.85)",
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
    region_style = region_active if carte_mode == "region" else base_btn
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

    # Affichage simple: une seule carte selon le mode + année courante
    maps_content = html.Div(
        [dcc.Graph(figure=fig, config={"responsive": True, "displayModeBar": True})],
        className="page-card",
        style={"padding": "20px", "flex": "1", "minWidth": "0"},
    )

    return html.Div(
        [
            html.H2("carte choroplèthe des accidents"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "vue",
                                style={
                                    "fontSize": "12px",
                                    "color": "var(--text-300)",
                                    "marginBottom": "6px",
                                },
                            ),
                            html.Button(
                                "vue par région",
                                id="btn-carte-region",
                                n_clicks=0,
                                style=region_style,
                            ),
                            html.Button(
                                "vue par département",
                                id="btn-carte-dept",
                                n_clicks=0,
                                style=dept_style,
                            ),
                            html.Button(
                                "vue par commune",
                                id="btn-carte-commune",
                                n_clicks=0,
                                style=commune_style,
                            ),
                            html.Hr(style={"margin": "16px 0"}),
                            html.Div(
                                "année",
                                style={
                                    "fontSize": "12px",
                                    "color": "var(--text-300)",
                                    "marginBottom": "8px",
                                },
                            ),
                            html.Div(
                                year_buttons,
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(2, 1fr)",
                                    "gap": "10px",
                                },
                            ),
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
                    maps_content,
                ],
                style={"display": "flex", "gap": "24px", "alignItems": "flex-start"},
            ),
            # Hidden flags to keep current mode/year in state
            html.Div(carte_mode, id="carte-mode-flag", style={"display": "none"}),
            html.Div(str(year), id="carte-year-flag", style={"display": "none"}),
        ],
        id="choropleth-page-container",
    )


try:
    choropleth_page = create_choropleth_page("dept")
except Exception:
    choropleth_page = html.Div(
        html.P("Données en chargement... Rafraîchissez la page dans quelques secondes."),
        style={"padding": "40px", "textAlign": "center", "color": "#999", "fontSize": "16px"},
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
                        html.Label(
                            "sexe",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-usager-sexe",
                            options=[
                                {"label": "tous", "value": "all"},
                                {"label": "homme", "value": 1},
                                {"label": "femme", "value": 2},
                            ],
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label(
                            "trajet",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-usager-trajet",
                            options=[
                                {"label": "tous", "value": "all"},
                                {"label": "domicile - travail", "value": 1},
                                {"label": "domicile - école", "value": 2},
                                {"label": "courses - achats", "value": 3},
                                {"label": "professionnel", "value": 4},
                                {"label": "promenade - loisirs", "value": 5},
                                {"label": "autre", "value": 9},
                            ],
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label(
                            "âge du conducteur",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Min:", style={"fontSize": "11px", "color": "#b9bfd3", "marginRight": "6px"}),
                                        dcc.Input(
                                            id="filter-usager-age-min",
                                            type="number",
                                            value=18,
                                            min=0,
                                            max=120,
                                            style={
                                                "width": "70px",
                                                "padding": "6px",
                                                "borderRadius": "4px",
                                                "border": "1px solid var(--border)",
                                                "backgroundColor": "#1a2035",
                                                "color": "#e6e9f2",
                                            },
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Max:", style={"fontSize": "11px", "color": "#b9bfd3", "marginRight": "6px"}),
                                        dcc.Input(
                                            id="filter-usager-age-max",
                                            type="number",
                                            value=99,
                                            min=0,
                                            max=120,
                                            style={
                                                "width": "70px",
                                                "padding": "6px",
                                                "borderRadius": "4px",
                                                "border": "1px solid var(--border)",
                                                "backgroundColor": "#1a2035",
                                                "color": "#e6e9f2",
                                            },
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                            ],
                            style={"marginBottom": "12px"},
                        ),
                        html.Hr(style={"margin": "16px 0"}),
                        html.H6(
                            "Filtres véhicule",
                            style={
                                "color": "#6b5bd3",
                                "fontWeight": "700",
                                "marginBottom": "8px",
                                "borderBottom": "2px solid #6b5bd3",
                                "paddingBottom": "12px",
                            },
                        ),
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-info-circle",
                                    style={"marginRight": "6px", "color": "#ff9800"},
                                ),
                                html.Span(
                                    "⚠️ Les données véhicule pour l'année 2024 ne sont pas disponibles.",
                                    style={
                                        "fontSize": "11px",
                                        "color": "#ff9800",
                                        "fontStyle": "italic",
                                    },
                                ),
                            ],
                            style={
                                "backgroundColor": "rgba(255, 152, 0, 0.1)",
                                "padding": "8px",
                                "borderRadius": "6px",
                                "marginBottom": "12px",
                                "border": "1px solid rgba(255, 152, 0, 0.3)",
                            },
                        ),
                        html.Label(
                            "catégorie véhicule",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-vehicule-catv",
                            options=[
                                {"label": "tous", "value": "all"},
                                {"label": "vélo", "value": 1},
                                {"label": "cyclo <50cm3", "value": 2},
                                {"label": "voiturette", "value": 3},
                                {"label": "scooter immatriculé", "value": 30},
                                {"label": "moto >50cm3", "value": 31},
                                {"label": "scooter <50cm3", "value": 32},
                                {"label": "moto >125cm3", "value": 33},
                                {"label": "scooter >125cm3", "value": 34},
                                {"label": "quad léger", "value": 40},
                                {"label": "quad lourd", "value": 41},
                                {"label": "cyclomoteur", "value": 42},
                                {"label": "VL seul", "value": 7},
                                {"label": "VL + caravane", "value": 10},
                                {"label": "VL + remorque", "value": 13},
                                {"label": "VU seul 1.5T-3.5T", "value": 14},
                                {"label": "VU seul + 3.5T", "value": 15},
                                {"label": "VU + remorque", "value": 16},
                                {"label": "PL seul 3.5T-7.5T", "value": 17},
                                {"label": "PL seul > 7.5T", "value": 18},
                                {"label": "PL > 3.5T + remorque", "value": 19},
                                {"label": "tracteur routier seul", "value": 20},
                                {"label": "tracteur routier + semi-remorque", "value": 21},
                                {"label": "transport en commun", "value": 37},
                                {"label": "tramway", "value": 38},
                                {"label": "EDP motorisé", "value": 50},
                                {"label": "EDP non motorisé", "value": 60},
                                {"label": "autre", "value": 99},
                            ],
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label(
                            "motorisation",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-vehicule-motor",
                            options=[
                                {"label": "tous", "value": "all"},
                                {"label": "hydrocarbure", "value": 1},
                                {"label": "électrique", "value": 2},
                                {"label": "hydrogène", "value": 3},
                                {"label": "humaine", "value": 4},
                                {"label": "hybride", "value": 5},
                                {"label": "GPL", "value": 6},
                                {"label": "autre", "value": 9},
                            ],
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Hr(style={"margin": "16px 0"}),
                        html.Label(
                            "année",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-annee",
                            options=(
                                [{"label": "toutes", "value": "all"}]
                                + [
                                    {"label": str(y), "value": y}
                                    for y in sorted(_available_years(), reverse=True)
                                ]
                            ),
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label(
                            "luminosité",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
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
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label(
                            "conditions atmosphériques",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-atm",
                            options=[
                                {"label": "toutes", "value": "all"},
                                {"label": "normale", "value": 1},
                                {"label": "pluie légère", "value": 2},
                                {"label": "pluie forte", "value": 3},
                                {"label": "neige/grêle", "value": 4},
                                {"label": "brouillard/fumée", "value": 5},
                                {"label": "vent fort/tempête", "value": 6},
                                {"label": "éblouissant", "value": 7},
                                {"label": "couvert", "value": 8},
                                {"label": "autre", "value": 9},
                            ],
                            value="all",
                            clearable=False,
                            style={"marginBottom": "12px"},
                        ),
                        html.Label(
                            "agglomération",
                            style={"fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"},
                        ),
                        dcc.Dropdown(
                            id="filter-agglomeration",
                            options=[
                                {"label": "tous", "value": "all"},
                                {"label": "agglomération", "value": 1},
                                {"label": "hors agglomération", "value": 2},
                            ],
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
                                                html.Button(
                                                    "heures",
                                                    id="btn-ts-hour",
                                                    n_clicks=0,
                                                    style={
                                                        "padding": "8px 14px",
                                                        "borderRadius": "8px",
                                                        "border": "1px solid var(--border)",
                                                        "backgroundColor": "#1a2035",
                                                        "color": "#b9bfd3",
                                                    },
                                                ),
                                                html.Button(
                                                    "jours",
                                                    id="btn-ts-day",
                                                    n_clicks=0,
                                                    style={
                                                        "padding": "8px 14px",
                                                        "borderRadius": "8px",
                                                        "border": "1px solid var(--border)",
                                                        "backgroundColor": "#1a2035",
                                                        "color": "#b9bfd3",
                                                        "marginLeft": "8px",
                                                    },
                                                ),
                                                html.Button(
                                                    "mois",
                                                    id="btn-ts-month",
                                                    n_clicks=0,
                                                    style={
                                                        "padding": "8px 14px",
                                                        "borderRadius": "8px",
                                                        "border": "1px solid var(--border)",
                                                        "backgroundColor": "#1a2035",
                                                        "color": "#b9bfd3",
                                                        "marginLeft": "8px",
                                                    },
                                                ),
                                                html.Button(
                                                    "jours semaine",
                                                    id="btn-ts-weekday",
                                                    n_clicks=0,
                                                    style={
                                                        "padding": "8px 14px",
                                                        "borderRadius": "8px",
                                                        "border": "1px solid var(--border)",
                                                        "backgroundColor": "#1a2035",
                                                        "color": "#b9bfd3",
                                                        "marginLeft": "8px",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "display": "flex",
                                                "justifyContent": "flex-start",
                                                "marginBottom": "12px",
                                            },
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
                                    "courbe 2 — distribution par sexe",
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
                            style={
                                "padding": "20px",
                                "borderTop": "4px solid #ff57c2",
                                "marginTop": "24px",
                            },
                        ),
                        html.Div(
                            [
                                html.H3(
                                    "courbe 3 — top catégories véhicule",
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
                                    id="graph-catv-pie",
                                    figure=_make_catv_pie_chart(),
                                    config={"responsive": True, "displayModeBar": True},
                                ),
                            ],
                            className="page-card",
                            style={
                                "padding": "20px",
                                "borderTop": "4px solid #3ae7ff",
                                "marginTop": "24px",
                            },
                        ),
                        html.Div(
                            [
                                html.H3(
                                    "courbe 4 — distribution par motorisation",
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
                                    id="graph-motor-pie",
                                    figure=_make_motor_pie_chart(),
                                    config={"responsive": True, "displayModeBar": True},
                                ),
                            ],
                            className="page-card",
                            style={
                                "padding": "20px",
                                "borderTop": "4px solid #ff57c2",
                                "marginTop": "24px",
                            },
                        ),
                        html.Div(
                            [
                                html.H3(
                                    "courbe 5 — répartition H/F par véhicule",
                                    style={
                                        "fontSize": "16px",
                                        "fontWeight": "600",
                                        "color": "#e6e9f2",
                                        "marginBottom": "16px",
                                        "borderLeft": "4px solid #3ae7ff",
                                        "paddingLeft": "12px",
                                    },
                                ),
                                dcc.Graph(
                                    id="graph-catv-gender",
                                    figure=_make_catv_gender_bar_chart(),
                                    config={"responsive": True, "displayModeBar": True},
                                ),
                            ],
                            className="page-card",
                            style={
                                "padding": "20px",
                                "borderTop": "4px solid #3ae7ff",
                                "marginTop": "24px",
                            },
                        ),
                        html.Div(
                            [
                                html.H3(
                                    "courbe 6 — répartition des conducteurs par âge",
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
                                    id="graph-age-histogram",
                                    figure=_make_age_histogram(),
                                    config={"responsive": True, "displayModeBar": True},
                                ),
                            ],
                            className="page-card",
                            style={
                                "padding": "20px",
                                "borderTop": "4px solid #f093fb",
                                "marginTop": "24px",
                            },
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
                html.Div(
                    [
                        html.H3("auteurs", style={"marginBottom": "8px"}),
                        html.P(
                            "Iris Carron et Cléo Detrez — Novembre 2025",
                            style={"fontSize": "16px", "color": "var(--text-300)"},
                        ),
                        html.Hr(style={"margin": "16px 0", "borderColor": "var(--border)"}),
                        html.H3("sources", style={"marginBottom": "8px"}),
                        html.Ul(
                            [
                                html.Li(
                                    html.A(
                                        "Base accidents corporels (data.gouv.fr)",
                                        href="https://www.data.gouv.fr/fr/datasets/base-de-donnees-accidents-corporels-de-la-circulation/",
                                        target="_blank",
                                        style={"color": "var(--accent-blue)"},
                                    )
                                ),
                                html.Li(
                                    html.A(
                                        "Mesures radars automatiques (data.gouv.fr)",
                                        href="https://www.data.gouv.fr/fr/datasets/radars/",
                                        target="_blank",
                                        style={"color": "var(--accent-pink)"},
                                    )
                                ),
                            ],
                            style={"marginLeft": "18px", "lineHeight": "1.9"},
                        ),
                    ]
                ),
            ],
            className="page-card",
            style={
                "padding": "24px",
                "borderTop": "4px solid #f093fb",
            },
        ),
    ]
)


# ============================================================================
# barre de navigation
# ============================================================================


def create_nav_button(label, button_id, _active=False):
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
                            style={
                                "color": "white",
                                "margin": "0 20px 0 0",
                                "letterSpacing": "0.5px",
                            },
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
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "gap": "10px",
                        "flex": "1",
                    },
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
        Input("btn-carte-region", "n_clicks"),
        Input("btn-carte-dept", "n_clicks"),
        Input("btn-carte-commune", "n_clicks"),
        *[Input(f"btn-carte-year-{y}", "n_clicks") for y in _available_years()],
    ],
    [State("carte-mode-flag", "children"), State("carte-year-flag", "children")],
    prevent_initial_call=True,
)
def update_carte_view(*_args):
    """met à jour la vue de la carte selon le mode et l'année."""
    ctx = dash.callback_context
    if not ctx.triggered:
        default_year = _available_years()[-1] if _available_years() else 2023
        return create_choropleth_page("dept", default_year)

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Déterminer le mode (dept, region, ou commune)
    if button_id in ["btn-carte-region", "btn-carte-dept", "btn-carte-commune"]:
        mode = (
            "region"
            if button_id == "btn-carte-region"
            else ("commune" if button_id == "btn-carte-commune" else "dept")
        )
        # garder l'année courante si possible
        current_year_str = dash.callback_context.states.get("carte-year-flag.children")
        try:
            current_year = int(current_year_str) if current_year_str else None
        except Exception:
            current_year = None
        year_to_use = current_year or (_available_years()[-1] if _available_years() else 2023)
        return create_choropleth_page(mode, year_to_use)

    # Déterminer l'année
    m = re.match(r"btn-carte-year-(\d{4})", button_id)
    if m:
        year = int(m.group(1))
        # lire le mode courant depuis le state caché
        current_mode = dash.callback_context.states.get("carte-mode-flag.children")
        mode = current_mode if current_mode in ("dept", "region", "commune") else "dept"
        return create_choropleth_page(mode, year)

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
    [
        Output("graph-accidents-heure", "figure"),
        Output("graph-accidents-pie", "figure"),
        Output("graph-catv-pie", "figure"),
        Output("graph-motor-pie", "figure"),
        Output("graph-catv-gender", "figure"),
        Output("graph-age-histogram", "figure"),
    ],
    [
        Input("filter-annee", "value"),
        Input("filter-agglomeration", "value"),
        Input("filter-luminosite", "value"),
        Input("filter-atm", "value"),
        Input("filter-usager-sexe", "value"),
        Input("filter-usager-trajet", "value"),
        Input("filter-usager-age-min", "value"),
        Input("filter-usager-age-max", "value"),
        Input("filter-vehicule-catv", "value"),
        Input("filter-vehicule-motor", "value"),
        Input("btn-ts-hour", "n_clicks"),
        Input("btn-ts-day", "n_clicks"),
        Input("btn-ts-month", "n_clicks"),
        Input("btn-ts-weekday", "n_clicks"),
    ],
)
def update_graph_page_charts(
    annee,
    agg_value,
    lum_value,
    atm_value,
    sexe_value,
    trajet_value,
    age_min,
    age_max,
    catv_value,
    motor_value,
    _n_h,
    _n_d,
    _n_m,
    _n_w,
):
    """met à jour la courbe temporelle (heures/jours/mois/jour de semaine) et les camemberts."""
    ctx = dash.callback_context
    year = annee

    # normaliser l'agglo
    if agg_value == "all" or agg_value is None:
        agg_filter = None
    elif agg_value in (1, 2):
        agg_filter = agg_value
    elif isinstance(agg_value, str) and agg_value in ("1", "2"):
        agg_filter = int(agg_value)
    else:
        agg_filter = None

    # normaliser la luminosité
    if lum_value == "all" or lum_value is None:
        lum_filter = None
    elif lum_value in (1, 2, 3, 4, 5):
        lum_filter = lum_value
    elif isinstance(lum_value, str) and lum_value in ("1", "2", "3", "4", "5"):
        lum_filter = int(lum_value)
    else:
        lum_filter = None

    # normaliser les conditions atmosphériques
    if atm_value == "all" or atm_value is None:
        atm_filter = None
    elif atm_value in (1, 2, 3, 4, 5, 6, 7, 8, 9):
        atm_filter = atm_value
    elif isinstance(atm_value, str) and atm_value in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
        atm_filter = int(atm_value)
    else:
        atm_filter = None

    # normaliser filtres usagers
    sexe_filter = None if (sexe_value in (None, "all")) else int(sexe_value)
    trajet_filter = None if (trajet_value in (None, "all")) else int(trajet_value)
    
    # Convertir les âges en années de naissance
    birth_year_min, birth_year_max = (None, None)
    if age_min is not None and age_max is not None:
        # Calculer l'année de naissance correspondante (en utilisant 2024 comme année de référence max)
        birth_year_max = 2024 - int(age_min)  # L'âge min correspond à l'année de naissance max
        birth_year_min = 2024 - int(age_max)  # L'âge max correspond à l'année de naissance min

    # normaliser filtres vehicule
    catv_filter = None if (catv_value in (None, "all")) else int(catv_value)
    motor_filter = None if (motor_value in (None, "all")) else int(motor_value)

    # déterminer l'unité depuis le bouton cliqué
    unit = "hour"
    if ctx.triggered:
        btn = ctx.triggered[0]["prop_id"].split(".")[0]
        if btn == "btn-ts-day":
            unit = "day"
        elif btn == "btn-ts-month":
            unit = "month"
        elif btn == "btn-ts-weekday":
            unit = "weekday"

    return (
        _make_time_series(
            year,
            agg_filter=agg_filter,
            lum_filter=lum_filter,
            atm_filter=atm_filter,
            unit=unit,
            sexe_filter=sexe_filter,
            trajet_filter=trajet_filter,
            birth_year_min=birth_year_min,
            birth_year_max=birth_year_max,
            catv_filter=catv_filter,
            motor_filter=motor_filter,
        ),
        _make_accidents_pie_chart(
            year,
            agg_filter=agg_filter,
            lum_filter=lum_filter,
            atm_filter=atm_filter,
            sexe_filter=sexe_filter,
            trajet_filter=trajet_filter,
            birth_year_min=birth_year_min,
            birth_year_max=birth_year_max,
            catv_filter=catv_filter,
            motor_filter=motor_filter,
        ),
        _make_catv_pie_chart(
            year,
            agg_filter=agg_filter,
            lum_filter=lum_filter,
            atm_filter=atm_filter,
            sexe_filter=sexe_filter,
            trajet_filter=trajet_filter,
            birth_year_min=birth_year_min,
            birth_year_max=birth_year_max,
            catv_filter=catv_filter,
            motor_filter=motor_filter,
        ),
        _make_motor_pie_chart(
            year,
            agg_filter=agg_filter,
            lum_filter=lum_filter,
            atm_filter=atm_filter,
            sexe_filter=sexe_filter,
            trajet_filter=trajet_filter,
            birth_year_min=birth_year_min,
            birth_year_max=birth_year_max,
            catv_filter=catv_filter,
            motor_filter=motor_filter,
        ),
        _make_catv_gender_bar_chart(
            year,
            agg_filter=agg_filter,
            lum_filter=lum_filter,
            atm_filter=atm_filter,
            sexe_filter=sexe_filter,
            trajet_filter=trajet_filter,
            birth_year_min=birth_year_min,
            birth_year_max=birth_year_max,
            catv_filter=catv_filter,
            motor_filter=motor_filter,
        ),
        _make_age_histogram(
            year,
            agg_filter=agg_filter,
            lum_filter=lum_filter,
            atm_filter=atm_filter,
            sexe_filter=sexe_filter,
            trajet_filter=trajet_filter,
            birth_year_min=birth_year_min,
            birth_year_max=birth_year_max,
            catv_filter=catv_filter,
            motor_filter=motor_filter,
        ),
    )


# Réinitialisation des filtres de la page graphique
@callback(
    Output("filter-annee", "value"),
    Output("filter-agglomeration", "value"),
    Output("filter-luminosite", "value"),
    Output("filter-atm", "value"),
    Output("filter-usager-sexe", "value"),
    Output("filter-usager-trajet", "value"),
    Output("filter-usager-age-min", "value"),
    Output("filter-usager-age-max", "value"),
    Output("filter-vehicule-catv", "value"),
    Output("filter-vehicule-motor", "value"),
    Input("btn-reset-filters", "n_clicks"),
    prevent_initial_call=True,
)
def reset_graph_filters(_n_clicks):
    # Valeurs par défaut
    return "all", "all", "all", "all", "all", "all", 18, 99, "all", "all"
