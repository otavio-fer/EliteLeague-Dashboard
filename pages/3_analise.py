# pages/3_analise.py

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
# <<<<<<< CORREÇÃO AQUI >>>>>>>
from data_store import df_analise_completo, dfs 

dash.register_page(__name__, name='Análise Detalhada')

# (O resto do arquivo continua exatamente igual...)
# --- Legenda de Estatísticas ---
legenda_accordion = dbc.Accordion([
    dbc.AccordionItem("PPG (Pontos por Jogo): Média de pontos que um jogador marca por partida.", title="PPG"),
    dbc.AccordionItem("RPG (Rebotes por Jogo): Média de rebotes (ofensivos + defensivos) que um jogador pega por partida.", title="RPG"),
    dbc.AccordionItem("APG (Assistências por Jogo): Média de passes que resultam diretamente em uma cesta de um companheiro de equipe.", title="APG"),
    dbc.AccordionItem("SPG (Roubos por Jogo): Média de roubos de bola por partida.", title="SPG - Steals per Game"),
    dbc.AccordionItem("BPG (Tocos por Jogo): Média de bloqueios (tocos) por partida.", title="BPG - Blocks per Game"),
    dbc.AccordionItem("+/- (Plus/Minus): O saldo de pontos da equipe enquanto o jogador esteve em quadra.", title="+/-"),
    dbc.AccordionItem("EFI (Eficiência): Uma medida geral do valor de um jogador, calculada com a fórmula: (Pontos + Rebotes + Assistências + Roubos + Tocos) - (Arremessos Errados + Lances Livres Errados + Turnovers).", title="EFI"),
], start_collapsed=True)


# --- Layout da Página de Análise ---
layout = dbc.Container([
    dbc.Tabs([
        dbc.Tab(label='Análise Individual', children=[
            dbc.Row(dbc.Col(dbc.Card([dbc.CardBody(dcc.Dropdown(id='player-dropdown', options=[{'label': apelido, 'value': apelido} for apelido in sorted(df_analise_completo['APELIDO'].unique())], value=sorted(df_analise_completo['APELIDO'].unique())[0] if not df_analise_completo.empty else None))]), width={"size": 10, "offset": 1}, lg={"size": 6, "offset": 3}, className="my-4")),
            dbc.Row(id='player-stat-cards', justify="center", className="p-4"),
            dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader("Aproveitamento de Arremessos (%)", className="fw-bold"), dbc.CardBody(id='shooting-progress-bars')]), width=12, lg=8, className="mx-auto p-4")], ),
            dbc.Row(dbc.Col(legenda_accordion, width=12, lg=8, className="mx-auto p-4"))
        ]),
        dbc.Tab(label='Análise por Equipe', children=[
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody(dcc.Dropdown(id='team-dropdown', options=[{'label': equipe, 'value': equipe} for equipe in sorted(dfs["analise_equipes"]['EQUIPE'].unique())], value=sorted(dfs["analise_equipes"]['EQUIPE'].unique())[0]))]), lg=7, sm=12),
                dbc.Col(html.Img(id='team-logo-display', height="150px"), lg=5, sm=12, className="text-center align-self-center mt-3 mt-lg-0")
            ], className="my-4 px-4", justify="center", align="center"),
            dbc.Row(id='team-stat-cards', justify="center", className="p-4"),
            dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='points-composition-team')), width=12, lg=8, className="mx-auto p-4")], )
        ])
    ])
], fluid=True)

