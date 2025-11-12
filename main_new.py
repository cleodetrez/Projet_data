"""
main.py : Dashboard Dash unifié (Accidents + Radars)

Usage:
  python main.py --pipeline   # Exécute le pipeline de données
  python main.py             # Lance le dashboard
  python main.py --pipeline --dash  # Exécute pipeline puis lance dashboard
"""
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import plotly.express as px
import dash
from dash import Dash, html, dcc, callback, Input, Output
import json

# Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Chemins des données
CLEAN_DIR = ROOT / "data" / "cleaned"
GEOJSON_PATH = ROOT / "communes.geojson"

# Imports de nettoyage (optionnel)
try:
    from src.utils.get_data import get_caract_2023, get_radar_2023
    from src.utils.clean_caract_2023 import clean_caract
    from src.utils.clean_radars_2023 import clean_radars
    from src.utils.merge_data import merge_cleaned_year
except ImportError as e:
    print(f"⚠ Imports de nettoyage échoués (optionnel) : {e}")

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Utilitaires de données
# ============================================================================

@staticmethod
def load_clean_data(dataset: str = "caract") -> pd.DataFrame:
    """Charge les données nettoyées.
    
    Args:
        dataset: 'caract' (accidents) ou 'radars'
    
    Returns:
        DataFrame avec les données nettoyées
    """
    if dataset == "caract":
        path = CLEAN_DIR / "caract_clean.csv"
    elif dataset == "radars":
        path = CLEAN_DIR / "radars_delta_clean.csv"
    else:
        raise ValueError(f"Dataset inconnu: {dataset}")
    
    if not path.exists():
        raise FileNotFoundError(f"Fichier manquant : {path}")
    
    logger.info(f"Chargement de {path}")
    df = pd.read_csv(path)
    return df


def load_geojson() -> dict:
    """Charge le GeoJSON des départements."""
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"GeoJSON manquant : {GEOJSON_PATH}")
    
    logger.info(f"Chargement du GeoJSON : {GEOJSON_PATH}")
    with GEOJSON_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def detect_featureidkey(geojson: dict) -> str:
    """Détecte automatiquement la clé featureidkey dans le GeoJSON."""
    features = geojson.get("features", [])
    if not features:
        return "properties.code"
    
    props = features[0].get("properties", {})
    candidates = list(props.keys())
    
    for k in ("code", "insee", "dep", "CODE_DEPT", "code_dept", "dept"):
        for pk in candidates:
            if k.lower() in pk.lower():
                return f"properties.{pk}"
    
    return f"properties.{candidates[0]}" if candidates else "properties.code"


# ============================================================================
# Figures Plotly
# ============================================================================

