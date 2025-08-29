# pages/3_analise.py (Atualizado)

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
from data_store import df_analise_completo, dfs, cores_times, cor_padrao, logo_mapping

dash.register_page(__name__, name='Análise Detalhada')

# --- Legenda de Estatísticas ---
legenda_accordion = dbc.Accordion([
    dbc.AccordionItem("PPG (Pontos por Jogo): Média de pontos que um jogador marca por partida.", title="PPG"),
    dbc.AccordionItem("RPG (Rebotes por Jogo): Média de rebotes que um jogador pega por partida.", title="RPG"),
    dbc.AccordionItem("APG (Assistências por Jogo): Média de passes que resultam em cesta.", title="APG"),
    dbc.AccordionItem("SPG (Roubos por Jogo): Média de roubos de bola por partida.", title="SPG - Steals per Game"),
    dbc.AccordionItem("BPG (Tocos por Jogo): Média de bloqueios (tocos) por partida.", title="BPG - Blocks per Game"),
    dbc.AccordionItem("MPG (Minutos por Jogo): Estimativa da média de minutos em quadra por partida.", title="MPG - Minutos por Jogo (Estimativa)"),
    dbc.AccordionItem("%FT (Aproveitamento de Lance Livre): Porcentagem de lances livres convertidos.", title="%FT - Free Throw Percentage"),
    dbc.AccordionItem("EFI (Eficiência): Medida geral do valor de um jogador.", title="EFI"),
], start_collapsed=True, flush=True)

# --- Layout da Página de Análise ---
layout = dbc.Container([
    ### ABA PADRÃO DEFINIDA AQUI ###
    dbc.Tabs(active_tab='tab-equipe', children=[
        dbc.Tab(label='Análise Individual', tab_id='tab-individual', children=[
            dbc.Row(dbc.Col(dbc.Card([dbc.CardBody(dcc.Dropdown(id='player-dropdown', options=[{'label': apelido, 'value': apelido} for apelido in sorted(df_analise_completo['APELIDO'].unique())], value=sorted(df_analise_completo['APELIDO'].unique())[0] if not df_analise_completo.empty else None))]), width={"size": 10, "offset": 1}, lg={"size": 6, "offset": 3}, className="my-4")),
            dbc.Row(id='player-stat-cards', justify="center", className="p-4"),
            dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader("Aproveitamento de Arremessos (%)", className="fw-bold"), dbc.CardBody(id='shooting-progress-bars')]), width=12, lg=8, className="mx-auto p-4")], ),
            dbc.Row(dbc.Col(legenda_accordion, width=12, lg=8, className="mx-auto p-4"))
        ]),
        dbc.Tab(label='Análise por Equipe', tab_id='tab-equipe', children=[
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
    
    ### %FT REMOVIDO DOS CARDS ###
    card_style = {'borderTop': '5px solid', 'minHeight': '150px'}
    stats_to_show = {
        "PPG": (player_data['PPG'], "bi-dribbble"), "RPG": (player_data['RPG'], "bi-arrow-down-up"),
        "APG": (player_data['APG'], "bi-people-fill"), "SPG": (player_data['ROUB_PG'], "bi-person-bounding-box"),
        "BPG": (player_data['TOCOS_PG'], "bi-hand-index-thumb-fill"), 
        "MPG": (player_data['MPG'], "bi-clock-history"), "EFI": (player_data['EFI_PG'], "bi-star-fill")
    }
    colors = ["#ff7f0e", "#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
    stat_cards = [dbc.Col(dbc.Card(dbc.CardBody([
                    html.Div([
                        html.I(className=f"{icon} fs-1", style={'color': colors[i]}),
                        html.H2(f"{value:.1f}", className="fw-bolder my-2"),
                        html.P(stat, className="text-muted mb-0 fw-bold")
                    ])
                ], className="text-center"), style={**card_style, 'borderTopColor': colors[i]}), 
                lg=3, md=4, sm=6, className="mb-4") for i, (stat, (value, icon)) in enumerate(stats_to_show.items())]

    ### %FT ADICIONADO ÀS BARRAS DE PROGRESSO ###
    shooting_stats = {"FG%": player_data['%FG']*100, "2P%": player_data['%2P']*100, "3P%": player_data['%3P']*100, "FT%": player_data['%FT']*100}
    progress_bars = []
    colors = ["primary", "info", "success", "danger"]
    for (stat, value), color in zip(shooting_stats.items(), colors):
        bar = html.Div([
            html.Div([html.Span(stat, className="fw-bold"), html.Span(f"{value:.1f}%", className="float-end")], className="mb-1"), 
            dbc.Progress(value=value, color=color, style={"height": "20px"})
        ], className="mb-3")
        progress_bars.append(bar)
        
    return stat_cards, progress_bars

@callback([Output('team-stat-cards', 'children'), Output('points-composition-team', 'figure'), Output('team-logo-display', 'src')], [Input('team-dropdown', 'value')])
def update_team_graphs(selected_team):
    if not selected_team: return [], go.Figure(), ''
    
    team_data = dfs["analise_equipes"][dfs["analise_equipes"]['EQUIPE'] == selected_team].iloc[0]
    cor_time = cores_times.get(selected_team, cor_padrao)
    logo_path = f'/assets/{logo_mapping.get(selected_team, "default.png")}'

    card_style = {'borderTop': '5px solid', 'minHeight': '150px'}
    stats_to_show = {"PPG": (team_data['PPG'], "bi-dribbble", "#ff7f0e"), "RPG": (team_data['RPG'], "bi-arrow-down-up", "#1f77b4"), "APG": (team_data['APG'], "bi-people-fill", "#2ca02c")}
    team_cards = [dbc.Col(dbc.Card(dbc.CardBody([
                    html.Div([
                        html.I(className=f"{icon} fs-1", style={'color': color}),
                        html.H2(f"{value:.1f}", className="fw-bolder my-2"),
                        html.P(stat, className="text-muted mb-0 fw-bold")
                    ])
                ], className="text-center"), style={**card_style, 'borderTopColor': color}), 
                lg=4, md=6, sm=12, className="mb-4") for stat, (value, icon, color) in stats_to_show.items()]

    pontos_2, pontos_3, pontos_ll = team_data['2PM'] * 2, team_data['3PM'] * 3, team_data['FTM']
    composition_data = {'Tipo': ['Pontos de 2', 'Pontos de 3', 'Lances Livres'], 'Pontos': [pontos_2, pontos_3, pontos_ll]}
    fig_composition_team = px.pie(composition_data, names='Tipo', values='Pontos', title="Composição da Pontuação", hole=0.5, template="plotly_dark", color_discrete_sequence=[cor_time, '#636E72', '#B2BEC3'])
    fig_composition_team.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", legend_title_text='', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    fig_composition_team.update_traces(textinfo='percent', textfont_size=16)

    return team_cards, fig_composition_team, logo_path