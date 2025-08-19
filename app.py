# app.py (Versão com Correção de Erros de Tabela, Callback e Limpeza de Nomes)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import sys

# --- 1. Carregar os Dados ---
try:
    sheet_names = {
        "analise_jogadores": "2K25 ELITE LEAGUE",
        "analise_equipes": "2K25 EQUIPES ELITE LEAGUE",
        "ranking_jogadores": "ESTATÍSTICAS ATLETAS",
        "ranking_equipes": "ESTATÍSTICAS EQUIPES"
    }
    dfs = {name: pd.read_excel("ESTATÍSTICAS.xlsx", sheet_name=sheet) for name, sheet in sheet_names.items()}

    for df in dfs.values():
        df.columns = df.columns.astype(str).str.strip()
        
    dfs["analise_jogadores"].rename(columns={'# RPG': 'RPG', '#APG': 'APG'}, inplace=True)
    dfs["analise_equipes"].rename(columns={'# RPG': 'RPG', '#APG': 'APG'}, inplace=True)
    
    dfs["analise_jogadores"]["ROUB_PG"] = (dfs["analise_jogadores"]["ROUB"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
    dfs["analise_jogadores"]["TOCOS_PG"] = (dfs["analise_jogadores"]["TOCOS"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
    dfs["analise_jogadores"]["EFI_PG"] = (dfs["analise_jogadores"]["EFICIÊNCIA"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
    
    ### CORREÇÃO PARA LOGOS (Ex: MED UNAERP) ###
    for key in ["analise_jogadores", "ranking_jogadores", "analise_equipes", "ranking_equipes"]:
        if "EQUIPE" in dfs[key].columns:
            dfs[key]["EQUIPE"] = dfs[key]["EQUIPE"].str.strip()
    
    dfs["analise_equipes"] = dfs["analise_equipes"][dfs["analise_equipes"]["EQUIPE"] != 'TOTAIS'].copy()
    dfs["ranking_equipes"] = dfs["ranking_equipes"][dfs["ranking_equipes"]["EQUIPE"] != 'TOTAIS'].copy()
    
    min_jogos = 2
    jogadores_elegiveis = dfs["analise_jogadores"][dfs["analise_jogadores"]['JOGOS'] >= min_jogos]['APELIDO']
    dfs["analise_jogadores"] = dfs["analise_jogadores"][dfs["analise_jogadores"]['APELIDO'].isin(jogadores_elegiveis)].copy()
    dfs["ranking_jogadores"] = dfs["ranking_jogadores"][dfs["ranking_jogadores"]['APELIDO'].isin(jogadores_elegiveis)].copy()

except Exception as e:
    print(f"ERRO AO LER O ARQUIVO EXCEL: {e}", file=sys.stderr)
    sys.exit()

# Dicionários e Mapeamentos
logo_mapping = {
    "DIREITO USP RP": "DIREITO USP RP.png", "EDUCA USP RP": "EDUCA USP RP.png",
    "FILÔ USP RP": "FILÔ USP RP.png", "LUS USP RP": "LUS USP RP.png",
    "MED BARÃO": "MED BARÃO.png", "MED UNAERP": "MED UNAERP.PNG",
    "MED USP RP": "MED USP RP.png", "ODONTO USP RP": "ODONTO USP RP.png",
}
cores_times = {
    "DIREITO USP RP": "#FFD700", "MED USP RP": "#87CEEB", "ODONTO USP RP": "#880e4f",
    "FILÔ USP RP": "#424242", "LUS USP RP": "#00FFFF", "MED UNAERP": "#00008B", "MED BARÃO": "#006400",
}
cor_padrao = "#66bb6a"
col_j_nome, col_j_equipe = "APELIDO", "EQUIPE"
col_e_nome = "EQUIPE"

# --- 2. Inicialização do App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP], assets_folder='assets')
server = app.server

# --- 3. Função para Criar Visualização de Ranking (Pódio + Tabela) ---
def criar_visual_ranking(df, stat_col, name_col, title, unit="", is_total=True, team_col=None):
    if is_total:
        agg_dict = {stat_col: 'sum'}
        if team_col: agg_dict[team_col] = 'first'
        df_processed = df.groupby(name_col, as_index=False).agg(agg_dict)
    else:
        df_processed = df
    
    top_10 = df_processed.nlargest(10, stat_col).reset_index(drop=True)

    podium_cards, table = [], None
    medals = ["🥇", "🥈", "🥉"]
    
    if len(top_10) > 0:
        cols = {}
        for i in range(min(3, len(top_10))):
            player_or_team = top_10.iloc[i]
            team_name = player_or_team.get(team_col, player_or_team.get(name_col))
            logo_filename = logo_mapping.get(team_name, "default.png") # Adicione uma logo "default.png" se quiser
            logo_src = f"/assets/{logo_filename}"
            
            card_style = {"height": "100%"}
            card_class = "mb-3"
            if i == 0:
                card_style.update({'transform': 'translateY(-25px)', 'zIndex': 2, 'boxShadow': '0 0 25px rgba(255, 215, 0, 0.7)'})
                card_class += " border-warning border-3"
            
            cols[str(i+1)] = dbc.Col(dbc.Card([dbc.CardBody([
                    html.H4(f"{medals[i]} {i+1}º Lugar", className="card-title text-center"),
                    html.Img(src=logo_src, height="80px", className="mx-auto d-block my-2", alt=team_name),
                    html.H5(player_or_team[name_col], className="text-center fw-bold"),
                    html.P(f"{player_or_team[stat_col]:.1f} {unit}", className="text-center fs-4")
                ])], style=card_style, className=card_class), lg=4, md=6, sm=12)
        
        podium_cards.extend([cols.get("2"), cols.get("1"), cols.get("3")])

    if len(top_10) > 3:
        table_rows = [html.Tr([html.Th(f"{i+1}º"), html.Td(top_10.iloc[i][name_col]), html.Td(f"{top_10.iloc[i][stat_col]:.1f}")]) for i in range(3, len(top_10))]
        table_header_name = "Atleta" if team_col else "Equipe"
        ### CORREÇÃO AQUI: REMOVIDO 'dark=True' ###
        table = dbc.Row(dbc.Col(dbc.Table([html.Thead(html.Tr([html.Th("#"), html.Th(table_header_name), html.Th(unit)])), html.Tbody(table_rows)], striped=True, bordered=True, hover=True, size="sm"), width=12, lg={"size": 8, "offset": 2}), className="mt-4")

    return [html.H4(title, className="text-center mt-5 mb-4"), dbc.Row([c for c in podium_cards if c], justify="center"), table]

# --- 4. Layout do Dashboard ---
header = html.Div(
    dbc.Row([
        dbc.Col(html.Img(src="/assets/LOGO.png", height="70px", className="ms-3"), width="auto"),
        dbc.Col(html.H2("Elite League Dashboard", className="fw-bolder my-auto ms-3"), width=True)
    ], align="center", className="py-2 text-white"),
    style={"background": "linear-gradient(90deg, #0d1b2a 0%, #173d61 100%)", "boxShadow": "0 4px 8px 0 rgba(0, 0, 0, 0.4)"},
    className="mb-4"
)

opcoes_ranking_jogadores = [
    {'label': 'Média de Pontos (PPG)', 'value': 'j_media_pontos'}, {'label': 'Média de Rebotes (RPG)', 'value': 'j_media_rebotes'},
    {'label': 'Média de Assistências (APG)', 'value': 'j_media_assistencias'}, {'label': 'Média de Roubos de Bola (SPG)', 'value': 'j_media_roubos'},
    {'label': 'Média de Tocos (BPG)', 'value': 'j_media_tocos'}, {'label': 'Eficiência por Jogo', 'value': 'j_media_eficiencia'},
    {'label': 'Total de Pontos', 'value': 'j_total_pontos'}, {'label': 'Total de Rebotes', 'value': 'j_total_rebotes'},
    {'label': 'Total de Assistências', 'value': 'j_total_assistencias'},
]
opcoes_ranking_equipes = [
    {'label': 'Média de Pontos Marcados (PPG)', 'value': 'e_media_pontos'}, {'label': 'Média de Rebotes (RPG)', 'value': 'e_media_rebotes'},
    {'label': 'Média de Assistências (APG)', 'value': 'e_media_assistencias'}, {'label': 'Total de Pontos Marcados', 'value': 'e_total_pontos'},
    {'label': 'Total de Rebotes', 'value': 'e_total_rebotes'}, {'label': 'Total de Assistências', 'value': 'e_total_assistencias'},
]

app.layout = dbc.Container(fluid=True, children=[
    header,
    dbc.Tabs(id="tabs-principal", active_tab='tab-ranking-jogadores', children=[
        dbc.Tab(label='🏆 Ranking de Jogadores', tab_id='tab-ranking-jogadores', children=[
            dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-ranking-jogadores', options=opcoes_ranking_jogadores, value='j_media_pontos', clearable=False), width=12, lg=6, className="mx-auto my-4")),
            html.Div(id='ranking-display-jogadores')
        ]),
        dbc.Tab(label='🏆 Ranking de Equipes', tab_id='tab-ranking-equipes', children=[
            dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-ranking-equipes', options=opcoes_ranking_equipes, value='e_media_pontos', clearable=False), width=12, lg=6, className="mx-auto my-4")),
            html.Div(id='ranking-display-equipes')
        ]),
        dbc.Tab(label='🔎 Análise Individual', tab_id='tab-jogadores', children=[
            dbc.Row(dbc.Col(dbc.Card([dbc.CardBody(dcc.Dropdown(id='player-dropdown', options=[{'label': apelido, 'value': apelido} for apelido in sorted(dfs["analise_jogadores"][col_j_nome].unique())], value=sorted(dfs["analise_jogadores"][col_j_nome].unique())[0] if not dfs["analise_jogadores"].empty else None))]), width={"size": 10, "offset": 1}, lg={"size": 6, "offset": 3}, className="my-4")),
            dbc.Row(id='player-stat-cards', justify="center", className="p-4"),
            dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader("Aproveitamento de Arremessos (%)", className="fw-bold"), dbc.CardBody(id='shooting-progress-bars')]), width=12, lg=8, className="mx-auto p-4")], )
        ]),
        dbc.Tab(label='🔎 Análise por Equipe', tab_id='tab-equipes', children=[
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody(dcc.Dropdown(id='team-dropdown', options=[{'label': equipe, 'value': equipe} for equipe in sorted(dfs["analise_equipes"][col_e_nome].unique())], value=sorted(dfs["analise_equipes"][col_e_nome].unique())[0]))]), lg=7, sm=12),
                dbc.Col(html.Img(id='team-logo-display', height="150px"), lg=5, sm=12, className="text-center align-self-center mt-3 mt-lg-0")
            ], className="my-4 px-4", justify="center", align="center"),
            dbc.Row(id='team-stat-cards', justify="center", className="p-4"),
            dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='points-composition-team')), width=12, lg=8, className="mx-auto p-4")], )
        ])
    ]),
    
    ### ASSINATURA ADICIONADA AQUI ###
    html.Div(
        "Made by Caviar",
        style={
            'position': 'fixed',
            'bottom': '10px',
            'right': '15px',
            'fontSize': '12px',
            'color': 'grey',
            'zIndex': '9999'
        }
    )
])