# --- Callbacks de Análise ---
@callback(Output('player-stat-cards', 'children'), Output('shooting-progress-bars', 'children'), Input('player-dropdown', 'value'))
def update_player_analysis(selected_player):
    if not selected_player: return [], []
    player_data = df_analise_completo[df_analise_completo['APELIDO'] == selected_player].iloc[0]
    
    card_style = {'borderTop': '5px solid', 'minHeight': '150px'}
    stats_to_show = { "PPG": (player_data['PPG'], "bi-dribbble", "#ff7f0e"), "RPG": (player_data['RPG'], "bi-arrow-down-up", "#1f77b4"), "APG": (player_data['APG'], "bi-people-fill", "#2ca02c"), "SPG": (player_data['ROUB_PG'], "bi-person-bounding-box", "#d62728"), "BPG": (player_data['TOCOS_PG'], "bi-hand-index-thumb-fill", "#9467bd"), "+/-": (player_data['PLUS/MINUS'], "bi-graph-up-arrow", "#8c564b"), "EFI": (player_data['EFI_PG'], "bi-star-fill", "#e377c2") }
    stat_cards = [dbc.Col(dbc.Card(dbc.CardBody([html.Div([html.I(className=f"{icon} fs-1", style={'color': color}), html.H2(f"{value:.1f}", className="fw-bolder my-2"), html.P(stat, className="text-muted mb-0 fw-bold")])], className="text-center"), style={**card_style, 'borderTopColor': color}), lg=3, md=4, sm=6, className="mb-4") for stat, (value, icon, color) in stats_to_show.items()]

    shooting_stats = {"FG%": player_data['%FG']*100, "2P%": player_data['%2P']*100, "3P%": player_data['%3P']*100}
    progress_bars = [html.Div([html.Div([html.Span(stat, className="fw-bold"), html.Span(f"{value:.1f}%", className="float-end")], className="mb-1"), dbc.Progress(value=value, color=color, style={"height": "20px"})], className="mb-3") for (stat, value), color in zip(shooting_stats.items(), ["primary", "info", "success"])]
        
    return stat_cards, progress_bars

@callback([Output('team-stat-cards', 'children'), Output('points-composition-team', 'figure'), Output('team-logo-display', 'src')], [Input('team-dropdown', 'value')])
def update_team_graphs(selected_team):
    if not selected_team: return [], go.Figure(), ''
    
    team_data = dfs["analise_equipes"][dfs["analise_equipes"]['EQUIPE'] == selected_team].iloc[0]
    cores_times = { "DIREITO USP RP": "#FFD700", "MED USP RP": "#87CEEB", "ODONTO USP RP": "#880e4f", "FILÔ USP RP": "#424242", "LUS USP RP": "#00FFFF", "MED UNAERP": "#00008B", "MED BARÃO": "#006400" }
    cor_time = cores_times.get(selected_team, "#66bb6a")
    logo_mapping = { "DIREITO USP RP": "DIREITO USP RP.png", "EDUCA USP RP": "EDUCA USP RP.png", "FILÔ USP RP": "FILÔ USP RP.png", "LUS USP RP": "LUS USP RP.png", "MED BARÃO": "MED BARÃO.png", "MED UNAERP": "MED UNAERP.PNG", "MED USP RP": "MED USP RP.png", "ODONTO USP RP": "ODONTO USP RP.png" }
    logo_path = f'/assets/{logo_mapping.get(selected_team, "default.png")}'

    card_style = {'borderTop': '5px solid', 'minHeight': '150px'}
    stats_to_show = {"PPG": (team_data['PPG'], "bi-dribbble", "#ff7f0e"), "RPG": (team_data['RPG'], "bi-arrow-down-up", "#1f77b4"), "APG": (team_data['APG'], "bi-people-fill", "#2ca02c")}
    team_cards = [dbc.Col(dbc.Card(dbc.CardBody([html.Div([html.I(className=f"{icon} fs-1", style={'color': color}), html.H2(f"{value:.1f}", className="fw-bolder my-2"), html.P(stat, className="text-muted mb-0 fw-bold")])], className="text-center"), style={**card_style, 'borderTopColor': color}), lg=4, md=6, sm=12, className="mb-4") for stat, (value, icon, color) in stats_to_show.items()]

    pontos_2, pontos_3, pontos_ll = team_data['2PM'] * 2, team_data['3PM'] * 3, team_data['FTM']
    composition_data = {'Tipo': ['Pontos de 2', 'Pontos de 3', 'Lances Livres'], 'Pontos': [pontos_2, pontos_3, pontos_ll]}
    fig_composition_team = px.pie(composition_data, names='Tipo', values='Pontos', title="Composição da Pontuação", hole=0.5, template="plotly_dark", color_discrete_sequence=[cor_time, '#636E72', '#B2BEC3'])
    fig_composition_team.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", legend_title_text='', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    fig_composition_team.update_traces(textinfo='percent', textfont_size=16)

    return team_cards, fig_composition_team, logo_path