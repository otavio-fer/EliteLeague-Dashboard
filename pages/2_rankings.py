# pages/2_rankings.py (Atualizado para Múltiplas Ligas)

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from data_store import data, logo_mapping

dash.register_page(__name__, name='Rankings')

# --- Função para Criar Visualização de Ranking (sem alteração) ---
def criar_visual_ranking(df, stat_col, name_col, title, unit="", is_total=True, team_col=None):
    if df.empty or stat_col not in df.columns:
        return [html.H4(title, className="text-center mt-5 mb-4"), dbc.Alert("Não há dados suficientes para exibir este ranking.", color="info")]

    if is_total:
        agg_dict = {stat_col: 'sum'}
        if team_col and team_col in df.columns: agg_dict[team_col] = 'first'
        df_processed = df.groupby(name_col, as_index=False).agg(agg_dict)
    else:
        df_processed = df.copy()
    
    top_10 = df_processed.nlargest(10, stat_col).reset_index(drop=True)
    podium_cards, table = [], None
    medals = ["🥇", "🥈", "🥉"]

    if not top_10.empty:
        cols = {}
        for i in range(min(3, len(top_10))):
            player_or_team = top_10.iloc[i]
            team_name = player_or_team.get(team_col, player_or_team.get(name_col))
            logo_filename = logo_mapping.get(team_name, "default.png")
            logo_src = f"/assets/{logo_filename}"
            card_style = {"height": "100%"}
            card_class = "mb-3"
            if i == 0:
                card_style.update({'transform': 'translateY(-25px)', 'zIndex': 2, 'boxShadow': '0 0 25px rgba(255, 215, 0, 0.7)'})
                card_class += " border-warning border-3"
            cols[str(i+1)] = dbc.Col(dbc.Card([dbc.CardBody([html.H4(f"{medals[i]} {i+1}º Lugar", className="card-title text-center"), html.Img(src=logo_src, height="80px", className="mx-auto d-block my-2", alt=team_name), html.H5(player_or_team[name_col], className="text-center fw-bold"), html.P(f"{player_or_team[stat_col]:.1f} {unit}", className="text-center fs-4")])], style=card_style, className=card_class), lg=4, md=6, sm=12)
        podium_cards.extend([cols.get("2"), cols.get("1"), cols.get("3")])

    if len(top_10) > 3:
        table_rows = [html.Tr([html.Th(f"{i+1}º"), html.Td(top_10.iloc[i][name_col]), html.Td(f"{top_10.iloc[i][stat_col]:.1f}")]) for i in range(3, len(top_10))]
        table_header_name = "Atleta" if team_col else "Equipe"
        table = dbc.Row(dbc.Col(dbc.Table([html.Thead(html.Tr([html.Th("#"), html.Th(table_header_name), html.Th(unit)])), html.Tbody(table_rows)], striped=True, bordered=True, hover=True, size="sm"), width=12, lg={"size": 8, "offset": 2}), className="mt-4")
    
    return [html.H4(title, className="text-center mt-5 mb-4"), dbc.Row([c for c in podium_cards if c], justify="center"), table]

# --- Layout da Página ---
def layout():
    return dbc.Container([
        dbc.Tabs([
            dbc.Tab(label='Ranking de Jogadores', children=[
                dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-ranking-jogadores', value='j_media_pontos', clearable=False), width=12, lg=6, className="mx-auto my-4")),
                html.Div(id='ranking-display-jogadores')
            ]),
            dbc.Tab(label='Ranking de Equipes', children=[
                dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-ranking-equipes', value='e_media_pontos', clearable=False), width=12, lg=6, className="mx-auto my-4")),
                html.Div(id='ranking-display-equipes')
            ])
        ])
    ], fluid=True)

