# pages/4_premios.py (Atualizado para Múltiplas Ligas)

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from data_store import data, logo_mapping

dash.register_page(__name__, name='Prêmios')

# --- Funções de Visualização (com tratamento para dados vazios) ---
def criar_quadra_all_team(df_team, title):
    if df_team.empty or len(df_team) < 5:
        return dbc.Card([dbc.CardBody(dbc.Alert("Não há jogadoras/jogadores suficientes para formar o time ideal.", color="warning"))])

    fig = go.Figure()
    court_width, court_height = 250, 235
    
    fig.add_shape(type="rect", x0=-court_width, y0=-2, x1=court_width, y1=court_height, line=dict(color="white", width=2))
    fig.add_shape(type="circle", x0=-60, y0=60, x1=60, y1=180, line=dict(color="white", width=2))
    fig.add_shape(type="path", path=f"M -{court_width-30},-2 L -{court_width-30},120 C -{court_width-30},200 {court_width-30},200 {court_width-30},120 L {court_width-30},-2", line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-2, x1=80, y1=110, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-30, y0=-30, x1=30, y1=-2, line=dict(color="white", width=2), fillcolor="gray")

    posicoes = [(-100, 150), (100, 150), (-150, 70), (150, 70), (0, 180)]
    logo_size, font_size = 50, 12

    for i, (index, player) in enumerate(df_team.iterrows()):
        logo_filename = logo_mapping.get(player['EQUIPE'], "default.png")
        fig.add_layout_image(
            dict(source=f"/assets/{logo_filename}", xref="x", yref="y", x=posicoes[i][0], y=posicoes[i][1],
                 sizex=logo_size, sizey=logo_size, xanchor="center", yanchor="middle", sizing="contain")
        )
        fig.add_annotation(
            x=posicoes[i][0], y=posicoes[i][1] - (logo_size/2) - 15, text=f"<b>{player['APELIDO']}</b>", 
            showarrow=False, font=dict(color="white", size=font_size), bgcolor="rgba(0,0,0,0.5)", 
            bordercolor="white", borderwidth=1, borderpad=2, width=100, align="center"
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-court_width-20, court_width+20]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-50, court_height+50]),
        paper_bgcolor="#222222", plot_bgcolor="#222222", height=500, margin=dict(l=10, r=10, t=50, b=10)
    )
    return dbc.Card([dbc.CardBody(dcc.Graph(figure=fig))])

def create_candidates_view(df, stat_col, name_col, title, explanation_text, team_col=None):
    if df.empty or stat_col not in df.columns:
        return [html.H4(title, className="text-center mt-5 mb-4"), dbc.Alert("Não há dados suficientes para esta categoria.", color="info")]

    top_10 = df.nlargest(10, stat_col)
    
    explanation = html.P(explanation_text, className="text-center text-white-50 mb-4")
    
    candidates_list = dbc.ListGroup(
        [dbc.ListGroupItem(
            html.Div([
                html.Img(src=f"/assets/{logo_mapping.get(player[team_col], 'default.png')}", height="40px", className="me-3 rounded-circle"),
                html.Div([
                    html.H5(player[name_col], className="mb-1"),
                    html.Small(player[team_col], className="text-muted"),
                ], className="d-flex flex-column"),
            ], className="d-flex align-items-center")
        ) for _, player in top_10.iterrows()], flush=True
    )
    
    return [
        html.H4(title, className="text-center mt-5 mb-4"),
        dbc.Row(dbc.Col(explanation, width=12, lg=8), justify="center"),
        dbc.Row(dbc.Col(candidates_list, width=12, lg=8), justify="center")
    ]

# --- Layout da Página ---
def layout():
    return dbc.Container([
        dbc.Row(dbc.Col(html.H3("Prêmios da Temporada", className="text-center my-4"))),
        dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-premio', value='mvp', clearable=False), width=12, lg=6, className="mx-auto my-4")),
        html.Div(id='ranking-premio-display')
    ], fluid=True)

# --- Callback para ATUALIZAR as opções dos Dropdowns ---
@callback(
    Output('seletor-premio', 'options'),
    Input('league-store', 'data')
)
def update_awards_dropdown(league):
    opcoes_premios = [
        {'label': 'Corrida para MVP', 'value': 'mvp'},
        {'label': 'Defensor(a) do Ano', 'value': 'dpoy'},
        {'label': 'Corrida para o 1º Time Ideal', 'value': 'all_team_1'},
        {'label': 'Corrida para o 2º Time Ideal', 'value': 'all_team_2'},
    ]
    return opcoes_premios

# --- Callback Principal para ATUALIZAR a Página de Prêmios ---
@callback(
    Output('ranking-premio-display', 'children'),
    Input('seletor-premio', 'value'),
    Input('league-store', 'data')
)
def update_award_ranking_display(selected_award, league):
    league_data = data.get(league, {})
    if not league_data: return dbc.Alert("Selecione uma liga para ver os prêmios.", color="warning")

    df_analise = league_data.get('df_analise_premios_filtrado', pd.DataFrame())
    
    if df_analise.empty:
        return dbc.Alert("Não há dados de prêmios disponíveis para a liga selecionada.", color="info")

    df_sorted = df_analise.sort_values(by='ALL_TEAM_SCORE', ascending=False)
    
    mvp_explanation = ("A corrida para MVP é uma avaliação contínua que considera uma combinação de eficiência, estatísticas individuais (pontos, assistências, rebotes) e o desempenho da equipe (porcentagem de vitórias). Os jogadores abaixo são os que mais se destacaram até o momento.")
    dpoy_explanation = ("A corrida para Defensor(a) do Ano avalia o impacto de um jogador na defesa. São considerados principalmente os roubos de bola, tocos e a capacidade de pegar rebotes. Os jogadores abaixo demonstraram excelência defensiva ao longo da temporada.")

    if selected_award == 'mvp':
        return create_candidates_view(df_analise, 'MVP_SCORE', "APELIDO", "Corrida para MVP", mvp_explanation, team_col="EQUIPE")
    elif selected_award == 'dpoy':
        return create_candidates_view(df_analise, 'DEF_SCORE', "APELIDO", "Corrida para Defensor(a) do Ano", dpoy_explanation, team_col="EQUIPE")
    elif selected_award == 'all_team_1':
        primeiro_time = df_sorted.head(5)
        return criar_quadra_all_team(primeiro_time, "Corrida para o 1º Time Ideal da Liga")
    elif selected_award == 'all_team_2':
        segundo_time = df_sorted.iloc[5:10]
        return criar_quadra_all_team(segundo_time, "Corrida para o 2º Time Ideal da Liga")
    
    return "Selecione um prêmio para ver o ranking."