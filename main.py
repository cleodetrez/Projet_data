import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dash
from dash import Dash, html, dcc
from src.pages.home import layout as home_layout

app = Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([home_layout])

if __name__ == "__main__":
    print("Dashboard sur http://127.0.0.1:8050/")
    app.run(debug=True, port=8050)
