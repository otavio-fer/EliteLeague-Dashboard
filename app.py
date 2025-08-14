# app.py 

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

except Exception as e:
    print(f"ERRO AO LER O ARQUIVO EXCEL: {e}", file=sys.stderr)
    sys.exit()

# --- NOVO: Dicionário de Cores dos Times ATUALIZADO ---
cores_times = {
    "DIREITO USP RP": "#FFD700",  # Dourado
    "MED USP RP": "#87CEEB",      # Azul Claro
    "ODONTO USP RP": "#880e4f",   # Vinho
    "FILÔ USP RP": "#212121",     # Preto/Cinza
    "LUS USP RP": "#00FFFF",      # Ciano
    "MED UNAERP": "#00008B",      # Azul Escuro
    "MED BARÃO": "#006400",       # Verde Escuro
    "TOTAIS" : "#212121",         #Preto/Cinza
}
cor_padrao = "#66bb6a" # Verde para a EDUCA USP RP e outros times sem cor definida

# --- 2. Função para criar Gráficos de Ranking ---
def criar_grafico_ranking(df, coluna_valor, coluna_nome, titulo, cor_barra):
    df_agrupado = df.groupby(coluna_nome, as_index=False)[coluna_valor].sum()
    df_agrupado[coluna_valor] = pd.to_numeric(df_agrupado[coluna_valor], errors='coerce')
    df_agrupado.dropna(subset=[coluna_valor, coluna_nome], inplace=True)
    top_10 = df_agrupado.nlargest(10, coluna_valor)

    fig = px.bar(top_10, x=coluna_valor, y=coluna_nome, orientation='h', text_auto=True, template="plotly_white")
    fig.update_layout(
        title_text=titulo, title_x=0.5, yaxis_title=None, xaxis_title=None,
        yaxis={'categoryorder':'total ascending'}, uniformtext_minsize=8, uniformtext_mode='hide',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_traces(marker_color=cor_barra, textposition='outside', textfont_size=12)
    return fig

# --- 3. Nomes das colunas e criação dos gráficos de ranking ---
col_jogador_pontos = "PONTOS"
col_jogador_rebotes = "TOTAL REB"
col_jogador_assistencias = "AST"
col_jogador_roubos = "ROUB"
col_jogador_nome = "APELIDO"
col_equipe_pontos_marcados = "PONTOS MARCADOS"
col_equipe_pontos_sofridos = "PONTOS SOFRIDOS"
col_equipe_rebotes = "TOTAL REB"
col_equipe_nome = "EQUIPE"

cores_ranking = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

fig_cestinhas = criar_grafico_ranking(dfs["ranking_jogadores"], col_jogador_pontos, col_jogador_nome, 'Top 10 Cestinhas (Total)', cores_ranking[0])
fig_rebotes = criar_grafico_ranking(dfs["ranking_jogadores"], col_jogador_rebotes, col_jogador_nome, 'Top 10 Reboteiros (Total)', cores_ranking[1])
fig_assistencias = criar_grafico_ranking(dfs["ranking_jogadores"], col_jogador_assistencias, col_jogador_nome, 'Top 10 em Assistências (Total)', cores_ranking[2])
fig_roubos = criar_grafico_ranking(dfs["ranking_jogadores"], col_jogador_roubos, col_jogador_nome, 'Top 10 em Roubos de Bola (Total)', cores_ranking[3])

fig_equipes_pontos = criar_grafico_ranking(dfs["ranking_equipes"], col_equipe_pontos_marcados, col_equipe_nome, 'Equipes com Mais Pontos Marcados', cores_ranking[0])
fig_equipes_defesa = criar_grafico_ranking(dfs["ranking_equipes"], col_equipe_pontos_sofridos, col_equipe_nome, 'Equipes com Menos Pontos Sofridos', cores_ranking[1])
fig_equipes_rebotes = criar_grafico_ranking(dfs["ranking_equipes"], col_equipe_rebotes, col_equipe_nome, 'Equipes com Mais Rebotes', cores_ranking[2])

# Lógica para encontrar logos das equipes líderes
df_equipes_total = dfs["ranking_equipes"].groupby(col_equipe_nome).sum(numeric_only=True).reset_index()

logo_ext = ".png" # Assumindo .png, mude se for .jpg para alguns
top_ataque_logo = f'/assets/{df_equipes_total.loc[df_equipes_total[col_equipe_pontos_marcados].idxmax()][col_equipe_nome]}{logo_ext}'
top_defesa_logo = f'/assets/{df_equipes_total.loc[df_equipes_total[col_equipe_pontos_sofridos].idxmin()][col_equipe_nome]}{logo_ext}'
top_rebote_logo = f'/assets/{df_equipes_total.loc[df_equipes_total[col_equipe_rebotes].idxmax()][col_equipe_nome]}{logo_ext}'


# --- 4. Inicialização do App com Tema Bootstrap ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], assets_folder='assets')
server = app.server

# --- 5. Layout do Dashboard com Bootstrap ---
app.layout = dbc.Container(fluid=True, style={'backgroundColor': '#f8f9fa'}, children=[
    dbc.Row(dbc.Col(html.H1("Dashboard de Estatísticas - Elite League", className="text-center my-4"), width=12)),
    dbc.Tabs(id="tabs-principal", active_tab='tab-ranking-jogadores', children=[
        
        dbc.Tab(label='🏆 Ranking de Jogadores', tab_id='tab-ranking-jogadores', children=[
            dbc.Row(className="p-4", children=[
                dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_cestinhas))]), md=6, className="mb-4"),
                dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_rebotes))]), md=6, className="mb-4"),
                dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_assistencias))]), md=6, className="mb-4"),
                dbc.Col(dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_roubos))]), md=6, className="mb-4"),
            ])]),
        
        dbc.Tab(label='🏆 Ranking de Equipes', tab_id='tab-ranking-equipes', children=[
            dbc.Row(className="p-4", children=[
                dbc.Col(dbc.Card([html.H4("Melhor Ataque", className="card-title text-center mt-3"), html.Img(src=top_ataque_logo, height="80px", className="mx-auto d-block"), dbc.CardBody(dcc.Graph(figure=fig_equipes_pontos))]), md=4, className="mb-4"),
                dbc.Col(dbc.Card([html.H4("Melhor Defesa", className="card-title text-center mt-3"), html.Img(src=top_defesa_logo, height="80px", className="mx-auto d-block"), dbc.CardBody(dcc.Graph(figure=fig_equipes_defesa))]), md=4, className="mb-4"),
                dbc.Col(dbc.Card([html.H4("Mais Rebotes", className="card-title text-center mt-3"), html.Img(src=top_rebote_logo, height="80px", className="mx-auto d-block"), dbc.CardBody(dcc.Graph(figure=fig_equipes_rebotes))]), md=4, className="mb-4"),
            ])]),

        dbc.Tab(label='🔎 Análise Individual', tab_id='tab-jogadores', children=[
            dbc.Row(dbc.Col(dbc.Card([dbc.CardHeader("Selecione o Atleta"), dbc.CardBody(dcc.Dropdown(id='player-dropdown', options=[{'label': apelido, 'value': apelido} for apelido in sorted(dfs["analise_jogadores"]['APELIDO'].unique())], value=sorted(dfs["analise_jogadores"]['APELIDO'].unique())[0]))]), width={"size": 6, "offset": 3}, className="my-4")),
            dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='stats-graph-player')), md=6), dbc.Col(dbc.Card(dcc.Graph(id='shooting-graph-player')), md=6)], className="p-4")]),

        dbc.Tab(label='🔎 Análise por Equipe', tab_id='tab-equipes', children=[
             dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("Selecione a Equipe"), dbc.CardBody(dcc.Dropdown(id='team-dropdown', options=[{'label': equipe, 'value': equipe} for equipe in sorted(dfs["analise_equipes"]['EQUIPE'].unique())], value=sorted(dfs["analise_equipes"]['EQUIPE'].unique())[0]))]), md=8),
                dbc.Col(html.Img(id='team-logo-display', height="150px"), md=4, className="text-center align-self-center")
             ], className="my-4", justify="center", align="center"),
            dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='stats-graph-team')), md=6), dbc.Col(dbc.Card(dcc.Graph(id='points-composition-team')), md=6)], className="p-4")
        ])
    ])
])

