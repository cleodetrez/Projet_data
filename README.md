# Projet Data
# Dashboard Accidentologie

Notre Dashboard propose une analyse interactive des accidents de la circulation routière et des données de vitesse relevées par radars en France par année.

---

## User Guide

### Installation

**Prérequis**
   - Python 3.8+
**Cloner/télécharger le projet**
   ```bash
   cd c:\Users\icarr\Downloads\projet data\Projet_data
   ```
**Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```
   Manuellement :
   ```bash
   pip install dash dash-bootstrap-components plotly pandas pyproj sqlalchemy
   ```

### Utilisation

#### Mode 1 : Pipeline complet (téléchargement + nettoyage + dashboard)
```bash
python main.py --pipeline --dash
```
#### Mode 2 : Dashboard uniquement (données déjà nettoyées)
```bash
python main.py
```
⏱️ *Durée : < 1 minute*

#### Mode 3 : Pipeline uniquement (sans dashboard)
```bash
python main.py --pipeline
```

### Accès au dashboard

Une fois lancé, il faut accéder au lien ci dessous sur un navigateur du PC :
```
http://127.0.0.1:8050/
```

### Structure des données

- **Données brutes** : `data/raw/`
- **Données nettoyées** : `data/cleaned/` 
- **Base de données SQLite** : `bdd/database.db` 

---

## Data

### Sources de données

1. **Accidents corporels de la circulation routière (2023)**
   - Source : [data.gouv.fr](https://www.data.gouv.fr/)
   - Fichier : `caracteristiques-2023.csv`
   - Colonnes principales : `Num_Acc`, `date`, `heure`, `agg`, `int`, `atm`, `col`, `adr`, `gps_lat`, `gps_lon`
   - Format : CSV 

2. **Vitesses relevées par radars (2023)**
   - Source : [data.gouv.fr](https://www.data.gouv.fr/)
   - Fichier : `radars-2023.csv`
   - Colonnes principales : `position`, `vitesse_moyenne`, `vitesse_max`, `nb_depassements`
   - Format : CSV
   - Projection géographique : Lambert 93 → WGS84 (lat/lon)

### Transformations appliquées

#### Nettoyage des accidents (`clean_caract_2023.py`)
- Parsing des dates/heures au format ISO
- Encodage des variables catégoriques (agg, int, atm, col)
- Suppression des valeurs manquantes critiques
- Filtrage des lignes invalides
- Sortie: `data/cleaned/caract_2023_clean.csv`

#### Nettoyage des radars (`clean_radars_2023.py`)
- Extraction de coordonnées (lat/lon) depuis le champ `position`
- Conversion de projection Lambert 93 → WGS84
- Suppression des enregistrements sans coordonnées valides
- Sortie: `data/cleaned/radars_2023_clean.csv`

#### Fusion (`merge_data.py`)
- Fusion spatiale : accidents et radars par proximité géographique
- Clé primaire : `Num_Acc` (accidents)
- Sortie: `data/cleaned/merged_2023.csv`

---

## Developer Guide

### Architecture du projet

```
Projet_data/
├── main.py                          # Point d'entrée principal
├── dash-01.py                       # Prototype dashboard (optionnel)
├── requirements.txt                 # Dépendances Python
├── README.md                        # Ce fichier
│
├── src/
│   ├── __init__.py
│   ├── pages/                       # Pages Dash
│   │   ├── __init__.py
│   │   ├── home.py                  # Page d'accueil
│   │   └── setup.py                 # Page de chargement
│   │
│   └── utils/                       # Utilitaires
│       ├── __init__.py
│       ├── get_data.py              # Téléchargement + DB
│       ├── clean_caract_2023.py     # Nettoyage accidents
│       ├── clean_radars_2023.py     # Nettoyage radars
│       └── merge_data.py            # Fusion données
│
├── data/
│   ├── raw/                         # Données brutes (téléchargées)
│   └── cleaned/                     # Données nettoyées
│
└── bdd/
    └── database.db                  # Base SQLite (optionnel)