def make_choropleth_map() -> px.choropleth:
    """Crée une carte choroplèthe par département."""
    try:
        # Charger données accidents
        df_accidents = load_clean_data("caract")
        
        # Agrégation par département
        df_dept = df_accidents.groupby("dep").size().reset_index(name="accidents")
        df_dept["dep"] = df_dept["dep"].astype(str).str.zfill(2)
        
        # Charger GeoJSON
        geojson = load_geojson()
        featureidkey = detect_featureidkey(geojson)
        
        # Créer la figure
        fig = px.choropleth(
            df_dept,
            geojson=geojson,
            locations="dep",
            color="accidents",
            featureidkey=featureidkey,
            projection="mercator",
            color_continuous_scale="Blues",
            hover_name="dep",
            labels={"accidents": "Nombre d'accidents"},
            title="Accidentologie par département (France 2023)",
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            height=600,
            template="plotly_white",
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Erreur création carte : {e}")
        return px.scatter(title=f"Erreur : {e}")


def make_speed_histogram() -> px.histogram:
    """Crée un histogramme des vitesses mesurées."""
    try:
        df_radars = load_clean_data("radars")
        
        if df_radars.empty:
            return px.histogram(title="Aucune donnée disponible")
        
        # Sélectionner la colonne vitesse (mesure)
        df_plot = df_radars[["mesure"]].copy()
        df_plot.columns = ["speed"]
        df_plot["speed"] = pd.to_numeric(df_plot["speed"], errors="coerce")
        df_plot = df_plot.dropna(subset=["speed"])
        
        if df_plot.empty:
            return px.histogram(title="Pas de données valides")
        
        fig = px.histogram(
            df_plot,
            x="speed",
            nbins=40,
            title="Distribution des vitesses mesurées (2023)",
            labels={"speed": "Vitesse (km/h)"},
        )
        
        fig.update_layout(
            template="plotly_white",
            bargap=0.05,
            height=500,
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Erreur création histogramme : {e}")
        return px.histogram(title=f"Erreur : {e}")


def make_accidents_by_hour() -> px.histogram:
    """Crée un histogramme des accidents par heure."""
    try:
        df_accidents = load_clean_data("caract")
        
        if df_accidents.empty or "heure" not in df_accidents.columns:
            return px.histogram(title="Aucune donnée disponible")
        
        df_plot = df_accidents[["heure"]].copy()
        df_plot["heure"] = pd.to_numeric(df_plot["heure"], errors="coerce")
        df_plot = df_plot.dropna(subset=["heure"])
        
        if df_plot.empty:
            return px.histogram(title="Pas de données valides")
        
        fig = px.histogram(
            df_plot,
            x="heure",
            nbins=24,
            title="Accidents par heure du jour (2023)",
            labels={"heure": "Heure (0-23)"},
        )
        
        fig.update_layout(
            template="plotly_white",
            bargap=0.05,
            height=500,
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Erreur création histogramme : {e}")
        return px.histogram(title=f"Erreur : {e}")


# ============================================================================
# Initialisation Dash
# ============================================================================

app = Dash(__name__)

app.layout = html.Div([
    html.H1(
        "Dashboard — Accidents et Radars 2023",
        style={"textAlign": "center", "marginBottom": "8px", "color": "#333"}
    ),
    html.P(
        "Vue d'ensemble : accidents corporels et vitesses mesurées en France",
        style={"textAlign": "center", "color": "#666", "marginBottom": "24px"}
    ),
    
    # Conteneur principal
    html.Div([
        # Ligne 1 : Carte choroplèthe
        html.Div([
            dcc.Graph(
                id="choropleth-map",
                figure=make_choropleth_map(),
                style={"marginBottom": "24px"}
            ),
        ], style={
            "maxWidth": "1200px",
            "margin": "0 auto",
            "padding": "16px",
            "backgroundColor": "white",
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        }),
        
        # Ligne 2 : Graphiques côte à côte
        html.Div([
            html.Div([
                dcc.Graph(
                    id="speed-histogram",
                    figure=make_speed_histogram(),
                )
            ], style={"width": "48%", "display": "inline-block", "paddingRight": "2%"}),
            
            html.Div([
                dcc.Graph(
                    id="accidents-by-hour",
                    figure=make_accidents_by_hour(),
                )
            ], style={"width": "48%", "display": "inline-block"}),
        ], style={
            "maxWidth": "1200px",
            "margin": "24px auto",
            "padding": "16px",
            "backgroundColor": "white",
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        }),
        
        # Footer
        html.Div([
            html.P(
                "Données publiques issues de data.gouv.fr • "
                "Source: Caractéristiques des accidents et vitesses radars 2023",
                style={"textAlign": "center", "color": "#999", "fontSize": "12px", "marginTop": "40px"}
            ),
        ], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "16px"}),
        
    ], style={"padding": "16px", "backgroundColor": "#fafafa", "minHeight": "100vh"}),
], style={"fontFamily": "Arial, sans-serif"})


# ============================================================================
# Pipeline données (optionnel)
# ============================================================================

def run_data_pipeline():
    """Exécute le pipeline de données."""
    try:
        logger.info("Démarrage du pipeline de données...")
        
        logger.info("Étape 1 : Téléchargement...")
        get_caract_2023()
        get_radar_2023()
        
        logger.info("Étape 2 : Nettoyage...")
        clean_caract()
        clean_radars()
        
        logger.info("Étape 3 : Fusion...")
        merge_cleaned_year(None, primary_key="acc_id")
        
        logger.info("✓ Pipeline terminé avec succès.")
        return True
    
    except Exception as e:
        logger.error(f"✗ Erreur pipeline : {e}", exc_info=True)
        return False


def check_clean_files_exist() -> bool:
    """Vérifie l'existence des fichiers nettoyés."""
    required = [
        CLEAN_DIR / "caract_clean.csv",
        CLEAN_DIR / "radars_delta_clean.csv",
    ]
    missing = [p for p in required if not p.exists()]
    
    if missing:
        logger.warning(f"Fichiers manquants : {', '.join(str(p) for p in missing)}")
        return False
    
    return True


# ============================================================================
# Point d'entrée principal
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dashboard Accidents & Radars")
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Exécute le pipeline de données (téléchargement + nettoyage)"
    )
    parser.add_argument(
        "--dash",
        action="store_true",
        help="Lance le dashboard"
    )
    
    args = parser.parse_args()
    
    # Si aucun argument, lance juste le dashboard
    if not (args.pipeline or args.dash):
        args.dash = True
    
    # Exécuter le pipeline si demandé
    if args.pipeline:
        success = run_data_pipeline()
        if not success:
            sys.exit(1)
    
    # Lancer le dashboard si demandé
    if args.dash:
        if not check_clean_files_exist():
            logger.error(
                "Fichiers nettoyés manquants. "
                "Exécutez d'abord : python main.py --pipeline"
            )
            sys.exit(1)
        
        logger.info("Lancement du dashboard sur http://127.0.0.1:8050/")
        app.run(debug=False, host="127.0.0.1", port=8050)
