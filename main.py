"""
main.py : Point d'entrée principal de l'application (version Flask + Plotly).
"""
import sys
from pathlib import Path

# Ajouter la racine du projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, render_template_string
import plotly.express as px
import pandas as pd

# Charger les données une seule fois (tu peux garder cette logique)
try:
    from src.utils.get_data import query_db
except Exception as e:
    print(f"⚠ Erreur import query_db: {e}")

app = Flask(__name__)

@app.route("/")
def home():
    # Exemple : graphique barres top départements
    try:
        sql = """
        SELECT dep AS dept, COUNT(*) AS accidents
        FROM caracteristiques
        WHERE annee = :year
        GROUP BY dep
        ORDER BY accidents DESC
        LIMIT 10
        """
        df = query_db(sql, {"year": 2023})
        if df is None or df.empty:
            fig1 = px.bar(title="Aucune donnée disponible")
        else:
            fig1 = px.bar(df, x="dept", y="accidents", title="Top 10 départements (2023)")
    except Exception as e:
        fig1 = px.bar(title=f"Erreur: {e}")

    graph1 = fig1.to_html(full_html=False)

    # Exemple : histogramme des vitesses
    try:
        sql = """
        SELECT mesure AS speed FROM radars
        WHERE mesure IS NOT NULL LIMIT 5000
        """
        df2 = query_db(sql)
        if df2 is None or df2.empty:
            fig2 = px.histogram(title="Aucune donnée")
        else:
            df2["speed"] = pd.to_numeric(df2["speed"], errors="coerce")
            df2 = df2.dropna(subset=["speed"])
            fig2 = px.histogram(df2, x="speed", nbins=40, title="Distribution des vitesses")
    except Exception as e:
        fig2 = px.histogram(title=f"Erreur: {e}")

    graph2 = fig2.to_html(full_html=False)

    # Affichage dans une page HTML simple
    return render_template_string("""
    <html>
    <head>
        <title>Dashboard Accidents et Radars (Flask)</title>
    </head>
    <body>
        <h1>Dashboard Accidents et Radars (Flask)</h1>
        <div style="max-width:1100px; margin:24px auto; padding:12px;">
            {{ graph1|safe }}
        </div>
        <div style="max-width:1100px; margin:24px auto; padding:12px;">
            {{ graph2|safe }}
        </div>
    </body>
    </html>
    """, graph1=graph1, graph2=graph2)

if __name__ == '__main__':
    print("Lancement du dashboard sur http://127.0.0.1:5000/")
    app.run(debug=True)