# --- 5. Callbacks ---
@app.callback(Output('ranking-display-jogadores', 'children'), Input('seletor-ranking-jogadores', 'value'))
def update_player_ranking_display(selected_stat):
    df_media, df_total = dfs["analise_jogadores"], dfs["ranking_jogadores"]
    ### CORREÇÃO AQUI: ORDEM DOS ARGUMENTOS AJUSTADA ###
    map_stats = {
        'j_media_pontos':       (df_media, 'PPG', col_j_nome, "Média de Pontos", "PPG", False, col_j_equipe),
        'j_media_rebotes':      (df_media, 'RPG', col_j_nome, "Média de Rebotes", "RPG", False, col_j_equipe),
        'j_media_assistencias': (df_media, 'APG', col_j_nome, "Média de Assistências", "APG", False, col_j_equipe),
        'j_media_roubos':       (df_media, 'ROUB_PG', col_j_nome, "Média de Roubos de Bola", "SPG", False, col_j_equipe),
        'j_media_tocos':        (df_media, 'TOCOS_PG', col_j_nome, "Média de Tocos", "BPG", False, col_j_equipe),
        'j_media_eficiencia':   (df_media, 'EFI_PG', col_j_nome, "Eficiência por Jogo", "EFI", False, col_j_equipe),
        'j_total_pontos':       (df_total, 'PONTOS', col_j_nome, "Total de Pontos", "Pontos", True, col_j_equipe),
        'j_total_rebotes':      (df_total, 'TOTAL REB', col_j_nome, "Total de Rebotes", "Rebotes", True, col_j_equipe),
        'j_total_assistencias': (df_total, 'AST', col_j_nome, "Total de Assistências", "AST", True, col_j_equipe),
    }
    params = map_stats.get(selected_stat)
    return criar_visual_ranking(*params) if params else "Selecione uma estatística."

