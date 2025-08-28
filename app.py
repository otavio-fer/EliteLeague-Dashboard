# app.py (Arquivo Principal - Versão Final)

import dash
import dash_bootstrap_components as dbc
from dash import html
import data_store # Importa o novo arquivo

# --- 1. Inicialização do App ---
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP], assets_folder='assets')
server = app.server

# --- 2. Layout Principal da Aplicação ---
header = html.Div(
    dbc.Row([
        dbc.Col(html.Img(src="/assets/LOGO.png", height="70px", className="ms-3"), width="auto"),
        dbc.Col(html.H2("Elite League Dashboard", className="fw-bolder my-auto ms-3"), width=True),
        dbc.Col(
            dbc.Nav([
                dbc.NavLink(page['name'], href=page["relative_path"], className="fw-bold") for page in dash.page_registry.values()
            ]), width="auto"
        )
    ], align="center", className="py-2 text-white"),
    style={"background": "linear-gradient(90deg, #0d1b2a 0%, #173d61 100%)", "boxShadow": "0 4px 8px 0 rgba(0, 0, 0, 0.4)"},
    className="mb-4"
)

app.layout = dbc.Container(fluid=True, children=[
    header,
    dash.page_container,
    html.Div("Made by Caviar", style={'position': 'fixed', 'bottom': '10px', 'right': '15px', 'fontSize': '12px', 'color': 'grey', 'zIndex': '9999'})
])

# --- 3. Execução do Servidor ---
if __name__ == '__main__':
    app.run(debug=True)