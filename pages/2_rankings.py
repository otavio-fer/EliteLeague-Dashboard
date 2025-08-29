# pages/2_rankings.py (Atualizado)

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
from data_store import df_analise_filtrado, df_ranking_filtrado, dfs

dash.register_page(__name__, name='Rankings')

# (A função criar_visual_ranking permanece a mesma)
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
    logo_mapping = dfs['logo_mapping']

    if len(top_10) > 0:
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

# --- Layout da Página de Rankings ---
opcoes_ranking_jogadores = [
    {'label': 'Média de Pontos (PPG)', 'value': 'j_media_pontos'}, {'label': 'Média de Rebotes (RPG)', 'value': 'j_media_rebotes'},
    {'label': 'Média de Assistências (APG)', 'value': 'j_media_assistencias'}, {'label': 'Média de Roubos de Bola (SPG)', 'value': 'j_media_roubos'},
    {'label': 'Média de Tocos (BPG)', 'value': 'j_media_tocos'}, {'label': 'Eficiência por Jogo', 'value': 'j_media_eficiencia'},
    {'label': 'Total de Pontos', 'value': 'j_total_pontos'}, {'label': 'Total de Rebotes', 'value': 'j_total_rebotes'},
    {'label': 'Total de Assistências', 'value': 'j_total_assistencias'},
]
### NOVAS OPÇÕES AQUI ###
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

layout = dbc.Container([
    dbc.Tabs([
        dbc.Tab(label='Ranking de Jogadores', children=[
            dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-ranking-jogadores', options=opcoes_ranking_jogadores, value='j_media_pontos', clearable=False), width=12, lg=6, className="mx-auto my-4")),
            html.Div(id='ranking-display-jogadores')
        ]),
        dbc.Tab(label='Ranking de Equipes', children=[
            dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-ranking-equipes', options=opcoes_ranking_equipes, value='e_media_pontos', clearable=False), width=12, lg=6, className="mx-auto my-4")),
            html.Div(id='ranking-display-equipes')
        ])
    ])
], fluid=True)

# --- Callbacks dos Rankings ---
@callback(Output('ranking-display-jogadores', 'children'), Input('seletor-ranking-jogadores', 'value'))
def update_player_ranking_display(selected_stat):
    map_stats = {
        'j_media_pontos': (df_analise_filtrado, 'PPG', "APELIDO", "Média de Pontos", "PPG", False, "EQUIPE"),
        'j_media_rebotes': (df_analise_filtrado, 'RPG', "APELIDO", "Média de Rebotes", "RPG", False, "EQUIPE"),
        'j_media_assistencias': (df_analise_filtrado, 'APG', "APELIDO", "Média de Assistências", "APG", False, "EQUIPE"),
        'j_media_roubos': (df_analise_filtrado, 'ROUB_PG', "APELIDO", "Média de Roubos de Bola", "SPG", False, "EQUIPE"),
        'j_media_tocos': (df_analise_filtrado, 'TOCOS_PG', "APELIDO", "Média de Tocos", "BPG", False, "EQUIPE"),
        'j_media_eficiencia': (df_analise_filtrado, 'EFI_PG', "APELIDO", "Eficiência por Jogo", "EFI", False, "EQUIPE"),
        'j_total_pontos': (df_ranking_filtrado, 'PONTOS', "APELIDO", "Total de Pontos", "Pontos", True, "EQUIPE"),
        'j_total_rebotes': (df_ranking_filtrado, 'TOTAL REB', "APELIDO", "Total de Rebotes", "Rebotes", True, "EQUIPE"),
        'j_total_assistencias': (df_ranking_filtrado, 'AST', "APELIDO", "Total de Assistências", "AST", True, "EQUIPE"),
    }
    params = map_stats.get(selected_stat)
    return criar_visual_ranking(*params) if params else "Selecione uma estatística."

@callback(Output('ranking-display-equipes', 'children'), Input('seletor-ranking-equipes', 'value'))
def update_team_ranking_display(selected_stat):
    ### NOVAS OPÇÕES AQUI ###
    map_stats = {
        'e_media_pontos': (dfs['analise_equipes'], 'PPG', "EQUIPE", "Média de Pontos Marcados", "PPG", False),
        'e_media_rebotes': (dfs['analise_equipes'], 'RPG', "EQUIPE", "Média de Rebotes", "RPG", False),
        'e_media_assistencias': (dfs['analise_equipes'], 'APG', "EQUIPE", "Média de Assistências", "APG", False),
        'e_media_roubos': (dfs['analise_equipes'], 'SPG', "EQUIPE", "Média de Roubos de Bola", "SPG", False),
        'e_media_tocos': (dfs['analise_equipes'], 'BPG', "EQUIPE", "Média de Tocos", "BPG", False),
        'e_total_pontos': (dfs['ranking_equipes'], 'PONTOS MARCADOS', "EQUIPE", "Total de Pontos Marcados", "Pontos", True),
        'e_total_rebotes': (dfs['ranking_equipes'], 'TOTAL REB', "EQUIPE", "Total de Rebotes", "Rebotes", True),
        'e_total_assistencias': (dfs['ranking_equipes'], 'AST', "EQUIPE", "Total de Assistências", "AST", True),
    }
    params = map_stats.get(selected_stat)
    return criar_visual_ranking(*params) if params else "Selecione uma estatística."