```

### Ajouter une nouvelle page

1. **Créer un fichier dans `src/pages/`**
   ```python
   # filepath: src/pages/ma_page.py
   import dash
   from dash import html, dcc, callback, Input, Output
   import plotly.express as px

   dash.register_page(__name__, path="/ma-page")

   layout = html.Div([
       html.H1("Ma nouvelle page"),
       dcc.Graph(id="mon-graphique"),
   ])

   @callback(
       Output("mon-graphique", "figure"),
       Input("url", "pathname")
   )
   def update_graph(pathname):
       # Charger data/cleaned/merged_2023.csv
       df = pd.read_csv("data/cleaned/merged_2023.csv")
       fig = px.scatter(df, x="gps_lon", y="gps_lat", title="Localisation")
       return fig
   ```

2. **La page apparaît automatiquement** dans le menu de navigation Dash

### Ajouter un graphique à la page d'accueil

Modifiez `src/pages/home.py` :
```python
import plotly.express as px
import pandas as pd

def get_home_figure():
    df = pd.read_csv("data/cleaned/merged_2023.csv")
    fig = px.histogram(df, x="heure", title="Accidents par heure")
    return fig
```

### Structure des fichiers de nettoyage

Chaque script de nettoyage suit ce pattern :
```python
def clean_<dataset>():
    """Nettoie et valide le dataset."""
    input_path = "data/raw/<dataset>.csv"
    output_path = "data/cleaned/<dataset>_clean.csv"
    
    # 1. Charger
    df = pd.read_csv(input_path, sep=";", low_memory=False)
    
    # 2. Valider/transformer
    # ... traitement ...
    
    # 3. Sauvegarder
    df.to_csv(output_path, index=False, sep=";")
    print(f"✓ {output_path} créé")

if __name__ == "__main__":
    clean_<dataset>()
```

---

## Rapport d'analyse

### Résumé exécutif

Ce dashboard analyse **2 jeux de données majeurs** sur l'année 2023 :
- Accidents de la circulation avec blessés/tués
- Vitesses relevées par radars externes

### Conclusions préliminaires

*À remplir après analyse des données*

Exemples de questions/insights possibles :
- Hotspots d'accidents (géographie)
- Corrélation entre vitesse et accidents ?
- Évolutions horaires/mensuelles
- Types d'accidents dominants

### Méthodologie

1. **Collecte** : Data.gouv.fr (données publiques)
2. **Nettoyage** : Suppression anomalies, standardisation formats
3. **Fusion** : Jointure spatiale accidents ↔ radars
4. **Visualisation** : Dashboard interactif Dash + Plotly

---

## Copyright

### Déclaration d'originalité

Je déclare sur l'honneur que le code fourni a été produit par nous-même, à l'exception des éléments listés ci-dessous :

La carte des communes de france : https://github.com/gregoiredavid/france-geojson/tree/master

#### Lignes/concepts empruntés

| Ligne(s) | Source | Explication |
|----------|--------|-------------|
| `src/pages/setup.py` (pattern page Dash) | [Dash Documentation](https://dash.plotly.com/multi-page-apps) | Pattern standard Dash pour multi-page apps |
| `src/utils/get_data.py` (SQLAlchemy usage) | [SQLAlchemy Docs](https://docs.sqlalchemy.org/) | API standard pour ORM Python |
| `src/utils/clean_radars_2023.py` (pyproj) | [pyproj Documentation](https://pyproj4.github.io/pyproj/) | Libraire standard de conversion de projections géographiques |
| `main.py` (argparse for CLI) | [Python argparse](https://docs.python.org/3/library/argparse.html) | Module natif Python pour CLI |

#### Données utilisées

- **Accidents routiers 2023** : Données publiques [data.gouv.fr](https://www.data.gouv.fr/) (domaine public / licence ODbL)
- **Radars 2023** : Données publiques [data.gouv.fr](https://www.data.gouv.fr/) (domaine public / licence ODbL)

#### Toute ligne non déclarée ci-dessus est réputée produite par l'auteur du projet.

---

**Dernière mise à jour** : 12 novembre 2025  
**Version** : 1.0  
**Auteur** : Iris Carron et Cléo Detrez