@app.callback(Output('ranking-display-equipes', 'children'), Input('seletor-ranking-equipes', 'value'))
def update_team_ranking_display(selected_stat):
    df_media, df_total = dfs["analise_equipes"], dfs["ranking_equipes"]
    ### CORREÇÃO AQUI: ORDEM DOS ARGUMENTOS AJUSTADA ###
    map_stats = {
        'e_media_pontos':       (df_media, 'PPG', col_e_nome, "Média de Pontos Marcados", "PPG", False),
        'e_media_rebotes':      (df_media, 'RPG', col_e_nome, "Média de Rebotes", "RPG", False),
        'e_media_assistencias': (df_media, 'APG', col_e_nome, "Média de Assistências", "APG", False),
        'e_total_pontos':       (df_total, 'PONTOS MARCADOS', col_e_nome, "Total de Pontos Marcados", "Pontos", True),
        'e_total_rebotes':      (df_total, 'TOTAL REB', col_e_nome, "Total de Rebotes", "Rebotes", True),
        'e_total_assistencias': (df_total, 'AST', col_e_nome, "Total de Assistências", "AST", True),
    }
    params = map_stats.get(selected_stat)
    return criar_visual_ranking(*params) if params else "Selecione uma estatística."

@app.callback(Output('player-stat-cards', 'children'), Output('shooting-progress-bars', 'children'), Input('player-dropdown', 'value'))
def update_player_analysis(selected_player):
    if not selected_player: return [], []
    player_data = dfs["analise_jogadores"][dfs["analise_jogadores"][col_j_nome] == selected_player].iloc[0]
    
    card_style = {'borderTop': '5px solid', 'minHeight': '150px'}
    stats_to_show = {
        "PPG": (player_data['PPG'], "bi-dribbble", "#ff7f0e"), "RPG": (player_data['RPG'], "bi-arrow-down-up", "#1f77b4"),
        "APG": (player_data['APG'], "bi-people-fill", "#2ca02c"), "SPG": (player_data['ROUB_PG'], "bi-person-bounding-box", "#d62728"),
        "BPG": (player_data['TOCOS_PG'], "bi-hand-index-thumb-fill", "#9467bd"), "+/-": (player_data['PLUS/MINUS'], "bi-graph-up-arrow", "#8c564b"), "EFI": (player_data['EFI_PG'], "bi-star-fill", "#e377c2")
    }
    stat_cards = [dbc.Col(dbc.Card(dbc.CardBody([
                    html.Div([
                        html.I(className=f"{icon} fs-1", style={'color': color}),
                        html.H2(f"{value:.1f}", className="fw-bolder my-2"),
                        html.P(stat, className="text-muted mb-0 fw-bold")
                    ])
                ], className="text-center"), style={**card_style, 'borderTopColor': color}), 
                lg=3, md=4, sm=6, className="mb-4") for stat, (value, icon, color) in stats_to_show.items()]

    shooting_stats = {"FG%": player_data['%FG']*100, "2P%": player_data['%2P']*100, "3P%": player_data['%3P']*100}
    progress_bars = []
    colors = ["primary", "info", "success"]
    for (stat, value), color in zip(shooting_stats.items(), colors):
        bar = html.Div([
            html.Div([html.Span(stat, className="fw-bold"), html.Span(f"{value:.1f}%", className="float-end")], className="mb-1"),
            dbc.Progress(value=value, color=color, style={"height": "20px"})
        ], className="mb-3")
        progress_bars.append(bar)
        
    return stat_cards, progress_bars

@app.callback([Output('team-stat-cards', 'children'), Output('points-composition-team', 'figure'), Output('team-logo-display', 'src')], [Input('team-dropdown', 'value')])
def update_team_graphs(selected_team):
    if not selected_team: return [], go.Figure(), ''
    
    team_data = dfs["analise_equipes"][dfs["analise_equipes"][col_e_nome] == selected_team].iloc[0]
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

# --- 6. Execução do Servidor ---
if __name__ == '__main__':
    app.run(debug=True)