# --- Callbacks para ATUALIZAR as opções dos Dropdowns ---
@callback(
    Output('seletor-ranking-jogadores', 'options'),
    Output('seletor-ranking-equipes', 'options'),
    Input('league-store', 'data')
)
def update_ranking_dropdowns(league):
    opcoes_ranking_jogadores = [
        {'label': 'Média de Pontos (PPG)', 'value': 'j_media_pontos'}, {'label': 'Média de Rebotes (RPG)', 'value': 'j_media_rebotes'},
        {'label': 'Média de Assistências (APG)', 'value': 'j_media_assistencias'}, {'label': 'Média de Roubos de Bola (SPG)', 'value': 'j_media_roubos'},
        {'label': 'Média de Tocos (BPG)', 'value': 'j_media_tocos'}, {'label': 'Eficiência por Jogo', 'value': 'j_media_eficiencia'},
        {'label': 'Total de Pontos', 'value': 'j_total_pontos'}, {'label': 'Total de Rebotes', 'value': 'j_total_rebotes'},
        {'label': 'Total de Assistências', 'value': 'j_total_assistencias'},
    ]
    opcoes_ranking_equipes = [
        {'label': 'Média de Pontos Marcados (PPG)', 'value': 'e_media_pontos'},
        {'label': 'Média de Rebotes (RPG)', 'value': 'e_media_rebotes'},
        {'label': 'Média de Assistências (APG)', 'value': 'e_media_assistencias'},
        {'label': 'Média de Roubos de Bola (SPG)', 'value': 'e_media_roubos'},
        {'label': 'Média de Tocos (BPG)', 'value': 'e_media_tocos'},
        {'label': 'Total de Pontos Marcados', 'value': 'e_total_pontos'},
        {'label': 'Total de Rebotes', 'value': 'e_total_rebotes'},
        {'label': 'Total de Assistências', 'value': 'e_total_assistencias'},
    ]
    return opcoes_ranking_jogadores, opcoes_ranking_equipes

# --- Callbacks para ATUALIZAR os Rankings ---
@callback(
    Output('ranking-display-jogadores', 'children'),
    Input('seletor-ranking-jogadores', 'value'),
    Input('league-store', 'data')
)
def update_player_ranking_display(selected_stat, league):
    league_data = data.get(league, {})
    if not league_data: return "Selecione uma liga."

    df_analise = league_data['df_analise_filtrado']
    df_ranking = league_data['df_ranking_filtrado']

    map_stats = {
        'j_media_pontos': (df_analise, 'PPG', "APELIDO", "Média de Pontos", "PPG", False, "EQUIPE"),
        'j_media_rebotes': (df_analise, 'RPG', "APELIDO", "Média de Rebotes", "RPG", False, "EQUIPE"),
        'j_media_assistencias': (df_analise, 'APG', "APELIDO", "Média de Assistências", "APG", False, "EQUIPE"),
        'j_media_roubos': (df_analise, 'ROUB_PG', "APELIDO", "Média de Roubos de Bola", "SPG", False, "EQUIPE"),
        'j_media_tocos': (df_analise, 'TOCOS_PG', "APELIDO", "Média de Tocos", "BPG", False, "EQUIPE"),
        'j_media_eficiencia': (df_analise, 'EFI_PG', "APELIDO", "Eficiência por Jogo", "EFI", False, "EQUIPE"),
        'j_total_pontos': (df_ranking, 'PONTOS', "APELIDO", "Total de Pontos", "Pontos", True, "EQUIPE"),
        'j_total_rebotes': (df_ranking, 'TOTAL REB', "APELIDO", "Total de Rebotes", "Rebotes", True, "EQUIPE"),
        'j_total_assistencias': (df_ranking, 'AST', "APELIDO", "Total de Assistências", "AST", True, "EQUIPE"),
    }
    params = map_stats.get(selected_stat)
    return criar_visual_ranking(*params) if params else "Selecione uma estatística."

@callback(
    Output('ranking-display-equipes', 'children'),
    Input('seletor-ranking-equipes', 'value'),
    Input('league-store', 'data')
)
def update_team_ranking_display(selected_stat, league):
    league_data = data.get(league, {})
    if not league_data: return "Selecione uma liga."

    dfs = league_data['dfs']
    df_analise_equipes = dfs.get('analise_equipes', pd.DataFrame())
    df_ranking_equipes = dfs.get('ranking_equipes', pd.DataFrame())

    map_stats = {
        'e_media_pontos': (df_analise_equipes, 'PPG', "EQUIPE", "Média de Pontos Marcados", "PPG", False),
        'e_media_rebotes': (df_analise_equipes, 'RPG', "EQUIPE", "Média de Rebotes", "RPG", False),
        'e_media_assistencias': (df_analise_equipes, 'APG', "EQUIPE", "Média de Assistências", "APG", False),
        'e_media_roubos': (df_analise_equipes, 'SPG', "EQUIPE", "Média de Roubos de Bola", "SPG", False),
        'e_media_tocos': (df_analise_equipes, 'BPG', "EQUIPE", "Média de Tocos", "BPG", False),
        'e_total_pontos': (df_ranking_equipes, 'PONTOS MARCADOS', "EQUIPE", "Total de Pontos Marcados", "Pontos", True),
        'e_total_rebotes': (df_ranking_equipes, 'TOTAL REB', "EQUIPE", "Total de Rebotes", "Rebotes", True),
        'e_total_assistencias': (df_ranking_equipes, 'AST', "EQUIPE", "Total de Assistências", "AST", True),
    }
    params = map_stats.get(selected_stat)
    return criar_visual_ranking(*params) if params else "Selecione uma estatística."