# --- 6. Callbacks ---
@app.callback(
    [Output('stats-graph-player', 'figure'), Output('shooting-graph-player', 'figure')],
    [Input('player-dropdown', 'value')])
def update_player_graphs(selected_player):
    if not selected_player: return go.Figure(), go.Figure()
    player_data = dfs["analise_jogadores"][dfs["analise_jogadores"]['APELIDO'] == selected_player].iloc[0]
    stats_player = {'PPG': player_data['PPG'], 'RPG': player_data['RPG'], 'APG': player_data['APG']}
    fig_stats_player = px.bar(x=list(stats_player.keys()), y=list(stats_player.values()), title=f"Médias por Jogo - {selected_player}", text_auto=True, template="plotly_white")
    fig_stats_player.update_traces(marker_color='#5c6bc0')
    shooting_player = {'%FG': player_data['%FG']*100, '%2P': player_data['%2P']*100, '%3P': player_data['%3P']*100}
    fig_shooting_player = px.bar(x=list(shooting_player.keys()), y=list(shooting_player.values()), title=f"Aproveitamento (%) - {selected_player}", text_auto=".2f", template="plotly_white")
    fig_shooting_player.update_layout(yaxis_range=[0,100])
    fig_shooting_player.update_traces(marker_color='#42a5f5')
    return fig_stats_player, fig_shooting_player

@app.callback(
    [Output('stats-graph-team', 'figure'), Output('points-composition-team', 'figure'), Output('team-logo-display', 'src')],
    [Input('team-dropdown', 'value')])
def update_team_graphs(selected_team):
    if not selected_team: return go.Figure(), go.Figure(), ''
    
    team_data = dfs["analise_equipes"][dfs["analise_equipes"]['EQUIPE'] == selected_team].iloc[0]
    
    cor_time = cores_times.get(selected_team, cor_padrao)
    logo_path = f'/assets/{selected_team}{logo_ext}'

    stats_team = {'PPG': team_data['PPG'], 'RPG': team_data['RPG'], 'APG': team_data['APG']}
    fig_stats_team = px.bar(x=list(stats_team.keys()), y=list(stats_team.values()), title=f"Médias por Jogo - {selected_team}", text_auto=True, template="plotly_white")
    fig_stats_team.update_traces(marker_color=cor_time)
    
    pontos_2 = team_data['2PM'] * 2; pontos_3 = team_data['3PM'] * 3; pontos_ll = team_data['FTM']
    composition_data = {'Tipo': ['Pontos de 2', 'Pontos de 3', 'Lances Livres'], 'Pontos': [pontos_2, pontos_3, pontos_ll]}
    fig_composition_team = px.pie(composition_data, names='Tipo', values='Pontos', title=f"Composição da Pontuação - {selected_team}", hole=0.4, template="plotly_white", color_discrete_sequence=[cor_time, '#a9a9a9', '#d3d3d3'])
    
    return fig_stats_team, fig_composition_team, logo_path

# --- 7. Execução do Servidor ---
if __name__ == '__main__':
    app.run(debug=True)