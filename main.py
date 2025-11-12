"""
main.py : Point d'entrée principal de l'application (Flask + Plotly)
Appelle le Blueprint de la carte et affiche un histogramme en page d'accueil.
"""
import sys
from pathlib import Path
from flask import Flask, render_template_string
import plotly.express as px
import pandas as pd

# Ajouter la racine du projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importer la fonction d’accès aux données
try:
    from src.utils.get_data import query_db
except Exception as e:
    print(f"⚠ Erreur import query_db: {e}")

# Importer le blueprint de la carte
from src.pages.carte import carte_bp

# Créer l’app Flask
app = Flask(__name__)
app.register_blueprint(carte_bp)  # 🔹 <-- Enregistrement du blueprint /carte

# --- Page d’accueil avec l’histogramme ---
@app.route("/")
def home():
    """Page d’accueil : affiche uniquement l’histogramme."""
    try:
        sql = """
        SELECT mesure AS speed FROM radars
        WHERE mesure IS NOT NULL LIMIT 5000
        """
        df = query_db(sql)

        if df is None or df.empty:
            fig = px.histogram(title="Aucune donnée disponible")
        else:
            df["speed"] = pd.to_numeric(df["speed"], errors="coerce")
            df = df.dropna(subset=["speed"])
            fig = px.histogram(df, x="speed", nbins=40, title="Distribution des vitesses (radars)")
            fig.update_layout(template="plotly_white", bargap=0.1)

    except Exception as e:
        fig = px.histogram(title=f"Erreur : {e}")

    graph_html = fig.to_html(full_html=False)

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Radars </title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #fafafa;
                margin: 0;
                padding: 0;
            }
            h1 {
                text-align: center;
                color: #333;
                padding-top: 20px;
            }
            .graph-container {
                max-width: 1100px;
                margin: 24px auto;
                padding: 16px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            a {
                display: block;
                text-align: center;
                margin-top: 20px;
                font-size: 18px;
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Dashboard Radars (Flask)</h1>
        <div class="graph-container">
            <h2>Histogramme — Vitesses mesurées</h2>
            {{ graph_html|safe }}
        </div>
        <a href="/carte">➡ Voir la carte choroplèthe</a>
    </body>
    </html>
    """, graph_html=graph_html)


if __name__ == "__main__":
    print("Application Flask lancée sur http://127.0.0.1:5000/")
    app.run(debug=True)
